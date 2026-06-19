import json
import os
from flask import Blueprint, render_template, request, jsonify
from config import Config
from app.models.session import SessionManager

assessment_bp = Blueprint("assessment", __name__)

PHASE1_INSTRUMENTS = ["bfi2", "rses"]


def load_instrument(instrument_id):
    path = os.path.join(Config.INSTRUMENTS_DIR, f"{instrument_id}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_all_phase1_items():
    """获取阶段一所有题目，打乱量表间顺序但保持量表内顺序"""
    items = []
    for inst_id in PHASE1_INSTRUMENTS:
        inst = load_instrument(inst_id)
        for item in inst["items"]:
            item["_instrument_id"] = inst_id
            item["_scale_type"] = inst["response_scale"]["type"]
            item["_scale_points"] = inst["response_scale"]["points"]
            item["_scale_labels"] = inst["response_scale"]["labels"]
            item["_instructions"] = inst["instructions"]
            items.append(item)
    return items


def get_instrument_items(instrument_id):
    """获取某个量表的所有题目"""
    inst = load_instrument(instrument_id)
    items = []
    for item in inst["items"]:
        item["_instrument_id"] = instrument_id
        item["_scale_type"] = inst["response_scale"]["type"]
        item["_scale_points"] = inst["response_scale"]["points"]
        item["_scale_labels"] = inst["response_scale"]["labels"]
        item["_instructions"] = inst["instructions"]
        items.append(item)
    return items


@assessment_bp.route("/")
def assessment_page():
    """渲染评估页面"""
    return render_template("assessment.html")


@assessment_bp.route("/start", methods=["POST"])
def start():
    """初始化评估会话，返回第一个问题"""
    mgr = SessionManager()
    session = mgr.create_session()

    # 设置阶段一
    session.current_phase = 1
    session.phase_instruments = PHASE1_INSTRUMENTS
    session.current_instrument = "bfi2"
    session.current_item_index = 0

    all_items = get_all_phase1_items()
    mgr.save_session(session)

    return jsonify({
        "session_id": session.session_id,
        "phase": 1,
        "total_items": len(all_items),
        "current_index": 0,
        "question": _format_question(all_items[0], 0, len(all_items)),
    })


@assessment_bp.route("/question", methods=["GET"])
def get_question():
    """获取当前题目"""
    session_id = request.args.get("session_id")
    mgr = SessionManager()
    session = mgr.get_session(session_id)
    if not session:
        return jsonify({"error": "session not found"}), 404

    items = _get_current_items(session)
    idx = session.current_item_index

    if idx >= len(items):
        return jsonify({"phase_complete": True, "phase": session.current_phase})

    question = _format_question(items[idx], idx, len(items))
    return jsonify({
        "session_id": session.session_id,
        "phase": session.current_phase,
        "total_items": len(items),
        "current_index": idx,
        "question": question,
        "has_previous": idx > 0,
        "current_answer": session.responses.get(items[idx]["id"]),
    })


@assessment_bp.route("/answer", methods=["POST"])
def answer():
    """接收答案，移动到下一题或触发阶段转换"""
    data = request.get_json()
    session_id = data.get("session_id")
    item_id = data.get("item_id")
    score = data.get("score")
    direction = data.get("direction", "next")  # "next" or "prev"

    mgr = SessionManager()
    session = mgr.get_session(session_id)
    if not session:
        return jsonify({"error": "session not found"}), 404

    # 保存答案
    if score is not None:
        session.responses[item_id] = score

    items = _get_current_items(session)

    if direction == "next":
        session.current_item_index += 1
    elif direction == "prev" and session.current_item_index > 0:
        session.current_item_index -= 1

    # 检查当前阶段是否完成
    if session.current_item_index >= len(items):
        if session.current_phase == 1:
            return _handle_phase1_complete(session)
        elif session.current_phase == 2:
            return _handle_phase2_complete(session)
        elif session.current_phase == 3:
            return _handle_phase3_complete(session)

    mgr.save_session(session)
    return jsonify({
        "status": "ok",
        "current_index": session.current_item_index,
        "total_items": len(items),
    })


@assessment_bp.route("/progress", methods=["GET"])
def progress():
    """返回当前进度"""
    session_id = request.args.get("session_id")
    mgr = SessionManager()
    session = mgr.get_session(session_id)
    if not session:
        return jsonify({"error": "session not found"}), 404

    items = _get_current_items(session)
    return jsonify({
        "phase": session.current_phase,
        "current_index": session.current_item_index,
        "total_items": len(items),
        "answered_count": len(session.responses),
        "is_complete": session.is_complete,
    })


def _get_current_items(session):
    """获取当前阶段的所有题目"""
    if session.current_phase == 1:
        return get_all_phase1_items()
    elif session.current_phase == 2:
        all_items = []
        for inst_id in session.phase_instruments:
            all_items.extend(get_instrument_items(inst_id))
        return all_items
    elif session.current_phase == 3:
        return _get_open_questions(session)
    return []


def _format_question(item, index, total):
    """将原始题目格式化为前端可用的结构"""
    q = {
        "id": item["id"],
        "text": item.get("text", ""),
        "number": index + 1,
        "total": total,
        "scale_type": item.get("_scale_type", "likert"),
        "scale_points": item.get("_scale_points", 5),
        "scale_labels": item.get("_scale_labels", {}),
        "instructions": item.get("_instructions", ""),
        "instrument_id": item.get("_instrument_id", ""),
    }
    # 强制选择题的选项文本
    if item.get("text_a"):
        q["text_a"] = item["text_a"]
        q["text_b"] = item["text_b"]
    return q


def _handle_phase1_complete(session):
    """阶段一完成：计算基础分数，决定阶段二的量表"""
    mgr = SessionManager()

    # 简单评分：计算各维度原始分
    from app.models.scoring import ScoringEngine
    from app.models.norms import NormsManager

    norms_mgr = NormsManager()
    engine = ScoringEngine(norms_mgr)

    bfi2 = load_instrument("bfi2")
    rses = load_instrument("rses")

    # 提取 BFI-2 回答
    bfi2_responses = {k: v for k, v in session.responses.items() if k.startswith("bfi2_")}
    rses_responses = {k: v for k, v in session.responses.items() if k.startswith("rses_")}

    bfi2_scores = engine.score_bfi2(bfi2_responses, bfi2)
    rses_scores = engine.score_rses(rses_responses, rses)

    session.phase1_scores = {
        "bfi2": {k: v for k, v in bfi2_scores["domains"].items()},
        "rses": rses_scores,
    }

    # 决定阶段二
    from app.services.adaptive_engine import AdaptiveEngine
    adaptive = AdaptiveEngine()
    phase2_instruments = adaptive.determine_phase2(session.phase1_scores)

    session.completed_instruments = PHASE1_INSTRUMENTS[:]
    session.current_phase = 2
    session.current_item_index = 0
    session.phase_instruments = phase2_instruments

    mgr.save_session(session)

    if not phase2_instruments:
        # 无需额外量表，直接进入阶段三
        return _start_phase3(session)

    instrument_names = [load_instrument(i)["name"] for i in phase2_instruments]
    return jsonify({
        "phase_complete": True,
        "phase": 1,
        "next_phase": 2,
        "phase2_instruments": instrument_names,
        "message": f"第一阶段完成。接下来将进行补充评估，约 {sum(len(load_instrument(i)['items']) for i in phase2_instruments)} 题。",
    })


def _handle_phase2_complete(session):
    """阶段二完成"""
    session.completed_instruments.extend(session.phase_instruments)
    return _start_phase3(session)


def _start_phase3(session):
    """开始阶段三：开放式自述题"""
    mgr = SessionManager()
    session.current_phase = 3
    session.current_item_index = 0
    session.phase_instruments = []

    from app.services.adaptive_engine import AdaptiveEngine
    adaptive = AdaptiveEngine()

    all_scores = _compute_all_scores(session)
    session.all_scores = all_scores

    open_questions = adaptive.generate_phase3_questions(all_scores)
    session.phase_instruments = ["open_text"]
    session._open_questions = open_questions

    mgr.save_session(session)

    if not open_questions:
        return _complete_assessment(session)

    return jsonify({
        "phase_complete": True,
        "phase": 2,
        "next_phase": 3,
        "total_items": len(open_questions),
        "message": "接下来是最后几个开放式问题，请根据自己的实际情况简要作答。",
    })


def _handle_phase3_complete(session):
    """阶段三完成，生成报告"""
    return _complete_assessment(session)


def _complete_assessment(session):
    """完成整个评估"""
    mgr = SessionManager()
    session.is_complete = True
    session.all_scores = _compute_all_scores(session)
    mgr.save_session(session)

    return jsonify({
        "complete": True,
        "session_id": session.session_id,
        "redirect": f"/report/{session.session_id}",
    })


def _compute_all_scores(session):
    """计算所有量表的完整评分"""
    from app.models.scoring import ScoringEngine
    from app.models.norms import NormsManager

    norms_mgr = NormsManager()
    engine = ScoringEngine(norms_mgr)

    all_scores = {"bfi2": None, "rses": None, "sd3": None, "ecr_r": None, "crt": None, "rotter_ie": None}

    for inst_id in session.completed_instruments + session.phase_instruments:
        if inst_id in ("open_text",):
            continue
        try:
            inst = load_instrument(inst_id)
            responses = {k: v for k, v in session.responses.items() if k.startswith(f"{inst_id}_")}
            if not responses:
                continue

            if inst_id == "bfi2":
                all_scores["bfi2"] = engine.score_bfi2(responses, inst)
            elif inst_id == "rses":
                all_scores["rses"] = engine.score_rses(responses, inst)
            elif inst_id == "sd3":
                all_scores["sd3"] = engine.score_sd3(responses, inst)
            elif inst_id == "ecr_r":
                all_scores["ecr_r"] = engine.score_ecr_r(responses, inst)
            elif inst_id == "crt":
                all_scores["crt"] = engine.score_crt(responses, inst)
            elif inst_id == "rotter_ie":
                all_scores["rotter_ie"] = engine.score_rotter_ie(responses, inst)
        except Exception:
            pass

    return all_scores


def _get_open_questions(session):
    """获取阶段三的开放式问题"""
    qs = getattr(session, "_open_questions", [])
    items = []
    for i, q in enumerate(qs):
        items.append({
            "id": f"open_{i}",
            "text": q["text"],
            "scale_type": "open_text",
            "scale_points": 0,
            "scale_labels": {},
            "instructions": q.get("instructions", "请根据自己的实际情况简要作答。（建议 50-200 字）"),
            "_instrument_id": "open_text",
            "_scale_type": "open_text",
            "_scale_points": 0,
            "_scale_labels": {},
            "_instructions": q.get("instructions", "请根据自己的实际情况简要作答。（建议 50-200 字）"),
        })
    return items
