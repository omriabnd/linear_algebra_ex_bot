# Linear Algebra Exercise Bot

## Course Mastery Topics

A student who completes a first course in linear algebra should be assessed across these major topics:

1. Systems of linear equations and Gaussian elimination.
2. Matrix operations, inverses, and elementary matrices.
3. Vectors, linear combinations, span, and geometric interpretation.
4. Linear independence, bases, coordinates, and dimension.
5. Subspaces, including column space, null space, row space, and their bases.
6. Rank, nullity, the rank-nullity theorem, and consistency criteria.
7. Linear transformations, kernels, images, standard matrices, and composition.
8. Change of basis and coordinate representations.
9. Determinants and their algebraic and geometric meanings.
10. Eigenvalues, eigenvectors, eigenspaces, diagonalization, and powers of matrices.
11. Orthogonality, projections, Gram-Schmidt, and least squares when included in the course.
12. Proof skills: definitions, counterexamples, theorem application, and abstraction.

Track student level per topic on a `1-10` scale, where `1` means beginner recognition and `10` means exam-ready mastery including proofs and synthesis. Store confidence separately from level because sparse evidence should not look like certainty.

Represent each student by their complete append-only history log. Do not treat a separate profile object as the source of truth. Current topic levels, weaknesses, mastery tags, and recommendations should be derived from the student's log, or read from the latest `student_profile_after_attempt` snapshot inside that log.

## Exercise Grading JSON

Return the result of grading a single exercise as JSON with this shape:

```json
{
  "schema_version": "1.0",
  "student_id": "student-123",
  "exercise_id": "la1-rank-nullity-0007",
  "submitted_at": "2026-05-07T12:00:00+03:00",
  "graded_at": "2026-05-07T12:01:30+03:00",
  "course": "Linear Algebra 1",
  "exercise": {
    "difficulty": 6,
    "topics": ["rank-nullity", "null-space", "basis"],
    "prompt": "Find a basis for the null space of A and compute rank(A)."
  },
  "grade": {
    "score": 0.78,
    "max_score": 1.0,
    "is_correct": false,
    "rubric": [
      {
        "criterion": "row reduction",
        "score": 0.3,
        "max_score": 0.3,
        "feedback": "Correct row-reduction steps."
      },
      {
        "criterion": "null-space basis",
        "score": 0.28,
        "max_score": 0.4,
        "feedback": "The basis direction is correct, but the final vector has a sign error."
      },
      {
        "criterion": "rank-nullity reasoning",
        "score": 0.2,
        "max_score": 0.3,
        "feedback": "Rank-nullity was applied correctly."
      }
    ]
  },
  "diagnosis": {
    "mastered_skills": ["sets up homogeneous systems", "uses rank-nullity"],
    "weaknesses": ["arithmetic accuracy", "basis normalization"],
    "misconceptions": ["treats scalar multiples as different one-dimensional bases"],
    "recommended_next_topics": ["null-space basis practice", "linear independence checks"]
  },
  "topic_level_updates": [
    {
      "topic": "Subspaces and null space",
      "previous_level": 5.2,
      "new_level": 5.4,
      "confidence": 0.68,
      "evidence": "Mostly correct null-space computation with minor arithmetic error."
    }
  ],
  "feedback_to_student": "Your method is solid. Recheck the final substitution step: the basis vector may be scaled, but it must satisfy Ax = 0."
}
```

Use `score` as a normalized value from `0` to `1`. Use `is_correct` for quick pass/fail decisions, but prefer the rubric and diagnosis for learning decisions. Keep `topic_level_updates` limited to topics directly evidenced by the submitted solution.

## Student Representation And History Log

Represent each student as one newline-delimited JSON (`.jsonl`) log containing the student's entire exercise-solution history. The log is the canonical student record. Each line is one immutable event, usually one graded exercise attempt. This makes the student representation append-only, easy to stream, and easy to recover if one record is malformed.

Use one file per student:

```text
students/{student_id}.jsonl
```

Each log line should use this shape:

```json
{
  "schema_version": "1.0",
  "event_type": "exercise_attempt_graded",
  "student_id": "student-123",
  "attempt_id": "attempt-20260507-0001",
  "exercise_id": "la1-rank-nullity-0007",
  "timestamp": "2026-05-07T12:01:30+03:00",
  "exercise": {
    "difficulty": 6,
    "topics": ["rank-nullity", "null-space", "basis"],
    "prompt_hash": "sha256:..."
  },
  "submission": {
    "answer_text_hash": "sha256:...",
    "answer_text_ref": "submissions/student-123/attempt-20260507-0001.txt"
  },
  "grading_result": {
    "score": 0.78,
    "max_score": 1.0,
    "is_correct": false,
    "weaknesses": ["arithmetic accuracy", "basis normalization"],
    "topic_level_updates": [
      {
        "topic": "Subspaces and null space",
        "previous_level": 5.2,
        "new_level": 5.4,
        "confidence": 0.68
      }
    ]
  },
  "student_profile_after_attempt": {
    "overall_level": 5.8,
    "topics": [
      {
        "topic": "Subspaces and null space",
        "level": 5.4,
        "confidence": 0.68,
        "last_assessed": "2026-05-07T12:01:30+03:00"
      },
      {
        "topic": "Eigenvalues and diagonalization",
        "level": 4.9,
        "confidence": 0.51,
        "last_assessed": "2026-05-01T09:15:00+03:00"
      }
    ]
  }
}
```

Keep full student answers outside the JSONL log when they may be long; store `answer_text_ref` and a hash instead. Include `student_profile_after_attempt` as a derived snapshot for convenience, but keep the full log as the authoritative record. If a snapshot disagrees with prior events, prefer recomputing the profile from the full event history.
