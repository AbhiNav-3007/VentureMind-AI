"""
VentureMind AI — Financial Calculation Engine
=============================================
Pure Python math utilities for the Business & Finance Agent.
These provide deterministic results instead of relying entirely on LLM output
for numerical calculations.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BreakEvenResult:
    break_even_units: float
    break_even_revenue: float
    months_to_break_even: float
    gross_margin_percent: float
    formula_shown: str


@dataclass
class FinancialProjection:
    year: int
    revenue: float
    expenses: float
    profit: float
    customers: int
    mrr: float


@dataclass
class UnitEconomics:
    cac: float
    ltv: float
    ltv_cac_ratio: float
    payback_months: float
    gross_margin: float


def calculate_break_even(
    monthly_fixed_costs: float,
    price_per_unit: float,
    variable_cost_per_unit: float,
    monthly_units_sold: float = 0,
) -> BreakEvenResult:
    """
    Break-even analysis using the contribution margin method.

    Formula:
        Break-Even Units = Fixed Costs ÷ (Price − Variable Cost)
        Break-Even Revenue = Break-Even Units × Price
    """
    if price_per_unit <= variable_cost_per_unit:
        # Contribution margin is zero or negative — cannot break even
        return BreakEvenResult(
            break_even_units=float("inf"),
            break_even_revenue=float("inf"),
            months_to_break_even=float("inf"),
            gross_margin_percent=0.0,
            formula_shown="Cannot break even: Price ≤ Variable Cost",
        )

    contribution_margin = price_per_unit - variable_cost_per_unit
    gross_margin_pct = (contribution_margin / price_per_unit) * 100
    break_even_units = monthly_fixed_costs / contribution_margin
    break_even_revenue = break_even_units * price_per_unit
    months = (break_even_units / monthly_units_sold) if monthly_units_sold > 0 else 0

    formula = (
        f"FC({monthly_fixed_costs:,.0f}) ÷ "
        f"(P({price_per_unit:,.0f}) − VC({variable_cost_per_unit:,.0f})) "
        f"= {break_even_units:,.1f} units"
    )

    return BreakEvenResult(
        break_even_units=round(break_even_units, 1),
        break_even_revenue=round(break_even_revenue, 2),
        months_to_break_even=round(months, 1),
        gross_margin_percent=round(gross_margin_pct, 1),
        formula_shown=formula,
    )


def project_financials(
    year1_customers: int,
    avg_revenue_per_customer: float,
    monthly_fixed_costs: float,
    variable_cost_ratio: float = 0.25,
    year2_growth: float = 2.0,
    year3_growth: float = 2.5,
) -> list[FinancialProjection]:
    """
    Generate 3-year financial projections from basic parameters.

    Args:
        year1_customers: Number of paying customers at end of Year 1.
        avg_revenue_per_customer: Annual revenue per customer (₹).
        monthly_fixed_costs: Monthly fixed operating costs (₹).
        variable_cost_ratio: Variable cost as fraction of revenue (e.g. 0.25 = 25%).
        year2_growth: Multiplier for Year 2 customers (e.g. 2.0 = 2× Year 1).
        year3_growth: Multiplier for Year 3 customers (e.g. 2.5 = 2.5× Year 2).

    Returns:
        List of FinancialProjection for years 1, 2, 3.
    """
    projections = []
    customers = [
        year1_customers,
        int(year1_customers * year2_growth),
        int(year1_customers * year2_growth * year3_growth),
    ]
    annual_fixed = monthly_fixed_costs * 12

    for i, n_customers in enumerate(customers, start=1):
        revenue = n_customers * avg_revenue_per_customer
        variable_costs = revenue * variable_cost_ratio
        total_expenses = annual_fixed + variable_costs
        profit = revenue - total_expenses
        mrr = revenue / 12

        projections.append(FinancialProjection(
            year=i,
            revenue=round(revenue, 2),
            expenses=round(total_expenses, 2),
            profit=round(profit, 2),
            customers=n_customers,
            mrr=round(mrr, 2),
        ))

    return projections


def calculate_unit_economics(
    cac: float,
    monthly_revenue_per_customer: float,
    monthly_churn_rate: float = 0.02,
    gross_margin: float = 0.70,
) -> UnitEconomics:
    """
    Calculate unit economics including LTV and LTV/CAC ratio.

    LTV = (ARPU × Gross Margin) / Churn Rate
    Payback = CAC / (ARPU × Gross Margin)
    """
    if monthly_churn_rate <= 0:
        monthly_churn_rate = 0.001  # avoid div/0
    arpu_gm = monthly_revenue_per_customer * gross_margin
    ltv = arpu_gm / monthly_churn_rate
    ltv_cac = ltv / cac if cac > 0 else 0
    payback = cac / arpu_gm if arpu_gm > 0 else 0

    return UnitEconomics(
        cac=round(cac, 2),
        ltv=round(ltv, 2),
        ltv_cac_ratio=round(ltv_cac, 2),
        payback_months=round(payback, 1),
        gross_margin=round(gross_margin * 100, 1),
    )


def estimate_startup_costs(
    domain: str,
    team_size: int = 3,
    months: int = 12,
) -> dict[str, float]:
    """
    Domain-aware startup cost estimation (monthly INR values).
    Returns a cost breakdown dictionary.
    """
    # Base costs by headcount
    avg_salary = 80_000  # ₹80k/month per person
    salaries = team_size * avg_salary

    # Domain-specific multipliers for infra & compliance
    domain_multipliers = {
        "HealthTech": {"infra": 1.5, "compliance": 2.0, "marketing": 1.2},
        "FinTech": {"infra": 1.3, "compliance": 2.5, "marketing": 1.5},
        "EdTech": {"infra": 1.0, "compliance": 0.8, "marketing": 2.0},
        "AgriTech": {"infra": 0.8, "compliance": 0.7, "marketing": 1.5},
        "SaaS": {"infra": 1.2, "compliance": 0.6, "marketing": 1.3},
        "E-Commerce": {"infra": 1.0, "compliance": 1.0, "marketing": 2.5},
        "AI/ML": {"infra": 2.0, "compliance": 0.8, "marketing": 1.0},
        "CleanTech": {"infra": 1.2, "compliance": 1.5, "marketing": 1.2},
    }
    mults = domain_multipliers.get(domain, {"infra": 1.0, "compliance": 1.0, "marketing": 1.0})

    base_infra = 30_000
    base_compliance = 15_000
    base_marketing = 50_000

    costs = {
        "salaries": round(salaries, 2),
        "cloud_infrastructure": round(base_infra * mults["infra"], 2),
        "compliance_legal": round(base_compliance * mults["compliance"], 2),
        "marketing_sales": round(base_marketing * mults["marketing"], 2),
        "office_operations": 25_000,
        "tools_subscriptions": 15_000,
        "miscellaneous": 10_000,
    }
    costs["total_monthly"] = round(sum(costs.values()), 2)
    costs["total_annual"] = round(costs["total_monthly"] * 12, 2)
    costs["burn_rate_months"] = months
    costs["total_runway_cost"] = round(costs["total_monthly"] * months, 2)
    return costs


def format_inr(amount: float) -> str:
    """Format a number as Indian currency string."""
    if amount >= 1_00_00_000:  # 1 crore
        return f"₹{amount / 1_00_00_000:.2f} Cr"
    elif amount >= 1_00_000:   # 1 lakh
        return f"₹{amount / 1_00_000:.2f} L"
    else:
        return f"₹{amount:,.0f}"
