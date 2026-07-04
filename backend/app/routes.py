from flask import Blueprint, Response, jsonify, request

from app.claude_client import generate_wealth_memo
from app.pdf_generator import build_pdf_report
from app.plan_service import InvalidPlanInput, build_plan

bp = Blueprint("routes", __name__)

PLAN_SECTIONS = ("tax_and_accounts", "asset_allocation", "monte_carlo", "sip_plan")


@bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@bp.post("/generate-plan")
def generate_plan():
    user_input = request.get_json(silent=True)
    if not user_input:
        return jsonify({"error": "Request body must be JSON."}), 400

    try:
        structured_plan = build_plan(user_input)
    except InvalidPlanInput as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"Failed to calculate wealth plan: {exc}"}), 500

    try:
        memo = generate_wealth_memo(structured_plan)
    except Exception as exc:
        return jsonify({"error": f"Failed to generate advisory memo: {exc}"}), 502

    return jsonify({**structured_plan, "memo": memo})


@bp.post("/generate-report")
def generate_report():
    """Render the wealth plan as a downloadable PDF.

    Expects a body of the form {"user_input": {...questionnaire...}, "plan": {...}}
    where "plan" is the exact JSON returned by /generate-plan (including the
    Claude-generated "memo"). This avoids re-running the deterministic engines
    or re-calling Claude for a plan already generated in the same session.
    """
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Request body must be JSON."}), 400

    user_input = body.get("user_input")
    plan = body.get("plan")

    if not isinstance(user_input, dict) or not isinstance(plan, dict):
        return jsonify({"error": "Request body must include 'user_input' and 'plan' objects."}), 400

    missing_sections = [section for section in PLAN_SECTIONS if section not in plan]
    if missing_sections or "memo" not in plan:
        return jsonify({
            "error": f"'plan' is missing required sections: "
                     f"{', '.join(missing_sections + (['memo'] if 'memo' not in plan else []))}"
        }), 400

    try:
        pdf_bytes = build_pdf_report(user_input, plan)
    except Exception as exc:
        return jsonify({"error": f"Failed to generate PDF report: {exc}"}), 500

    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=zaelor-wealth-plan.pdf",
        },
    )
