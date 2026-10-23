"""
NOTYET - Community Validation Service Module (Feature 3)
Handles search, filtering, duplicate-vote prevention, and validation comments/testimonials.
Implemented as an isolated service module to maintain clean separation and avoid editing other members' code.
"""

from datetime import datetime


def compute_demand_level(validation_count):
    """
    Computes a demand milestone and badge information based on the validation count.
    Used for the demand progress bar and visual tier badge.
    """
    count = int(validation_count or 0)
    if count >= 10:
        target = 15
        percent = min(100, int((count / target) * 100))
        return {
            "tier": "high",
            "label": "High Priority Demand",
            "class_name": "badge-demand-high",
            "icon": "🔥",
            "target": target,
            "percent": percent,
            "description": "Ready for local business proposal",
        }
    elif count >= 5:
        target = 10
        percent = min(100, int((count / target) * 100))
        return {
            "tier": "growing",
            "label": "Growing Community Interest",
            "class_name": "badge-demand-growing",
            "icon": "⚡",
            "target": target,
            "percent": percent,
            "description": f"{10 - count} more validations for High Priority",
        }
    else:
        target = 5
        percent = min(100, int((count / target) * 100))
        return {
            "tier": "emerging",
            "label": "Emerging Need",
            "class_name": "badge-demand-emerging",
            "icon": "🌱",
            "target": target,
            "percent": percent,
            "description": f"{5 - count} more validations to reach Growing Demand",
        }


def get_validated_needs(
    db, category=None, neighborhood=None, search_query=None, sort_by="popular"
):
    """
    Retrieves unmet needs from SQLite with multi-criteria filtering, search, and sorting.
    Returns a list of dicts enriched with demand level milestones.
    """
    query = "SELECT * FROM needs WHERE status = 'open'"
    params = []

    # Category filter
    if category:
        query += " AND category = ?"
        params.append(category)

    # Neighborhood filter
    if neighborhood:
        query += " AND neighborhood LIKE ?"
        params.append(f"%{neighborhood}%")

    # Full text search across title, description, and neighborhood
    if search_query:
        query += " AND (title LIKE ? OR description LIKE ? OR neighborhood LIKE ? OR zip_code LIKE ?)"
        term = f"%{search_query.strip()}%"
        params.extend([term, term, term, term])

    # Sorting
    if sort_by in ("newest", "recent"):
        query += " ORDER BY created_at DESC"
    elif sort_by in ("support_needed", "unmet"):
        query += " ORDER BY validation_count ASC, created_at DESC"
    else:  # default 'popular' / 'most_validated'
        query += " ORDER BY validation_count DESC, created_at DESC"

    cursor = db.execute(query, params)
    rows = cursor.fetchall()

    needs = []
    for row in rows:
        need_dict = dict(row)
        need_dict["demand_info"] = compute_demand_level(
            need_dict.get("validation_count", 1)
        )
        needs.append(need_dict)

    return needs


def get_validations_by_need_ids(db, need_ids):
    """
    Fetches recent testimonials / support reasons for a list of need IDs.
    Returns a dictionary mapping {need_id: {'reasons': [...], 'total_reasons': int}}
    """
    if not need_ids:
        return {}

    placeholders = ",".join("?" for _ in need_ids)

    # 1. Fetch recent support reasons (non-empty comments)
    reasons_query = f"""
        SELECT id, need_id, supporter_name, support_reason, created_at
        FROM validations
        WHERE need_id IN ({placeholders}) 
          AND support_reason IS NOT NULL 
          AND TRIM(support_reason) != ''
        ORDER BY created_at DESC
    """
    rows = db.execute(reasons_query, need_ids).fetchall()

    validations_map = {nid: {"reasons": [], "total_reasons": 0} for nid in need_ids}

    for row in rows:
        nid = row["need_id"]
        if nid in validations_map:
            validations_map[nid]["total_reasons"] += 1
            # Keep top 3 for preview cards
            if len(validations_map[nid]["reasons"]) < 3:
                validations_map[nid]["reasons"].append(dict(row))

    return validations_map


def get_all_validations_for_need(db, need_id):
    """
    Fetches all validations and comments for a single need (used for the testimonials modal/API).
    """
    rows = db.execute(
        """
        SELECT id, need_id, supporter_name, support_reason, created_at
        FROM validations
        WHERE need_id = ?
        ORDER BY created_at DESC
        """,
        (need_id,),
    ).fetchall()

    return [dict(r) for r in rows]


def validate_need_entry(db, need_id, supporter_name, support_reason, session):
    """
    Performs duplicate-prevented validation of a community need.
    - Checks session to prevent multiple votes by the same resident.
    - Increments validation_count on the needs record.
    - Records an entry in validations with optional reason/testimonial.
    - Returns a structured dictionary with outcome status and updated metrics.
    """
    # 1. Verify existence of the need
    need = db.execute("SELECT * FROM needs WHERE id = ?", (need_id,)).fetchone()
    if not need:
        return {
            "success": False,
            "status": "not_found",
            "message": "The requested community need could not be found.",
        }

    # 2. Duplicate vote prevention via session
    validated_needs = session.get("validated_needs", [])
    if need_id in validated_needs:
        return {
            "success": False,
            "status": "already_validated",
            "need_id": need_id,
            "validation_count": need["validation_count"],
            "message": f"You have already validated '{need['title']}'. Thank you for supporting your community!",
            "demand_info": compute_demand_level(need["validation_count"]),
        }

    # 3. Clean up inputs
    clean_name = (supporter_name or "").strip() or "Supportive Neighbour"
    clean_reason = (support_reason or "").strip()
    if not clean_reason:
        clean_reason = None

    # 4. Atomic update & insert
    db.execute(
        "UPDATE needs SET validation_count = validation_count + 1 WHERE id = ?",
        (need_id,),
    )
    db.execute(
        "INSERT INTO validations (need_id, supporter_name, support_reason) VALUES (?, ?, ?)",
        (need_id, clean_name, clean_reason),
    )
    db.commit()

    # 5. Fetch updated count
    updated = db.execute(
        "SELECT validation_count, title FROM needs WHERE id = ?", (need_id,)
    ).fetchone()
    new_count = updated["validation_count"]

    # 6. Mark as validated in session
    if need_id not in validated_needs:
        validated_needs.append(need_id)
        session["validated_needs"] = validated_needs
        session.modified = True

    demand_info = compute_demand_level(new_count)

    return {
        "success": True,
        "status": "validated",
        "need_id": need_id,
        "title": updated["title"],
        "validation_count": new_count,
        "supporter_name": clean_name,
        "support_reason": clean_reason,
        "demand_info": demand_info,
        "message": f"You successfully validated '{updated['title']}'! Local demand increased to {new_count}.",
    }
