---
name: lin-algebra-1-assess
description: Evaluate a Linear Algebra 1 question-answer pair, convert the grading result into the append-only student JSONL event format consumed by generate_exercise_from_log.py, and append it to the requested student log.
---

# Linear Algebra 1 Assess

## Overview

Evaluate one Linear Algebra 1 exercise-answer pair, create a graded-attempt event in the append-only student JSONL log format, append that event to disk, and return the appended event as JSON.

The appended event must be compatible with `generate_exercise_from_log.py`. In particular, it must include:

- `event_type: "exercise_attempt_graded"`
- top-level `student_id`, `attempt_id`, `exercise_id`, and `timestamp`
- top-level `exercise` with at least `difficulty` and `topics`
- `grading_result` with `score`, `max_score`, `is_correct`, `weaknesses`, and `topic_level_updates`
- `student_profile_after_attempt`

## Input

Prefer receiving an envelope with the student and log destination:

```json
{
  "student_id": "student-123",
  "log_file": "students/student-123.jsonl",
  "exercise_answer_pair": {
    "id": "la1-000001",
    "exercise": "Let A = \\begin{pmatrix}1 & 2 \\\\ 3 & 4\\end{pmatrix}. Compute \\det(A).",
    "solution": "\\det(A) = 1\\cdot4 - 2\\cdot3 = -2.",
    "time_submitted": "2026-05-07T12:30:00+03:00"
  }
}
```

For backward compatibility, also accept a bare exercise-answer pair:

```json
{
  "id": "la1-000001",
  "exercise": "Let A = \\begin{pmatrix}1 & 2 \\\\ 3 & 4\\end{pmatrix}. Compute \\det(A).",
  "solution": "\\det(A) = 1\\cdot4 - 2\\cdot3 = -2.",
  "time_submitted": "2026-05-07T12:30:00+03:00"
}
```

Interpret `exercise` as the question prompt and `solution` as the student's submitted answer. Both fields may contain plain text, LaTeX, or a mix of both.

If only the bare pair is provided, require the user to also provide a `student_id` and destination log path, or infer them only when the request unambiguously names an existing student log file. Do not append to an arbitrary default log.

## Workflow

1. Validate that the exercise-answer pair has `id`, `exercise`, `solution`, and `time_submitted`.
2. Determine `student_id` and `log_file`. If either is missing and cannot be inferred unambiguously, return an error JSON and do not append.
3. Read `AGENTS.md` if the grading schema or log event schema is not already in context.
4. If the log file exists, read all valid JSONL events in it. Use the latest `student_profile_after_attempt` as the previous profile. If no snapshot exists, derive topic levels from prior `grading_result.topic_level_updates`.
5. Identify the relevant Linear Algebra 1 topics and approximate difficulty from the exercise.
6. Grade the submitted `solution` for mathematical correctness, method, notation, and conceptual understanding.
7. Build a schema-compatible grading object internally, then convert it to one JSONL event using the event format below.
8. Append exactly one compact JSON object as one newline-terminated line to `log_file`. Create the parent directory if needed.
9. Return only the appended event JSON. Do not wrap it in prose.

Use `scripts/evaluate_pair.py` to validate the input and generate a schema-compatible draft:

```bash
python3 scripts/evaluate_pair.py path/to/pair.json
```

The script does not replace mathematical judgment. Fill or revise its rubric, diagnosis, topic updates, and feedback after checking the student's solution.

If `scripts/evaluate_pair.py` is missing, continue manually using these instructions and `AGENTS.md`.

## JSONL Event Format

Append one line matching this shape:

```json
{
  "schema_version": "1.0",
  "event_type": "exercise_attempt_graded",
  "student_id": "student-123",
  "attempt_id": "attempt-20260507-0001",
  "exercise_id": "la1-000001",
  "timestamp": "2026-05-07T12:01:30+03:00",
  "exercise_answer_pair": {
    "id": "la1-000001",
    "exercise": "Let A = \\begin{pmatrix}1 & 2 \\\\ 3 & 4\\end{pmatrix}. Compute \\det(A).",
    "solution": "\\det(A) = 1\\cdot4 - 2\\cdot3 = -2.",
    "time_submitted": "2026-05-07T12:30:00+03:00"
  },
  "exercise": {
    "difficulty": 2,
    "topics": ["determinants"],
    "prompt": "Let A = \\begin{pmatrix}1 & 2 \\\\ 3 & 4\\end{pmatrix}. Compute \\det(A)."
  },
  "submission": {
    "answer_text_hash": "sha256:...",
    "answer_text_ref": null
  },
  "grading_result": {
    "score": 1.0,
    "max_score": 1.0,
    "is_correct": true,
    "weaknesses": [],
    "topic_level_updates": [
      {
        "topic": "Determinants and their algebraic and geometric meanings",
        "previous_level": 3.0,
        "new_level": 3.3,
        "confidence": 0.4
      }
    ],
    "rubric": [],
    "mastered_skills": [],
    "misconceptions": [],
    "recommended_next_topics": [],
    "feedback_to_student": "..."
  },
  "student_profile_after_attempt": {
    "overall_level": 3.3,
    "topics": [
      {
        "topic": "Determinants and their algebraic and geometric meanings",
        "level": 3.3,
        "confidence": 0.4,
        "last_assessed": "2026-05-07T12:01:30+03:00"
      }
    ]
  }
}
```

Keep this event as a single JSON object on one line in the `.jsonl` file. Do not pretty-print the appended line.

`generate_exercise_from_log.py` specifically reads:

- `event_type`
- `student_id`
- `timestamp`
- `exercise.difficulty`
- `exercise.topics`
- `grading_result.score`
- `grading_result.weaknesses`
- `grading_result.topic_level_updates`
- `student_profile_after_attempt`

Additional fields are allowed, but do not omit the fields above.

## Attempt IDs And Timestamps

- Set `timestamp` to the grading time as an ISO 8601 timestamp with timezone.
- Generate `attempt_id` as `attempt-YYYYMMDD-NNNN`, using the grading date and the next sequence number for that student log. If prior events already use a higher same-day sequence, increment it.
- Set `exercise_id` to the pair's `id`.
- Compute `submission.answer_text_hash` as a SHA-256 hash of the exact submitted `solution`, prefixed with `sha256:`.
- Use `submission.answer_text_ref: null` unless the answer was separately written to a submissions file.

## Profile Update Rules

Use the latest profile snapshot in the log as the starting point. For each directly evidenced topic update:

- `previous_level` is the prior level for that course topic, or a conservative baseline such as `3.0` when no prior evidence exists.
- `new_level` should move gradually according to score, difficulty, and quality of reasoning. Avoid jumps larger than about `0.6` from one attempt unless the evidence is unusually strong.
- `confidence` should increase with repeated evidence, but remain modest for sparse evidence.
- Update or add the corresponding topic object in `student_profile_after_attempt`.
- Set `overall_level` to the rounded average of known topic levels.

Use the canonical course topic names from `AGENTS.md` for `topic_level_updates.topic` and `student_profile_after_attempt.topics[].topic`. The shorter tags in `exercise.topics` may be compact slugs such as `determinants`, `rank-nullity`, or `eigenvectors`.

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

If the log destination is missing, return:

```json
{
  "error": "missing_log_destination",
  "message": "Provide student_id and log_file so the graded attempt can be appended."
}
```
