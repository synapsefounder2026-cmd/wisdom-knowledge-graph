"""
Wisdom OPC Digital Passport
So hoa OPC thanh tai san so co the dinh gia, chuyen nhuong, thua ke.

Modules:
  - OPCPassport     : Schema + generator
  - OPCValuation    : SDE multiple engine
  - OPCTransfer     : Transfer protocol
  - OPCSuccession   : Succession plan

Usage:
    python wisdom_passport.py --score        # Tinh OPC Score hien tai
    python wisdom_passport.py --generate     # Tao Digital Passport
    python wisdom_passport.py --valuation    # Tinh dinh gia
    python wisdom_passport.py --dataroom     # Xuat Data Room cho buyer
"""

import os
import sys
import json
import uuid
import hashlib
import re
import argparse
from datetime import datetime, timedelta
from pathlib import Path

from neo4j import GraphDatabase

# ── Config ────────────────────────────────────────────────────────────────────
NEO4J_URI    = "bolt://localhost:7687"
NEO4J_USER   = "neo4j"
NEO4J_PASS   = "password123"
PASSPORT_DIR = os.environ.get("WISDOM_PASSPORT_DIR", "passport")

def strip_emoji(text: str) -> str:
    if not isinstance(text, str):
        return str(text) if text else ""
    emoji_pattern = re.compile(
        "[" u"\U0001F600-\U0001F64F" u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF" u"\U0001F1E0-\U0001F1FF"
        u"\U00002600-\U000027BF" u"\U0001F900-\U0001F9FF" "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub("", text).strip()


# ── OPC Threshold Check ───────────────────────────────────────────────────────

# Dieu kien de OPC du tieu chuan so hoa
THRESHOLD = {
    "min_monthly_revenue_usd": 500,      # $500/thang lien tuc 3 thang
    "min_consistent_months":   3,
    "min_products":            1,
    "min_verified_nodes":      50,
    "min_paying_customers":    10,
}

# Bonus conditions (cong diem)
BONUS = {
    "has_recurring_revenue":   10,
    "has_branded_content":     5,
    "email_list_500plus":      5,
    "automation_rate_60pct":   10,
    "profit_margin_40pct":     10,
    "active_years_2plus":      5,
}


def query_opc_metrics() -> dict:
    """Lay metrics tu Neo4j + Wisdom Ledger de tinh OPC Score."""
    metrics = {
        "verified_nodes":       0,
        "total_concepts":       0,
        "total_products":       0,
        "monthly_revenue_usd":  0.0,
        "monthly_profit_usd":   0.0,
        "paying_customers":     0,
        "recurring_revenue_pct": 0.0,
        "profit_margin":        0.0,
        "automation_count":     0,
        "content_count":        0,
        "active_months":        0,
    }
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        with driver.session() as s:
            # Verified knowledge nodes
            r = s.run("MATCH (n) WHERE n.epistemic_status = 'VERIFIED' RETURN count(n) AS c").single()
            metrics["verified_nodes"] = r["c"] if r else 0

            # Total concepts
            r = s.run("MATCH (c:Concept) RETURN count(c) AS c").single()
            metrics["total_concepts"] = r["c"] if r else 0

            # Products (neu co Product node)
            r = s.run("MATCH (p:Product) RETURN count(p) AS c").single()
            metrics["total_products"] = r["c"] if r else 0

            # Financial data (neu co Transaction node)
            r = s.run("""
                MATCH (t:Transaction)
                WHERE t.type = 'income'
                  AND t.date >= $since
                RETURN sum(t.amount) AS total, count(DISTINCT t.customer_id) AS customers
            """, since=(datetime.now() - timedelta(days=90)).isoformat()).single()
            if r and r["total"]:
                metrics["monthly_revenue_usd"] = float(r["total"]) / 3
                metrics["paying_customers"]    = r["customers"] or 0

        driver.close()
    except Exception as e:
        print(f"  Neo4j metrics ERROR: {e}")
    return metrics


def calculate_opc_score(metrics: dict) -> dict:
    """
    Tinh OPC Score 0-100.
    >= 60: Eligible so hoa
    >= 80: Eligible listing/transfer
    """
    score    = 0
    passed   = []
    failed   = []
    bonuses  = []

    # --- Required conditions ---
    if metrics["monthly_revenue_usd"] >= THRESHOLD["min_monthly_revenue_usd"]:
        score += 20
        passed.append(f"Revenue ${metrics['monthly_revenue_usd']:.0f}/month >= $500")
    else:
        failed.append(f"Revenue ${metrics['monthly_revenue_usd']:.0f}/month < $500 required")

    if metrics["total_products"] >= THRESHOLD["min_products"]:
        score += 15
        passed.append(f"{metrics['total_products']} digital product(s)")
    else:
        failed.append("No digital products yet")

    if metrics["verified_nodes"] >= THRESHOLD["min_verified_nodes"]:
        score += 20
        passed.append(f"{metrics['verified_nodes']} verified knowledge nodes >= 50")
    else:
        failed.append(f"Only {metrics['verified_nodes']} verified nodes (need 50)")

    if metrics["paying_customers"] >= THRESHOLD["min_paying_customers"]:
        score += 20
        passed.append(f"{metrics['paying_customers']} paying customers >= 10")
    else:
        failed.append(f"Only {metrics['paying_customers']} paying customers (need 10)")

    # --- Bonus conditions ---
    if metrics.get("recurring_revenue_pct", 0) > 0.3:
        score += BONUS["has_recurring_revenue"]
        bonuses.append(f"+{BONUS['has_recurring_revenue']}pts: Has recurring revenue")

    if metrics.get("profit_margin", 0) > 0.4:
        score += BONUS["profit_margin_40pct"]
        bonuses.append(f"+{BONUS['profit_margin_40pct']}pts: Profit margin > 40%")

    if metrics.get("automation_count", 0) > 5:
        score += BONUS["automation_rate_60pct"]
        bonuses.append(f"+{BONUS['automation_rate_60pct']}pts: Strong automation")

    if metrics.get("active_months", 0) >= 24:
        score += BONUS["active_years_2plus"]
        bonuses.append(f"+{BONUS['active_years_2plus']}pts: 2+ years active")

    score = min(score, 100)

    if score >= 80:
        status = "ELIGIBLE_TRANSFER"
        msg    = "OPC du dieu kien so hoa va chuyen nhuong"
    elif score >= 60:
        status = "ELIGIBLE_PASSPORT"
        msg    = "OPC du dieu kien tao Digital Passport"
    elif score >= 40:
        status = "GROWING"
        msg    = "OPC dang phat trien, can them 2-3 thang"
    else:
        status = "EARLY"
        msg    = "OPC con som, focus vao revenue va products truoc"

    return {
        "score":   score,
        "status":  status,
        "message": msg,
        "passed":  passed,
        "failed":  failed,
        "bonuses": bonuses,
    }


# ── Valuation Engine ──────────────────────────────────────────────────────────

def calculate_valuation(metrics: dict) -> dict:
    """
    SDE Multiple valuation (chuan Flippa/Empire Flippers).
    SDE = Annual Profit (Seller's Discretionary Earnings)
    Value = SDE x Multiple (2x-5x)
    """
    annual_profit = metrics.get("monthly_profit_usd", 0) * 12
    if annual_profit <= 0:
        annual_profit = metrics.get("monthly_revenue_usd", 0) * 12 * 0.4  # Estimate 40% margin

    base_multiple = 2.0
    breakdown     = {"base": 2.0}

    # Recurring revenue bonus
    rec_pct = metrics.get("recurring_revenue_pct", 0)
    if rec_pct > 0.7:
        base_multiple += 1.0
        breakdown["recurring_revenue_70pct"] = +1.0
    elif rec_pct > 0.4:
        base_multiple += 0.5
        breakdown["recurring_revenue_40pct"] = +0.5

    # Churn bonus
    churn = metrics.get("churn_rate", 0.1)
    if churn < 0.03:
        base_multiple += 0.5
        breakdown["low_churn"] = +0.5
    elif churn < 0.05:
        base_multiple += 0.3
        breakdown["moderate_churn"] = +0.3

    # Automation bonus
    if metrics.get("automation_count", 0) > 5:
        base_multiple += 0.5
        breakdown["high_automation"] = +0.5

    # Age bonus
    if metrics.get("active_months", 0) >= 24:
        base_multiple += 0.3
        breakdown["age_2yr_plus"] = +0.3

    # Growth bonus
    growth = metrics.get("revenue_growth_rate", 0)
    if growth > 0.5:
        base_multiple += 0.5
        breakdown["high_growth"] = +0.5
    elif growth > 0.2:
        base_multiple += 0.2
        breakdown["moderate_growth"] = +0.2

    # Cap tai 5x cho OPC (chua co team)
    multiple         = round(min(base_multiple, 5.0), 2)
    estimated_value  = round(annual_profit * multiple, 2)
    confidence       = min(0.9, 0.3 + (metrics.get("verified_nodes", 0) / 200))

    return {
        "annual_sde":          round(annual_profit, 2),
        "multiple":            multiple,
        "estimated_value_usd": estimated_value,
        "confidence":          round(confidence, 2),
        "breakdown":           breakdown,
        "note": "SDE multiple chuẩn Flippa/Empire Flippers. Cap 5x cho single-owner OPC.",
    }


# ── Digital Passport Generator ────────────────────────────────────────────────

def generate_passport(owner_name: str, opc_name: str,
                      opc_type: str, niche: str,
                      jurisdiction: str = "VN") -> dict:
    """Tao OPC Digital Passport. passport_id la IMMUTABLE."""
    metrics   = query_opc_metrics()
    score_res = calculate_opc_score(metrics)
    valuation = calculate_valuation(metrics)

    passport = {
        # Identity — IMMUTABLE
        "passport_id":   str(uuid.uuid4()),
        "created_at":    datetime.now().isoformat(),
        "schema_version": "1.0",

        # Owner
        "owner_name":    owner_name,
        "jurisdiction":  jurisdiction,

        # Business
        "opc_name":      opc_name,
        "opc_type":      opc_type,
        "niche":         niche,
        "founding_date": datetime.now().strftime("%Y-%m"),

        # Score & Status
        "opc_score":     score_res["score"],
        "opc_status":    score_res["status"],

        # Metrics snapshot
        "metrics_snapshot": {
            **metrics,
            "snapshot_date": datetime.now().isoformat(),
        },

        # Valuation
        "valuation": valuation,

        # Assets
        "transferable_assets": [
            "domain_name", "email_list", "product_files",
            "brand_assets", "sops", "customer_database",
            "automation_workflows", "wisdom_knowledge_base_explicit",
            "social_media_accounts", "revenue_contracts",
        ],
        "non_transferable_assets": [
            "tacit_knowledge_owner",
            "personal_client_relationships",
            "personal_reputation",
            "creative_voice_style",
        ],

        # Transfer status
        "transfer_status": "locked",
        "transfer_history": [],

        # Succession (placeholder — can notarize)
        "succession_plan": {
            "primary_heir":    "",
            "conditions":      "upon_death_or_voluntary",
            "notarized":       False,
            "document_hash":   "",
            "knowledge_base_access": {
                "public_nodes":  "inherit_immediately",
                "private_nodes": "inherit_after_30_days",
                "tacit_nodes":   "archive_permanent",
            }
        },

        # Integrity
        "passport_hash": "",  # Set sau khi sign
    }

    # Self-sign hash
    passport_str         = json.dumps(passport, sort_keys=True, ensure_ascii=False)
    passport["passport_hash"] = hashlib.sha256(passport_str.encode()).hexdigest()

    return passport


def save_passport(passport: dict) -> str:
    """Luu passport ra file JSON."""
    Path(PASSPORT_DIR).mkdir(parents=True, exist_ok=True)
    pid      = passport["passport_id"][:8]
    filename = f"opc_passport_{pid}_{datetime.now().strftime('%Y%m%d')}.json"
    filepath = os.path.join(PASSPORT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(passport, f, ensure_ascii=False, indent=2)
    return filepath


# ── Data Room Generator ───────────────────────────────────────────────────────

def generate_dataroom(passport: dict) -> str:
    """Xuat Data Room markdown cho buyer due diligence."""
    v   = passport["valuation"]
    m   = passport["metrics_snapshot"]
    now = datetime.now().strftime("%d/%m/%Y")

    lines = [
        f"# {passport['opc_name']} — Data Room",
        f"**Prepared:** {now}  ",
        f"**Jurisdiction:** {passport['jurisdiction']}  ",
        f"**OPC Score:** {passport['opc_score']}/100 ({passport['opc_status']})",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"- **Business type:** {passport['opc_type']} | {passport['niche']}",
        f"- **Founded:** {passport['founding_date']}",
        f"- **Asking price:** ${v['estimated_value_usd']:,.0f} USD",
        f"- **Revenue/month:** ${m['monthly_revenue_usd']:,.0f} USD",
        f"- **Profit/month:** ${m['monthly_profit_usd']:,.0f} USD",
        f"- **Paying customers:** {m['paying_customers']}",
        "",
        "## Valuation",
        "",
        f"- **Method:** SDE Multiple (Seller's Discretionary Earnings)",
        f"- **Annual SDE:** ${v['annual_sde']:,.0f}",
        f"- **Multiple:** {v['multiple']}x",
        f"- **Estimated value:** ${v['estimated_value_usd']:,.0f}",
        f"- **Confidence:** {v['confidence']*100:.0f}%",
        "",
        "## Knowledge Base",
        "",
        f"- **Verified nodes:** {m['verified_nodes']}",
        f"- **Total concepts:** {m['total_concepts']}",
        f"- **Digital products:** {m['total_products']}",
        "",
        "## Transferable Assets",
        "",
    ]
    for asset in passport["transferable_assets"]:
        lines.append(f"- {asset.replace('_', ' ').title()}")

    lines += [
        "",
        "## Non-Transferable (FYI)",
        "",
    ]
    for asset in passport["non_transferable_assets"]:
        lines.append(f"- {asset.replace('_', ' ').title()}")

    lines += [
        "",
        "## Passport Integrity",
        "",
        f"- **Passport ID:** `{passport['passport_id']}`",
        f"- **Hash:** `{passport['passport_hash'][:32]}...`",
        f"- **Schema version:** {passport['schema_version']}",
        "",
        "---",
        "*Generated by Wisdom OPC Digital Passport System*",
    ]

    Path(PASSPORT_DIR).mkdir(parents=True, exist_ok=True)
    filepath = os.path.join(PASSPORT_DIR, "dataroom.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return filepath


# ── CLI ───────────────────────────────────────────────────────────────────────

def print_score(score_res: dict):
    print(f"\nOPC Score: {score_res['score']}/100 — {score_res['status']}")
    print(f"Message:   {score_res['message']}\n")
    if score_res["passed"]:
        print("PASSED:")
        for p in score_res["passed"]:
            print(f"  + {p}")
    if score_res["failed"]:
        print("\nNEED:")
        for f in score_res["failed"]:
            print(f"  - {f}")
    if score_res["bonuses"]:
        print("\nBONUS:")
        for b in score_res["bonuses"]:
            print(f"  * {b}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wisdom OPC Digital Passport")
    parser.add_argument("--score",     action="store_true", help="Tinh OPC Score hien tai")
    parser.add_argument("--generate",  action="store_true", help="Tao Digital Passport")
    parser.add_argument("--valuation", action="store_true", help="Xem dinh gia")
    parser.add_argument("--dataroom",  action="store_true", help="Xuat Data Room")
    args = parser.parse_args()

    metrics   = query_opc_metrics()
    score_res = calculate_opc_score(metrics)

    if args.score or not any(vars(args).values()):
        print_score(score_res)

    if args.valuation or args.generate:
        v = calculate_valuation(metrics)
        print(f"\nValuation:")
        print(f"  Annual SDE:  ${v['annual_sde']:,.0f}")
        print(f"  Multiple:    {v['multiple']}x")
        print(f"  Est. Value:  ${v['estimated_value_usd']:,.0f} USD")
        print(f"  Confidence:  {v['confidence']*100:.0f}%")

    if args.generate:
        print("\nGenerating passport...")
        name      = input("Owner name: ").strip()
        opc_name  = input("OPC/Business name: ").strip()
        opc_type  = input("Type (solopreneur/freelancer/coach/creator): ").strip()
        niche     = input("Niche: ").strip()
        passport  = generate_passport(name, opc_name, opc_type, niche)
        filepath  = save_passport(passport)
        print(f"\nPassport saved: {filepath}")
        print(f"Passport ID:   {passport['passport_id']}")
        print(f"Hash:          {passport['passport_hash'][:32]}...")

    if args.dataroom:
        print("\nGenerating Data Room...")
        name     = input("Owner name: ").strip() or "Owner"
        opc_name = input("OPC name: ").strip() or "My OPC"
        passport = generate_passport(name, opc_name, "solopreneur", "")
        filepath = generate_dataroom(passport)
        print(f"Data Room saved: {filepath}")
