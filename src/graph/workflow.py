from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from langgraph.graph import StateGraph, END

from src.state import GraderState
from src.tools.pdf_to_images import pdf_to_images
from src.agents.extractor import extract_exam_pages
from src.tools.labeled_answers_to_json import structure_answers_from_manual_labels
from src.agents.java_exam_grader import grade_exam_from_structured_answers
from src.agents.qa_agent import run_qa
from src.agents.feedback_agent import generate_feedback
from src.agents.exporter import export_student_xlsx

from src.agents.attendance_compare_onefile import (
    _pdf_to_first_image,
    _gemini_json_from_image,
    ATTENDANCE_PROMPT,
    _read_sheet_identifiers,
    compare,
)


def _ensure_paths(state: GraderState) -> GraderState:
    out_root = state.get("out_root", "data/output")
    sheet_id = state.get("sheet_id", "sheet_001")
    base = Path(out_root) / sheet_id

    pages_dir = base / "pages"
    grading_dir = base / "grading_results"
    exports_dir = base / "exports"
    reports_dir = Path(out_root) / "_reports"

    pages_dir.mkdir(parents=True, exist_ok=True)
    grading_dir.mkdir(parents=True, exist_ok=True)
    exports_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    state["pages_dir"] = str(pages_dir)
    state["grades_json"] = str(grading_dir / "grades.json")
    state["qa_json"] = str(grading_dir / "qa_report.json")
    state["qa_txt"] = str(grading_dir / "qa_report.txt")
    state["feedback_txt"] = str(grading_dir / "feedback.txt")
    state["feedback_json"] = str(grading_dir / "feedback.json")
    state["export_xlsx"] = str(exports_dir / "results.xlsx")

    extraction_dir = state.get("extraction_dir", "answers")
    ext_dir = Path(extraction_dir)
    if not ext_dir.is_absolute():
        ext_dir = base / ext_dir
    ext_dir.mkdir(parents=True, exist_ok=True)

    state["extraction_dir_abs"] = str(ext_dir)
    state["extracted_answers_json"] = str(ext_dir / "raw_extraction.json")
    state["structured_answers_json"] = str(ext_dir / "structured_answers.json")
    state["sheet_identifiers_json"] = str(ext_dir / "sheet_identifiers.json")

    state["attendance_json"] = str(reports_dir / "attendance_present.json")
    state["attendance_compare_json"] = str(reports_dir / "attendance_compare.json")

    return state


def node_prepare(state: GraderState) -> GraderState:
    state.setdefault("logs", [])
    state.setdefault("errors", [])
    state = _ensure_paths(state)

    state["logs"].append("✅ prepare: paths ready")
    state["logs"].append(f"📌 raw extraction json: {state['extracted_answers_json']}")
    state["logs"].append(f"🧩 structured answers json: {state['structured_answers_json']}")
    state["logs"].append(f"🪪 identifiers json: {state['sheet_identifiers_json']}")
    state["logs"].append(f"📝 grades json: {state['grades_json']}")
    state["logs"].append(f"🛡️ qa json: {state['qa_json']}")
    state["logs"].append(f"🛡️ qa txt: {state['qa_txt']}")
    state["logs"].append(f"💬 feedback txt: {state['feedback_txt']}")
    state["logs"].append(f"🧾 feedback json: {state['feedback_json']}")
    state["logs"].append(f"📦 export xlsx: {state['export_xlsx']}")
    return state


def node_pdf_to_images(state: GraderState) -> GraderState:
    if not state.get("do_extract", False):
        state["logs"].append("⏭️ pdf_to_images skipped (do_extract=False)")
        return state

    student_pdf = state.get("student_pdf")
    if not student_pdf:
        state["errors"].append("Missing student_pdf for extraction")
        return state

    dpi = int(state.get("dpi", 300))
    mp = int(state.get("max_pages", 0))

    state["logs"].append(f"📄 pdf_to_images: dpi={dpi}, max_pages={mp}")
    pdf_to_images(student_pdf, state["pages_dir"], dpi=dpi, max_pages=mp)
    return state


def node_extract_exam(state: GraderState) -> GraderState:
    if not state.get("do_extract", False):
        state["logs"].append("⏭️ extract skipped (do_extract=False)")
        return state

    mp = state.get("max_pages")
    mp = None if (mp is None or int(mp) <= 0) else int(mp)

    state["logs"].append(f"🧠 extract_exam_pages: max_pages={mp}")
    extract_exam_pages(
        pages_dir=state["pages_dir"],
        out_dir=state["extraction_dir_abs"],
        max_pages=mp,
        manual_review=True,
    )

    if not Path(state["extracted_answers_json"]).exists():
        state["errors"].append(f"Extraction did not produce: {state['extracted_answers_json']}")
    else:
        state["logs"].append(f"✅ extraction ok: {state['extracted_answers_json']}")

    if not Path(state["sheet_identifiers_json"]).exists():
        state["errors"].append(f"Extraction did not produce: {state['sheet_identifiers_json']}")
    else:
        state["logs"].append(f"✅ identifiers ok: {state['sheet_identifiers_json']}")

    if not Path(state["structured_answers_json"]).exists():
        state["errors"].append(f"Extraction did not produce: {state['structured_answers_json']}")
    else:
        state["logs"].append(f"✅ structured answers ok: {state['structured_answers_json']}")

    return state


