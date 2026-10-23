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


def _load_env_if_present():
    """
    Safely loads key-value pairs from a local .env file if present,
    without requiring third-party libraries. Existing environment variables
    take precedence and will not be overwritten.
    """
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.isfile(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        key, val = key.strip(), val.strip()
                        if key and key not in os.environ:
                            os.environ[key] = val.strip("'\"")
        except Exception:
            pass


# Attempt to read local .env if present
_load_env_if_present()


def create_app():
    """Application factory for the NOTYET Flask app."""
    app = Flask(__name__)

    # Environment detection
    flask_env = os.environ.get("FLASK_ENV", os.environ.get("ENV", "development")).lower()
    is_production = flask_env in ("production", "prod")

    # Safe SECRET_KEY configuration
    secret_key = os.environ.get("SECRET_KEY")
    insecure_keys = {
        "notyet-hackathon-dev-key-2026",
        "change-this-to-a-secure-random-secret-key-in-production",
        "your-secret-key-here",
    }

    if is_production:
        if not secret_key or secret_key.strip() in insecure_keys:
            raise RuntimeError(
                "CRITICAL SECURITY CONFIGURATION ERROR: A strong, unique SECRET_KEY must "
                "be set via environment variable in production mode. "
                "Do not use default or placeholder keys in production."
            )
        app.config["SECRET_KEY"] = secret_key
    else:
        # Development fallback (safe for local development only)
        app.config["SECRET_KEY"] = secret_key or "notyet-hackathon-dev-key-2026"

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
            "category_icons": {c["name"]: c["icon"] for c in CATEGORIES},
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
    # FEATURE: BROWSE COMMUNITY NEEDS
    # ==========================================
    @app.route("/needs", methods=["GET"])
    @app.route("/browse", methods=["GET"])
    def browse_needs():
        """
        Browse Community Needs:
        Displays community needs dynamically from the SQLite database with filtering
        by category, neighborhood, status, or search keywords using parameterized SQL.
        """
        db = get_db()
        selected_category = request.args.get("category", "").strip()
        selected_neighborhood = request.args.get("neighborhood", "").strip()
        selected_status = request.args.get("status", "").strip()
        search_query = request.args.get("q", "").strip()

        # Base parameterized query
        query = """
            SELECT id, title, description, category, neighborhood, zip_code, validation_count, status, reporter_name, created_at
            FROM needs
            WHERE 1=1
        """
        params = []

        if selected_category:
            query += " AND category = ?"
            params.append(selected_category)

        if selected_neighborhood:
            query += " AND neighborhood LIKE ?"
            params.append(f"%{selected_neighborhood}%")

        if selected_status:
            query += " AND status = ?"
            params.append(selected_status)

        if search_query:
            query += " AND (title LIKE ? OR description LIKE ? OR neighborhood LIKE ?)"
            params.extend([f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"])

        query += " ORDER BY created_at DESC"

        needs = db.execute(query, params).fetchall()

        # Fetch distinct neighborhoods for filter dropdown
        neighborhoods = [
            row[0]
            for row in db.execute(
                "SELECT DISTINCT neighborhood FROM needs WHERE neighborhood IS NOT NULL AND neighborhood != '' ORDER BY neighborhood ASC"
            ).fetchall()
        ]

        # Total needs count in database for general platform statistics
        total_count = db.execute("SELECT COUNT(*) FROM needs").fetchone()[0]

        return render_template(
            "needs.html",
            active_page="browse",
            needs=needs,
            categories=CATEGORIES,
            neighborhoods=neighborhoods,
            selected_category=selected_category,
            selected_neighborhood=selected_neighborhood,
            selected_status=selected_status,
            search_query=search_query,
            total_count=total_count,
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
            willingness_to_pay = request.form.get("willingness_to_pay", "").strip() or None

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

            # Validate category against allowed CATEGORIES list
            valid_categories = {cat["name"] for cat in CATEGORIES}
            if category not in valid_categories:
                flash(
                    "Please select a valid category from the available options.",
                    "error",
                )
                return render_template(
                    "report.html",
                    active_page="report",
                    categories=CATEGORIES,
                    form_data=request.form,
                )

            # Validate title length (5 to 100 characters)
            if len(title) < 5 or len(title) > 100:
                flash(
                    "Need title must be between 5 and 100 characters.",
                    "error",
                )
                return render_template(
                    "report.html",
                    active_page="report",
                    categories=CATEGORIES,
                    form_data=request.form,
                )

            # Validate description length (20 to 1,000 characters)
            if len(description) < 20 or len(description) > 1000:
                flash(
                    "Description must be between 20 and 1,000 characters to provide sufficient context.",
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
                INSERT INTO needs (title, description, category, neighborhood, zip_code, validation_count, status, reporter_name, willingness_to_pay)
                VALUES (?, ?, ?, ?, ?, 1, 'open', ?, ?)
                """,
                (
                    title,
                    description,
                    category,
                    neighborhood,
                    zip_code,
                    reporter_name,
                    willingness_to_pay,
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
    # FEATURE 4: BUSINESS OPPORTUNITY DASHBOARD
    # ==========================================
    @app.route("/opportunities", methods=["GET"])
    def business_opportunities():
        """
        Feature A: Business Opportunity Dashboard
        Displays neighborhood needs with the highest community support, identifies
        repeated unmet needs/clusters, displays willingness-to-pay separately from support
        counts (or shows explicit demand research notice), and provides category filters and sorting.
        """
        db = get_db()
        selected_category = request.args.get("category", "").strip()
        selected_neighborhood = request.args.get("neighborhood", "").strip()
        selected_sort = request.args.get("sort", "support").strip()

        # Group unmet needs by category to highlight market demand
        category_demand = db.execute(
            """
            SELECT category, COUNT(*) as need_count, SUM(validation_count) as total_validations
            FROM needs
            WHERE status IN ('open', 'in_discussion')
            GROUP BY category
            ORDER BY total_validations DESC, need_count DESC
            """
        ).fetchall()

        # Identify demand clusters (repeated unmet needs in the same neighborhood or high validation)
        demand_clusters = db.execute(
            """
            SELECT neighborhood, category, COUNT(*) as cluster_count, SUM(validation_count) as cluster_validations
            FROM needs
            WHERE status IN ('open', 'in_discussion')
            GROUP BY neighborhood, category
            ORDER BY cluster_validations DESC, cluster_count DESC
            LIMIT 4
            """
        ).fetchall()

        # Base query joining needs with business leads count
        query = """
            SELECT 
                n.id, 
                n.title, 
                n.description, 
                n.category, 
                n.neighborhood, 
                n.zip_code, 
                n.validation_count, 
                n.status, 
                n.reporter_name, 
                n.willingness_to_pay,
                n.created_at,
                COUNT(b.id) AS lead_count
            FROM needs n
            LEFT JOIN business_leads b ON n.id = b.need_id
            WHERE n.status IN ('open', 'in_discussion')
        """
        params = []

        if selected_category:
            query += " AND n.category = ?"
            params.append(selected_category)
        if selected_neighborhood:
            query += " AND n.neighborhood = ?"
            params.append(selected_neighborhood)

        query += " GROUP BY n.id"

        # Apply sorting
        if selected_sort == "newest":
            query += " ORDER BY n.created_at DESC"
        elif selected_sort == "interest":
            query += " ORDER BY lead_count DESC, n.validation_count DESC"
        else:  # default: support
            query += " ORDER BY n.validation_count DESC, n.created_at DESC"

        opportunities = db.execute(query, params).fetchall()

        # Compute summary KPIs strictly from live database data
        total_opps = db.execute(
            "SELECT COUNT(*) FROM needs WHERE status IN ('open', 'in_discussion')"
        ).fetchone()[0]

        high_demand_count = db.execute(
            "SELECT COUNT(*) FROM needs WHERE status IN ('open', 'in_discussion') AND validation_count >= 4"
        ).fetchone()[0]

        total_leads = db.execute("SELECT COUNT(*) FROM business_leads").fetchone()[0]

        top_sector_row = db.execute(
            """
            SELECT category, SUM(validation_count) as total_val
            FROM needs
            WHERE status IN ('open', 'in_discussion')
            GROUP BY category
            ORDER BY total_val DESC
            LIMIT 1
            """
        ).fetchone()
        top_sector = top_sector_row[0] if top_sector_row else "Various"

        # Fetch distinct neighborhoods for filter dropdown
        neighborhoods = [
            row[0]
            for row in db.execute(
                "SELECT DISTINCT neighborhood FROM needs WHERE neighborhood IS NOT NULL AND neighborhood != '' ORDER BY neighborhood ASC"
            ).fetchall()
        ]

        return render_template(
            "opportunities.html",
            active_page="opportunities",
            opportunities=opportunities,
            category_demand=category_demand,
            demand_clusters=demand_clusters,
            kpis={
                "total_opps": total_opps,
                "high_demand_count": high_demand_count,
                "total_leads": total_leads,
                "top_sector": top_sector,
            },
            categories=CATEGORIES,
            neighborhoods=neighborhoods,
            selected_category=selected_category,
            selected_neighborhood=selected_neighborhood,
            selected_sort=selected_sort,
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

    # ==========================================
    # FEATURE B: SUCCESS STORIES
    # ==========================================
    @app.route("/success-stories", methods=["GET"])
    def success_stories():
        """
        Feature B: Success Stories Page
        Displays completed neighborhood projects and problems that have been resolved.
        Shows only records with status 'completed' or 'resolved'.
        Displays problem, solution, neighborhood, impact, and completion status.
        Includes category filtering and clear labeling of any demonstration data.
        """
        db = get_db()
        selected_category = request.args.get("category", "").strip()
        selected_neighborhood = request.args.get("neighborhood", "").strip()

        query = """
            SELECT * FROM success_stories
            WHERE status IN ('completed', 'resolved')
        """
        params = []

        if selected_category:
            query += " AND category = ?"
            params.append(selected_category)
        if selected_neighborhood:
            query += " AND neighborhood = ?"
            params.append(selected_neighborhood)

        query += " ORDER BY completed_date DESC, created_at DESC"

        stories = db.execute(query, params).fetchall()

        # Fetch distinct neighborhoods for filter dropdown
        neighborhoods = [
            row[0]
            for row in db.execute(
                "SELECT DISTINCT neighborhood FROM success_stories WHERE neighborhood IS NOT NULL AND neighborhood != '' ORDER BY neighborhood ASC"
            ).fetchall()
        ]

        # Aggregate counts for header badges
        total_completed = db.execute(
            "SELECT COUNT(*) FROM success_stories WHERE status IN ('completed', 'resolved')"
        ).fetchone()[0]

        demo_count = db.execute(
            "SELECT COUNT(*) FROM success_stories WHERE status IN ('completed', 'resolved') AND is_demo = 1"
        ).fetchone()[0]

        neighborhoods_served = db.execute(
            "SELECT COUNT(DISTINCT neighborhood) FROM success_stories WHERE status IN ('completed', 'resolved')"
        ).fetchone()[0]

        return render_template(
            "stories.html",
            active_page="stories",
            stories=stories,
            categories=CATEGORIES,
            neighborhoods=neighborhoods,
            selected_category=selected_category,
            selected_neighborhood=selected_neighborhood,
            total_completed=total_completed,
            demo_count=demo_count,
            neighborhoods_served=neighborhoods_served,
        )

    @app.route("/success-stories/<int:story_id>", methods=["GET"])
    def success_story_detail(story_id):
        """
        Feature B Detail View:
        Allows users to view deep-dive case study details for a resolved story.
        """
        db = get_db()
        story = db.execute(
            "SELECT * FROM success_stories WHERE id = ? AND status IN ('completed', 'resolved')",
            (story_id,),
        ).fetchone()

        if not story:
            flash("The requested success story could not be found or has not been marked resolved.", "error")
            return redirect(url_for("success_stories"))

        # If story is linked to a need, fetch that need for extra context
        linked_need = None
        if story["need_id"]:
            linked_need = db.execute(
                "SELECT * FROM needs WHERE id = ?", (story["need_id"],)
            ).fetchone()

        return render_template(
            "story_detail.html",
            active_page="stories",
            story=story,
            linked_need=linked_need,
        )

    return app


# Initialize the database safely when the module loads
init_db()
app = create_app()

if __name__ == "__main__":
    flask_env = os.environ.get("FLASK_ENV", os.environ.get("ENV", "development")).lower()
    is_prod = flask_env in ("production", "prod")

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 5000))

    # In production, debug mode must ALWAYS be disabled
    if is_prod:
        debug_mode = False
    else:
        # In development, default to True unless explicitly disabled (FLASK_DEBUG=0)
        debug_flag = os.environ.get("FLASK_DEBUG", "1").lower()
        debug_mode = debug_flag in ("1", "true", "yes")

    app.run(host=host, port=port, debug=debug_mode)
