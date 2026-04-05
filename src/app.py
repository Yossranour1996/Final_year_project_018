from __future__ import annotations

from src.graph.workflow import build_graph


def main():
    graph = build_graph()

    final_state = graph.invoke({
        "sheet_id": "sheet_008",
        "student_pdf": "data/input/exams/sheet_008.pdf",
        "dpi": 300,
        "max_pages": 10,
        "out_root": "data/output",
        "extraction_dir": "answers",

        "do_extract": False,
        "do_grade": False,
        "do_qa": True,
        "do_feedback": True,
        "do_export": True,
        "do_attendance": False,

        "grader_model": "gemini-2.0-flash",
        "logs": [],
        "errors": [],
    })

    print("\n".join(final_state.get("logs", [])))

    if final_state.get("errors"):
        print("\n❌ Errors:")
        for e in final_state["errors"]:
            print("-", e)
        return

    print("\n✅ Done.")
    print("Structured:", final_state.get("structured_answers_json"))
    print("Grades:", final_state.get("grades_json"))


if __name__ == "__main__":
    main()