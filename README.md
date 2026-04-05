# Agentic Java Exam Grading System

This project is a modular pipeline for grading **handwritten Java exam papers** from scanned PDF files.


---

## Project idea

Handwritten exam papers are difficult to grade automatically so lets use agents.

## Main agents

## 1. Extractor Agent
This agent is responsible for the early processing steps.

It does the following:

- converts the exam PDF into page images
- extracts the student ID and student name from the first page
- OCRs the student's answers from all pages
- creates a manual labeling file for human review
- waits for the human to edit the labels
- builds `structured_answers.json` from the reviewed labels

This is the stage where the human checks that each answer belongs to the correct question.

---

## 2. Grader Agent
This agent reads the structured answers and grades them.

It does the following:

- loads `structured_answers.json`
- reads the grading rubric for each question
- sends each answer to the LLM grader
- assigns per-question scores
- computes totals for each section
- computes the overall total

The grader is designed to follow the rubric and tolerate weak spelling or OCR noise when the intended meaning is still clear.

---

## 3. QA Agent
This agent checks whether the grading output looks suspicious.

It can detect things such as:

- invalid scores
- blank answers with non-zero marks
- non-blank answers with zero
- total mismatches
- cases that may need review

It produces QA reports if this stage is enabled.

---

## 4. Feedback Agent
This agent generates student feedback from the grading output.

It summarizes:

- strengths
- weaknesses
- question-level comments
- areas for improvement


---

## 5. Export Agent
This agent exports the final results into Excel.

It collects:

- student information
- totals
- QA status
- grading details

and writes them to an Excel file.


---

## 6. Attendance Agent
This agent compares extracted exam sheets with an attendance sheet.

It can help detect:

- present students with no answer sheet
- answer sheets with no matching attendance record
- duplicate IDs
- unidentified sheets

This stage is optional.

---

## To run:
python -m src.app , make the values in the script True or False depending on the agent you want to run.

## Simple project structure

```text
data/
  input/
    exams/
    attendance/
  output/
    <sheet_id>/
      pages/
      answers/
      grading_results/
      exports/
    _reports/

src/
  agents/
    extractor.py
    java_exam_grader.py
    qa_agent.py
    feedback_agent.py
    exporter.py
    attendance_compare_onefile.py

  tools/
    pdf_to_images.py
    openai_vision.py
    manual_labeling_tool.py
    labeled_answers_to_json.py

  graph/
    workflow.py

  state.py
  app.py

