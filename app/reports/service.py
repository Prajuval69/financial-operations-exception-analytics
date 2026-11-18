"""Professional offline reports from computed results, with safe atomic file output."""

import html
import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd
import plotly.express as px
import plotly.io as pio
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.styles import Alignment, Font, PatternFill

from app.domain.kpis import CATALOG
from app.domain.rules import RULES
from app.domain.time import now_iso, parse_date
from app.services.dictionary import data_dictionary

log = logging.getLogger(__name__)
PALETTE = ["#167d8d", "#203b59", "#d49c44", "#bf6258", "#83a9a4", "#78748c"]


def display_metric(code: str, value) -> str:
    if value is None:
        return "N/A"
    unit = CATALOG[code][1]
    if unit == "rate":
        return f"{value:.2%}"
    if unit == "hours":
        return f"{value:,.2f} h"
    if unit == "buckets":
        return "; ".join(f"{k}: {v}" for k, v in value.items())
    return f"{value:,}"


def findings(analytics: dict) -> list[str]:
    k = analytics["kpis"]["values"]
    return [
        f"{k['KPI001']:,} transaction rows include {k['KPI003']:,} unprocessed records.",
        f"{display_metric('KPI013', k['KPI013'])} of rows have exception history; {k['KPI030']:,} exceptions remain open.",
        f"The project data quality score is {display_metric('KPI014', k['KPI014'])}; completeness is {display_metric('KPI010', k['KPI010'])}.",
        f"SLA compliance is {display_metric('KPI022', k['KPI022'])}; {analytics['kpis']['context']['excluded_completed']:,} completed rows lack an eligible duration.",
        f"{k['KPI041']:,} remediation actions are overdue and {k['KPI051']:,} open risks meet the project high-risk threshold.",
    ]


