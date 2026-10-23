"""
NOTYET - Database Management Module
Handles SQLite connection pooling per request and safe schema initialization.
"""

import os
import sqlite3
from flask import g, current_app

DB_NAME = "notyet.db"


def get_db():
    """
    Get or create a SQLite database connection for the current Flask request context.
    Configures row_factory to sqlite3.Row for convenient column-name key access.
    """
    if "db" not in g:
        # Determine database path relative to the app root
        db_path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), DB_NAME
        )
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        # Enforce foreign key constraints
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db


def close_db(e=None):
    """Closes the current database connection if one was opened during this request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app=None):
    """
    Executes schema.sql safely without dropping existing tables or deleting existing data.
    Uses CREATE TABLE IF NOT EXISTS.
    """
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), DB_NAME)
    schema_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "schema.sql"
    )

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")

    with open(schema_path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    # Safe column migration: Ensure optional willingness_to_pay column exists in needs table
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(needs);")
    existing_columns = [col[1] for col in cursor.fetchall()]
    if "willingness_to_pay" not in existing_columns:
        cursor.execute("ALTER TABLE needs ADD COLUMN willingness_to_pay TEXT DEFAULT NULL;")

    # Optional starter data check: Only seed if the database has zero records
    _seed_starter_data_if_empty(conn)

    conn.commit()
    conn.close()


def _seed_starter_data_if_empty(conn):
    """
    Inserts a few realistic initial neighbourhood needs ONLY if the database is brand new and empty.
    Also seeds demonstrative success stories (strictly labeled as demo data) if the stories table is empty.
    Does NOT fabricate fake aggregate statistics, ensuring genuine metrics.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM needs")
    count = cursor.fetchone()[0]

    if count == 0:
        starter_needs = [
            (
                "Fresh Organic Produce & Farmers Market Stall",
                "Our neighborhood lacks a walkable grocery store with fresh greens, vegetables, and fruit. We currently travel over 3 miles just for fresh produce.",
                "Grocery & Food",
                "Oakridge North",
                "94016",
                4,
                "open",
                "Elena Vance",
                "$15 - $30 / basket",
            ),
            (
                "Extended Hours Pharmacy & Health Clinic",
                "All nearby pharmacies close strictly by 6:00 PM. Parents and shift workers desperately need access to infant medicine and first aid after hours.",
                "Healthcare & Pharmacy",
                "Riverside District",
                "94018",
                7,
                "open",
                "Marcus Sterling",
                None,  # No willingness-to-pay collected yet -> triggers clear Demand Research Needed notice
            ),
            (
                "Community Coworking Space & High-Speed Hub",
                "Remote workers, students, and freelancers here are sitting in crowded coffee shops with no power outlets or quiet meeting booths.",
                "Workspace & Technology",
                "Downtown West",
                "94015",
                5,
                "open",
                "Priya Sharma",
                None,  # No willingness-to-pay collected yet -> triggers clear Demand Research Needed notice
            ),
        ]
        cursor.executemany(
            """
            INSERT INTO needs (title, description, category, neighborhood, zip_code, validation_count, status, reporter_name, willingness_to_pay)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            starter_needs,
        )

    # Seed demonstrative resolved stories if success_stories table is empty
    cursor.execute("SELECT COUNT(*) FROM success_stories")
    story_count = cursor.fetchone()[0]

    if story_count == 0:
        demo_stories = [
            (
                None,
                "Oakridge Fresh Produce Farm Stand",
                "Grocery & Food",
                "Oakridge North",
                "Residents lacked access to fresh fruits and vegetables within a 3-mile radius, leaving over 400 households dependent on convenience store processed foods.",
                "In response to community validation on NOTYET, GreenCorner Co-op partnered with local urban growers to launch a bi-weekly fresh produce stall and pre-order basket delivery at the community pavilion.",
                "Over 420 local families now source fresh vegetables locally every week. Average travel time for groceries dropped from 35 minutes to under 8 minutes.",
                "GreenCorner Co-op & Local Growers Alliance",
                "2026-09-15",
                "completed",
                1,  # Strictly marked as demo data
            ),
            (
                None,
                "Westside Remote Work & Creator Hub",
                "Workspace & Technology",
                "Downtown West",
                "Freelancers, remote employees, and students faced noisy coffee shops with zero phone booths and scarce power outlets, creating an acute need for a walkable workspace.",
                "A neighborhood property owner transformed an underutilized high-street retail unit into a dedicated coworking space with hot-desks, high-speed fiber internet, and quiet audio-conferencing pods.",
                "Now serves 85+ active local monthly members. Local cafe foot traffic increased by 22% from members taking lunch breaks on the block.",
                "Westside Workspace Collective",
                "2026-10-01",
                "resolved",
                1,  # Strictly marked as demo data
            ),
        ]
        cursor.executemany(
            """
            INSERT INTO success_stories (need_id, title, category, neighborhood, original_problem, solution_provided, impact_summary, business_or_initiator, completed_date, status, is_demo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            demo_stories,
        )

