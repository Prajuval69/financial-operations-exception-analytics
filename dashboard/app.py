"""Local dashboard. Business rules and mutations are shared with the API services."""

import sys
from datetime import datetime
from pathlib import Path

# Streamlit executes the script by path; allow an editable install or source checkout.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
from sqlalchemy import select

from app.api.schemas import ActionCreate, ActionPatch, ExceptionPatch, RiskCreate, RiskPatch
from app.core.config import get_settings
from app.db.models import DatasetMeta, Reference
from app.db.session import init_db, make_engine, session_scope
from app.domain.kpis import CATALOG, enriched_transactions
from app.domain.time import age_days, aging_bucket
from app.reports.service import (
    PALETTE,
    display_metric,
    findings,
    generate_excel,
    generate_executive,
)
from app.services.analytics import build_analytics, grouped_counts
from app.services.query import Filters
from app.services.validation import run_validation
from app.services.workflow import (
    TRANSITIONS,
    create_action,
    create_risk,
    update_action,
    update_exception,
    update_risk,
)

PAGES = [
    "Executive Overview",
    "Data Quality",
    "Operational Performance",
    "Exceptions",
    "Actions & Risks",
    "Recommendations",
]


@st.cache_resource
def database_engine(url: str):
    policy = get_settings().model_copy(update={"database_url": url})
    engine = make_engine(policy)
    init_db(engine)
    return engine


def chart(rows, x: str, y: str, title: str, kind: str = "bar", percent: bool = False):
    st.subheader(title)
    if not len(rows):
        st.info("No observations in the selected scope.")
        return
    frame = pd.DataFrame(rows)
    builder = {"bar": px.bar, "line": px.line, "histogram": px.histogram}[kind]
    args = {"x": x, "color_discrete_sequence": PALETTE}
    if kind != "histogram":
        args["y"] = y
    figure = builder(frame, **args)
    figure.update_layout(
        height=320,
        margin=dict(l=15, r=15, t=15, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#203b59"),
        xaxis_title=None,
        yaxis_title=None,
        showlegend=False,
    )
    figure.update_xaxes(showgrid=False)
    figure.update_yaxes(gridcolor="#dce5e8")
    if percent:
        figure.update_yaxes(tickformat=".0%", range=[0, 1])
    if kind == "line":
        figure.update_traces(connectgaps=False)
    st.plotly_chart(figure, use_container_width=True)


def metric_cards(analytics: dict, codes: list[str]) -> None:
    values, context = analytics["kpis"]["values"], analytics["kpis"]["context"]
    for offset in range(0, len(codes), 4):
        columns = st.columns(min(4, len(codes) - offset))
        for col, code in zip(columns, codes[offset : offset + 4], strict=False):
            name, _, definition = CATALOG[code]
            col.metric(
                "Data Quality Score" if code == "KPI014" else name,
                display_metric(code, values[code]),
                help=f"{definition}\nSource: SQLite synthetic records. Simulation as-of {context['as_of']}. Current sidebar filters apply; refreshed {context['refresh_timestamp']} UTC.",
            )


def pareto_chart(rows: list[dict]) -> None:
    st.subheader("Rule failure Pareto (persisted history)")
    if not rows:
        st.info("No rule failures in this scope.")
        return
    frame = pd.DataFrame(rows)
    frame["cumulative_rate"] = frame["count"].cumsum() / frame["count"].sum()
    figure = make_subplots(specs=[[{"secondary_y": True}]])
    figure.add_trace(
        go.Bar(x=frame.rule_code, y=frame["count"], name="Failures", marker_color=PALETTE[0])
    )
    figure.add_trace(
        go.Scatter(
            x=frame.rule_code,
            y=frame.cumulative_rate,
            name="Cumulative share",
            line_color=PALETTE[2],
        ),
        secondary_y=True,
    )
    figure.update_layout(
        height=320,
        margin=dict(l=10, r=15, t=15, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h"),
    )
    figure.update_yaxes(tickformat=".0%", range=[0, 1], secondary_y=True)
    st.plotly_chart(figure, use_container_width=True)


def table_and_download(frame: pd.DataFrame, filename: str) -> None:
    if frame.empty:
        st.info("No records match these filters.")
        return
    st.caption(
        f"{len(frame):,} matching records · displaying up to 1,000; CSV includes all matches"
    )
    st.dataframe(frame.head(1000), use_container_width=True, hide_index=True)
    # Escape potential spreadsheet formulas in exported source strings.
    safe = frame.copy()
    for column in safe.select_dtypes(include="object"):
        safe[column] = safe[column].map(
            lambda value: (
                "'" + value
                if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@"))
                else value
            )
        )
    st.download_button(
        "Download filtered CSV",
        safe.to_csv(index=False).encode("utf-8"),
        filename,
        "text/csv",
        key=filename,
    )


def exception_editor(engine, frame: pd.DataFrame) -> None:
    if frame.empty:
        return
    with st.expander("Manage an exception"):
        selected = st.selectbox(
            "Exception ID", frame.exception_id.tolist(), key="exception_selection"
        )
        item = frame[frame.exception_id.eq(selected)].iloc[0]
        st.write(f"**{item.rule_code} · {item.severity} · {item.root_cause}**")
        st.write(item.description)
        st.caption(
            f"Detected {item.detected_at}; due {item.due_date}; source row {item.source_record_id}"
        )
        with st.form("exception_update"):
            owner = st.text_input("Owner", value=item.owner or "")
            status = st.selectbox("Status", [item.status, *sorted(TRANSITIONS[item.status])])
            priority = st.selectbox(
                "Priority",
                ["P1", "P2", "P3", "P4"],
                index=["P1", "P2", "P3", "P4"].index(item.priority),
            )
            notes = st.text_area("Resolution notes", value=item.resolution_notes or "")
            if st.form_submit_button("Save exception", type="primary"):
                try:
                    with session_scope(engine) as session:
                        update_exception(
                            session,
                            int(selected),
                            ExceptionPatch(
                                owner=owner,
                                status=status,
                                priority=priority,
                                resolution_notes=notes,
                            ),
                        )
                    st.success("Exception updated.")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))


