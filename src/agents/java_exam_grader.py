from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Dict, Any, Tuple, List

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(override=True)

# =========================================================
# Allowed question keys
# =========================================================

QUESTION_KEYS = [
    "1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8", "1.9", "1.10",
    "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7",
    "3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7",
    "4.1", "4.2",
]

# =========================================================
# Rubric / solutions encoded from your grading policy
# =========================================================

QUESTION_SPECS: Dict[str, Dict[str, Any]] = {
    "1.1": {
        "question": "What is meant by Java is architecture-neutral?",
        "expected": "Student should express that Java can work across different architectures / is not restricted to one specific system architecture.",
        "allowed_scores": [0, 3],
        "grading_policy": (
            "Give 3 if the student conveys the idea that Java can work on different "
            "architectures/devices/systems, even if the wording is weak or grammatically wrong. "
            "Otherwise 0."
        ),
    },
"1.2": {
    "question": "What was the role of WWW and Internet in Java's emergence?",
    "expected": (
        "They created a need/demand for Java to support Internet/WWW-related programming, "
        "including platform-independent programs, distributed programs, applets, web applications, "
        "or similar Internet-based uses."
    ),
    "allowed_scores": [0, 3],
    "grading_policy": (
        "Give 3 if the student clearly expresses ANY valid meaning related to why WWW/Internet "
        "created the need for Java or influenced its emergence. "
        "This includes mentioning need/demand/requirement/necessity, platform-independent programs, "
        "distributed/network programs, Internet applications, applets, web applications, or equivalent meanings. "
        "If the student's wording is weak but the intended meaning is clearly about Java serving WWW/Internet needs, "
        "award full marks. Otherwise 0."
    ),
},
    "1.3": {
        "question": "Difference between OOP and POP.",
        "expected": "POP is procedure/data oriented; OOP is object/class oriented.",
        "allowed_scores": [0, 3],
        "grading_policy": (
            "Give 3 if the student conveys that POP is related to procedures/functions/data "
            "and OOP is related to objects/classes. Exact textbook wording is not required. "
            "Otherwise 0."
        ),
    },
    "1.4": {
        "question": "Components of JRE.",
        "expected": "JVM, libraries, supporting files/components.",
        "allowed_scores": [0, 3],
        "grading_policy": (
            "Give 3 if the student mentions ANY one valid JRE component such as JVM, libraries, "
            "or supporting files/components. The student does NOT need to list all of them. "
            "Otherwise 0."
        ),
    },
    "1.5": {
        "question": "Inheritance vs polymorphism.",
        "expected": (
            "Inheritance = class gets properties/behavior from another existing class. "
            "Polymorphism = many forms / one interface / general class of actions / "
            "common type with different forms."
        ),
        "allowed_scores": [0, 2, 3],
        "grading_policy": (
            "Give 3 if both inheritance and polymorphism meanings are correct. "
            "Give 2 if only one of the two is clearly correct. "
            "Give 0 if neither is correct."
        ),
    },
    "1.6": {
        "question": "What is encapsulation?",
        "expected": "Binding/bundling code and data together in one unit/class.",
        "allowed_scores": [0, 3],
        "grading_policy": (
            "Give 3 if the student expresses binding/bundling code and data together, "
            "or an equivalent meaning. Otherwise 0."
        ),
    },
    "1.7": {
        "question": "Two ways to achieve abstraction.",
        "expected": "Abstract classes and interfaces.",
        "allowed_scores": [0, 3],
        "grading_policy": (
            "Give 3 if the student mentions abstract class/classes and interfaces, "
            "even if grammar/order is weak such as 'class abstract' or 'interfaces abstract'. "
            "Otherwise 0."
        ),
    },
    "1.8": {
        "question": "Reasons a thread may terminate.",
        "expected": "Finished normally, unusual event/exception/error, dead/stopped/terminated.",
        "allowed_scores": [0, 1, 2, 3],
        "grading_policy": (
            "Give 1 mark for each clearly correct reason among: "
            "(1) finished/completed task, "
            "(2) unusual event/exception/error, "
            "(3) dead/stopped/terminated/no longer available. "
            "Accept equivalent wording. Max 3."
        ),
    },
    "1.9": {
        "question": "Default streams in Java.",
        "expected": "System.in, System.out, System.err",
        "allowed_scores": [0, 1, 2, 3],
        "grading_policy": (
            "Give 1 mark for each correct intended stream among System.in, System.out, System.err. "
            "IMPORTANT: if the student writes weak spellings like System.i or System.o but the "
            "intended stream is clearly System.in and System.out, count them as correct. "
            "Minor spelling/OCR mistakes must not reduce the mark. Max 3."
        ),
    },
    "1.10": {
        "question": "Swing is built on top of what?",
        "expected": "AWT / Abstract Window Toolkit",
        "allowed_scores": [0, 3],
        "grading_policy": (
            "Give 3 only if the student gives AWT or Abstract Window Toolkit or a very clear equivalent. "
            "Otherwise 0."
        ),
    },

    "2.1": {
        "question": "True/False 2.1",
        "expected": "True",
        "allowed_scores": [0, 3],
        "grading_policy": "Give 3 only if the student chose True. Otherwise 0.",
    },
    "2.2": {
        "question": "True/False 2.2",
        "expected": "False",
        "allowed_scores": [0, 3],
        "grading_policy": "Give 3 only if the student chose False. Otherwise 0.",
    },
    "2.3": {
        "question": "True/False 2.3",
        "expected": "True",
        "allowed_scores": [0, 3],
        "grading_policy": "Give 3 only if the student chose True. Otherwise 0.",
    },
    "2.4": {
        "question": "True/False 2.4",
        "expected": "False",
        "allowed_scores": [0, 3],
        "grading_policy": "Give 3 only if the student chose False. Otherwise 0.",
    },
    "2.5": {
        "question": "True/False 2.5",
        "expected": "True",
        "allowed_scores": [0, 3],
        "grading_policy": "Give 3 only if the student chose True. Otherwise 0.",
    },
    "2.6": {
        "question": "True/False 2.6",
        "expected": "True",
        "allowed_scores": [0, 3],
        "grading_policy": "Give 3 only if the student chose True. Otherwise 0.",
    },
    "2.7": {
        "question": "True/False 2.7",
        "expected": "False",
        "allowed_scores": [0, 3],
        "grading_policy": "Give 3 only if the student chose False. Otherwise 0.",
    },

    "3.1": {
        "question": "Reason for computer language innovation.",
        "expected": "Improvement in programming OR adapting to changing environments/uses.",
        "allowed_scores": [0, 3],
        "grading_policy": (
            "Give 3 if the student mentions improvement/improving programming OR adapting "
            "to change/environment/uses. Weak spelling like 'improvement' still counts "
            "if the intended meaning is clear. Otherwise 0."
        ),
    },
    "3.2": {
        "question": "Example of POP language.",
        "expected": "C or Pascal",
        "allowed_scores": [0, 3],
        "grading_policy": (
            "Give 3 if the student gives C or Pascal, even inside a longer phrase such as "
            "'C programming language'. Otherwise 0."
        ),
    },
    "3.3": {
        "question": "POP does not allow _____ to flow freely in the program.",
        "expected": "data",
        "allowed_scores": [0, 3],
        "grading_policy": (
            "Give 3 if the intended answer is data, even if it appears in a phrase like "
            "'and data'. Otherwise 0."
        ),
    },
    "3.4": {
        "question": "Small programs that need a Java-enabled web browser to execute.",
        "expected": "Applets",
        "allowed_scores": [0, 3],
        "grading_policy": (
            "Give 3 if the student gives Applet/Applets or a very clear equivalent/OCR form. "
            "Otherwise 0."
        ),
    },
    "3.5": {
        "question": "A component which can contain other elements like buttons.",
        "expected": "Container or Frame",
        "allowed_scores": [0, 3],
        "grading_policy": (
            "Give 3 if the student gives Container. Also accept Frame. If extra noise appears "
            "but Container is clearly present, still give 3. Otherwise 0."
        ),
    },
    "3.6": {
        "question": "The model-view-_____ architecture used in Swing.",
        "expected": "Controller",
        "allowed_scores": [0, 3],
        "grading_policy": "Give 3 if the student gives Controller. Otherwise 0.",
    },
    "3.7": {
        "question": "Java API to connect and interact with databases.",
        "expected": "JDBC or Java Database Connectivity",
        "allowed_scores": [0, 3],
        "grading_policy": (
            "Give 3 if the student gives JDBC or Java Database Connectivity. Otherwise 0."
        ),
    },

    "4.1": {
        "question": "Complete the code for seat assignment output.",
        "expected": (
            'Accepted full answers include: students[i] + ", you will take seat " + '
            '(students.length - i - 1) OR students[i] + ", you will take seat " + '
            '(4 - i) OR students[i] + ", you will take seat " + (i)'
        ),
        "allowed_scores": [0, 5, 7, 14],
        "grading_policy": (
            "IMPORTANT: There are THREE accepted full model answers for this question: "
            "(students.length - i - 1), OR (4 - i), OR (i). "
            "If the student gives ANY of these three accepted answers, or a very clear equivalent "
            "with spelling/OCR issues, award FULL 14. "
            "Give 7 only if the answer is close but not one of the accepted full answers. "
            "Give 5 for a weak but relevant attempt. Give 0 if blank."
        ),
    },
    "4.2": {
        "question": "Missing code for vote calculation output.",
        "expected": "calculateVotes(totalVotes);",
        "allowed_scores": [0, 5, 7, 14],
        "grading_policy": (
            "Give 14 if the student clearly gives calculateVotes(totalVotes); "
            "or a very clear equivalent. "
            "Give 7 if the student attempts the answer in the correct direction and mentions "
            "totalVotes or the intended function logic but the final function/code is wrong. "
            "Give 5 only for a weaker but still relevant attempt. "
            "Give 0 if blank. Do NOT give zero when the student clearly attempts the required logic "
            "in the right context."
        ),
    },
}

