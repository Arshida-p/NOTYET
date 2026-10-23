"""
NOTYET - Main Flask Web Application
Hackathon Project: Unmet Neighbourhood Needs & Local Business Opportunities

Planned Features:
1. Homepage & Discovery Hub (/)
2. Report a Need (/report)
3. Community Validation (/validation)
4. Business Opportunities (/opportunities)
"""

import os
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    session,
)
from database import get_db, close_db, init_db
from validation_service import (
    get_validated_needs,
    get_validations_by_need_ids,
    get_all_validations_for_need,
    validate_need_entry,
)

# Available Neighbourhood Categories (Shared taxonomy across all 4 features)
CATEGORIES = [
    {"id": "grocery", "name": "Grocery & Food", "icon": "🍎"},
    {"id": "healthcare", "name": "Healthcare & Pharmacy", "icon": "💊"},
    {"id": "workspace", "name": "Workspace & Technology", "icon": "💻"},
    {"id": "childcare", "name": "Childcare & Education", "icon": "🧸"},
    {"id": "fitness", "name": "Fitness & Recreation", "icon": "🏃"},
    {"id": "pets", "name": "Pet Care & Veterinary", "icon": "🐾"},
    {"id": "retail", "name": "Bookshop, Cafe & Retail", "icon": "☕"},
    {"id": "services", "name": "Repairs & Home Services", "icon": "🛠️"},
]


