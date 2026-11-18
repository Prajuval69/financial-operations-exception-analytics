from app.core.config import Settings


def calculate_priority(
    severity: str,
    age: float,
    amount: float | None,
    sla_breached: bool,
    impact: str,
    policy: Settings,
) -> str:
    """Portfolio policy: severity plus bounded age/value/SLA/impact escalation."""
    base = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}[severity]
    escalation = int(age >= policy.priority_age_days) + int(sla_breached)
    escalation += int(amount is not None and amount > policy.high_value_threshold)
    escalation += int(impact == "Material reporting risk")
    score = min(4, base + min(2, escalation))
    return {4: "P1", 3: "P2", 2: "P3", 1: "P4"}[score]
