#!/usr/bin/env python3
"""Extract reports from reports.html into data/reports.json."""

import json
import os
import re
from html.parser import HTMLParser

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def extract_reports():
    html_path = os.path.join(REPO, "reports.html")
    with open(html_path) as f:
        content = f.read()

    reports = []

    # Extract index rows for metadata (date, title, pick_preview, macro_preview)
    row_pattern = re.compile(
        r'<tr class="rpt-row" data-slug="([^"]+)"[^>]*>.*?</tr>',
        re.DOTALL
    )
    for m in row_pattern.finditer(content):
        slug = m.group(1)
        block = m.group(0)

        dow = ""
        dow_m = re.search(r'<div class="rpt-dow">([^<]+)</div>', block)
        if dow_m:
            dow = dow_m.group(1).strip()

        ds = ""
        ds_m = re.search(r'<div class="rpt-ds">([^<]+)</div>', block)
        if ds_m:
            ds = ds_m.group(1).strip()

        title = ""
        title_m = re.search(r'<div class="rpt-title">([^<]+)</div>', block)
        if title_m:
            title = title_m.group(1).strip()

        pick = ""
        pick_m = re.search(r'<div class="rpt-pick">([^<]*)</div>', block)
        if pick_m:
            pick = pick_m.group(1).strip()

        macro = ""
        macro_m = re.search(r'<div class="rpt-macro">([^<]*)</div>', block)
        if macro_m:
            macro = macro_m.group(1).strip()

        reports.append({
            "slug": slug,
            "date": slug,
            "day_of_week": dow,
            "display_date": ds,
            "title": title,
            "pick_preview": pick,
            "macro_preview": macro,
            "body_html": "",
        })

    # Extract panel bodies
    panel_pattern = re.compile(
        r'<div class="rpt-panel" id="panel-([^"]+)">\s*'
        r'<div class="rpt-panel-header">.*?</div>\s*'
        r'<div class="rpt-panel-body">(.*?)</div>\s*</div>',
        re.DOTALL
    )
    panel_bodies = {}
    for m in panel_pattern.finditer(content):
        slug = m.group(1)
        body = m.group(2).strip()
        panel_bodies[slug] = body

    for r in reports:
        r["body_html"] = panel_bodies.get(r["slug"], "")

    return reports


def main():
    reports = extract_reports()
    print(f"Extracted {len(reports)} reports")

    for r in reports:
        has_body = "yes" if r["body_html"] else "NO"
        print(f"  {r['slug']}: {r['title'][:60]}... body={has_body}")

    out_path = os.path.join(REPO, "data", "reports.json")
    with open(out_path, "w") as f:
        json.dump(reports, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {len(reports)} reports to {out_path}")


if __name__ == "__main__":
    main()