def workflow_forms(
    engine, actions: pd.DataFrame, risks: pd.DataFrame, exceptions: pd.DataFrame
) -> None:
    with st.expander("Create remediation action"):
        with st.form("action_create"):
            title = st.text_input("Action title")
            owner = st.text_input("Action owner", value="Control Desk")
            description = st.text_area("Action description")
            linked = st.selectbox(
                "Related exception",
                [None, *exceptions.exception_id.tolist()],
                format_func=lambda v: "Unlinked" if v is None else f"Exception #{v}",
            )
            due = st.date_input("Action due date", datetime(2026, 10, 7).date())
            if st.form_submit_button("Create action"):
                try:
                    with session_scope(engine) as session:
                        create_action(
                            session,
                            ActionCreate(
                                title=title,
                                owner=owner,
                                description=description,
                                exception_id=linked,
                                due_date=datetime.combine(due, datetime.max.time()),
                            ),
                        )
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))
    if not actions.empty:
        with st.expander("Update an action"):
            selected = st.selectbox("Action ID", actions.action_id.tolist())
            item = actions[actions.action_id.eq(selected)].iloc[0]
            with st.form("action_update"):
                status = st.selectbox(
                    "Action status",
                    ["Open", "In Progress", "Blocked", "Completed", "Cancelled"],
                    index=["Open", "In Progress", "Blocked", "Completed", "Cancelled"].index(
                        item.status
                    ),
                )
                owner = st.text_input("Update action owner", value=item.owner)
                dependency = st.selectbox(
                    "Dependency",
                    [None, *actions.action_id.tolist()],
                    index=(
                        [None, *actions.action_id.tolist()].index(int(item.dependency))
                        if pd.notna(item.dependency)
                        else 0
                    ),
                )
                if st.form_submit_button("Save action"):
                    try:
                        with session_scope(engine) as session:
                            update_action(
                                session,
                                int(selected),
                                ActionPatch(status=status, owner=owner, dependency=dependency),
                            )
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))
    with st.expander("Create an operational risk"):
        with st.form("risk_create"):
            title = st.text_input("Risk title")
            owner = st.text_input("Risk owner", value="Control Desk")
            probability = st.slider("Probability (project scale)", 1, 5, 3)
            impact = st.slider("Impact (project scale)", 1, 5, 3)
            mitigation = st.text_area("Mitigation")
            linked_ex = st.selectbox(
                "Risk related exception", [None, *exceptions.exception_id.tolist()]
            )
            linked_action = st.selectbox("Mitigation action", [None, *actions.action_id.tolist()])
            due = st.date_input("Risk due date", datetime(2026, 10, 14).date())
            if st.form_submit_button("Create risk"):
                try:
                    with session_scope(engine) as session:
                        create_risk(
                            session,
                            RiskCreate(
                                title=title,
                                owner=owner,
                                probability=probability,
                                impact=impact,
                                mitigation=mitigation,
                                related_exception_id=linked_ex,
                                action_id=linked_action,
                                due_date=datetime.combine(due, datetime.max.time()),
                            ),
                        )
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))
    if not risks.empty:
        with st.expander("Update a risk"):
            selected = st.selectbox("Risk ID", risks.risk_id.tolist())
            item = risks[risks.risk_id.eq(selected)].iloc[0]
            with st.form("risk_update"):
                status = st.selectbox(
                    "Risk status",
                    ["Open", "Mitigating", "Closed"],
                    index=["Open", "Mitigating", "Closed"].index(item.status),
                )
                mitigation = st.text_area("Update mitigation", value=item.mitigation)
                if st.form_submit_button("Save risk"):
                    try:
                        with session_scope(engine) as session:
                            update_risk(
                                session,
                                int(selected),
                                RiskPatch(status=status, mitigation=mitigation),
                            )
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))


