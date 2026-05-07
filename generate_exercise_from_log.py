#!/usr/bin/env python
"""Generate a personalized Linear Algebra 1 exercise set from a student JSONL log."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


COURSE = "Linear Algebra 1"

COURSE_TOPICS = [
    "Systems of linear equations and Gaussian elimination",
    "Matrix operations, inverses, and elementary matrices",
    "Vectors, linear combinations, span, and geometric interpretation",
    "Linear independence, bases, coordinates, and dimension",
    "Subspaces, including column space, null space, row space, and their bases",
    "Rank, nullity, the rank-nullity theorem, and consistency criteria",
    "Linear transformations, kernels, images, standard matrices, and composition",
    "Change of basis and coordinate representations",
    "Determinants and their algebraic and geometric meanings",
    "Eigenvalues, eigenvectors, eigenspaces, diagonalization, and powers of matrices",
    "Orthogonality, projections, Gram-Schmidt, and least squares when included in the course",
    "Proof skills: definitions, counterexamples, theorem application, and abstraction",
]


def load_dotenv(path: Path = Path(".env")) -> None:
    """Load simple KEY=value entries from .env without overriding existing env vars."""
    if not path.exists():
        return

    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    events: list[dict[str, Any]] = []
    warnings: list[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as exc:
                warnings.append(f"Skipped malformed JSON on line {line_number}: {exc}")
    if not events:
        raise ValueError(f"No valid JSONL events found in {path}")
    return events, warnings


def latest_profile(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    for event in reversed(events):
        profile = event.get("student_profile_after_attempt")
        if isinstance(profile, dict):
            return profile
    return None


def derive_profile_from_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    topics: dict[str, dict[str, Any]] = {}
    for event in events:
        timestamp = event.get("timestamp")
        updates = (
            event.get("grading_result", {})
            .get("topic_level_updates", [])
        )
        if not isinstance(updates, list):
            continue
        for update in updates:
            topic = update.get("topic")
            if not topic:
                continue
            topics[topic] = {
                "topic": topic,
                "level": float(update.get("new_level", 3.0)),
                "confidence": float(update.get("confidence", 0.35)),
                "last_assessed": timestamp,
            }

    if topics:
        overall = sum(topic["level"] for topic in topics.values()) / len(topics)
    else:
        overall = 3.0

    return {
        "overall_level": round(overall, 2),
        "topics": list(topics.values()),
    }


def summarize_performance(events: list[dict[str, Any]], window: int = 5) -> dict[str, Any]:
    graded_events = [event for event in events if event.get("event_type") == "exercise_attempt_graded"]
    recent = graded_events[-window:]

    scores = []
    attempted_difficulties = []
    weaknesses: Counter[str] = Counter()
    recent_topics: Counter[str] = Counter()

    for event in recent:
        grading = event.get("grading_result", {})
        if isinstance(grading.get("score"), (int, float)):
            scores.append(float(grading["score"]))
        exercise = event.get("exercise", {})
        if isinstance(exercise.get("difficulty"), (int, float)):
            attempted_difficulties.append(float(exercise["difficulty"]))
        for weakness in grading.get("weaknesses", []) or []:
            weaknesses[str(weakness)] += 1
        for topic in exercise.get("topics", []) or []:
            recent_topics[str(topic)] += 1

    return {
        "attempt_count": len(graded_events),
        "recent_average_score": round(sum(scores) / len(scores), 3) if scores else None,
        "recent_average_attempted_difficulty": (
            round(sum(attempted_difficulties) / len(attempted_difficulties), 2)
            if attempted_difficulties
            else None
        ),
        "common_recent_weaknesses": [item for item, _ in weaknesses.most_common(6)],
        "recent_topic_tags": [item for item, _ in recent_topics.most_common(8)],
    }


def target_difficulty(level: float, confidence: float) -> int:
    """Pick a challenge level just above observed mastery without jumping too far."""
    if confidence < 0.45:
        lift = 0.5
    elif confidence < 0.7:
        lift = 0.8
    else:
        lift = 1.1
    return int(clamp(math.ceil(level + lift), 1, 10))


def build_topic_plan(profile: dict[str, Any]) -> list[dict[str, Any]]:
    profile_topics = {
        topic_info.get("topic"): topic_info
        for topic_info in profile.get("topics", [])
        if isinstance(topic_info, dict)
    }
    overall_level = float(profile.get("overall_level", 3.0))
    fallback_level = clamp(overall_level - 1.0, 2.0, 7.0)

    plan = []
    for topic in COURSE_TOPICS:
        topic_info = profile_topics.get(topic)
        if topic_info:
            level = float(topic_info.get("level", overall_level))
            confidence = float(topic_info.get("confidence", 0.35))
            evidence = "directly assessed"
        else:
            level = fallback_level
            confidence = 0.25
            evidence = "not yet directly assessed; inferred conservatively from overall level"
        plan.append(
            {
                "topic": topic,
                "current_level": round(clamp(level, 1.0, 10.0), 2),
                "confidence": round(clamp(confidence, 0.0, 1.0), 2),
                "target_difficulty": target_difficulty(level, confidence),
                "evidence": evidence,
            }
        )
    return plan


def build_prompt(
    *,
    student_id: str,
    log_path: Path,
    profile: dict[str, Any],
    topic_plan: list[dict[str, Any]],
    performance: dict[str, Any],
    include_solutions: bool,
) -> str:
    solution_instruction = (
        "Include a concise worked solution and final answer for every question."
        if include_solutions
        else "Do not include solutions or final answers."
    )

    return f"""
