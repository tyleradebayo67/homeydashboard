# Homey Investment Dashboard

## Overview
Real estate investment analysis dashboard for Miami market properties, hosted on GitHub Pages.
- **Site**: https://tyleradebayo67.github.io/homeydashboard/
- **Repo**: tyleradebayo67/homeydashboard

## Architecture
- Static site: `index.html` (dashboard) + `reports.html` (daily reports)
- Data: `data/properties.json` (property data), `data/reports.json` (report data)
- No build tools, no framework — vanilla HTML/CSS/JS + Chart.js
- Both HTML files fetch their JSON data at load time and render dynamically

## Data Files
- `data/properties.json` — Array of 76 property objects with normalized schema
- `data/reports.json` — Array of 22 daily report objects with body_html
- `data/raw_properties.json` — Original un-normalized data (backup for re-normalization)
- `scripts/normalize_properties.py` — Normalizes raw data into canonical schema
- `scripts/extract_reports.py` — Extracts reports from legacy HTML

## Property Data Schema
Each property in `data/properties.json` has:
```
slug, address, url, market, neighborhood, state
bedrooms, bathrooms, sqft, first_seen, last_updated, status
deal_score (0-100)
price_history: [{date, price, note}]
listing_details: {hoa_monthly, year_built, property_type, short_term_rental, redfin_estimate, redfin_estimate_delta_pct, climate_risks}
investment_analysis: {
  config_snapshot: {down_payment_pct, loan_term_years, mortgage_rate_pct}
  purchase_price, down_payment, loan_amount, price_per_sqft
  neighborhood_avg_ppsf, ppsf_vs_avg_pct
  monthly_costs: {mortgage_pi, property_tax, hoa, insurance, maintenance_reserve, capex, property_management}
  total_monthly_cost, break_even_rent_gross, break_even_rent_vacancy_adjusted
  rental_comps: [{source, address, rent, beds, sqft, days_listed}]
  avg_market_rent, monthly_cash_flow_estimate, cash_flow_assessment
  str_analysis: {eligible, assumed_nightly_rate, assumed_nights_per_month, estimated_monthly_revenue, estimated_monthly_cash_flow}
  deal_score_breakdown: {price_drop_pct, price_per_sqft_vs_neighborhood, cash_flow_tier, hoa_level, climate_risk, redfin_estimate_delta}
  qualitative_notes
}
```

## Deal Score System (0-100)
| Component | Max Pts | Criteria |
|-----------|---------|----------|
| price_drop_pct | 25 | Price reductions from listing |
| price_per_sqft_vs_neighborhood | 25 | Discount vs area avg ppsf |
| cash_flow_tier | 25 | positive=25, near-breakeven=10-15, negative=0 |
| hoa_level | 10 | none=10, <$200=7, <$400=5, >$400=0 |
| climate_risk | 10 | no extreme=10, moderate=5-7, extreme=0 |
| redfin_estimate_delta | 5 | listed >5% below estimate=5, 1-5%=2-3, above=0 |

## Investment Assumptions (defaults)
- Down payment: 20%
- Loan term: 30 years
- Mortgage rate: current market (check Freddie Mac PMMS / Bankrate)
- Vacancy: 5%
- Monthly reserves: maintenance $300, capex $200
- Insurance: ~1.5% of value annually (FL)
- Property tax: ~1.0% of value annually (FL)

## Cash Flow Assessment
- **Positive**: cash flow > $0/mo
- **Near break-even**: cash flow between -$300 and $0/mo
- **Negative**: cash flow < -$300/mo

## Submission Channels
- **Website form** on the dashboard → creates a GitHub Issue with label `property-request`
- **Telegram bot** → messages picked up during analysis

## Workflow
Run `/analyze` to process pending property submissions and update the dashboard.
After updating `data/properties.json`, commit and push — the site updates automatically via GitHub Pages.

## Conventions
- Commit messages: `dashboard update: YYYY-MM-DD HH:MM UTC` for data updates
- Property slugs: lowercase address with hyphens, no special chars
- All monetary values in USD, no cents
- Dates in ISO format (YYYY-MM-DD)