def node_structure_answers(state: GraderState) -> GraderState:
    structured_json = Path(state["structured_answers_json"])
    if structured_json.exists():
        state["logs"].append("⏭️ structure skipped (already produced after manual labeling)")
        return state

    manual_label_path = Path(state["extraction_dir_abs"]) / "manual_labels.txt"
    if not manual_label_path.exists():
        state["errors"].append(
            "manual_labels.txt not found, and structured_answers.json does not exist."
        )
        return state

    try:
        state["logs"].append("🧩 fallback structuring from manual_labels.txt")
        structure_answers_from_manual_labels(
            label_file_path=str(manual_label_path),
            out_json_path=state["structured_answers_json"],
        )
        state["logs"].append(f"✅ structured answers saved: {state['structured_answers_json']}")
    except Exception as e:
        state["errors"].append(f"Answer structuring failed: {e}")

    return state


def node_grade(state: GraderState) -> GraderState:
    if not state.get("do_grade", False):
        state["logs"].append("⏭️ grade skipped (do_grade=False)")
        return state

    structured = Path(state["structured_answers_json"])
    if not structured.exists():
        state["errors"].append("Missing structured_answers.json. Run extraction/manual labeling first.")
        return state

    state["logs"].append("📝 java_exam_grader: structured_answers.json → grades.json")

    result = grade_exam_from_structured_answers(
        structured_answers_json_path=str(structured),
        out_json_path=state["grades_json"],
        model=state.get("grader_model", "gemini-2.0-flash"),
    )

    total = result.get("grading", {}).get("totals", {}).get("overall", 0)
    state["logs"].append(f"✅ grades saved: {state['grades_json']}")
    state["logs"].append(f"🏁 total score: {total}/100")
    return state


def node_qa(state: GraderState) -> GraderState:
    if not state.get("do_qa", False):
        state["logs"].append("⏭️ qa skipped (do_qa=False)")
        return state

    grades_path = Path(state["grades_json"])
    if not grades_path.exists():
        state["errors"].append("Missing grades.json (run grading first or provide existing grades).")
        return state

    student_name = ""
    student_id = ""

    ident_path = Path(state.get("sheet_identifiers_json", ""))
    if ident_path.exists():
        try:
            ident_obj = json.loads(ident_path.read_text(encoding="utf-8"))
            student_name = str(ident_obj.get("student_name", "") or "")
            student_id = str(ident_obj.get("student_id", "") or "")
        except Exception:
            pass

    state["logs"].append("🛡️ qa_agent: grades.json → qa_report.json / qa_report.txt")

    try:
        qa_payload = run_qa(
            grades_json_path=state["grades_json"],
            out_qa_json_path=state["qa_json"],
            out_qa_txt_path=state["qa_txt"],
            student_name=student_name,
            student_id=student_id,
        )

        qa_status = qa_payload.get("qa", {}).get("status", "UNKNOWN")
        review_qs = qa_payload.get("qa", {}).get("questions_to_review", [])

        state["logs"].append(f"✅ qa json saved: {state['qa_json']}")
        state["logs"].append(f"✅ qa txt saved: {state['qa_txt']}")
        state["logs"].append(f"🛡️ qa status: {qa_status}")

        if review_qs:
            state["logs"].append(f"🔎 questions to review: {', '.join(review_qs)}")

    except Exception as e:
        state["errors"].append(f"QA failed: {e}")

    return state


def node_feedback(state: GraderState) -> GraderState:
    if not state.get("do_feedback", False):
        state["logs"].append("⏭️ feedback skipped (do_feedback=False)")
        return state

    grades_path = Path(state["grades_json"])
    if not grades_path.exists():
        state["errors"].append("Missing grades.json (run grading first or provide existing grades).")
        return state

    policy_path = state.get("feedback_policy_txt")

    student_name = ""
    student_id = ""

    ident_path = Path(state.get("sheet_identifiers_json", ""))
    if ident_path.exists():
        try:
            ident_obj = json.loads(ident_path.read_text(encoding="utf-8"))
            student_name = str(ident_obj.get("student_name", "") or "")
            student_id = str(ident_obj.get("student_id", "") or "")
        except Exception:
            pass

    state["logs"].append("💬 feedback_agent: grades.json → feedback.txt / feedback.json")

    try:
        generate_feedback(
            grades_json_path=state["grades_json"],
            feedback_policy_path=policy_path,
            out_feedback_txt_path=state["feedback_txt"],
            out_feedback_json_path=state.get("feedback_json"),
            model=None,
            include_internal_notes=False,
            student_name=student_name,
            student_id=student_id,
        )

        state["logs"].append(f"✅ feedback saved: {state['feedback_txt']}")
        if state.get("feedback_json"):
            state["logs"].append(f"✅ feedback json saved: {state['feedback_json']}")

    except Exception as e:
        state["errors"].append(f"Feedback failed: {e}")

    return state


