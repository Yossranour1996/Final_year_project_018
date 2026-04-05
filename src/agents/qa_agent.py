from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List


# =========================================================
# Helpers
# =========================================================

def _load_json(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _norm_text(s: str) -> str:
    return " ".join((s or "").strip().lower().split())


def _is_blank_answer(answer: str) -> bool:
    return not _norm_text(answer)


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def _sort_qids(qid: str):
    a, b = qid.split(".")
    return (int(a), int(b))


def _get_questions(grading: Dict[str, Any]) -> Dict[str, Any]:
    questions = grading.get("questions", {})
    return questions if isinstance(questions, dict) else {}


def _get_totals(grading: Dict[str, Any]) -> Dict[str, Any]:
    totals = grading.get("totals", {})
    return totals if isinstance(totals, dict) else {}


# =========================================================
# QA checks
# =========================================================

def _check_score_validity(questions: Dict[str, Any]) -> List[Dict[str, Any]]:
    flags: List[Dict[str, Any]] = []

    for qid, obj in questions.items():
        score = _safe_float(obj.get("score", 0))
        max_score = _safe_float(obj.get("max_score", 0))

        if score < 0:
            flags.append({
                "qid": qid,
                "severity": "high",
                "type": "NEGATIVE_SCORE",
                "message": f"Question {qid} has a negative score ({score}).",
            })

        if score > max_score:
            flags.append({
                "qid": qid,
                "severity": "high",
                "type": "SCORE_EXCEEDS_MAX",
                "message": f"Question {qid} has score {score} greater than max_score {max_score}.",
            })

    return flags


def _check_blank_vs_score(questions: Dict[str, Any]) -> List[Dict[str, Any]]:
    flags: List[Dict[str, Any]] = []

    for qid, obj in questions.items():
        answer = str(obj.get("answer", "") or "")
        score = _safe_float(obj.get("score", 0))
        max_score = _safe_float(obj.get("max_score", 0))

        blank = _is_blank_answer(answer)

        if blank and score > 0:
            flags.append({
                "qid": qid,
                "severity": "high",
                "type": "BLANK_BUT_NONZERO_SCORE",
                "message": f"Question {qid} appears blank, but received {score}/{max_score}.",
            })

        # خلي هذا medium لأنه قد يكون صحيحًا لكنه يستحق المراجعة
        if (not blank) and score == 0:
            flags.append({
                "qid": qid,
                "severity": "medium",
                "type": "NONBLANK_BUT_ZERO_SCORE",
                "message": f"Question {qid} has an answer, but received zero. It may need a manual recheck.",
            })

    return flags


def _check_reason_presence(questions: Dict[str, Any]) -> List[Dict[str, Any]]:
    flags: List[Dict[str, Any]] = []

    for qid, obj in questions.items():
        reason = str(obj.get("reason", "") or "").strip()
        if not reason:
            flags.append({
                "qid": qid,
                "severity": "low",
                "type": "MISSING_REASON",
                "message": f"Question {qid} has no grading reason/note.",
            })

    return flags


def _check_partial_code_answers(questions: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Focus on programming questions (4.x):
    - If the answer is non-empty and got zero, escalate review priority.
    """
    flags: List[Dict[str, Any]] = []

    for qid, obj in questions.items():
        if not qid.startswith("4."):
            continue

        answer = str(obj.get("answer", "") or "")
        score = _safe_float(obj.get("score", 0))
        max_score = _safe_float(obj.get("max_score", 0))

        if (not _is_blank_answer(answer)) and score == 0:
            flags.append({
                "qid": qid,
                "severity": "high",
                "type": "CODE_ANSWER_ZERO",
                "message": (
                    f"Programming question {qid} has a non-empty answer but received 0/{max_score}. "
                    "Manual QA review is strongly recommended."
                ),
            })

    return flags


def _check_short_answer_suspicious_full_marks(questions: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Very short answer + full marks is not necessarily wrong,
    but may deserve optional inspection.
    """
    flags: List[Dict[str, Any]] = []

    for qid, obj in questions.items():
        if not qid.startswith(("1.", "3.")):
            continue

        answer = str(obj.get("answer", "") or "").strip()
        score = _safe_float(obj.get("score", 0))
        max_score = _safe_float(obj.get("max_score", 0))

        word_count = len(answer.split())
        if answer and score == max_score and word_count == 1 and max_score >= 3:
            flags.append({
                "qid": qid,
                "severity": "low",
                "type": "VERY_SHORT_FULL_MARK",
                "message": (
                    f"Question {qid} received full marks with a one-word answer. "
                    "This may be correct, but QA can optionally inspect it."
                ),
            })

    return flags


def _check_total_consistency(grading: Dict[str, Any]) -> List[Dict[str, Any]]:
    flags: List[Dict[str, Any]] = []

    questions = _get_questions(grading)
    totals = _get_totals(grading)

    calc_q1 = calc_q2 = calc_q3 = calc_q4 = 0.0

    for qid, obj in questions.items():
        score = _safe_float(obj.get("score", 0))
        if qid.startswith("1."):
            calc_q1 += score
        elif qid.startswith("2."):
            calc_q2 += score
        elif qid.startswith("3."):
            calc_q3 += score
        elif qid.startswith("4."):
            calc_q4 += score

    calc_overall = calc_q1 + calc_q2 + calc_q3 + calc_q4

    declared_q1 = _safe_float(totals.get("q1", 0))
    declared_q2 = _safe_float(totals.get("q2", 0))
    declared_q3 = _safe_float(totals.get("q3", 0))
    declared_q4 = _safe_float(totals.get("q4", 0))
    declared_overall = _safe_float(totals.get("overall", 0))

    checks = [
        ("q1", calc_q1, declared_q1),
        ("q2", calc_q2, declared_q2),
        ("q3", calc_q3, declared_q3),
        ("q4", calc_q4, declared_q4),
        ("overall", calc_overall, declared_overall),
    ]

    for name, calc_value, declared_value in checks:
        if abs(calc_value - declared_value) > 1e-6:
            flags.append({
                "qid": None,
                "severity": "high",
                "type": "TOTAL_MISMATCH",
                "message": (
                    f"Declared total '{name}' = {declared_value}, "
                    f"but recomputed total = {calc_value}."
                ),
            })

    return flags


def _check_payload_shape(grades_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    flags: List[Dict[str, Any]] = []

    grading = grades_payload.get("grading")
    if not isinstance(grading, dict):
        flags.append({
            "qid": None,
            "severity": "high",
            "type": "MISSING_GRADING_BLOCK",
            "message": "The grades payload does not contain a valid 'grading' object.",
        })
        return flags

    if not isinstance(grading.get("questions", {}), dict):
        flags.append({
            "qid": None,
            "severity": "high",
            "type": "INVALID_QUESTIONS_BLOCK",
            "message": "The 'grading.questions' field is missing or not a dictionary.",
        })

    if not isinstance(grading.get("totals", {}), dict):
        flags.append({
            "qid": None,
            "severity": "high",
            "type": "INVALID_TOTALS_BLOCK",
            "message": "The 'grading.totals' field is missing or not a dictionary.",
        })

    return flags


def _deduplicate_flags(flags: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove exact duplicate flags if any.
    """
    seen = set()
    out = []

    for f in flags:
        key = (
            f.get("qid"),
            f.get("severity"),
            f.get("type"),
            f.get("message"),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(f)

    return out


def _collect_questions_to_review(flags: List[Dict[str, Any]]) -> List[str]:
    qids = []
    for f in flags:
        qid = f.get("qid")
        if qid and qid not in qids:
            qids.append(qid)
    return sorted(qids, key=_sort_qids)


def _build_status(flags: List[Dict[str, Any]]) -> str:
    if any(f["severity"] == "high" for f in flags):
        return "REVIEW"
    if any(f["severity"] == "medium" for f in flags):
        return "PASS_WITH_WARNINGS"
    return "PASS"


def _build_summary(flags: List[Dict[str, Any]], questions_to_review: List[str]) -> str:
    if not flags:
        return "No major QA issues were detected. The grading output passed the basic consistency checks."

    high = sum(1 for f in flags if f["severity"] == "high")
    medium = sum(1 for f in flags if f["severity"] == "medium")
    low = sum(1 for f in flags if f["severity"] == "low")

    return (
        f"QA detected {len(flags)} issue(s): "
        f"{high} high, {medium} medium, {low} low. "
        f"Questions recommended for review: {', '.join(questions_to_review) if questions_to_review else 'none'}."
    )


# =========================================================
# Main API
# =========================================================

def run_qa_on_grades_payload(
    grades_payload: Dict[str, Any],
    student_name: str = "",
    student_id: str = "",
) -> Dict[str, Any]:
    flags: List[Dict[str, Any]] = []
    flags.extend(_check_payload_shape(grades_payload))

    grading = grades_payload.get("grading", {})
    questions = _get_questions(grading)

    # only run deeper checks if grading/questions exist
    if isinstance(grading, dict) and isinstance(questions, dict):
        flags.extend(_check_score_validity(questions))
        flags.extend(_check_blank_vs_score(questions))
        flags.extend(_check_reason_presence(questions))
        flags.extend(_check_partial_code_answers(questions))
        flags.extend(_check_short_answer_suspicious_full_marks(questions))
        flags.extend(_check_total_consistency(grading))

    flags = _deduplicate_flags(flags)

    flags = sorted(
        flags,
        key=lambda x: (
            {"high": 0, "medium": 1, "low": 2}.get(x.get("severity", "low"), 3),
            (999, 999) if not x.get("qid") else _sort_qids(x["qid"]),
            x.get("type", ""),
        )
    )

    questions_to_review = _collect_questions_to_review(flags)
    status = _build_status(flags)
    summary = _build_summary(flags, questions_to_review)

    high_count = sum(1 for f in flags if f["severity"] == "high")
    medium_count = sum(1 for f in flags if f["severity"] == "medium")
    low_count = sum(1 for f in flags if f["severity"] == "low")

    return {
        "student": {
            "student_name": student_name,
            "student_id": student_id,
        },
        "qa": {
            "status": status,
            "review_recommended": bool(questions_to_review or high_count > 0),
            "flag_count": len(flags),
            "high_count": high_count,
            "medium_count": medium_count,
            "low_count": low_count,
            "questions_to_review": questions_to_review,
            "summary": summary,
            "flags": flags,
        },
    }


def render_qa_text(payload: Dict[str, Any]) -> str:
    student = payload.get("student", {})
    qa = payload.get("qa", {})

    lines: List[str] = []
    lines.append("QA Review Report")
    lines.append("=" * 70)
    lines.append("")

    if student.get("student_name"):
        lines.append(f"Student Name: {student['student_name']}")
    if student.get("student_id"):
        lines.append(f"Student ID: {student['student_id']}")
    if student.get("student_name") or student.get("student_id"):
        lines.append("")

    lines.append(f"QA Status: {qa.get('status', 'UNKNOWN')}")
    lines.append(f"Review Recommended: {qa.get('review_recommended', False)}")
    lines.append(f"Flag Count: {qa.get('flag_count', 0)}")
    lines.append(
        f"Severity Breakdown: high={qa.get('high_count', 0)}, "
        f"medium={qa.get('medium_count', 0)}, low={qa.get('low_count', 0)}"
    )
    qrev = qa.get("questions_to_review", [])
    lines.append(f"Questions to Review: {', '.join(qrev) if qrev else 'None'}")
    lines.append(f"Summary: {qa.get('summary', '')}")
    lines.append("")

    lines.append("Flags")
    lines.append("-" * 70)
    flags = qa.get("flags", [])
    if not flags:
        lines.append("- No QA flags detected.")
    else:
        for f in flags:
            qid = f.get("qid") or "GENERAL"
            lines.append(f"- [{f.get('severity', 'low').upper()}] {qid} | {f.get('type', '')}")
            lines.append(f"  {f.get('message', '')}")

    lines.append("")
    lines.append("End of QA Report")
    return "\n".join(lines).strip() + "\n"


def run_qa(
    grades_json_path: str,
    out_qa_json_path: str,
    out_qa_txt_path: str | None = None,
    student_name: str = "",
    student_id: str = "",
) -> Dict[str, Any]:
    grades_payload = _load_json(grades_json_path)

    payload = run_qa_on_grades_payload(
        grades_payload=grades_payload,
        student_name=student_name,
        student_id=student_id,
    )

    out_json = Path(out_qa_json_path)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if out_qa_txt_path:
        out_txt = Path(out_qa_txt_path)
        out_txt.parent.mkdir(parents=True, exist_ok=True)
        out_txt.write_text(render_qa_text(payload), encoding="utf-8")

    return payload