# =========================================================
# Gemini helpers
# =========================================================

GRADER_SYSTEM_PROMPT = r"""
You are grading a student's Java exam answer.

You must grade according to the teacher's rubric exactly as given.
Do NOT use rigid keyword matching.
Judge by intended meaning, not exact wording.

Very important grading principles:
- If spelling is weak but the intended answer is clearly recoverable, award full credit.
- Minor spelling mistakes, OCR noise, missing letters, or malformed grammar must NOT reduce the score if the intended meaning is clear.
- If the teacher policy says a student should get full marks for mentioning one valid idea, then award full marks even if the wording is poor.
- For programming questions, if the student's answer matches one of the accepted model answers in meaning, give full marks.
- If the teacher policy says a weak but relevant attempt deserves attempt marks, do not give zero.

Return ONLY one valid JSON object:
{
  "score": <number>,
  "reason": "<short reason>"
}

Rules:
- The score must be EXACTLY one of the allowed scores provided.
- Be faithful to the grading policy for this specific question.
- Do not invent information not present in the student's answer.
- Do not explain outside the JSON.
"""


def _make_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY in environment (.env).")
    return genai.Client(api_key=api_key)


def _safe_json_obj(text: str) -> Dict[str, Any]:
    t = (text or "").strip()
    i = t.find("{")
    j = t.rfind("}")
    if i == -1 or j == -1 or j <= i:
        return {}
    try:
        obj = json.loads(t[i:j + 1])
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def _normalize_score(raw_score: Any, allowed_scores: List[float]) -> float:
    try:
        score = float(raw_score)
    except Exception:
        score = allowed_scores[0]

    if score in allowed_scores:
        return score

    return min(allowed_scores, key=lambda x: abs(x - score))


