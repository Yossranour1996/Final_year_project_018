from __future__ import annotations

from pathlib import Path
import math
import json
import re
import pandas as pd


# =========================
# عدلي هذه القيم
# =========================

# ملف الدرجات الحقيقية
TRUE_MARKS_FILE = r"C:\Users\hp\Desktop\018_Final\data\output\sheet_marks.csv"
# أو xlsx

# المجلد الذي يحتوي ملفات النتائج
OUTPUT_ROOT = Path(r"C:\Users\hp\Desktop\018_Final\data\output")

# ملف التقرير النهائي
OUTPUT_TXT = r"C:\Users\hp\Desktop\\018_Final\data\grading_analysis_all.txt"

# أسماء الأعمدة في ملفك الحقيقي
TRUE_ID_COL = "sheet_num"
TRUE_MARK_COL = "mark"

# =========================


def load_true_marks(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"True marks file not found: {path}")

    if p.suffix.lower() == ".csv":
        df = pd.read_csv(p, dtype=str)
    elif p.suffix.lower() in [".xlsx", ".xls"]:
        df = pd.read_excel(p, dtype=str)
    else:
        raise ValueError(f"Unsupported true marks file format: {p.suffix}")

    df.columns = df.columns.str.strip()
    return df


def clean_sheet_num(x) -> str:
    if pd.isna(x):
        return ""

    s = str(x).strip()

    # إزالة .0 لو جاء من Excel
    if s.endswith(".0"):
        s = s[:-2]

    # استخراج الرقم فقط
    m = re.search(r"(\d+)", s)
    if not m:
        return ""

    # توحيد الشكل إلى 3 خانات
    return m.group(1).zfill(3)


def safe_float(x):
    try:
        if pd.isna(x):
            return None
        return float(x)
    except Exception:
        return None


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sheet_dir_to_sheet_num(sheet_dir_name: str) -> str:
    """
    sheet_001 -> 001
    sheet_8   -> 008
    """
    m = re.search(r"sheet_(\d+)", sheet_dir_name, flags=re.IGNORECASE)
    if not m:
        return ""
    return m.group(1).zfill(3)


def extract_pred_record_from_grades(sheet_dir: Path) -> dict | None:
    grades_path = sheet_dir / "grading_results" / "grades.json"
    if not grades_path.exists():
        return None

    try:
        obj = load_json(grades_path)
    except Exception:
        return None

    totals = obj.get("grading", {}).get("totals", {})
    overall = safe_float(totals.get("overall"))

    if overall is None:
        return None

    sheet_num = sheet_dir_to_sheet_num(sheet_dir.name)

    return {
        "sheet_id": sheet_dir.name,
        "match_id": sheet_num,
        "pred_mark": overall,
        "q1_pred": safe_float(totals.get("q1")),
        "q2_pred": safe_float(totals.get("q2")),
        "q3_pred": safe_float(totals.get("q3")),
        "q4_pred": safe_float(totals.get("q4")),
        "grades_path": str(grades_path),
    }


def collect_predicted_records(output_root: Path) -> pd.DataFrame:
    rows = []

    for sheet_dir in sorted(output_root.iterdir()):
        if not sheet_dir.is_dir():
            continue
        if sheet_dir.name.startswith("_"):
            continue

        rec = extract_pred_record_from_grades(sheet_dir)
        if rec is not None:
            rows.append(rec)

    return pd.DataFrame(rows)


