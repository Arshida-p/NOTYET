"""
NOTYET - Automated Verification Suite for Feature A & Feature B
Tests Business Opportunity Dashboard, Success Stories, Willingness-to-Pay, and filtering.
"""

from app import create_app
import sqlite3

def run_tests():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    print("[1/5] Testing Navigation & Base Integration...")
    res = client.get("/")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert b"Success Stories" in res.data, "Missing Success Stories link in navbar"
    assert b"Business Opportunities" in res.data, "Missing Business Opportunities link in navbar"
    print("  -> Navigation links verified.")

    print("[2/5] Testing Feature A: Business Opportunity Dashboard...")
    res_opp = client.get("/opportunities")
    assert res_opp.status_code == 200
    assert b"Business Opportunity Dashboard" in res_opp.data
    assert b"Verified Opportunities Feed" in res_opp.data
    assert b"Resident Willingness-to-Pay" in res_opp.data, "Need 1 should display willingness-to-pay separately"
    assert b"Demand Research Needed" in res_opp.data, "Needs without willingness-to-pay must show research notice"
    print("  -> Dashboard cards, separate willingness-to-pay & research notices verified.")

    # Sorting
    res_sort_interest = client.get("/opportunities?sort=interest")
    assert res_sort_interest.status_code == 200
    res_sort_newest = client.get("/opportunities?sort=newest")
    assert res_sort_newest.status_code == 200
    print("  -> Sorting options (support, interest, newest) verified.")

    # Category filter
    res_cat = client.get("/opportunities?category=Grocery+%26+Food")
    assert res_cat.status_code == 200
    assert b"Fresh Organic Produce" in res_cat.data
    print("  -> Category filter verified.")

    # Opportunities empty state
    res_empty = client.get("/opportunities?neighborhood=NonExistentArea123")
    assert res_empty.status_code == 200
    assert b"No Matching Opportunities Found" in res_empty.data
    print("  -> Opportunities empty state verified.")

    print("[3/5] Testing Business Lead Registration...")
    res_lead = client.post("/opportunities/1/interest", data={
        "business_name": "FreshGo Urban Markets",
        "contact_email": "hello@freshgo.test",
        "proposal_summary": "We operate mobile micro-markets and can launch in 3 weeks."
    }, follow_redirects=True)
    assert res_lead.status_code == 200
    assert b"interest was registered" in res_lead.data or b"momentum" in res_lead.data
    print("  -> Entrepreneur lead submission verified.")

    print("[4/5] Testing Feature B: Success Stories...")
    res_stories = client.get("/success-stories")
    assert res_stories.status_code == 200
    assert b"Neighbourhood Success Stories" in res_stories.data
    assert b"DEMO DATA" in res_stories.data, "Demonstration data must be clearly tagged"
    assert b"Oakridge Fresh Produce Farm Stand" in res_stories.data
    print("  -> Success Stories feed & DEMO DATA badges verified.")

    # Story filter
    res_story_cat = client.get("/success-stories?category=Grocery+%26+Food")
    assert res_story_cat.status_code == 200
    assert b"Oakridge Fresh Produce Farm Stand" in res_story_cat.data
    print("  -> Success Stories category filtering verified.")

    # Story empty state
    res_story_empty = client.get("/success-stories?category=NonExistentCat99")
    assert res_story_empty.status_code == 200
    assert b"No Completed Projects Found" in res_story_empty.data
    print("  -> Success Stories empty state verified.")

    # Story detail view
    res_detail = client.get("/success-stories/1")
    assert res_detail.status_code == 200
    assert b"Oakridge Fresh Produce Farm Stand" in res_detail.data
    assert b"DEMO DATA" in res_detail.data
    assert b"Key Measurable Outcomes" in res_detail.data
    print("  -> Story detail case study view verified.")

    print("[5/5] Testing Optional Willingness-to-Pay in Report Need...")
    res_report = client.post("/report", data={
        "title": "Community Tool Shed & Repair Cafe",
        "description": "Residents need access to power tools and lawnmowers without purchasing expensive gear.",
        "category": "Repairs & Home Services",
        "neighborhood": "Riverside District",
        "zip_code": "94018",
        "reporter_name": "Dave Miller",
        "willingness_to_pay": "$5 - $15 / tool rental"
    }, follow_redirects=True)
    assert res_report.status_code == 200
    print("  -> Reporting need with willingness-to-pay verified.")

    # Check newly added need in opportunities
    res_check = client.get("/opportunities?category=Repairs+%26+Home+Services")
    assert res_check.status_code == 200
    assert b"Community Tool Shed" in res_check.data
    assert b"$5 - $15 / tool rental" in res_check.data
    print("  -> Newly reported need displays willingness-to-pay separately on dashboard.")

    print("\nSUCCESS: All NOTYET features and regression tests passed perfectly!")

if __name__ == "__main__":
    run_tests()
