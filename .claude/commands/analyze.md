# Analyze Properties

Process pending property submissions and optionally scan for new listings.

## Steps

1. **Check for pending requests**:
   - Run `gh issue list --repo tyleradebayo67/homeydashboard --label property-request --state open` to find submissions
   - Check for recent Telegram messages containing property URLs or addresses
   - List all pending items and confirm with the user before proceeding

2. **For each property to analyze**:

   a. **Get listing data** — Browse the property URL (Redfin or Zillow) using WebFetch/WebSearch:
      - Address, bedrooms, bathrooms, sqft, year built, lot size
      - Current price, price history, days on market
      - HOA amount, parking, amenities
      - Redfin/Zillow estimate and delta vs list
      - Climate risk data (flood, wind, heat, fire) from First Street
      - STR eligibility (check HOA rules)

   b. **Research rental comps** — Search for 3-5 comparable rentals nearby:
      - Same bedroom count, similar sqft, within 2 miles
      - Sources: Zillow rentals, Apartments.com, Rent.com
      - Record: address, rent, beds, sqft, days listed, source
      - Calculate average market rent

   c. **Calculate investment analysis**:
      - Use 20% down, 30-year fixed at current market rate (check Bankrate/Freddie Mac PMMS)
      - Monthly costs: mortgage P&I, property tax (~1% / 12), HOA, insurance (~1.5% / 12 for FL), maintenance ($300), capex ($200)
      - Break-even rent = total monthly cost / (1 - 0.05 vacancy)
      - Cash flow = avg market rent - total monthly cost
      - Assessment: positive (>0), near-breakeven (-300 to 0), negative (<-300)

   d. **STR analysis** (if eligible):
      - Research AirDNA or comparable data for nightly rates in the area
      - Assume 18 nights/month occupancy
      - STR cash flow = (nightly rate × nights) - total monthly cost

   e. **Score the property** using the Deal Score system:
      - price_drop_pct: 0-25 based on listing price reductions
      - price_per_sqft_vs_neighborhood: 0-25 based on ppsf discount
      - cash_flow_tier: 25 if positive, 10-15 if near-breakeven, 0 if negative
      - hoa_level: 10 if none, 7 if <$200, 5 if <$400, 0 if >$400
      - climate_risk: 10 if no extreme, 5-7 if moderate, 0 if extreme flood
      - redfin_estimate_delta: 5 if >5% below estimate, 2-3 if 1-5%, 0 if above

   f. **Write qualitative notes** (2-4 sentences): key strengths, key risks, recommendation.

   g. **Generate the slug** from the address (lowercase, hyphens, no special chars).

3. **Update data**:
   - Read `data/properties.json`
   - Append new properties or update existing ones (match by slug)
   - Write updated `data/properties.json`

4. **Commit and push**:
   ```
   git add data/properties.json
   git commit -m "dashboard update: $(date -u +'%Y-%m-%d %H:%M') UTC"
   git push origin main
   ```

5. **Close processed GitHub Issues**:
   ```
   gh issue close [NUMBER] --repo tyleradebayo67/homeydashboard -c "Property analyzed and added to dashboard."
   ```

6. **Reply via Telegram** if the request came from there, confirming analysis is complete.

## Property JSON Template
```json
{
  "slug": "123-main-st-miami-fl",
  "address": "123 Main St, Miami, FL 33101",
  "url": "https://www.redfin.com/FL/Miami/...",
  "market": "Miami",
  "neighborhood": "Downtown Miami",
  "state": "FL",
  "bedrooms": 3,
  "bathrooms": 2,
  "sqft": 1500,
  "first_seen": "2026-05-24",
  "last_updated": "2026-05-24",
  "status": "active",
  "deal_score": 45,
  "price_history": [{"date": "2026-05-24", "price": 500000}],
  "listing_details": {
    "hoa_monthly": 200,
    "year_built": 2005,
    "property_type": "Single Family",
    "short_term_rental": true,
    "redfin_estimate": 530000,
    "redfin_estimate_delta_pct": 6.0,
    "climate_risks": {"flood": "Moderate", "wind": "Extreme", "heat": "Extreme"}
  },
  "investment_analysis": {
    "config_snapshot": {"down_payment_pct": 20, "loan_term_years": 30, "mortgage_rate_pct": 6.5},
    "purchase_price": 500000,
    "down_payment": 100000,
    "loan_amount": 400000,
    "price_per_sqft": 333,
    "neighborhood_avg_ppsf": 380,
    "ppsf_vs_avg_pct": -12.4,
    "monthly_costs": {
      "mortgage_pi": 2528, "property_tax": 417, "hoa": 200,
      "insurance": 625, "maintenance_reserve": 300, "capex": 200, "property_management": 0
    },
    "total_monthly_cost": 4270,
    "break_even_rent_gross": 4270,
    "break_even_rent_vacancy_adjusted": 4495,
    "rental_comps": [],
    "avg_market_rent": 3200,
    "monthly_cash_flow_estimate": -1070,
    "cash_flow_assessment": "cash-flow negative",
    "str_analysis": {"eligible": true, "assumed_nightly_rate": 250, "assumed_nights_per_month": 18, "estimated_monthly_revenue": 4500, "estimated_monthly_cash_flow": 230},
    "deal_score_breakdown": {
      "price_drop_pct": 0, "price_per_sqft_vs_neighborhood": 15,
      "cash_flow_tier": 0, "hoa_level": 7, "climate_risk": 5,
      "redfin_estimate_delta": 5, "total": 32
    },
    "qualitative_notes": "Analysis notes here."
  }
}
```
