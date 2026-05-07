---
name: lin-algebra-1-assess
description: Evaluate a Linear Algebra 1 question-answer pair provided as JSON with id, exercise, solution, and time_submitted fields. Use when the user asks to grade, assess, evaluate, diagnose, or produce feedback for a submitted Linear Algebra 1 exercise answer using the grading JSON format defined in AGENTS.md.
---

# Linear Algebra 1 Assess

## Overview

Evaluate one Linear Algebra 1 exercise-answer pair and return a grading result in the JSON format defined in the repository `AGENTS.md`.

## Input

Receive a JSON object with exactly this canonical shape:

```json
{
  "id": "la1-000001",
  "exercise": "Let A = \\begin{pmatrix}1 & 2 \\\\ 3 & 4\\end{pmatrix}. Compute \\det(A).",
  "solution": "\\det(A) = 1\\cdot4 - 2\\cdot3 = -2.",
  "time_submitted": "2026-05-07T12:30:00+03:00"
}
```

Interpret `exercise` as the question prompt and `solution` as the student's submitted answer. Both fields may contain plain text, LaTeX, or a mix of both.

## Workflow

1. Validate that the input has `id`, `exercise`, `solution`, and `time_submitted`.
2. Read `AGENTS.md` if the grading schema is not already in context.
3. Identify the relevant Linear Algebra 1 topics and approximate difficulty from the exercise.
4. Grade the submitted `solution` for mathematical correctness, method, notation, and conceptual understanding.
5. Return only JSON matching the `Exercise Grading JSON` format in `AGENTS.md`.

Use `scripts/evaluate_pair.py` to validate the input and generate a schema-compatible draft:

```bash
python3 scripts/evaluate_pair.py path/to/pair.json
```

The script does not replace mathematical judgment. Fill or revise its rubric, diagnosis, topic updates, and feedback after checking the student's solution.

## Grading Guidance

Use normalized scores from `0` to `1`.

- Award high scores for correct reasoning even when notation is imperfect.
- Penalize arithmetic errors according to how much they affect the final result.
- Mark `is_correct` as `true` only when the final answer and required reasoning are mathematically acceptable.
- Keep `topic_level_updates` limited to topics directly evidenced by the submitted answer.
- Use clear feedback that tells the student what was correct, what failed, and what to practice next.

If the input is malformed, return a concise error JSON instead of guessing:

```json
{
  "error": "invalid_exercise_answer_pair",
  "message": "Missing required field: solution"
}
```
