#!/usr/bin/env python3
"""Extract and normalize the PROPERTIES array from index.html into data/properties.json."""

import json
import re
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_nested(obj, *keys, default=None):
    for k in keys:
        if isinstance(obj, dict) and k in obj:
            return obj[k]
    return default


def first_price(p):
    ph = p.get("price_history", [])
    if ph:
        return ph[0].get("price") or ph[0].get("list_price")
    return (
        p.get("price")
        or get_nested(p, "listing", default={}).get("list_price")
        or get_nested(p, "financials", default={}).get("purchase_price")
        or get_nested(p, "investment_analysis", default={}).get("purchase_price")
    )


def make_slug(p):
    slug = p.get("slug") or p.get("id")
    if slug:
        return slug
    addr = p["address"].lower()
    addr = re.sub(r"[^a-z0-9]+", "-", addr).strip("-")
    return addr


def normalize_monthly_costs(p):
    """Extract monthly costs into canonical dict from any schema variant."""
    ia = p.get("investment_analysis", {})
    fin = p.get("financials", {})
    top_mc = p.get("monthly_costs", {})
    ia_mc = ia.get("monthly_costs", {})

    mc = {}

    mc["mortgage_pi"] = (
        ia_mc.get("mortgage_pi")
        or ia.get("monthly_mortgage_pi")
        or ia.get("monthly_pi")
        or ia.get("mortgage_pi_monthly")
        or fin.get("monthly_pi")
        or top_mc.get("mortgage_pi")
    )

    mc["property_tax"] = (
        ia_mc.get("property_tax")
        or ia.get("monthly_property_tax")
        or ia.get("property_tax_monthly")
        or fin.get("monthly_tax")
        or top_mc.get("property_tax")
    )

    mc["hoa"] = (
        ia_mc.get("hoa")
        or ia.get("monthly_hoa")
        or ia.get("hoa_monthly")
        or fin.get("monthly_hoa")
        or top_mc.get("hoa")
    )

    mc["insurance"] = (
        ia_mc.get("insurance")
        or ia_mc.get("insurance_fl_1pt5pct")
        or ia.get("monthly_insurance")
        or ia.get("insurance_monthly")
        or fin.get("monthly_insurance")
        or top_mc.get("insurance")
    )

    mc["maintenance_reserve"] = (
        ia_mc.get("maintenance_reserve")
        or ia_mc.get("maintenance")
        or ia.get("monthly_maintenance")
        or ia.get("maintenance_monthly")
        or fin.get("monthly_maintenance")
        or top_mc.get("maintenance_reserve")
        or top_mc.get("maintenance")
        or 300
    )

    mc["capex"] = (
        ia_mc.get("capex")
        or ia_mc.get("capex_reserve")
        or ia.get("monthly_capex")
        or ia.get("capex_monthly")
        or fin.get("monthly_capex")
        or top_mc.get("capex")
        or 200
    )

    mc["property_management"] = (
        ia_mc.get("property_management")
        or ia_mc.get("property_management_ltr")
        or ia.get("monthly_property_management")
        or ia.get("property_management_monthly")
        or fin.get("monthly_mgmt")
        or top_mc.get("property_management")
        or 0
    )

    return {k: v for k, v in mc.items() if v is not None}


def normalize_rental_comps(p):
    ia = p.get("investment_analysis", {})
    ra = p.get("rental_analysis", {})
    ltr = ra.get("ltr", {})

    comps = (
        ia.get("rental_comps")
        or ltr.get("comparable_rentals")
        or p.get("rental_comps")
        or p.get("comparables")
    )
    if not comps:
        return []

    normalized = []
    for c in comps:
        normalized.append({
            "source": c.get("source", ""),
            "address": c.get("address", ""),
            "rent": c.get("rent"),
            "beds": c.get("beds") or c.get("bedrooms"),
            "sqft": c.get("sqft"),
            "days_listed": c.get("days_listed"),
        })
    return normalized


