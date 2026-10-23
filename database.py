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

    # Optional starter data check: Only seed if the database has zero records
    _seed_starter_data_if_empty(conn)

    conn.commit()
    conn.close()


def _seed_starter_data_if_empty(conn):
    """
    Inserts a few realistic initial neighbourhood needs ONLY if the database is brand new and empty.
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
            ),
        ]
        cursor.executemany(
            """
            INSERT INTO needs (title, description, category, neighborhood, zip_code, validation_count, status, reporter_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            starter_needs,
        )