def safe_cell(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def write_table(
    workbook: Workbook,
    name: str,
    rows: list[dict],
    headers: list[str] | None = None,
    high_risk_score: int = 12,
):
    sheet = workbook.create_sheet(name)
    keys = headers or (list(rows[0]) if rows else ["message"])
    sheet.append(keys)
    for row in rows:
        values = []
        for key in keys:
            value = row.get(key)
            if key.endswith(("_at", "_date")) and isinstance(value, str):
                value = parse_date(value) or value
            values.append(safe_cell(value))
        sheet.append(values)
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    sheet.sheet_view.showGridLines = False
    for cell in sheet[1]:
        cell.fill = PatternFill("solid", fgColor="203B59")
        cell.font = Font(color="FFFFFF", bold=True, size=11)
        cell.alignment = Alignment(vertical="center")
    sheet.row_dimensions[1].height = 26
    for index, key in enumerate(keys, 1):
        letter = sheet.cell(1, index).column_letter
        width = min(
            64,
            max(16, len(key) + 3, *[min(64, len(str(row.get(key, ""))) + 2) for row in rows[:100]]),
        )
        sheet.column_dimensions[letter].width = width
        for cell in list(sheet.columns)[index - 1][1:]:
            cell.font = Font(name="Calibri", size=11, color="203B59")
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            if isinstance(cell.value, datetime):
                cell.number_format = "yyyy-mm-dd hh:mm"
            elif key in {
                "completeness",
                "validity",
                "consistency",
                "timeliness",
                "score",
                "sla_compliance",
            }:
                cell.number_format = "0.00%"
            elif isinstance(cell.value, float):
                cell.number_format = "#,##0.00"
        if key == "severity" and len(rows):
            sheet.conditional_formatting.add(
                f"{letter}2:{letter}{sheet.max_row}",
                FormulaRule(
                    formula=[f'OR({letter}2="Critical",{letter}2="High")'],
                    fill=PatternFill("solid", fgColor="FCE2DB"),
                ),
            )
        if key == "risk_score" and len(rows):
            sheet.conditional_formatting.add(
                f"{letter}2:{letter}{sheet.max_row}",
                CellIsRule(
                    operator="greaterThanOrEqual",
                    formula=[high_risk_score],
                    fill=PatternFill("solid", fgColor="FCE2DB"),
                ),
            )
    return sheet


def output_paths(output_dir: Path, extension: str) -> tuple[Path, Path]:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    name = f"finops-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:8]}{extension}"
    final = output_dir / name
    fd, temporary = tempfile.mkstemp(prefix=".finops-", suffix=extension, dir=output_dir)
    os.close(fd)
    return Path(temporary), final


def generate_excel(analytics: dict, output_dir: Path) -> Path:
    book = Workbook()
    book.remove(book.active)
    context = analytics["kpis"]["context"]
    summary = [
        dict(section="Disclosure", detail="Synthetic data only; portfolio simulation."),
        dict(
            section="Reporting period", detail=f"{context['period_from']} to {context['period_to']}"
        ),
        dict(section="Simulation as-of", detail=context["as_of"]),
        dict(section="Generated at UTC", detail=now_iso()),
        dict(section="Filters", detail=json.dumps(context["filters"])),
        dict(section="Data refresh UTC", detail=context["refresh_timestamp"]),
    ]
    summary += [dict(section="Finding", detail=value) for value in findings(analytics)]
    summary += [
        dict(section="Recommendation", detail=r["title"] + ": " + r["action"])
        for r in analytics["recommendations"][:5]
    ]
    summary += [
        dict(section=metric["name"], detail=display_metric(metric["code"], metric["value"]))
        for metric in analytics["kpis"]["metrics"]
    ]
    critical = analytics["bundle"]["exceptions"]
    critical = critical[
        critical.severity.eq("Critical") & ~critical.status.isin(["Resolved", "Closed"])
    ]
    summary += [
        dict(section="Open critical item", detail=f"#{r.exception_id}: {r.rule_code} · {r.owner}")
        for r in critical.head(10).itertuples()
    ]
    write_table(book, "Executive Summary", summary)
    metrics = write_table(book, "KPI Summary", analytics["kpis"]["metrics"])
    for i, metric in enumerate(analytics["kpis"]["metrics"], 2):
        cell = metrics.cell(i, 5)
        if metric["unit"] == "rate":
            cell.number_format = "0.00%"
    write_table(
        book,
        "Data Quality",
        analytics["quality_by"]["source_system_id"]
        + [
            {"source_system_id": r["rule_code"], "rows": r["count"]}
            for r in analytics["rule_counts"]
        ],
        [
            "source_system_id",
            "completeness",
            "validity",
            "consistency",
            "timeliness",
            "score",
            "rows",
        ],
    )
    for key, title in [("exceptions", "Exceptions"), ("actions", "Actions"), ("risks", "Risks")]:
        frame = analytics["bundle"][key]
        write_table(
            book,
            title,
            frame.to_dict("records"),
            list(frame.columns),
            context["policy"]["high_risk_score"],
        )
    ops = write_table(
        book,
        "Operational Performance",
        analytics["trends"],
        ["day", "transactions", "exceptions", "backlog", "sla_compliance", "average_tat"],
    )
    if ops.max_row > 1:
        chart = BarChart()
        chart.title = "Daily transaction volume"
        chart.add_data(
            Reference(ops, min_col=2, min_row=1, max_row=ops.max_row), titles_from_data=True
        )
        chart.set_categories(Reference(ops, min_col=1, min_row=2, max_row=ops.max_row))
        chart.width, chart.height = 25, 10
        ops.add_chart(chart, "H2")
    sample = analytics["bundle"]["transactions"].drop(columns=["raw"]).head(1000)
    write_table(book, "Raw Processed Data Sample", sample.to_dict("records"), list(sample.columns))
    write_table(book, "Data Dictionary", data_dictionary())
    methodology = [
        dict(item="Policy", detail=json.dumps(context["policy"])),
        dict(
            item="Scope",
            detail="All data is synthetic. Cross-currency amounts are never summed. Empty denominators return N/A.",
        ),
        dict(
            item="Time",
            detail="Naive timestamps mean UTC. Simulation as-of drives elapsed calculations. Invalid or negative TAT is excluded from eligible completion metrics.",
        ),
        dict(
            item="History",
            detail="Exception rate includes resolved history. Rule counts list persisted history. Quality dimensions recompute current checks. Daily backlog is an origination cohort, not historical stock.",
        ),
        dict(
            item="Sample",
            detail="Raw Processed Data Sample contains at most 1,000 rows; other sheets contain all scoped exceptions/actions/risks.",
        ),
    ]
    methodology += [
        dict(item=code, detail=definition) for code, (_, _, definition) in CATALOG.items()
    ]
    methodology += [
        dict(
            item=r.code,
            detail=f"{r.entity}: {r.description}; severity {r.severity}; category {r.category}",
        )
        for r in RULES
    ]
    write_table(book, "Methodology", methodology)
    temp, final = output_paths(output_dir, ".xlsx")
    try:
        book.save(temp)
        temp.replace(final)
    finally:
        temp.unlink(missing_ok=True)
    log.info("excel report generated filename=%s", final.name)
    return final


def html_table(rows: list[dict], limit: int = 20) -> str:
    if not rows:
        return '<p class="muted">No records in this reporting scope.</p>'
    frame = pd.DataFrame(rows[:limit])
    for column in frame:
        if column in {
            "completeness",
            "validity",
            "consistency",
            "timeliness",
            "score",
            "sla_compliance",
        }:
            frame[column] = frame[column].map(
                lambda value: f"{value:.2%}" if pd.notna(value) else "N/A"
            )
        elif pd.api.types.is_float_dtype(frame[column]):
            frame[column] = frame[column].map(
                lambda value: f"{value:,.2f}" if pd.notna(value) else "N/A"
            )
    return frame.to_html(index=False, escape=True, border=0, classes="evidence") + (
        f"<p class='muted'>Showing {min(limit, len(rows))} of {len(rows)} records.</p>"
        if len(rows) > limit
        else ""
    )


def generate_executive(analytics: dict, output_dir: Path) -> Path:
    context = analytics["kpis"]["context"]
    esc = html.escape
    charts = []
    specs = [
        (analytics["trends"], "day", "transactions", "Transaction volume", "line"),
        (analytics["trends"], "day", "sla_compliance", "SLA compliance by origination day", "line"),
        (analytics["categories"], "category", "count", "Exception history by category", "bar"),
        (
            analytics["quality_by"]["source_system_id"],
            "source_system_id",
            "score",
            "Current quality score by source",
            "bar",
        ),
    ]
    for rows, x, y, title, kind in specs:
        if not rows:
            continue
        figure = (px.line if kind == "line" else px.bar)(
            pd.DataFrame(rows), x=x, y=y, title=title, color_discrete_sequence=PALETTE
        )
        figure.update_layout(
            template="plotly_white",
            height=330,
            margin=dict(l=35, r=20, t=60, b=45),
            font=dict(family="Arial", color="#203b59"),
            paper_bgcolor="#ffffff",
            showlegend=False,
        )
        if y in {"sla_compliance", "score"}:
            figure.update_yaxes(tickformat=".0%", range=[0, 1])
        charts.append(
            pio.to_html(
                figure,
                full_html=False,
                include_plotlyjs=True if not charts else False,
                config={"displayModeBar": False, "responsive": True},
            )
        )
    list_findings = "".join(f"<li>{esc(item)}</li>" for item in findings(analytics))
    recommendations = "".join(
        f"<li><strong>{esc(r['title'])}</strong><p>{esc(r['action'])} Evidence: {esc(r['metric_code'])} = {esc(str(r['observed_value']))}.</p></li>"
        for r in analytics["recommendations"]
    )
    scorecard = [
        {
            "KPI": m["name"],
            "Value": display_metric(m["code"], m["value"]),
            "Definition": m["definition"],
        }
        for m in analytics["kpis"]["metrics"]
    ]
    bundle = analytics["bundle"]
    sections = f"""
<section><h2>Executive Summary</h2><ul>{list_findings[:]}</ul></section>
<section><h2>Operational KPI Scorecard</h2>{html_table(scorecard, 30)}</section>
<section><h2>Data Quality Assessment</h2>{html_table(analytics["quality_by"]["source_system_id"])}<h3>Recurring control failures</h3>{html_table(analytics["rule_counts"])}</section>
<section><h2>Exception Analysis</h2>{html_table(analytics["categories"])}{html_table(analytics["root_causes"])}<h3>Open exception aging</h3>{html_table([{"bucket": k, "count": v} for k, v in analytics["kpis"]["values"]["KPI032"].items()])}</section>
<section><h2>Operational Trends</h2><div class="charts">{"".join(charts)}</div><h3>Processing teams</h3>{html_table(analytics["teams"])}<h3>Process stages</h3>{html_table(analytics["stages"])}</section>
<section><h2>Risks and Actions</h2>{html_table(bundle["risks"][["title", "owner", "risk_score", "status", "mitigation"]].to_dict("records"))}{html_table(bundle["actions"][["title", "owner", "due_date", "status"]].to_dict("records"))}</section>
<section><h2>Key Findings</h2><ul>{list_findings}</ul><p>These are observations of the synthetic dataset. Root-cause labels describe rule classes and are not proven causal findings.</p></section>
<section><h2>Recommendations</h2><ol>{recommendations or "<li>No recommendation thresholds triggered in this scope.</li>"}</ol><p class="muted">Rule-based analytical suggestions using project thresholds.</p></section>
<section><h2>Methodology</h2><p>Source: local SQLite, {esc(context["source"])}. Rates use row-level denominators and are recalculated after filtering. Completeness evaluates six mandatory fields. Validity includes reference integrity. Consistency and timeliness evaluate enabled transaction controls. Risk exposure sums ordinal probability × impact over open risks.</p><p>Simulation as-of: {esc(context["as_of"])}. Actual data refresh UTC: {esc(str(context["refresh_timestamp"]))}. Report generated UTC: {esc(now_iso())}.</p><p>Filter scope: {esc(json.dumps(context["filters"]))}</p><pre>{esc(json.dumps(context["policy"], indent=2))}</pre><details><summary>All KPI definitions</summary>{html_table(scorecard, 30)}</details></section>
<section><h2>Limitations</h2><p>All data is synthetic. This portfolio simulation does not represent a financial institution's systems or production policy. Thresholds and scoring weights are project assumptions. Amounts are compared within records; no cross-currency monetary total or FX conversion is provided. Invalid, missing and negative completion durations are excluded from eligible TAT/SLA denominators and disclosed in the scorecard context. Exception history includes resolved records. Daily backlog charts show current backlog by transaction origination day, not reconstructed historical backlog. Historical detections and remediation in the demo are explicitly simulated. This application has no authentication and is intended for trusted local use.</p></section>"""
    document = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Financial operations executive report</title>
<style>body{{background:#f2f4f3;color:#203b59;font:15px/1.6 Arial,sans-serif;margin:0}}main{{max-width:1120px;margin:auto;background:#fff;padding:50px 6%}}header{{border-bottom:3px solid #167d8d;padding-bottom:28px}}h1{{font-size:38px;line-height:1.15;max-width:850px}}h2{{font-size:25px;margin-top:40px}}h3{{font-size:18px}}.badge{{background:#e8f3ef;color:#146659;padding:7px 12px;display:inline-block;border-radius:4px;font-weight:bold}}.muted{{color:#647888;font-size:13px}}table{{width:100%;border-collapse:collapse;font-size:13px;margin:18px 0;display:block;overflow:auto}}th{{background:#203b59;color:#fff;text-align:left}}td,th{{padding:10px 12px;border-bottom:1px solid #dce3e5}}tr:nth-child(even){{background:#f6f8f8}}.charts{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}section{{break-inside:avoid}}li{{margin:10px 0}}pre{{overflow:auto;background:#f5f7f7;padding:20px}}@media(max-width:800px){{main{{padding:24px}}.charts{{grid-template-columns:1fr}}h1{{font-size:29px}}}}@media print{{body{{background:white}}main{{padding:20px}}.charts{{display:block}}section{{break-inside:auto}}h2{{break-after:avoid}}}}</style></head><body><main><header><span class="badge">SYNTHETIC OPERATIONS · MANAGEMENT REPORT</span><h1>Financial operations quality and exception review</h1><p>Reporting period: {esc(str(context["period_from"]))} — {esc(str(context["period_to"]))}</p></header>{sections}</main></body></html>"""
    temp, final = output_paths(output_dir, ".html")
    try:
        temp.write_text(document, encoding="utf-8")
        temp.replace(final)
    finally:
        temp.unlink(missing_ok=True)
    log.info("executive report generated filename=%s", final.name)
    return final