def node_export(state: GraderState) -> GraderState:
    if not state.get("do_export", False):
        state["logs"].append("⏭️ export skipped (do_export=False)")
        return state

    grades_path = Path(state["grades_json"])
    if not grades_path.exists():
        state["errors"].append("Missing grades.json (run grading first or provide existing grades).")
        return state

    identifiers_path = state.get("sheet_identifiers_json")
    if identifiers_path and not Path(identifiers_path).exists():
        identifiers_path = None

    qa_path = state.get("qa_json")
    if qa_path and not Path(qa_path).exists():
        qa_path = None

    feedback_path = state.get("feedback_txt")
    if feedback_path and not Path(feedback_path).exists():
        feedback_path = None

    state["logs"].append("📦 exporter: grades/ids/qa/feedback → results.xlsx")

    try:
        export_student_xlsx(
            sheet_id=state["sheet_id"],
            grades_json_path=state["grades_json"],
            identifiers_json_path=identifiers_path,
            qa_json_path=qa_path,
            feedback_txt_path=feedback_path,
            out_xlsx_path=state["export_xlsx"],
        )
        state["logs"].append(f"✅ export saved: {state['export_xlsx']}")
    except Exception as e:
        state["errors"].append(f"Export failed: {e}")

    return state


def node_attendance(state: GraderState) -> GraderState:
    if not state.get("do_attendance", False):
        state["logs"].append("⏭️ attendance skipped (do_attendance=False)")
        return state

    attendance_file = state.get("attendance_file")
    if not attendance_file:
        state["errors"].append("Missing attendance_file for attendance extraction")
        return state

    att_path = Path(attendance_file)
    if not att_path.exists():
        state["errors"].append(f"Attendance file not found: {attendance_file}")
        return state

    out_root = Path(state.get("out_root", "data/output"))
    reports_dir = out_root / "_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    dpi = int(state.get("dpi", 300))

    try:
        if att_path.suffix.lower() == ".pdf":
            att_img = _pdf_to_first_image(str(att_path), str(reports_dir), dpi=dpi)
        else:
            att_img = str(att_path)

        state["logs"].append(f"🧾 attendance image ready: {att_img}")

        att_obj = _gemini_json_from_image(att_img, ATTENDANCE_PROMPT)
        present = att_obj.get("present", [])
        if not isinstance(present, list):
            present = []

        Path(state["attendance_json"]).write_text(
            json.dumps({"present": present}, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        state["logs"].append(f"✅ attendance saved: {state['attendance_json']}")

        sheets = _read_sheet_identifiers(
            str(out_root),
            extraction_dir=state.get("extraction_dir", "answers")
        )

        report = compare(present, sheets)
        Path(state["attendance_compare_json"]).write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        state["logs"].append(f"✅ attendance compare saved: {state['attendance_compare_json']}")
        state["logs"].append(f"📊 attendance counts: {report.get('counts', {})}")

    except Exception as e:
        state["errors"].append(f"Attendance failed: {e}")

    return state


def route_if_errors(state: GraderState) -> Literal["ok", "has_errors"]:
    return "has_errors" if state.get("errors") else "ok"


def build_graph():
    g = StateGraph(GraderState)

    g.add_node("prepare", node_prepare)
    g.add_node("pdf_to_images", node_pdf_to_images)
    g.add_node("extract_exam", node_extract_exam)
    g.add_node("structure_answers", node_structure_answers)
    g.add_node("grade", node_grade)
    g.add_node("qa", node_qa)
    g.add_node("feedback", node_feedback)
    g.add_node("export", node_export)
    g.add_node("attendance", node_attendance)

    g.set_entry_point("prepare")

    g.add_edge("prepare", "pdf_to_images")
    g.add_edge("pdf_to_images", "extract_exam")
    g.add_edge("extract_exam", "structure_answers")
    g.add_edge("structure_answers", "grade")
    g.add_edge("grade", "qa")
    g.add_edge("qa", "feedback")
    g.add_edge("feedback", "export")
    g.add_edge("export", "attendance")

    g.add_conditional_edges(
        "attendance",
        route_if_errors,
        {
            "ok": END,
            "has_errors": END,
        },
    )

    return g.compile()