from __future__ import annotations
from typing import TypedDict, Optional, List


class GraderState(TypedDict, total=False):
    sheet_id: str

    student_pdf: Optional[str]
    criteria_txt: Optional[str]
    feedback_policy_txt: Optional[str]

    attendance_file: Optional[str]
    do_attendance: bool
    attendance_json: str
    attendance_compare_json: str

    out_root: str
    dpi: int
    max_pages: int
    extraction_dir: str

    do_extract: bool
    do_grade: bool
    do_qa: bool
    do_feedback: bool
    do_export: bool

    pages_dir: str
    extraction_dir_abs: str
    extracted_answers_json: str
    structured_answers_json: str
    sheet_identifiers_json: str

    grades_json: str

    qa_json: str
    qa_txt: str

    feedback_txt: str
    feedback_json: str

    export_xlsx: str
    grader_model: str

    logs: List[str]
    errors: List[str]