def collect_question_loss_stats(output_root: Path):
    per_question_rows = []
    per_section_rows = []

    for sheet_dir in sorted(output_root.iterdir()):
        if not sheet_dir.is_dir():
            continue
        if sheet_dir.name.startswith("_"):
            continue

        grades_path = sheet_dir / "grading_results" / "grades.json"
        if not grades_path.exists():
            continue

        try:
            obj = load_json(grades_path)
        except Exception:
            continue

        questions = obj.get("grading", {}).get("questions", {})
        totals = obj.get("grading", {}).get("totals", {})

        q1 = safe_float(totals.get("q1")) or 0.0
        q2 = safe_float(totals.get("q2")) or 0.0
        q3 = safe_float(totals.get("q3")) or 0.0
        q4 = safe_float(totals.get("q4")) or 0.0

        per_section_rows.append({"section": "Q1", "score": q1, "max_score": 30.0, "loss": 30.0 - q1})
        per_section_rows.append({"section": "Q2", "score": q2, "max_score": 21.0, "loss": 21.0 - q2})
        per_section_rows.append({"section": "Q3", "score": q3, "max_score": 21.0, "loss": 21.0 - q3})
        per_section_rows.append({"section": "Q4", "score": q4, "max_score": 28.0, "loss": 28.0 - q4})

        for qid, qobj in questions.items():
            score = safe_float(qobj.get("score"))
            max_score = safe_float(qobj.get("max_score"))
            if score is None or max_score is None:
                continue

            per_question_rows.append({
                "qid": qid,
                "score": score,
                "max_score": max_score,
                "loss": max_score - score,
            })

    question_df = pd.DataFrame(per_question_rows)
    section_df = pd.DataFrame(per_section_rows)

    return question_df, section_df


