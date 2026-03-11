"""Configuration, setup status, and AI provider routes.

Implements: FR-009 (configuration API), FR-010 (setup status), FR-074 (AI provider validation).
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from config.settings import AppConfig, is_first_run, load_config, save_config
from core.ai_engine import validate_api_key as _validate_api_key
from core.i18n import t
from routes.bot import check_ai_available

config_bp = Blueprint("config", __name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@config_bp.route("/api/config", methods=["GET"])
def get_config():
    config = load_config()
    if config is None:
        return jsonify({})
    return jsonify(config.model_dump())


@config_bp.route("/api/config", methods=["PUT"])
def update_config():
    data = request.get_json()
    if data is None:
        return jsonify({"error": t("errors.request_body_json")}), 400
    try:
        existing = load_config()
        if existing:
            merged = existing.model_dump()
            for key, value in data.items():
                if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                    merged[key].update(value)
                else:
                    merged[key] = value
            config = AppConfig(**merged)
        else:
            config = AppConfig(**data)
    except ValidationError as e:
        return jsonify({"error": t("errors.invalid_config", count=e.error_count())}), 400
    save_config(config)
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

@config_bp.route("/api/setup/status", methods=["GET"])
def setup_status():
    return jsonify({
        "is_first_run": is_first_run(),
        "ai_available": check_ai_available(),
    })


# ---------------------------------------------------------------------------
# AI Provider
# ---------------------------------------------------------------------------

@config_bp.route("/api/ai/validate", methods=["POST"])
def validate_ai_key():
    data = request.get_json(force=True) or {}
    provider = data.get("provider", "")
    api_key = data.get("api_key", "")
    model = data.get("model", "")
    if not provider or not api_key:
        return jsonify({"error": t("errors.provider_key_required")}), 400
    if provider not in ("anthropic", "openai", "google", "deepseek"):
        return jsonify({"error": t("errors.unsupported_provider", provider=provider)}), 400
    valid = _validate_api_key(provider, api_key, model or None)
    return jsonify({"valid": valid})