def normalize_str_analysis(p):
    ia = p.get("investment_analysis", {})
    ra = p.get("rental_analysis", {})

    str_a = ia.get("str_analysis", {})
    str_ra = ra.get("str", {})

    if str_a:
        return {
            "eligible": str_a.get("eligible", False),
            "assumed_nightly_rate": str_a.get("assumed_nightly_rate"),
            "assumed_nights_per_month": str_a.get("assumed_nights_per_month"),
            "estimated_monthly_revenue": str_a.get("estimated_monthly_revenue"),
            "estimated_monthly_cash_flow": str_a.get("estimated_monthly_cash_flow"),
        }

    if str_ra:
        return {
            "eligible": str_ra.get("eligible", False),
            "assumed_nightly_rate": str_ra.get("assumed_nightly_rate"),
            "assumed_nights_per_month": str_ra.get("assumed_occupied_nights_per_month"),
            "estimated_monthly_revenue": str_ra.get("estimated_monthly_revenue"),
            "estimated_monthly_cash_flow": str_ra.get("monthly_cash_flow"),
        }

    if ia.get("str_eligible") or p.get("str_eligible"):
        return {
            "eligible": ia.get("str_eligible") or p.get("str_eligible", False),
            "assumed_nightly_rate": ia.get("str_avg_nightly_rate"),
            "assumed_nights_per_month": ia.get("str_occupied_nights_per_month") or ia.get("str_assumed_occupied_nights_per_month"),
            "estimated_monthly_revenue": ia.get("str_monthly_revenue"),
            "estimated_monthly_cash_flow": ia.get("str_monthly_cash_flow") or ia.get("str_cash_flow"),
        }

    str_scen = p.get("str_scenario")
    if isinstance(str_scen, dict):
        return {
            "eligible": str_scen.get("eligible", False),
            "assumed_nightly_rate": str_scen.get("assumed_nightly_rate"),
            "assumed_nights_per_month": str_scen.get("assumed_occupied_nights_per_month"),
            "estimated_monthly_revenue": str_scen.get("estimated_monthly_revenue"),
            "estimated_monthly_cash_flow": str_scen.get("monthly_cash_flow") or str_scen.get("estimated_monthly_cash_flow"),
        }

    return {"eligible": False}


def normalize_climate_risks(p):
    ld = p.get("listing_details", {})
    cr = ld.get("climate_risks", {})

    if not cr:
        listing = p.get("listing", {})
        cr = listing.get("climate_risks", {})

    if not cr:
        climate = p.get("climate_risk", {})
        if isinstance(climate, dict):
            cr = climate

    if not cr:
        return {}
    normalized = {}
    for k, v in cr.items():
        if isinstance(v, dict):
            normalized[k] = v.get("label", str(v.get("score", "")))
        else:
            normalized[k] = str(v)
    return normalized


def normalize_deal_score_breakdown(p):
    ia = p.get("investment_analysis", {})
    dsb = ia.get("deal_score_breakdown") or p.get("deal_score_breakdown") or {}

    da = p.get("deal_analysis", {})
    if da and not dsb:
        dsb = da.get("deal_score_breakdown", {})

    return dsb