def _post_adjust_score(qid: str, answer: str, score: float) -> float:
    text = (answer or "").strip()
    low = text.lower()
    
    if qid == "1.2":
        if text and score == 0.0:
            if (
                "need" in low
                or "needs" in low
                or "require" in low
                or "requirement" in low
                or "necessity" in low
                or "internet" in low
                or "www" in low
                or "web" in low
                or "applet" in low
                or "applets" in low
                or "web application" in low
                or "web applications" in low
            ):
                return 3.0    

    if qid == "1.9":
        if text:
            has_in = ("system.in" in low) or ("system.i" in low)
            has_out = ("system.out" in low) or ("system.o" in low)
            has_err = "system.err" in low
            if has_in and has_out and has_err:
                return 3.0

    if qid == "4.1":
        if text:
            has_phrase = "you will take seat" in low
            has_i_form = (
                "(i)" in low
                or "( i )" in low
                or "+ (i)" in low
                or "+ ( i )" in low
                or "+(i)" in low
            )
            if has_phrase and has_i_form:
                return 14.0

    if qid == "4.2":
        if text and score == 0.0:
            if (
                "total votes" in low
                or "totalvotes" in low
                or "114" in low
                or "15%" in low
                or "0.15" in low
                or "votes" in low
            ):
                return 7.0

    return score


