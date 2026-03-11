"""Resume versioning routes.

Implements: FR-111 (resume list API), FR-112 (resume detail API),
            FR-113 (resume PDF serve), FR-114 (resume metrics API).
"""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, abort, jsonify, request, send_file

import app_state
from config.settings import get_data_dir
from core.i18n import t

resumes_bp = Blueprint("resumes", __name__)


def _get_db():
    """Return the database instance or abort 503 if not initialized."""
    db = app_state.db
    if db is None:
        abort(503, description=t("errors.database_not_initialized"))
    return db


def _is_safe_resume_path(file_path: str | Path) -> bool:
    """Verify file_path is within the autoapply data directory (no traversal)."""
    try:
        resolved = Path(file_path).resolve()
        allowed = get_data_dir().resolve()
        return resolved.is_relative_to(allowed) and resolved.exists()
    except (ValueError, OSError):
        return False


# Static routes before parameterized routes (lesson 11.2)

@resumes_bp.route("/api/resumes/metrics", methods=["GET"])
def resume_metrics():
    return jsonify(_get_db().get_resume_metrics())


@resumes_bp.route("/api/resumes", methods=["GET"])
def list_resumes():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    search = request.args.get("search")
    sort = request.args.get("sort", "created_at")
    order = request.args.get("order", "desc")

    items, total_count = _get_db().get_resume_versions(
        page=page, per_page=per_page, search=search, sort=sort, order=order
    )
    return jsonify({
        "items": items,
        "total_count": total_count,
        "page": max(1, page),
        "per_page": per_page,
    })


@resumes_bp.route("/api/resumes/<int:version_id>", methods=["GET"])
def resume_detail(version_id: int):
    version = _get_db().get_resume_version(version_id)
    if version is None:
        abort(404, description=t("errors.not_found"))

    # Read markdown content from disk
    md_path = version.get("resume_md_path", "")
    version["resume_md_content"] = None
    version["file_missing"] = False

    if md_path and _is_safe_resume_path(md_path):
        try:
            version["resume_md_content"] = Path(md_path).read_text(
                encoding="utf-8"
            )
        except OSError:
            version["file_missing"] = True
    elif md_path:
        # Path exists in DB but file is missing or traversal blocked
        version["file_missing"] = True

    return jsonify(version)


@resumes_bp.route("/api/resumes/<int:version_id>/pdf", methods=["GET"])
def resume_pdf(version_id: int):
    version = _get_db().get_resume_version(version_id)
    if version is None:
        abort(404, description=t("errors.not_found"))

    pdf_path = version.get("resume_pdf_path", "")
    if not pdf_path or not _is_safe_resume_path(pdf_path):
        abort(404, description=t("resumes.file_missing"))

    download = request.args.get("download", "").lower() == "true"
    return send_file(
        pdf_path,
        mimetype="application/pdf",
        as_attachment=download,
        download_name=f"resume_{version_id}.pdf",
    )