def render_page(page: str, analytics: dict, engine, policy) -> None:
    bundle = analytics["bundle"]
    if page == "Executive Overview":
        metric_cards(
            analytics, ["KPI001", "KPI013", "KPI014", "KPI022", "KPI030", "KPI031", "KPI041"]
        )
        left, right = st.columns(2)
        with left:
            chart(analytics["trends"], "day", "transactions", "Transaction volume", "line")
            chart(
                analytics["trends"],
                "day",
                "sla_compliance",
                "SLA compliance by origination day",
                "line",
                True,
            )
        with right:
            chart(analytics["trends"], "day", "exceptions", "Rows with exception history", "line")
            chart(analytics["categories"], "category", "count", "Exception history by category")
        st.subheader("Management readout")
        for finding in findings(analytics):
            st.write("• " + finding)
    elif page == "Data Quality":
        metric_cards(analytics, ["KPI010", "KPI011", "KPI012", "KPI014"])
        cols = st.columns(2)
        dims = analytics["kpis"]["dimensions"]
        cols[0].metric(
            "Consistency",
            f"{dims['consistency']:.2%}" if dims["consistency"] is not None else "N/A",
        )
        cols[1].metric(
            "Timeliness", f"{dims['timeliness']:.2%}" if dims["timeliness"] is not None else "N/A"
        )
        with cols[0]:
            chart(
                analytics["quality_by"]["source_system_id"],
                "source_system_id",
                "score",
                "Quality by source",
                percent=True,
            )
            pareto_chart(analytics["rule_counts"])
        with cols[1]:
            chart(
                analytics["quality_by"]["business_unit_id"],
                "business_unit_id",
                "score",
                "Quality by business unit",
                percent=True,
            )
            chart(
                analytics["quality_by"]["day"],
                "day",
                "score",
                "Current quality by origination day",
                "line",
                True,
            )
        st.caption(
            "Current quality recomputes enabled checks. Persisted failure history includes reviewed/resolved exceptions. Weights are project methodology."
        )
        table_and_download(pd.DataFrame(analytics["rule_counts"]), "rule_failures.csv")
    elif page == "Operational Performance":
        metric_cards(analytics, ["KPI020", "KPI021", "KPI022", "KPI003", "KPI023"])
        enriched = enriched_transactions(bundle["transactions"], policy)
        left, right = st.columns(2)
        with left:
            chart(
                enriched[enriched.eligible],
                "tat_hours",
                "",
                "Eligible completed TAT (hours)",
                "histogram",
            )
            chart(
                analytics["trends"], "day", "backlog", "Current backlog by origination day", "line"
            )
        with right:
            chart(
                analytics["teams"],
                "team",
                "sla_compliance",
                "SLA by operational team",
                percent=True,
            )
            chart(
                analytics["stages"],
                "stage",
                "average_minutes",
                "Process-stage average duration (minutes)",
            )
        st.caption(
            f"{analytics['kpis']['context']['excluded_completed']:,} Completed rows excluded from TAT/SLA due to missing, invalid or negative duration. Backlog chart is a current cohort view."
        )
        table_and_download(pd.DataFrame(analytics["teams"]), "team_performance.csv")
    elif page == "Exceptions":
        ex = bundle["exceptions"].copy()
        columns = st.columns(3)
        fields = ["status", "severity", "priority", "category", "owner", "root_cause"]
        for i, field in enumerate(fields):
            options = sorted(ex[field].dropna().unique().tolist())
            selected = columns[i % 3].multiselect(
                field.replace("_", " ").title(), options, key="ex_" + field
            )
            if selected:
                ex = ex[ex[field].isin(selected)]
        dates = st.date_input("Detection date range", value=(), key="exception_dates")
        if isinstance(dates, tuple) and len(dates) == 2:
            times = pd.to_datetime(ex.detected_at, utc=True, format="ISO8601").dt.date
            ex = ex[times.ge(dates[0]) & times.le(dates[1])]
        if not ex.empty:
            ex["age_days"] = ex.detected_at.map(
                lambda date: round(age_days(date, bundle["as_of"]), 1)
            )
        leading = [
            "exception_id",
            "status",
            "severity",
            "priority",
            "rule_code",
            "category",
            "owner",
            "age_days",
            "due_date",
            "root_cause",
            "description",
        ]
        leading = [c for c in leading if c in ex]
        table_and_download(ex[leading + [c for c in ex if c not in leading]], "exceptions.csv")
        open_ex = ex[~ex.status.isin(["Resolved", "Closed"])]
        aging = open_ex.detected_at.map(
            lambda value: aging_bucket(age_days(value, bundle["as_of"]), policy.aging_days)
        ).value_counts()
        left, right = st.columns(2)
        with left:
            chart(
                [{"bucket": key, "count": value} for key, value in aging.items()],
                "bucket",
                "count",
                "Open exception aging",
            )
        with right:
            chart(
                grouped_counts(ex, "root_cause"),
                "root_cause",
                "count",
                "Rule-based root-cause classification",
            )
        chart(
            grouped_counts(ex, "rule_code")[:10],
            "rule_code",
            "count",
            "Top recurring validation rules",
        )
        exception_editor(engine, ex)
    elif page == "Actions & Risks":
        metric_cards(analytics, ["KPI040", "KPI041", "KPI042", "KPI050", "KPI051", "KPI052"])
        st.subheader("Remediation actions")
        actions = bundle["actions"].sort_values("due_date")
        table_and_download(actions, "actions.csv")
        st.subheader("Operational risks")
        risks = bundle["risks"].sort_values("risk_score", ascending=False)
        table_and_download(risks, "risks.csv")
        upcoming = actions[~actions.status.isin(["Completed", "Cancelled"])]
        st.subheader("Upcoming and overdue deadlines")
        st.dataframe(
            upcoming[["action_id", "title", "owner", "due_date", "status"]].head(20),
            hide_index=True,
            use_container_width=True,
        )
        workflow_forms(engine, actions, risks, bundle["exceptions"])
    else:
        st.caption(
            "Analytical suggestions derived from observed metrics and documented project thresholds."
        )
        if not analytics["recommendations"]:
            st.success("No recommendation thresholds triggered in this scope.")
        for recommendation in analytics["recommendations"]:
            st.subheader(f"{recommendation['priority']} · {recommendation['title']}")
            st.write(recommendation["action"])
            code = recommendation["metric_code"]
            value = recommendation["observed_value"]
            st.caption(
                f"Evidence: {code} · observed {display_metric(code, value) if code != 'KPI032' else str(value) + ' exceptions >30 days'} · as-of {recommendation['basis']}"
            )