def build_report(merged: pd.DataFrame, question_df: pd.DataFrame, section_df: pd.DataFrame) -> str:
    lines = []
    lines.append("GRADING ANALYSIS REPORT")
    lines.append("=" * 80)
    lines.append("")

    total_rows = len(merged)
    usable = merged[
        merged["true_mark"].notna() &
        merged["pred_mark"].notna() &
        (merged["match_id"].astype(str).str.strip() != "")
    ].copy()

    lines.append(f"Total predicted rows found: {total_rows}")
    lines.append(f"Matched usable rows: {len(usable)}")
    lines.append("")

    if usable.empty:
        lines.append("No usable matched rows were found.")
        lines.append("")
        lines.append("DEBUG INFO")
        lines.append("-" * 80)
        if "match_id" in merged.columns:
            lines.append("Predicted match_ids:")
            for x in merged["match_id"].dropna().astype(str).tolist():
                lines.append(f"- {x}")
            lines.append("")
        return "\n".join(lines)

    usable["error"] = usable["pred_mark"] - usable["true_mark"]
    usable["abs_error"] = usable["error"].abs()
    usable["sq_error"] = usable["error"] ** 2
    usable["within_5"] = usable["abs_error"] <= 5

    mean_error = usable["error"].mean()
    mae = usable["abs_error"].mean()
    mse = usable["sq_error"].mean()
    rmse = math.sqrt(mse)
    within_5_count = int(usable["within_5"].sum())
    within_5_pct = (within_5_count / len(usable)) * 100.0

    lines.append("OVERALL METRICS")
    lines.append("-" * 80)
    lines.append(f"Mean Error (pred - true): {mean_error:.3f}")
    lines.append(f"Mean Absolute Error (MAE): {mae:.3f}")
    lines.append(f"Mean Squared Error (MSE): {mse:.3f}")
    lines.append(f"Root Mean Squared Error (RMSE): {rmse:.3f}")
    lines.append(f"Within ±5 marks: {within_5_count}/{len(usable)} ({within_5_pct:.2f}%)")
    lines.append("")

    over_df = usable[usable["error"] > 0]
    under_df = usable[usable["error"] < 0]
    exact_df = usable[usable["error"] == 0]

    lines.append("ERROR DIRECTION")
    lines.append("-" * 80)
    lines.append(f"Overgraded cases  (system > true): {len(over_df)}")
    lines.append(f"Undergraded cases (system < true): {len(under_df)}")
    lines.append(f"Exact matches: {len(exact_df)}")
    lines.append("")

    big_fail = usable[usable["abs_error"] > 5]
    moderate_fail = usable[(usable["abs_error"] > 2) & (usable["abs_error"] <= 5)]
    small_fail = usable[usable["abs_error"] <= 2]

    lines.append("WHERE THE SYSTEM FAILS MOST")
    lines.append("-" * 80)
    lines.append(f"Large errors   (> 5): {len(big_fail)}")
    lines.append(f"Moderate errors(> 2 and <= 5): {len(moderate_fail)}")
    lines.append(f"Small errors   (<= 2): {len(small_fail)}")
    lines.append("")

    worst_cases = usable.sort_values("abs_error", ascending=False).head(20)

    lines.append("WORST CASES")
    lines.append("-" * 80)
    for _, row in worst_cases.iterrows():
        lines.append(
            f"{row['sheet_id']} | sheet_num={row['match_id']} | true={row['true_mark']:.2f} | "
            f"pred={row['pred_mark']:.2f} | error={row['error']:+.2f} | abs_error={row['abs_error']:.2f}"
        )
    lines.append("")

    if not section_df.empty:
        section_stats = (
            section_df.groupby("section")
            .agg(
                count=("section", "count"),
                avg_score=("score", "mean"),
                avg_loss=("loss", "mean"),
                max_score=("max_score", "mean"),
            )
            .reset_index()
            .sort_values("avg_loss", ascending=False)
        )

        lines.append("WHICH MAJOR QUESTION GROUP LOSES THE MOST MARKS")
        lines.append("-" * 80)
        for _, row in section_stats.iterrows():
            lines.append(
                f"{row['section']}: "
                f"average loss={row['avg_loss']:.3f} out of {row['max_score']:.1f}, "
                f"average score={row['avg_score']:.3f}, "
                f"count={int(row['count'])}"
            )
        lines.append("")

        worst_section = section_stats.iloc[0]
        lines.append(
            f"Most deducted major section overall: {worst_section['section']} "
            f"(average loss = {worst_section['avg_loss']:.3f})"
        )
        lines.append("")

    if not question_df.empty:
        question_stats = (
            question_df.groupby("qid")
            .agg(
                count=("qid", "count"),
                avg_score=("score", "mean"),
                avg_loss=("loss", "mean"),
                max_score=("max_score", "mean"),
            )
            .reset_index()
            .sort_values("avg_loss", ascending=False)
        )

        lines.append("WHICH SUB-QUESTIONS LOSE THE MOST MARKS")
        lines.append("-" * 80)
        for _, row in question_stats.head(15).iterrows():
            lines.append(
                f"{row['qid']}: "
                f"average loss={row['avg_loss']:.3f} out of {row['max_score']:.1f}, "
                f"average score={row['avg_score']:.3f}, "
                f"count={int(row['count'])}"
            )
        lines.append("")

        worst_question = question_stats.iloc[0]
        lines.append(
            f"Most deducted sub-question overall: {worst_question['qid']} "
            f"(average loss = {worst_question['avg_loss']:.3f})"
        )
        lines.append("")

    missing_true = merged[merged["true_mark"].isna()]
    missing_pred_id = merged[merged["match_id"].astype(str).str.strip() == ""]

    lines.append("MATCHING ISSUES")
    lines.append("-" * 80)
    lines.append(f"Predicted rows with no matching true mark: {len(missing_true)}")
    lines.append(f"Predicted rows with missing sheet_num: {len(missing_pred_id)}")
    lines.append("")

    if not missing_true.empty:
        lines.append("Sample rows missing in true marks file:")
        for _, row in missing_true.head(10).iterrows():
            lines.append(f"- {row.get('sheet_id', '')} | sheet_num={row.get('match_id', '')}")
        lines.append("")

    lines.append("End of report")
    return "\n".join(lines)


def main():
    true_df = load_true_marks(TRUE_MARKS_FILE).copy()
    true_df["match_id"] = true_df[TRUE_ID_COL].apply(clean_sheet_num)
    true_df["true_mark"] = true_df[TRUE_MARK_COL].apply(safe_float)

    pred_df = collect_predicted_records(OUTPUT_ROOT)

    if pred_df.empty:
        raise ValueError("No grades.json files were found under OUTPUT_ROOT.")

    pred_df["match_id"] = pred_df["match_id"].apply(clean_sheet_num)

    print("TRUE columns:", true_df.columns.tolist())
    print("TRUE match_ids:", true_df["match_id"].tolist())
    print("PRED match_ids:", pred_df["match_id"].tolist())

    merged = pd.merge(
        pred_df,
        true_df[["match_id", "true_mark"]],
        on="match_id",
        how="left"
    )

    question_df, section_df = collect_question_loss_stats(OUTPUT_ROOT)
    report = build_report(merged, question_df, section_df)

    out_path = Path(OUTPUT_TXT)
    out_path.write_text(report, encoding="utf-8")

    print(f"Done. Report saved to: {out_path}")


if __name__ == "__main__":
    main()