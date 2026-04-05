from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple


# =========================================================
# Question specs for concept-aware feedback
# =========================================================

QUESTION_FEEDBACK_GUIDE: Dict[str, Dict[str, str]] = {
    "1.1": {
        "concept": "Architecture-neutral in Java",
        "expected_short": "Java can run across different architectures/systems, not only one specific machine.",
        "wrong": (
            "Your answer did not clearly explain architecture-neutrality. "
            "The main idea is that Java is designed to work across different architectures "
            "and is not restricted to one specific system."
        ),
        "partial": (
            "Your answer points in the correct direction, but it should more clearly state "
            "that Java is not tied to one specific architecture or hardware platform."
        ),
        "full": "You correctly explained that Java is not limited to one architecture.",
    },
    "1.2": {
        "concept": "Role of WWW and Internet in Java's emergence",
        "expected_short": "WWW/Internet created a need for portable or platform-independent programs.",
        "wrong": (
            "Your answer did not clearly explain the role of the WWW/Internet. "
            "The expected idea is that they created a need for platform-independent "
            "or distributed programs."
        ),
        "partial": (
            "You mentioned part of the context, but your answer should more clearly connect "
            "the WWW/Internet with the demand for portable Java programs."
        ),
        "full": "You correctly linked the WWW/Internet to the need for portable Java programs.",
    },
    "1.3": {
        "concept": "Difference between OOP and POP",
        "expected_short": "POP is procedure/data-oriented; OOP is object/class-oriented.",
        "wrong": (
            "Your answer did not clearly distinguish OOP from POP. "
            "The key point is that POP focuses on procedures/functions, while OOP focuses "
            "on objects/classes."
        ),
        "partial": (
            "You identified part of the difference, but the answer should clearly show "
            "that POP is procedure-oriented and OOP is object-oriented."
        ),
        "full": "You correctly distinguished OOP from POP.",
    },
    "1.4": {
        "concept": "Components of JRE",
        "expected_short": "Examples include JVM, libraries, and supporting files/components.",
        "wrong": (
            "Your answer did not mention a valid JRE component. "
            "A correct answer could include JVM, libraries, or supporting files/components."
        ),
        "partial": (
            "Your answer was close, but it needed a clearer valid JRE component such as JVM or libraries."
        ),
        "full": "You correctly mentioned a valid JRE component.",
    },
    "1.5": {
        "concept": "Inheritance vs polymorphism",
        "expected_short": (
            "Inheritance means a class gets properties/behavior from another class; "
            "polymorphism means one interface/common type with multiple forms."
        ),
        "wrong": (
            "Your answer did not clearly explain inheritance or polymorphism. "
            "Inheritance is about deriving from another class, while polymorphism is about "
            "having multiple forms under one common type/interface."
        ),
        "partial": (
            "You explained one of the two ideas correctly, but the other part was missing or unclear. "
            "You needed both inheritance and polymorphism for full credit."
        ),
        "full": "You correctly explained both inheritance and polymorphism.",
    },
    "1.6": {
        "concept": "Encapsulation",
        "expected_short": "Encapsulation means binding data and code/methods together in one class/unit.",
        "wrong": (
            "Your answer did not clearly define encapsulation. "
            "The expected idea is combining data and the methods that operate on it "
            "into one unit, usually a class."
        ),
        "partial": (
            "Your answer captured part of the idea, but it should more clearly connect "
            "data and methods inside one unit/class."
        ),
        "full": "You correctly explained encapsulation.",
    },
    "1.7": {
        "concept": "Ways to achieve abstraction",
        "expected_short": "Abstract classes and interfaces.",
        "wrong": (
            "Your answer did not state the two standard ways to achieve abstraction. "
            "The expected answer is abstract classes and interfaces."
        ),
        "partial": (
            "You mentioned one valid way, but full credit required both abstract classes and interfaces."
        ),
        "full": "You correctly identified the ways to achieve abstraction.",
    },
    "1.8": {
        "concept": "Reasons a thread may terminate",
        "expected_short": "Finish normally, stop due to exception/error, or become dead/stopped/terminated.",
        "wrong": (
            "Your answer did not include valid reasons for thread termination. "
            "Valid examples include normal completion, exception/error, or the thread being stopped/dead."
        ),
        "partial": (
            "You gave one or more correct reasons, but more valid reasons were needed for full credit."
        ),
        "full": "You correctly gave valid reasons for thread termination.",
    },
    "1.9": {
        "concept": "Default streams in Java",
        "expected_short": "System.in, System.out, and System.err.",
        "wrong": (
            "Your answer did not correctly identify the default Java streams. "
            "The expected streams are System.in, System.out, and System.err."
        ),
        "partial": (
            "You identified some of the correct streams, but full credit required all three: "
            "System.in, System.out, and System.err."
        ),
        "full": "You correctly identified the default Java streams.",
    },
    "1.10": {
        "concept": "Swing built on top of",
        "expected_short": "AWT (Abstract Window Toolkit).",
        "wrong": (
            "Your answer did not correctly identify the toolkit under Swing. "
            "The expected answer is AWT (Abstract Window Toolkit)."
        ),
        "partial": (
            "Your answer was close, but it needed to clearly identify AWT / Abstract Window Toolkit."
        ),
        "full": "You correctly identified AWT as the base for Swing.",
    },

    "2.1": {
        "concept": "True/False item 2.1",
        "expected_short": "Correct choice: True.",
        "wrong": "The correct choice for this statement was True.",
        "partial": "The True/False choice was not fully correct.",
        "full": "You selected the correct True/False answer.",
    },
    "2.2": {
        "concept": "True/False item 2.2",
        "expected_short": "Correct choice: False.",
        "wrong": "The correct choice for this statement was False.",
        "partial": "The True/False choice was not fully correct.",
        "full": "You selected the correct True/False answer.",
    },
    "2.3": {
        "concept": "True/False item 2.3",
        "expected_short": "Correct choice: True.",
        "wrong": "The correct choice for this statement was True.",
        "partial": "The True/False choice was not fully correct.",
        "full": "You selected the correct True/False answer.",
    },
    "2.4": {
        "concept": "True/False item 2.4",
        "expected_short": "Correct choice: False.",
        "wrong": "The correct choice for this statement was False.",
        "partial": "The True/False choice was not fully correct.",
        "full": "You selected the correct True/False answer.",
    },
    "2.5": {
        "concept": "True/False item 2.5",
        "expected_short": "Correct choice: True.",
        "wrong": "The correct choice for this statement was True.",
        "partial": "The True/False choice was not fully correct.",
        "full": "You selected the correct True/False answer.",
    },
    "2.6": {
        "concept": "True/False item 2.6",
        "expected_short": "Correct choice: True.",
        "wrong": "The correct choice for this statement was True.",
        "partial": "The True/False choice was not fully correct.",
        "full": "You selected the correct True/False answer.",
    },
    "2.7": {
        "concept": "True/False item 2.7",
        "expected_short": "Correct choice: False.",
        "wrong": "The correct choice for this statement was False.",
        "partial": "The True/False choice was not fully correct.",
        "full": "You selected the correct True/False answer.",
    },

    "3.1": {
        "concept": "Reason for computer language innovation",
        "expected_short": "Improving programming or adapting to changing needs/environments.",
        "wrong": (
            "Your answer did not state the expected reason clearly. "
            "The answer should mention improvement in programming or adapting to changing environments/uses."
        ),
        "partial": (
            "Your answer was partly relevant, but it needed to more clearly mention improvement "
            "or adaptation to changing needs."
        ),
        "full": "You correctly stated the reason for language innovation.",
    },
    "3.2": {
        "concept": "Example of POP language",
        "expected_short": "C or Pascal.",
        "wrong": "The expected example of a POP language was C or Pascal.",
        "partial": "Your answer was close, but the expected example was C or Pascal.",
        "full": "You correctly gave an example of a POP language.",
    },
    "3.3": {
        "concept": "POP does not allow _____ to flow freely",
        "expected_short": "data",
        "wrong": "The expected missing word was data.",
        "partial": "Your answer was close, but the required word was data.",
        "full": "You correctly identified the missing word.",
    },
    "3.4": {
        "concept": "Java-enabled browser programs",
        "expected_short": "Applets",
        "wrong": "The expected answer was Applets.",
        "partial": "Your answer was close, but the required term was Applets.",
        "full": "You correctly identified Applets.",
    },
    "3.5": {
        "concept": "Component that can contain other elements",
        "expected_short": "Container or Frame",
        "wrong": "The expected answer was Container. Frame was also accepted.",
        "partial": "Your answer was close, but it needed to clearly identify Container or Frame.",
        "full": "You correctly identified Container / Frame.",
    },
    "3.6": {
        "concept": "Model-view-_____ in Swing",
        "expected_short": "Controller",
        "wrong": "The expected missing term was Controller.",
        "partial": "Your answer was close, but the expected term was Controller.",
        "full": "You correctly identified Controller.",
    },
    "3.7": {
        "concept": "Java database API",
        "expected_short": "JDBC or Java Database Connectivity",
        "wrong": (
            "Your answer did not correctly identify the Java database API. "
            "The expected answer was JDBC (Java Database Connectivity)."
        ),
        "partial": "Your answer was close, but it needed to clearly identify JDBC.",
        "full": "You correctly identified JDBC.",
    },

    "4.1": {
        "concept": "Seat assignment output code",
        "expected_short": (
            "Accepted full answers included one of the valid seat expressions such as "
            "(students.length - i - 1), (4 - i), or (i) in the accepted context."
        ),
        "wrong": (
            "Your code did not match one of the accepted full answers. "
            "To get full credit, the output logic needed to match one of the accepted seat expressions."
        ),
        "partial": (
            "Your code was relevant, but it did not fully match one of the accepted final solutions, "
            "so some marks were deducted."
        ),
        "full": "You provided an accepted full solution for the seat assignment logic.",
    },
    "4.2": {
        "concept": "Vote calculation output code",
        "expected_short": "calculateVotes(totalVotes);",
        "wrong": (
            "Your code did not clearly provide the required method call. "
            "The expected solution was calculateVotes(totalVotes);"
        ),
        "partial": (
            "Your answer showed relevant logic, but the final code was not fully correct, "
            "so only partial credit was awarded."
        ),
        "full": "You correctly provided the required vote calculation code.",
    },
}