def normalize_property(p):
    ia = p.get("investment_analysis", {})
    ld = p.get("listing_details", {})
    fin = p.get("financials", {})
    listing = p.get("listing", {})
    ra = p.get("rental_analysis", {})
    ltr = ra.get("ltr", {})

    monthly_costs = normalize_monthly_costs(p)

    total_monthly = (
        ia.get("total_monthly_cost")
        or ia.get("total_monthly_cost_base")
        or ia.get("total_monthly_cost_ltr")
        or ia.get("total_monthly_cost_self_managed")
        or fin.get("monthly_total_cost")
        or p.get("monthly_costs", {}).get("total")
        or p.get("monthly_costs", {}).get("total_monthly")
        or ia.get("monthly_costs", {}).get("total")
        or ia.get("monthly_costs", {}).get("total_monthly")
    )
    if not total_monthly and monthly_costs:
        total_monthly = sum(v for v in monthly_costs.values() if isinstance(v, (int, float)))

    break_even_gross = (
        ia.get("break_even_rent_gross")
        or ia.get("break_even_gross")
        or ia.get("break_even_rent")
        or ia.get("break_even_rent_base")
        or ltr.get("break_even_gross")
        or p.get("break_even_rent")
    )

    break_even_vac = (
        ia.get("break_even_rent_vacancy_adjusted")
        or ia.get("break_even_vacancy_adjusted")
        or ltr.get("break_even_vacancy_adjusted")
    )

    raw_cf = ia.get("cash_flow")
    if isinstance(raw_cf, dict):
        cash_flow = raw_cf.get("vs_total_cost") or raw_cf.get("vs_break_even") or raw_cf.get("monthly_shortfall")
    else:
        cash_flow = raw_cf

    ltr_scenario = ia.get("ltr_scenario", {})
    cash_flow = next((v for v in [
        ia.get("monthly_cash_flow_estimate"),
        ia.get("monthly_cash_flow"),
        cash_flow,
        ia.get("est_cash_flow_monthly"),
        ia.get("cash_flow_monthly"),
        ia.get("cash_flow_base"),
        ia.get("cash_flow_gross"),
        ia.get("cash_flow_gross_no_flood"),
        ia.get("cash_flow_main_only"),
        ia.get("cash_flow_all_units"),
        ltr.get("cash_flow_monthly"),
        ltr.get("monthly_cash_flow"),
        ltr.get("monthly_cash_flow_at_target"),
        p.get("cash_flow_monthly"),
        ltr_scenario.get("monthly_cash_flow_self_managed"),
        ltr_scenario.get("monthly_cash_flow_with_pm"),
        ltr_scenario.get("monthly_cash_flow"),
    ] if v is not None), None)

    cash_flow_assessment = (
        ia.get("cash_flow_assessment")
        or ia.get("cash_flow_tier")
        or ltr.get("cash_flow_tier")
        or p.get("cash_flow_tier")
    )
    if cash_flow_assessment and "negative" in str(cash_flow_assessment).lower():
        cash_flow_assessment = "cash-flow negative"
    elif cash_flow_assessment and ("positive" in str(cash_flow_assessment).lower()):
        cash_flow_assessment = "cash-flow positive"
    elif cash_flow_assessment and ("break" in str(cash_flow_assessment).lower() or "near" in str(cash_flow_assessment).lower()):
        cash_flow_assessment = "near break-even"
    elif cash_flow is not None:
        if cash_flow > 0:
            cash_flow_assessment = "cash-flow positive"
        elif cash_flow >= -300:
            cash_flow_assessment = "near break-even"
        else:
            cash_flow_assessment = "cash-flow negative"

    avg_rent = (
        ia.get("avg_market_rent")
        or ia.get("avg_market_rent_all_units")
        or ia.get("avg_market_rent_main_only")
        or ia.get("market_rent_used")
        or ltr.get("estimated_monthly_rent")
        or p.get("avg_market_rent")
        or ltr_scenario.get("estimated_rent")
    )

    purchase_price = (
        ia.get("purchase_price")
        or ia.get("list_price")
        or fin.get("purchase_price")
        or listing.get("list_price")
        or first_price(p)
    )

    down_payment = (
        ia.get("down_payment")
        or ia.get("down_payment_amt")
        or ia.get("down_payment_usd")
        or fin.get("down_payment")
    )
    if not down_payment and purchase_price:
        down_payment = int(purchase_price * 0.2)

    loan_amount = (
        ia.get("loan_amount")
        or fin.get("loan_amount")
        or get_nested(p, "investment_inputs", default={}).get("loan_amount")
    )

    ppsf = (
        ia.get("price_per_sqft")
        or p.get("price_per_sqft")
        or listing.get("price_per_sqft")
        or ia.get("property_ppsf")
    )

    nbhd_ppsf = (
        ia.get("neighborhood_avg_ppsf")
        or p.get("neighborhood_avg_ppsf")
        or p.get("neighborhood_avg_ppsf_est")
    )

    ppsf_vs = (
        ia.get("ppsf_vs_avg_pct")
        or ia.get("ppsf_discount_pct")
        or ia.get("ppsf_vs_neighborhood_pct")
        or p.get("ppsf_vs_neighborhood_pct")
        or p.get("ppsf_discount_pct")
    )
    if ppsf_vs and ppsf_vs > 0:
        ppsf_vs = -ppsf_vs

    qualitative = (
        ia.get("qualitative_notes")
        or ltr.get("qualitative_notes")
        or p.get("qualitative_notes")
        or ia.get("action")
        or p.get("action")
        or ""
    )

    redfin_est = (
        ld.get("redfin_estimate")
        or ia.get("redfin_estimate")
        or p.get("redfin_estimate")
        or get_nested(p, "redfin", default={}).get("estimate")
    )
    redfin_delta = (
        ld.get("redfin_estimate_delta_pct")
        or ia.get("redfin_estimate_delta_pct")
        or p.get("redfin_estimate_delta_pct")
        or get_nested(p, "redfin", default={}).get("delta_pct")
    )

    hoa = (
        ld.get("hoa_monthly")
        or p.get("hoa_monthly")
        or listing.get("hoa_monthly")
        or get_nested(p, "investment_inputs", default={}).get("hoa_monthly")
        or monthly_costs.get("hoa")
    )

    str_elig = (
        ld.get("short_term_rental")
        or ia.get("str_eligible")
        or p.get("str_eligible")
        or get_nested(p, "str_scenario", default={}).get("eligible") if isinstance(p.get("str_scenario"), dict) else None
    )

    config = ia.get("config_snapshot") or {}
    inv_inputs = p.get("investment_inputs", {})
    if not config and inv_inputs:
        config = {
            "down_payment_pct": inv_inputs.get("down_payment_pct", 20),
            "loan_term_years": inv_inputs.get("loan_term_years", 30),
            "mortgage_rate_pct": inv_inputs.get("mortgage_rate_pct") or fin.get("interest_rate", 0) * 100 if fin.get("interest_rate", 0) < 1 else fin.get("interest_rate", 6.0),
        }
    if not config:
        rate = ia.get("mortgage_rate_pct") or ia.get("mortgage_rate_used_pct") or fin.get("interest_rate", 0)
        if isinstance(rate, float) and rate < 1:
            rate = rate * 100
        config = {
            "down_payment_pct": ia.get("down_payment_pct", 20),
            "loan_term_years": ia.get("loan_term_years", 30),
            "mortgage_rate_pct": rate or 6.0,
        }

    result = {
        "slug": make_slug(p),
        "address": p["address"],
        "url": p.get("url") or p.get("redfin_url") or "",
        "market": p.get("market") or p.get("region", "Miami").title(),
        "neighborhood": p.get("neighborhood", ""),
        "state": p.get("state", "FL"),
        "bedrooms": p.get("bedrooms") or p.get("beds") or listing.get("bedrooms"),
        "bathrooms": p.get("bathrooms") or p.get("baths") or listing.get("bathrooms"),
        "sqft": p.get("sqft") or listing.get("sqft"),
        "first_seen": p.get("first_seen") or p.get("first_seen_date") or p.get("date_added") or p.get("scan_date"),
        "last_updated": p.get("last_updated") or ia.get("last_updated") or p.get("first_seen"),
        "status": (p.get("status") or listing.get("status", "active")).lower(),
        "deal_score": p.get("deal_score") or ia.get("deal_score") or 0,
        "price_history": p.get("price_history") or listing.get("price_history", []),
        "listing_details": {
            "hoa_monthly": hoa,
            "year_built": p.get("year_built") or ld.get("year_built") or listing.get("year_built"),
            "property_type": p.get("property_type") or listing.get("property_type"),
            "lot_sqft": p.get("lot_sqft") or listing.get("lot_sqft"),
            "short_term_rental": bool(str_elig) if str_elig is not None else None,
            "redfin_estimate": redfin_est,
            "redfin_estimate_delta_pct": redfin_delta,
            "climate_risks": normalize_climate_risks(p),
        },
        "investment_analysis": {
            "last_updated": ia.get("last_updated") or p.get("last_updated"),
            "config_snapshot": config,
            "purchase_price": purchase_price,
            "down_payment": down_payment,
            "loan_amount": loan_amount,
            "price_per_sqft": ppsf,
            "neighborhood_avg_ppsf": nbhd_ppsf,
            "ppsf_vs_avg_pct": ppsf_vs,
            "monthly_costs": monthly_costs,
            "total_monthly_cost": total_monthly,
            "break_even_rent_gross": break_even_gross,
            "break_even_rent_vacancy_adjusted": break_even_vac,
            "rental_comps": normalize_rental_comps(p),
            "avg_market_rent": avg_rent,
            "monthly_cash_flow_estimate": cash_flow,
            "cash_flow_assessment": cash_flow_assessment,
            "str_analysis": normalize_str_analysis(p),
            "deal_score_breakdown": normalize_deal_score_breakdown(p),
            "qualitative_notes": qualitative,
        },
    }

    return result