def create_app():
    """Application factory for the NOTYET Flask app."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY", "notyet-hackathon-dev-key-2026"
    )

    # Register teardown to clean up SQLite connections
    app.teardown_appcontext(close_db)

    # CLI command: `flask init-db` for manual safe schema execution
    @app.cli.command("init-db")
    def init_db_command():
        """Initialize the database safely without wiping existing data."""
        init_db()
        print("Initialized the SQLite database successfully (safe execution).")

    # Inject shared helper variables into all Jinja2 templates
    @app.context_processor
    def inject_global_data():
        return {
            "all_categories": CATEGORIES,
            "app_name": "NOTYET",
            "tagline": "Discover what your neighborhood is missing.",
        }

    # ==========================================
    # FEATURE 1: HOMEPAGE ROUTE
    # ==========================================
    @app.route("/")
    def index():
        """
        Homepage: Welcomes visitors, explains the value for both residents and entrepreneurs,
        and displays dynamic genuine metrics directly from SQLite.
        """
        db = get_db()

        # Dynamic metrics computed strictly from real data (no fake stats)
        total_needs = db.execute("SELECT COUNT(*) FROM needs").fetchone()[0]
        total_neighborhoods = db.execute(
            "SELECT COUNT(DISTINCT neighborhood) FROM needs WHERE neighborhood IS NOT NULL AND neighborhood != ''"
        ).fetchone()[0]
        total_validations = db.execute(
            "SELECT COALESCE(SUM(validation_count), 0) FROM needs"
        ).fetchone()[0]

        # Recent unmet needs for homepage highlights
        recent_needs = db.execute(
            """
            SELECT id, title, description, category, neighborhood, validation_count, status, created_at
            FROM needs
            ORDER BY created_at DESC
            LIMIT 6
            """
        ).fetchall()

        return render_template(
            "index.html",
            active_page="home",
            total_needs=total_needs,
            total_neighborhoods=total_neighborhoods,
            total_validations=total_validations,
            recent_needs=recent_needs,
        )

    # ==========================================
    # FEATURE 2: REPORT A NEED (Scaffolded Route)
    # ==========================================
    @app.route("/report", methods=["GET", "POST"])
    def report_need():
        """
        Feature 2 Scaffold:
        Allows local residents to voice an unmet community service or store need.
        Team Member Notes:
        - Ready for field extensions (e.g. photo uploads, map pinpointing, urgency level).
        """
        if request.method == "POST":
            # Extract form inputs
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            category = request.form.get("category", "").strip()
            neighborhood = request.form.get("neighborhood", "").strip()
            zip_code = request.form.get("zip_code", "").strip()
            reporter_name = request.form.get("reporter_name", "").strip() or "Anonymous Resident"

            # Basic input validation
            if not title or not description or not category or not neighborhood:
                flash(
                    "Please fill in all required fields (Title, Category, Neighborhood, and Description).",
                    "error",
                )
                return render_template(
                    "report.html",
                    active_page="report",
                    categories=CATEGORIES,
                    form_data=request.form,
                )

            db = get_db()
            db.execute(
                """
                INSERT INTO needs (title, description, category, neighborhood, zip_code, validation_count, status, reporter_name)
                VALUES (?, ?, ?, ?, ?, 1, 'open', ?)
                """,
                (
                    title,
                    description,
                    category,
                    neighborhood,
                    zip_code,
                    reporter_name,
                ),
            )
            db.commit()

            flash(
                f"Your need '{title}' has been recorded! Neighbors can now validate it.",
                "success",
            )
            return redirect(url_for("community_validation"))

        return render_template(
            "report.html", active_page="report", categories=CATEGORIES
        )

    # ==========================================
    # FEATURE 3: COMMUNITY VALIDATION (Member 3)
    # ==========================================
    @app.route("/validation", methods=["GET"])
    def community_validation():
        """
        Community Validation Hub:
        Allows residents to browse unmet needs with search, category filtering,
        neighborhood filtering, and sorting, and validate them with optional testimonials.
        """
        db = get_db()
        selected_category = request.args.get("category", "").strip()
        selected_neighborhood = request.args.get("neighborhood", "").strip()
        search_query = request.args.get("q", "").strip()
        sort_by = request.args.get("sort", "popular").strip()

        # Fetch needs matching search/filter/sort parameters
        needs = get_validated_needs(
            db,
            category=selected_category,
            neighborhood=selected_neighborhood,
            search_query=search_query,
            sort_by=sort_by,
        )

        # Fetch recent neighbor testimonials/reasons for the displayed needs
        need_ids = [need["id"] for need in needs]
        validations_map = get_validations_by_need_ids(db, need_ids)

        # Fetch distinct neighborhoods for filter dropdown
        neighborhoods = [
            row[0]
            for row in db.execute(
                "SELECT DISTINCT neighborhood FROM needs WHERE neighborhood IS NOT NULL AND neighborhood != '' ORDER BY neighborhood ASC"
            ).fetchall()
        ]

        # Get list of already validated need IDs for duplicate vote prevention
        user_validated_ids = session.get("validated_needs", [])

        return render_template(
            "validation.html",
            active_page="validation",
            needs=needs,
            validations_map=validations_map,
            categories=CATEGORIES,
            neighborhoods=neighborhoods,
            selected_category=selected_category,
            selected_neighborhood=selected_neighborhood,
            search_query=search_query,
            sort_by=sort_by,
            user_validated_ids=user_validated_ids,
        )

    @app.route("/validate/<int:need_id>", methods=["POST"])
    def validate_need_action(need_id):
        """
        Endpoint for community upvoting / validating a specific need.
        Supports duplicate vote prevention via session, records optional support reasons,
        and returns JSON for AJAX or redirects for standard form submissions.
        """
        db = get_db()
        supporter_name = request.form.get("supporter_name", "").strip()
        support_reason = request.form.get("support_reason", "").strip()

        result = validate_need_entry(
            db, need_id, supporter_name, support_reason, session
        )

        # Check if client requested JSON (AJAX)
        is_ajax = (
            request.headers.get("X-Requested-With") == "XMLHttpRequest"
            or request.is_json
            or "application/json" in request.accept_mimetypes
        )

        if is_ajax:
            status_code = (
                200
                if result["success"]
                else (400 if result.get("status") == "already_validated" else 404)
            )
            return jsonify(result), status_code

        # Standard HTML form submit fallback
        if result["success"]:
            flash(result["message"], "success")
        elif result.get("status") == "already_validated":
            flash(result["message"], "info")
        else:
            flash(result["message"], "error")

        return redirect(url_for("community_validation"))

    @app.route("/api/need/<int:need_id>/validations", methods=["GET"])
    def get_need_validations_api(need_id):
        """
        API endpoint returning all testimonials / support reasons for a specific need.
        Used for the 'View neighbor stories' modal.
        """
        db = get_db()
        validations = get_all_validations_for_need(db, need_id)
        return jsonify(validations)

    # ==========================================
    # FEATURE 4: BUSINESS OPPORTUNITIES (Scaffolded Route)
    # ==========================================
    @app.route("/opportunities", methods=["GET"])
    def business_opportunities():
        """
        Feature 4 Scaffold:
        Translates validated community needs into actionable insights for local entrepreneurs.
        Team Member Notes:
        - Teammate can build analytics charts, export summaries, and business interest forms.
        """
        db = get_db()

        # Group unmet needs by category to highlight market demand
        category_demand = db.execute(
            """
            SELECT category, COUNT(*) as need_count, SUM(validation_count) as total_validations
            FROM needs
            GROUP BY category
            ORDER BY total_validations DESC, need_count DESC
            """
        ).fetchall()

        # High priority opportunities (needs sorted by highest validation count)
        top_opportunities = db.execute(
            """
            SELECT * FROM needs
            ORDER BY validation_count DESC, created_at DESC
            LIMIT 10
            """
        ).fetchall()

        return render_template(
            "opportunities.html",
            active_page="opportunities",
            category_demand=category_demand,
            top_opportunities=top_opportunities,
        )

    @app.route("/opportunities/<int:need_id>/interest", methods=["POST"])
    def express_business_interest(need_id):
        """
        Feature 4 Action: Lets a local business submit interest in addressing an unmet need.
        """
        db = get_db()
        business_name = request.form.get("business_name", "").strip()
        contact_email = request.form.get("contact_email", "").strip()
        proposal_summary = request.form.get("proposal_summary", "").strip()

        if not business_name or not contact_email:
            flash(
                "Please provide both your business name and contact email.",
                "error",
            )
            return redirect(url_for("business_opportunities"))

        db.execute(
            """
            INSERT INTO business_leads (need_id, business_name, contact_email, proposal_summary)
            VALUES (?, ?, ?, ?)
            """,
            (need_id, business_name, contact_email, proposal_summary),
        )
        db.commit()

        flash(
            "Thank you! Your interest was registered. Community members will be thrilled to see business momentum.",
            "success",
        )
        return redirect(url_for("business_opportunities"))

    return app


# Initialize the database safely when the module loads
init_db()
app = create_app()

if __name__ == "__main__":
    # Host on 127.0.0.1:5000 in debug mode for development
    app.run(host="127.0.0.1", port=5000, debug=True)
