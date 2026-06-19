from flask import Blueprint, render_template, jsonify
from app.models.session import SessionManager
from app.models.report_engine import ReportEngine
from app.services.visualizer import Visualizer

report_bp = Blueprint("report", __name__)


@report_bp.route("/<session_id>")
def view_report(session_id):
    """展示完整报告页面"""
    return render_template("report.html", session_id=session_id)


@report_bp.route("/<session_id>/data")
def report_data(session_id):
    """返回报告 JSON 数据"""
    mgr = SessionManager()
    session = mgr.get_session(session_id)

    if not session:
        return jsonify({"error": "session not found"}), 404

    if not session.is_complete:
        return jsonify({"error": "assessment not complete"}), 400

    # 生成报告
    engine = ReportEngine()
    report = engine.generate(
        all_scores=session.all_scores,
        open_text_responses=session.open_text_responses,
    )

    # 生成图表数据
    viz = Visualizer()
    charts = viz.build_all_chart_data(session.all_scores)

    return jsonify({
        "session_id": session_id,
        "report": report,
        "charts": charts,
        "completed_at": session.created_at,
    })
