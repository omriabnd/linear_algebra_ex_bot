#!/usr/bin/env python3
"""Validate a Linear Algebra 1 exercise-answer pair and draft grading JSON."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = ("id", "exercise", "solution", "time_submitted")

TOPIC_KEYWORDS = {
    "Systems of linear equations and Gaussian elimination": [
        "system",
        "gaussian",
        "row-reduc",
        "rref",
        "elimination",
    ],
    "Matrix operations, inverses, and elementary matrices": [
        "matrix",
        "inverse",
        "elementary",
        "multiply",
        "product",
    ],
    "Vectors, linear combinations, span, and geometric interpretation": [
        "vector",
        "span",
        "linear combination",
    ],
    "Linear independence, bases, coordinates, and dimension": [
        "independent",
        "basis",
        "coordinate",
        "dimension",
    ],
    "Subspaces, column space, null space, row space, and bases": [
        "subspace",
        "null space",
        "kernel",
        "column space",
        "row space",
    ],
    "Rank, nullity, rank-nullity, and consistency": [
        "rank",
        "nullity",
        "consistent",
        "inconsistent",
    ],
    "Linear transformations, kernels, images, and standard matrices": [
        "linear transformation",
        "kernel",
        "image",
        "onto",
        "one-to-one",
    ],
    "Change of basis and coordinate representations": [
        "change of basis",
        "basis b",
        "coordinate vector",
    ],
    "Determinants": [
        "det",
        "determinant",
    ],
    "Eigenvalues, eigenvectors, eigenspaces, and diagonalization": [
        "eigen",
        "diagonal",
        "diagonalizable",
    ],
    "Orthogonality, projections, Gram-Schmidt, and least squares": [
        "orthogonal",
        "projection",
        "gram-schmidt",
        "least squares",
    ],
    "Proof skills and abstraction": [
        "prove",
        "proof",
        "show that",
        "counterexample",
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pair_json", type=Path, help="path to the exercise-answer pair JSON")
    parser.add_argument("--student-id", default="unknown-student")
    parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    return parser.parse_args()


def load_pair(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Input must be a JSON object")

    for field in REQUIRED_FIELDS:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
        if not isinstance(data[field], str) or not data[field].strip():
            raise ValueError(f"Field must be a nonempty string: {field}")

    return data


def infer_topics(exercise: str) -> list[str]:
    text = exercise.lower()
    topics = [
        topic
        for topic, keywords in TOPIC_KEYWORDS.items()
        if any(keyword in text for keyword in keywords)
    ]
    return topics or ["Linear Algebra 1 general reasoning"]


def infer_difficulty(exercise: str, topics: list[str]) -> int:
    text = exercise.lower()
    difficulty = 3
    if any(word in text for word in ["prove", "proof", "show that", "diagonalizable"]):
        difficulty += 2
    if any(word in text for word in ["parameter", "for which", "all values"]):
        difficulty += 2
    if len(topics) >= 3:
        difficulty += 1
    if any(word in text for word in ["eigen", "change of basis", "rank-nullity"]):
        difficulty += 1
    return max(1, min(10, difficulty))


def draft_evaluation(pair: dict[str, Any], student_id: str) -> dict[str, Any]:
    topics = infer_topics(pair["exercise"])
    difficulty = infer_difficulty(pair["exercise"], topics)
    graded_at = datetime.now().astimezone().isoformat(timespec="seconds")

    return {
        "schema_version": "1.0",
        "student_id": student_id,
        "exercise_id": pair["id"],
        "submitted_at": pair["time_submitted"],
        "graded_at": graded_at,
        "course": "Linear Algebra 1",
        "exercise": {
            "difficulty": difficulty,
            "topics": topics,
            "prompt": pair["exercise"],
        },
        "grade": {
            "score": None,
            "max_score": 1.0,
            "is_correct": None,
            "rubric": [
                {
                    "criterion": "mathematical correctness",
                    "score": None,
                    "max_score": 0.5,
                    "feedback": "Assess whether the final answer is mathematically correct.",
                },
                {
                    "criterion": "method and reasoning",
                    "score": None,
                    "max_score": 0.35,
                    "feedback": "Assess whether the submitted reasoning supports the answer.",
                },
                {
                    "criterion": "notation and clarity",
                    "score": None,
                    "max_score": 0.15,
                    "feedback": "Assess whether notation is clear enough to follow.",
                },
            ],
        },
        "diagnosis": {
            "mastered_skills": [],
            "weaknesses": [],
            "misconceptions": [],
            "recommended_next_topics": [],
        },
        "topic_level_updates": [
            {
                "topic": topic,
                "previous_level": None,
                "new_level": None,
                "confidence": None,
                "evidence": "Fill after evaluating the submitted solution.",
            }
            for topic in topics
        ],
        "feedback_to_student": "Fill after evaluating the submitted solution.",
    }


def main() -> int:
    args = parse_args()
    try:
        pair = load_pair(args.pair_json)
    except ValueError as exc:
        print(
            json.dumps(
                {
                    "error": "invalid_exercise_answer_pair",
                    "message": str(exc),
                },
                indent=2,
            )
        )
        return 1

    indent = 2 if args.pretty else None
    print(json.dumps(draft_evaluation(pair, args.student_id), indent=indent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
