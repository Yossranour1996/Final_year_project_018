from __future__ import annotations

from pathlib import Path

from src.graph.workflow import build_graph


SHEETS = [
    "sheet_010",
]


def run_one_sheet(graph, sheet_id: str) -> None:
    pdf_path = Path(f"data/input/answers_sheets/{sheet_id}.pdf")

    print("\n" + "=" * 80)
    print(f"RUNNING: {sheet_id}")
    print("=" * 80)

    if not pdf_path.exists():
        print(f"❌ Missing PDF: {pdf_path}")
        return

    try:
        final_state = graph.invoke({
            "sheet_id": sheet_id,
            "student_pdf": str(pdf_path),
            "dpi": 300,
            "max_pages": 10,
            "out_root": "data/output",
            "extraction_dir": "answers",

            "do_extract": True,
            "do_grade": True,
            "do_qa": False,
            "do_feedback": False,
            "do_export": False,
            "do_attendance": False,

            "grader_model": "gemini-2.5-flash",
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

    except Exception as e:
        print(f"\n❌ Unhandled error in {sheet_id}: {e}")


def main():
    graph = build_graph()

    for sheet_id in SHEETS:
        run_one_sheet(graph, sheet_id)


if __name__ == "__main__":
    main()