def _grade_with_gemini(
    qid: str,
    answer: str,
    spec: Dict[str, Any],
    model: str,
) -> Tuple[float, str]:
    if not (answer or "").strip():
        return 0.0, "Blank answer"

    client = _make_client()

    user_prompt = f"""
Question ID: {qid}

Question:
{spec['question']}

Expected answer / concept:
{spec['expected']}

Allowed scores:
{spec['allowed_scores']}

Teacher grading policy:
{spec['grading_policy']}

Student answer:
\"\"\"
{answer}
\"\"\"
"""

    resp = client.models.generate_content(
        model=model,
        contents=[
            types.Part.from_text(text=GRADER_SYSTEM_PROMPT),
            types.Part.from_text(text=user_prompt),
        ],
    )

    obj = _safe_json_obj(resp.text or "")
    score = _normalize_score(obj.get("score"), spec["allowed_scores"])
    score = _post_adjust_score(qid, answer, score)
    reason = str(obj.get("reason", "")).strip() or "LLM grading result"

    return score, reason


# =========================================================
# Main grading
# =========================================================

def grade_answers(
    answer_map: Dict[str, str],
    model: str = "gemini-2.0-flash",
) -> Dict[str, Any]:
    results: Dict[str, Any] = {
        "questions": {},
        "totals": {
            "q1": 0.0,
            "q2": 0.0,
            "q3": 0.0,
            "q4": 0.0,
            "overall": 0.0,
        }
    }

    for qid in QUESTION_KEYS:
        answer = answer_map.get(qid, "")
        spec = QUESTION_SPECS[qid]
        score, reason = _grade_with_gemini(qid, answer, spec, model=model)

        max_score = 14.0 if qid.startswith("4.") else 3.0

        results["questions"][qid] = {
            "answer": answer,
            "score": score,
            "max_score": max_score,
            "reason": reason,
        }

        if qid.startswith("1."):
            results["totals"]["q1"] += score
        elif qid.startswith("2."):
            results["totals"]["q2"] += score
        elif qid.startswith("3."):
            results["totals"]["q3"] += score
        elif qid.startswith("4."):
            results["totals"]["q4"] += score

    results["totals"]["overall"] = (
        results["totals"]["q1"] +
        results["totals"]["q2"] +
        results["totals"]["q3"] +
        results["totals"]["q4"]
    )

    return results


def grade_exam_from_structured_answers(
    structured_answers_json_path: str,
    out_json_path: str | None = None,
    model: str = "gemini-2.0-flash",
) -> Dict[str, Any]:
    answers_path = Path(structured_answers_json_path)
    answer_map = json.loads(answers_path.read_text(encoding="utf-8"))

    graded = grade_answers(answer_map, model=model)

    payload = {
        "parsed_answers": answer_map,
        "grading": graded,
    }

    if out_json_path:
        out_path = Path(out_json_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return payload