# =========================================================
# Helpers
# =========================================================

def _load_json(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _safe_read_text(path: str | None) -> str:
    if not path:
        return ""
    p = Path(path)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8").strip()


def _score_band(total: float, max_total: float) -> Tuple[str, str]:
    percent = 0.0 if max_total <= 0 else (total / max_total) * 100.0

    if percent >= 85:
        return "Excellent", "Excellent overall performance with only minor weaknesses."
    if percent >= 70:
        return "Very Good", "Very good performance with a solid understanding of most topics."
    if percent >= 50:
        return "Good / متوسط", "Reasonable performance, but there are several areas that need improvement."
    if percent >= 35:
        return "Weak", "The student shows partial understanding, but important concepts are missing or unclear."
    return "Very Weak", "The student needs major improvement across several core Java topics."


def _question_label(qid: str) -> str:
    if qid.startswith("1."):
        return f"Short Answer {qid}"
    if qid.startswith("2."):
        return f"True/False {qid}"
    if qid.startswith("3."):
        return f"Fill in the Blank {qid}"
    if qid.startswith("4."):
        return f"Programming {qid}"
    return qid


def _section_max_scores(questions: Dict[str, Any]) -> Dict[str, float]:
    out = {"q1": 0.0, "q2": 0.0, "q3": 0.0, "q4": 0.0, "overall": 0.0}
    for qid, obj in questions.items():
        mx = float(obj.get("max_score", 0))
        if qid.startswith("1."):
            out["q1"] += mx
        elif qid.startswith("2."):
            out["q2"] += mx
        elif qid.startswith("3."):
            out["q3"] += mx
        elif qid.startswith("4."):
            out["q4"] += mx
        out["overall"] += mx
    return out


def _sort_qids(qid: str):
    a, b = qid.split(".")
    return (int(a), int(b))


def _classify_result(score: float, max_score: float) -> str:
    if max_score <= 0:
        return "wrong"
    if score <= 0:
        return "wrong"
    if score >= max_score:
        return "full"
    return "partial"


def _build_question_feedback(
    qid: str,
    score: float,
    max_score: float,
    answer: str,
    grader_reason: str,
) -> Dict[str, Any]:
    guide = QUESTION_FEEDBACK_GUIDE.get(qid, {})
    result_type = _classify_result(score, max_score)
    lost_marks = max(0.0, max_score - score)

    concept = guide.get("concept", qid)
    expected_short = guide.get("expected_short", "Review the expected answer for this question.")

    if not (answer or "").strip():
        comment = (
            "No usable answer was detected for this question, so full marks could not be awarded. "
            f"Expected idea: {expected_short}"
        )
    else:
        if result_type == "full":
            comment = guide.get("full", "Good answer. The required idea was captured correctly.")
        elif result_type == "partial":
            comment = guide.get(
                "partial",
                f"Your answer was partially correct. Expected idea: {expected_short}"
            )
        else:
            comment = guide.get(
                "wrong",
                f"Your answer did not match the expected concept. Expected idea: {expected_short}"
            )

    regrade_note = ""
    if lost_marks > 0:
        regrade_note = (
            "If the student believes this answer was misunderstood due to handwriting, OCR issues, "
            "or because the intended meaning was correct but not recognized, this question can be reviewed again."
        )

    return {
        "qid": qid,
        "label": _question_label(qid),
        "concept": concept,
        "score": score,
        "max_score": max_score,
        "lost_marks": lost_marks,
        "student_answer": answer.strip(),
        "expected_short": expected_short,
        "result_type": result_type,
        "comment": comment,
        "grader_reason": grader_reason.strip(),
        "regrade_note": regrade_note,
    }


def _collect_strengths(question_feedback: List[Dict[str, Any]]) -> List[str]:
    strengths: List[str] = []

    full_qids = {x["qid"] for x in question_feedback if x["result_type"] == "full"}

    oop_group = {"1.3", "1.5", "1.6", "1.7"}
    api_group = {"1.4", "1.9", "1.10", "3.5", "3.6", "3.7"}
    tf_group = {"2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7"}
    code_group = {"4.1", "4.2"}

    if len(full_qids & oop_group) >= 2:
        strengths.append("Good understanding of key OOP concepts.")
    if len(full_qids & api_group) >= 2:
        strengths.append("Good recall of Java platform/components and APIs.")
    if len(full_qids & tf_group) >= 5:
        strengths.append("Strong performance in conceptual True/False distinctions.")
    if len(full_qids & code_group) >= 1:
        strengths.append("Good performance in programming/application questions.")

    if not strengths:
        strengths.append("There are some correct answers that can be built on with more revision.")

    return strengths


def _collect_weaknesses(question_feedback: List[Dict[str, Any]]) -> List[str]:
    weaknesses: List[str] = []

    not_full = [x for x in question_feedback if x["result_type"] != "full"]
    low_qids = {x["qid"] for x in not_full}

    oop_group = {"1.3", "1.5", "1.6", "1.7"}
    java_core_group = {"1.1", "1.2", "1.4", "1.8", "1.9", "1.10"}
    terms_group = {"3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7"}
    code_group = {"4.1", "4.2"}

    if len(low_qids & oop_group) >= 2:
        weaknesses.append("There are weaknesses in core OOP concepts such as abstraction, encapsulation, inheritance, or polymorphism.")
    if len(low_qids & java_core_group) >= 3:
        weaknesses.append("Java fundamentals and platform-related concepts need more review.")
    if len(low_qids & terms_group) >= 3:
        weaknesses.append("Short technical terms and exact Java keywords need more precision.")
    if len(low_qids & code_group) >= 1:
        weaknesses.append("Programming/code-completion answers need more attention to exact logic and final syntax.")

    if not weaknesses:
        weaknesses.append("No major weakness pattern was detected from the current grading output.")

    return weaknesses


def _collect_recommendations(question_feedback: List[Dict[str, Any]]) -> List[str]:
    recs: List[str] = []
    low_qids = {x["qid"] for x in question_feedback if x["result_type"] != "full"}

    if low_qids & {"1.3", "1.5", "1.6", "1.7"}:
        recs.append("Revise OOP fundamentals: OOP vs POP, encapsulation, abstraction, inheritance, and polymorphism.")
    if low_qids & {"1.4", "1.9", "1.10", "3.5", "3.6", "3.7"}:
        recs.append("Review Java platform/components and common APIs such as JRE, AWT, MVC, Container, and JDBC.")
    if low_qids & {"2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7"}:
        recs.append("Practice conceptual True/False questions and pay close attention to the exact wording of each statement.")
    if low_qids & {"4.1", "4.2"}:
        recs.append("Practice short code-completion questions and verify the exact final output, method call, and expression.")
    if low_qids & {"3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7"}:
        recs.append("Memorize short Java technical terms and standard definitions more precisely.")

    if not recs:
        recs.append("Keep practicing mixed Java questions to maintain this level.")

    return recs


def _build_regrade_summary(question_feedback: List[Dict[str, Any]]) -> List[str]:
    flagged = [x for x in question_feedback if x["lost_marks"] > 0]

    if not flagged:
        return ["No deductions were recorded, so there is nothing to recheck in this script."]

    lines: List[str] = []
    for item in flagged:
        lines.append(
            f"{item['label']}: lost {item['lost_marks']:.1f} mark(s). "
            f"Reason to review if needed: possible unclear wording / handwriting / OCR or partially recognized intended meaning."
        )
    return lines


# =========================================================
# Main feedback generation
# =========================================================

def build_feedback_payload(
    grades_payload: Dict[str, Any],
    feedback_policy_text: str = "",
    student_name: str = "",
    student_id: str = "",
) -> Dict[str, Any]:
    grading = grades_payload.get("grading", {})
    questions = grading.get("questions", {})
    totals = grading.get("totals", {})

    question_feedback: List[Dict[str, Any]] = []

    for qid in sorted(questions.keys(), key=_sort_qids):
        obj = questions[qid]
        score = float(obj.get("score", 0))
        max_score = float(obj.get("max_score", 0))
        answer = str(obj.get("answer", "") or "")
        grader_reason = str(obj.get("reason", "") or "")

        question_feedback.append(
            _build_question_feedback(
                qid=qid,
                score=score,
                max_score=max_score,
                answer=answer,
                grader_reason=grader_reason,
            )
        )

    section_max = _section_max_scores(questions)

    overall = float(totals.get("overall", 0))
    q1_total = float(totals.get("q1", 0))
    q2_total = float(totals.get("q2", 0))
    q3_total = float(totals.get("q3", 0))
    q4_total = float(totals.get("q4", 0))

    band, band_comment = _score_band(overall, section_max["overall"])
    strengths = _collect_strengths(question_feedback)
    weaknesses = _collect_weaknesses(question_feedback)
    recommendations = _collect_recommendations(question_feedback)
    regrade_summary = _build_regrade_summary(question_feedback)

    lost_total = max(0.0, section_max["overall"] - overall)

    return {
        "student": {
            "student_name": student_name,
            "student_id": student_id,
        },
        "overall": {
            "score": overall,
            "max_score": section_max["overall"],
            "lost_marks": lost_total,
            "band": band,
            "summary": band_comment,
        },
        "sections": {
            "q1": {"score": q1_total, "max_score": section_max["q1"], "label": "Short Answer"},
            "q2": {"score": q2_total, "max_score": section_max["q2"], "label": "True/False"},
            "q3": {"score": q3_total, "max_score": section_max["q3"], "label": "Fill in the Blank"},
            "q4": {"score": q4_total, "max_score": section_max["q4"], "label": "Programming"},
        },
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommendations": recommendations,
        "regrade_summary": regrade_summary,
        "question_feedback": question_feedback,
        "feedback_policy_text": feedback_policy_text,
    }


def render_feedback_text(payload: Dict[str, Any], include_internal_notes: bool = False) -> str:
    student = payload.get("student", {})
    overall = payload.get("overall", {})
    sections = payload.get("sections", {})
    strengths = payload.get("strengths", [])
    weaknesses = payload.get("weaknesses", [])
    recommendations = payload.get("recommendations", [])
    regrade_summary = payload.get("regrade_summary", [])
    qitems = payload.get("question_feedback", [])
    feedback_policy_text = payload.get("feedback_policy_text", "")

    lines: List[str] = []

    lines.append("Java Exam Feedback Report")
    lines.append("=" * 70)
    lines.append("")

    if student.get("student_name"):
        lines.append(f"Student Name: {student['student_name']}")
    if student.get("student_id"):
        lines.append(f"Student ID: {student['student_id']}")
    if student.get("student_name") or student.get("student_id"):
        lines.append("")

    lines.append(f"Overall Score: {overall.get('score', 0):.1f}/{overall.get('max_score', 0):.1f}")
    lines.append(f"Marks Lost: {overall.get('lost_marks', 0):.1f}")
    lines.append(f"Performance Level: {overall.get('band', '')}")
    lines.append(f"Summary: {overall.get('summary', '')}")
    lines.append("")

    lines.append("Section Scores")
    lines.append("-" * 70)
    lines.append(
        f"Question 1 (Short Answer): {sections.get('q1', {}).get('score', 0):.1f}/"
        f"{sections.get('q1', {}).get('max_score', 0):.1f}"
    )
    lines.append(
        f"Question 2 (True/False): {sections.get('q2', {}).get('score', 0):.1f}/"
        f"{sections.get('q2', {}).get('max_score', 0):.1f}"
    )
    lines.append(
        f"Question 3 (Fill in the Blank): {sections.get('q3', {}).get('score', 0):.1f}/"
        f"{sections.get('q3', {}).get('max_score', 0):.1f}"
    )
    lines.append(
        f"Question 4 (Programming): {sections.get('q4', {}).get('score', 0):.1f}/"
        f"{sections.get('q4', {}).get('max_score', 0):.1f}"
    )
    lines.append("")

    lines.append("Strengths")
    lines.append("-" * 70)
    for s in strengths:
        lines.append(f"- {s}")
    lines.append("")

    lines.append("Main Areas to Improve")
    lines.append("-" * 70)
    for w in weaknesses:
        lines.append(f"- {w}")
    lines.append("")

    lines.append("Question-by-Question Comments")
    lines.append("-" * 70)
    for item in qitems:
        lines.append(
            f"{item['label']} -> {item['score']:.1f}/{item['max_score']:.1f} "
            f"(lost {item['lost_marks']:.1f})"
        )
        lines.append(f"  Concept: {item['concept']}")
        lines.append(f"  Expected: {item['expected_short']}")
        if item["student_answer"]:
            lines.append(f"  Your answer: {item['student_answer']}")
        else:
            lines.append("  Your answer: [No usable answer detected]")
        lines.append(f"  Comment: {item['comment']}")
        if item["regrade_note"]:
            lines.append(f"  Recheck note: {item['regrade_note']}")
        if include_internal_notes and item.get("grader_reason"):
            lines.append(f"  Internal grading note: {item['grader_reason']}")
        lines.append("")

    lines.append("Recommendations")
    lines.append("-" * 70)
    for r in recommendations:
        lines.append(f"- {r}")
    lines.append("")

    lines.append("Regrade / Recheck Summary")
    lines.append("-" * 70)
    for r in regrade_summary:
        lines.append(f"- {r}")
    lines.append("")

    if feedback_policy_text:
        lines.append("Feedback Policy / Notes")
        lines.append("-" * 70)
        lines.append(feedback_policy_text)
        lines.append("")

    lines.append("End of Feedback")
    return "\n".join(lines).strip() + "\n"


def build_feedback_text(
    grades_payload: Dict[str, Any],
    feedback_policy_text: str = "",
    student_name: str = "",
    student_id: str = "",
    include_internal_notes: bool = False,
) -> str:
    payload = build_feedback_payload(
        grades_payload=grades_payload,
        feedback_policy_text=feedback_policy_text,
        student_name=student_name,
        student_id=student_id,
    )
    return render_feedback_text(payload, include_internal_notes=include_internal_notes)


def generate_feedback(
    grades_json_path: str,
    feedback_policy_path: str | None,
    out_feedback_txt_path: str,
    model: str | None = None,   # kept for compatibility
    out_feedback_json_path: str | None = None,
    include_internal_notes: bool = False,
    student_name: str = "",
    student_id: str = "",
) -> str:
    grades_payload = _load_json(grades_json_path)
    feedback_policy_text = _safe_read_text(feedback_policy_path)

    payload = build_feedback_payload(
        grades_payload=grades_payload,
        feedback_policy_text=feedback_policy_text,
        student_name=student_name,
        student_id=student_id,
    )

    feedback_text = render_feedback_text(
        payload,
        include_internal_notes=include_internal_notes,
    )

    out_path = Path(out_feedback_txt_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(feedback_text, encoding="utf-8")

    if out_feedback_json_path:
        json_path = Path(out_feedback_json_path)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return feedback_text