def main() -> None:
    st.set_page_config(
        page_title="Financial Operations | Quality & Exceptions", page_icon="◈", layout="wide"
    )
    st.markdown(
        """<style>.block-container{padding-top:2rem;max-width:1560px}h1{letter-spacing:-.035em}div[data-testid="stMetric"]{background:white;border-top:3px solid #167d8d;padding:18px 20px;border-radius:4px;margin-bottom:12px}div[data-testid="stMetricValue"]{font-size:1.9rem}section[data-testid="stSidebar"]{border-right:1px solid #dce5e8}h3{font-size:1.05rem!important}button{font-weight:600!important}</style>""",
        unsafe_allow_html=True,
    )
    policy = get_settings()
    engine = database_engine(policy.database_url)
    st.sidebar.title("Financial Ops")
    st.sidebar.caption("QUALITY & EXCEPTION ANALYTICS")
    page = st.sidebar.radio("Workspace", PAGES, label_visibility="collapsed")
    st.sidebar.divider()
    st.sidebar.subheader("Reporting scope")
    with session_scope(engine) as session:
        refs = [
            {"kind": r.kind, "code": r.code, "label": r.label}
            for r in session.scalars(select(Reference))
        ]
        meta = session.get(DatasetMeta, 1)
        as_of = meta.as_of if meta else None
    choices = {}
    for kind, title in [
        ("business_unit_id", "Business unit"),
        ("team_id", "Team"),
        ("source_system_id", "Source system"),
    ]:
        labels = {r["code"]: f"{r['code']} · {r['label']}" for r in refs if r["kind"] == kind}
        choices[kind] = st.sidebar.selectbox(
            title,
            [None, *labels],
            format_func=lambda code, labels=labels: "All" if code is None else labels[code],
        )
    date_range = st.sidebar.date_input(
        "Transaction date range",
        value=(),
        help="Leave empty for all rows, including missing/invalid dates.",
    )
    date_from, date_to = (
        (date_range[0].isoformat(), date_range[1].isoformat())
        if isinstance(date_range, tuple) and len(date_range) == 2
        else (None, None)
    )
    scope = Filters(
        business_unit=choices["business_unit_id"],
        team=choices["team_id"],
        source_system=choices["source_system_id"],
        date_from=date_from,
        date_to=date_to,
    )
    if st.sidebar.button("Refresh data", use_container_width=True):
        st.rerun()
    if st.sidebar.button("Run validation", use_container_width=True):
        with session_scope(engine) as session:
            result = run_validation(session, policy)
        st.sidebar.success(f"{result['new_exceptions']:,} new exceptions")
    st.sidebar.caption(
        "Synthetic data only. Configurable portfolio methodology; no financial institution policy is implied."
    )
    st.title(page)
    st.caption(
        f"Financial Operations Data Quality & Exception Analytics · simulation as-of {as_of or 'not seeded'}"
    )
    try:
        with session_scope(engine) as session:
            analytics = build_analytics(session, policy, scope)
        context = analytics["kpis"]["context"]
        st.caption(
            f"Data refresh: {context['refresh_timestamp'] or 'N/A'} UTC · period {context['period_from'] or 'N/A'} to {context['period_to'] or 'N/A'} · SQLite synthetic records"
        )
        if analytics["kpis"]["values"]["KPI001"] == 0:
            st.info("No transactions in this scope. Adjust filters or run: python -m app.cli demo")
        render_page(page, analytics, engine, policy)
        with st.expander("KPI definitions and reporting context"):
            st.dataframe(
                pd.DataFrame(analytics["kpis"]["metrics"]).drop(columns=["value"]),
                hide_index=True,
                use_container_width=True,
            )
            st.json(context)
        with st.expander("Export management reports"):
            kind = st.radio("Report format", ["Excel workbook", "Executive HTML"], horizontal=True)
            if st.button("Generate scoped report"):
                path = (generate_excel if kind == "Excel workbook" else generate_executive)(
                    analytics, policy.output_dir
                )
                st.session_state["report_download"] = {
                    "data": path.read_bytes(),
                    "name": path.name,
                    "filters": vars(scope),
                }
            saved = st.session_state.get("report_download")
            if saved and saved["filters"] == vars(scope):
                st.download_button(
                    "Download report", saved["data"], saved["name"], key="report_download_button"
                )
    except Exception as error:
        import logging

        logging.getLogger(__name__).error("dashboard load failed type=%s", type(error).__name__)
        st.error(
            "Could not load this view. Check local logs and database configuration, then refresh."
        )


if __name__ == "__main__":
    main()