def main():
    raw_path = os.path.join(REPO, "data", "raw_properties.json")
    if os.path.exists(raw_path):
        with open(raw_path) as f:
            data = json.load(f)
    else:
        html_path = os.path.join(REPO, "index.html")
        with open(html_path) as f:
            lines = f.readlines()

        start = None
        end = None
        for i, line in enumerate(lines):
            if line.strip().startswith("var PROPERTIES"):
                start = i
            if start is not None and line.strip() == "];":
                end = i
                break

        raw_js = "".join(lines[start:end + 1])
        raw_js = raw_js.replace("var PROPERTIES = ", "", 1).rstrip().rstrip(";")
        data = json.loads(raw_js)

    print(f"Parsed {len(data)} raw properties")

    normalized = []
    for p in data:
        try:
            n = normalize_property(p)
            normalized.append(n)
        except Exception as e:
            print(f"ERROR normalizing {p.get('address', 'unknown')}: {e}")
            raise

    out_path = os.path.join(REPO, "data", "properties.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(normalized, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(normalized)} properties to {out_path}")

    # Validate: check every property has key fields
    issues = []
    for p in normalized:
        if not p["slug"]:
            issues.append(f"{p['address']}: missing slug")
        if p["deal_score"] is None:
            issues.append(f"{p['slug']}: missing deal_score")
        ia = p["investment_analysis"]
        if not ia["total_monthly_cost"]:
            issues.append(f"{p['slug']}: missing total_monthly_cost")
        if not ia["monthly_cash_flow_estimate"]:
            issues.append(f"{p['slug']}: missing monthly_cash_flow_estimate")
        if not ia["monthly_costs"]:
            issues.append(f"{p['slug']}: missing monthly_costs")

    if issues:
        print(f"\n{len(issues)} validation issues:")
        for i in issues:
            print(f"  - {i}")
    else:
        print("All properties validated OK")


if __name__ == "__main__":
    main()
