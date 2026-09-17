#!/usr/bin/env python3
"""
Part Sniper — eBay Resale Arbitrage Bot
Scores listings by arbitrage potential using keyword analysis.
Demo mode with sample listings; production mode with eBay API.
Cron-ready: runs once and exits.
"""

import json
import os
from datetime import datetime

CONFIG_FILE = "config.json"
RESULTS_FILE = "sniper_results.json"

# ── Scoring Keywords ────────────────────────────────────────────
HIGH_VALUE_KEYWORDS = {
    "plc": 15, "allen bradley": 20, "siemens": 18, "toyota": 12,
    "fanuc": 20, "servo": 15, "vfd": 14, "drive": 10,
    "controller": 12, "hmi": 14, "encoder": 10, "inverter": 12,
    "mitsubishi": 15, "omron": 14, "yaskawa": 16, "abb": 14,
    "schneider": 12, "rockwell": 18, "cnc": 15, "stepper": 8,
}

LOW_INFO_KEYWORDS = {
    "lot": 8, "untested": 10, "as-is": 12, "unknown": 10,
    "misc": 8, "parts only": 10, "for parts": 10, "surplus": 6,
    "estate": 8, "clearance": 6, "moving sale": 8, "no returns": 4,
}

# ── Demo Listings ───────────────────────────────────────────────
DEMO_LISTINGS = [
    {"title": "Allen Bradley PLC 1756 Lot of 5 - Untested As-Is", "price": 35.00,
     "seller": "estateclearout99", "url": "https://ebay.com/demo/1"},
    {"title": "Siemens S7-300 CPU Module - Unknown Condition", "price": 22.50,
     "seller": "garagesale2024", "url": "https://ebay.com/demo/2"},
    {"title": "Fanuc Servo Amplifier A06B - Parts Only", "price": 45.00,
     "seller": "industrialsurplus", "url": "https://ebay.com/demo/3"},
    {"title": "Misc Electronic Components Box Lot", "price": 15.00,
     "seller": "randomstuff42", "url": "https://ebay.com/demo/4"},
    {"title": "Toyota Forklift Controller Board", "price": 28.00,
     "seller": "warehouseclean", "url": "https://ebay.com/demo/5"},
    {"title": "VFD Variable Frequency Drive 5HP - Untested", "price": 40.00,
     "seller": "factoryclose", "url": "https://ebay.com/demo/6"},
    {"title": "Brand New Arduino Starter Kit", "price": 35.00,
     "seller": "hobbyshop", "url": "https://ebay.com/demo/7"},
    {"title": "Yaskawa Sigma-5 SGDV Servo Drive Lot Surplus", "price": 48.00,
     "seller": "closeoutkings", "url": "https://ebay.com/demo/8"},
    {"title": "ABB ACS355 VFD Drive As-Is No Returns", "price": 50.00,
     "seller": "industrialdump", "url": "https://ebay.com/demo/9"},
    {"title": "Used Raspberry Pi 4 8GB", "price": 55.00,
     "seller": "techreseller", "url": "https://ebay.com/demo/10"},
]


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"mode": "demo", "ebay_app_id": "", "ebay_cert_id": "", "search_terms": ["PLC", "servo drive", "VFD"]}


def score_listing(listing):
    """Score a listing based on arbitrage potential."""
    title_lower = listing["title"].lower()
    price = listing.get("price", 999)
    score = 0
    matched_keywords = []

    # High-value keyword matching
    for keyword, points in HIGH_VALUE_KEYWORDS.items():
        if keyword in title_lower:
            score += points
            matched_keywords.append(f"+{points} [{keyword}]")

    # Low-info keyword matching (seller doesn't know value)
    for keyword, points in LOW_INFO_KEYWORDS.items():
        if keyword in title_lower:
            score += points
            matched_keywords.append(f"+{points} [{keyword}]")

    # Price bonus
    if price < 20:
        score += 15
        matched_keywords.append("+15 [price <$20]")
    elif price < 50:
        score += 8
        matched_keywords.append("+8 [price <$50]")

    return {
        **listing,
        "score": score,
        "matched_keywords": matched_keywords,
        "scored_at": datetime.now().isoformat(),
    }


def fetch_ebay_listings(config):
    """Fetch real eBay listings. Placeholder for production use."""
    print("[Part Sniper] Production mode requires eBay API keys in config.json")
    print("  Set mode='production', ebay_app_id, and ebay_cert_id")
    print("  Using eBay Finding API: findItemsByKeywords")
    return []


def main():
    print("=" * 60)
    print("  Part Sniper — eBay Resale Arbitrage Scorer")
    print("=" * 60)

    config = load_config()
    mode = config.get("mode", "demo")

    if mode == "production":
        listings = fetch_ebay_listings(config)
        if not listings:
            print("  No listings fetched. Falling back to demo mode.")
            listings = DEMO_LISTINGS
    else:
        print("  Running in DEMO mode with sample listings.\n")
        listings = DEMO_LISTINGS

    # Score all listings
    scored = [score_listing(l) for l in listings]
    scored.sort(key=lambda x: x["score"], reverse=True)

    # Display results
    print(f"{'RANK':<5} {'SCORE':<7} {'PRICE':<8} {'TITLE'}")
    print("-" * 80)
    for i, item in enumerate(scored, 1):
        color = "\033[92m" if item["score"] >= 30 else "\033[93m" if item["score"] >= 15 else "\033[0m"
        print(f"{color}{i:<5} {item['score']:<7} ${item['price']:<7.2f} {item['title'][:55]}\033[0m")
        if item["matched_keywords"]:
            print(f"      Scoring: {', '.join(item['matched_keywords'])}")

    # Save results
    with open(RESULTS_FILE, "w") as f:
        json.dump(scored, f, indent=2)

    print(f"\n  Results saved to {RESULTS_FILE}")
    print(f"  Top pick: {scored[0]['title']} (score: {scored[0]['score']})")

    # Save default config if it doesn't exist
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump(load_config(), f, indent=2)
        print(f"  Default config saved to {CONFIG_FILE}")


if __name__ == "__main__":
    main()