You are generating a personalized exercise set for {COURSE}.

Goal:
- Promote the student slightly beyond their current demonstrated mastery.
- Include exactly one question for each course topic in topic_plan.
- Use each topic's target_difficulty as the question difficulty.
- Make questions self-contained and mathematically precise.
- Avoid making the set feel like a survey of trivia; each question should assess a real skill.
- {solution_instruction}

Student:
- student_id: {student_id}
- source_log: {log_path.as_posix()}

Recent performance summary:
{json.dumps(performance, indent=2)}

Latest or derived profile:
{json.dumps(profile, indent=2)}

Topic plan:
{json.dumps(topic_plan, indent=2)}

Return only valid JSON with this shape:
{{
  "schema_version": "1.0",
  "student_id": "{student_id}",
  "course": "{COURSE}",
  "source_log": "{log_path.as_posix()}",
  "generated_at": "ISO-8601 timestamp",
  "overall_target_difficulty": 1,
  "rationale": "Brief explanation of how the set is calibrated.",
  "exercise_set": {{
    "title": "Personalized Linear Algebra 1 Practice",
    "questions": [
      {{
        "question_id": "q01",
        "topic": "Systems of linear equations and Gaussian elimination",
        "difficulty": 1,
        "learning_goal": "What this question is meant to strengthen.",
        "prompt": "The actual exercise question.",
        "expected_techniques": ["technique 1", "technique 2"]
      }}
    ]
  }}
}}
""".strip()


def call_openai_model(prompt: str, model: str) -> str:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("The openai package is not installed. Install it or use --dry-run.") from exc

    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set. Set it or use --dry-run.")

    client = OpenAI()
    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": (
                    "You are a careful Linear Algebra 1 exercise generator. "
                    "Return only valid JSON and match the requested schema."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    )

    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text

    # Fallback for SDK response shapes that do not expose output_text.
    chunks: list[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if text:
                chunks.append(text)
    if not chunks:
        raise RuntimeError("The model response did not contain text output.")
    return "\n".join(chunks)


def call_gemini_model(prompt: str, model: str) -> str:
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError("The google-genai package is not installed. Install it or use --dry-run.") from exc

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set. Set it in .env/the shell or use --dry-run.")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            system_instruction=(
                "You are a careful Linear Algebra 1 exercise generator. "
                "Return only valid JSON and match the requested schema."
            ),
        ),
    )

    output_text = getattr(response, "text", None)
    if output_text:
        return output_text
    raise RuntimeError("The Gemini response did not contain text output.")


def resolve_provider_and_model(provider: str, model: str | None) -> tuple[str, str]:
    if provider == "auto":
        if os.environ.get("GOOGLE_API_KEY"):
            provider = "gemini"
        elif os.environ.get("OPENAI_API_KEY"):
            provider = "openai"
        else:
            raise RuntimeError(
                "No LLM API key found. Set GOOGLE_API_KEY or OPENAI_API_KEY in .env/the shell, "
                "or use --dry-run."
            )

    if provider == "gemini":
        resolved_model = model or os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash"
    elif provider == "openai":
        resolved_model = model or os.environ.get("OPENAI_MODEL") or "gpt-5.4-mini"
    else:
        raise RuntimeError(f"Unsupported provider: {provider}")

    return provider, resolved_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a personalized Linear Algebra 1 exercise set from a student JSONL log."
    )
    parser.add_argument("log_file", type=Path, help="Path to a student's append-only JSONL log.")
    parser.add_argument(
        "--model",
        default=None,
        help=(
            "Model to use. Defaults to GEMINI_MODEL/gemini-2.5-flash for Gemini, "
            "or OPENAI_MODEL/gpt-5.4-mini for OpenAI."
        ),
    )
    parser.add_argument(
        "--provider",
        choices=["auto", "gemini", "openai"],
        default="auto",
        help="LLM provider to use. Defaults to auto-detecting from available API keys.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the generated exercise JSON. Prints to stdout if omitted.",
    )
    parser.add_argument(
        "--include-solutions",
        action="store_true",
        help="Ask the model to include concise worked solutions.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not call the model; print the inferred topic plan and model prompt.",
    )
    return parser.parse_args()


def main() -> int:
    load_dotenv()
    args = parse_args()
    events, warnings = load_jsonl(args.log_file)
    student_id = str(events[-1].get("student_id", "unknown-student"))
    profile = latest_profile(events) or derive_profile_from_events(events)
    performance = summarize_performance(events)
    topic_plan = build_topic_plan(profile)
    prompt = build_prompt(
        student_id=student_id,
        log_path=args.log_file,
        profile=profile,
        topic_plan=topic_plan,
        performance=performance,
        include_solutions=args.include_solutions,
    )

    if args.dry_run:
        result = {
            "dry_run": True,
            "student_id": student_id,
            "warnings": warnings,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "topic_plan": topic_plan,
            "prompt": prompt,
        }
        output = json.dumps(result, indent=2)
    else:
        provider, model = resolve_provider_and_model(args.provider, args.model)
        if provider == "gemini":
            output = call_gemini_model(prompt, model).strip()
        else:
            output = call_openai_model(prompt, model).strip()
        try:
            parsed = json.loads(output)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Model returned invalid JSON: {exc}\n\nRaw output:\n{output}") from exc
        parsed.setdefault("generated_at", datetime.now(timezone.utc).isoformat())
        output = json.dumps(parsed, indent=2)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
