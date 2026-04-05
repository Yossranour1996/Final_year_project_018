from __future__ import annotations

import argparse
from pathlib import Path

from src.graph.workflow import build_graph


def main():
    parser = argparse.ArgumentParser("Exam Agentic Grader (LangGraph)")

    parser.add_argument(
        "--sheet_id",
        type=str,
        required=True,
        help="Internal sheet identifier (e.g., sheet_001)"
    )
    parser.add_argument("--student_pdf", type=str, default=None)

    parser.add_argument("--criteria", type=str, default=None)
    parser.add_argument("--feedback_policy", type=str, default=None)

    parser.add_argument("--attendance_file", type=str, default=None)
    parser.add_argument("--do_attendance", action="store_true")

    parser.add_argument(
        "--extraction_dir",
        type=str,
        default="answers",
        help="Folder under data/output/<sheet_id>/ that contains extracted answers"
    )

    parser.add_argument("--full-workflow", action="store_true")
    parser.add_argument("--grader-only", action="store_true")
    parser.add_argument("--extract-only", action="store_true")
    parser.add_argument("--qa-only", action="store_true")
    parser.add_argument("--feedback-only", action="store_true")
    parser.add_argument("--export-only", action="store_true")

    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--max_pages", type=int, default=0)
    parser.add_argument("--out_root", type=str, default="data/output")
    parser.add_argument("--grader_model", type=str, default="gemini-2.0-flash")

    args = parser.parse_args()

    selected_modes = sum([
        bool(args.full_workflow),
        bool(args.grader_only),
        bool(args.extract_only),
        bool(args.qa_only),
        bool(args.feedback_only),
        bool(args.export_only),
        bool(args.do_attendance),
    ])

    if selected_modes == 0:
        raise ValueError(
            "Choose one: --full-workflow OR --grader-only OR --extract-only OR --qa-only OR --feedback-only OR --export-only OR --do_attendance"
        )

    if selected_modes > 1:
        raise ValueError(
            "Please choose only one main mode at a time: "
            "--full-workflow OR --grader-only OR --extract-only OR --qa-only OR --feedback-only OR --export-only OR --do_attendance"
        )

    state = {
        "sheet_id": args.sheet_id,
        "student_pdf": args.student_pdf,

        "criteria_txt": args.criteria,
        "feedback_policy_txt": args.feedback_policy,

        "attendance_file": args.attendance_file,
        "do_attendance": bool(args.do_attendance),

        "out_root": args.out_root,
        "dpi": args.dpi,
        "max_pages": args.max_pages,
        "extraction_dir": args.extraction_dir,
        "grader_model": args.grader_model,

        "do_extract": bool(args.full_workflow or args.extract_only),
        "do_grade": bool(args.full_workflow or args.grader_only),
        "do_qa": bool(args.full_workflow or args.grader_only or args.qa_only),
        "do_feedback": bool(args.full_workflow or args.feedback_only),
        "do_export": bool(args.full_workflow or args.export_only),

        "logs": [],
        "errors": [],
    }

    graph = build_graph()
    final_state = graph.invoke(state)

    print("\n".join(final_state.get("logs", [])))

    if final_state.get("errors"):
        print("\n❌ Errors:")
        for e in final_state["errors"]:
            print("-", e)
        return

    print("\n✅ Done.")

    extraction = final_state.get("extracted_answers_json")
    if extraction and Path(extraction).exists():
        print("Extraction:", extraction)

    identifiers = final_state.get("sheet_identifiers_json")
    if identifiers and Path(identifiers).exists():
        print("Identifiers:", identifiers)

    grades = final_state.get("grades_json")
    if grades and Path(grades).exists():
        print("Grades:", grades)

    qa_json = final_state.get("qa_json")
    if qa_json and Path(qa_json).exists():
        print("QA JSON:", qa_json)

    qa_txt = final_state.get("qa_txt")
    if qa_txt and Path(qa_txt).exists():
        print("QA TXT:", qa_txt)

    feedback = final_state.get("feedback_txt")
    if feedback and Path(feedback).exists():
        print("Feedback TXT:", feedback)

    feedback_json = final_state.get("feedback_json")
    if feedback_json and Path(feedback_json).exists():
        print("Feedback JSON:", feedback_json)

    export = final_state.get("export_xlsx")
    if export and Path(export).exists():
        print("Export:", export)

    attendance = final_state.get("attendance_json")
    if attendance and Path(attendance).exists():
        print("Attendance:", attendance)

    attendance_compare = final_state.get("attendance_compare_json")
    if attendance_compare and Path(attendance_compare).exists():
        print("Attendance Compare:", attendance_compare)


if __name__ == "__main__":
    main()