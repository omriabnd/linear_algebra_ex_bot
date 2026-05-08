#!/usr/bin/env python3
"""Local web app for iterative Linear Algebra 1 practice."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import ssl
import threading
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import generate_exercise_from_log as generator


ROOT = Path(__file__).resolve().parent
SKILL_PATH = ROOT / ".codex" / "skills" / "lin-algebra-1-assess" / "SKILL.md"
AGENTS_PATH = ROOT / "AGENTS.md"
BASELINE_LOG = ROOT / "mock_logs" / "average_student.jsonl"
RUNTIME_DIR = ROOT / "runtime"
LOG_PATH = RUNTIME_DIR / "web_student.jsonl"
STATE_PATH = RUNTIME_DIR / "app_state.json"
COURSE = "Linear Algebra 1"
JSON_HEADERS = {"Content-Type": "application/json; charset=utf-8"}

STATE_LOCK = threading.Lock()


HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Linear Algebra Practice</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #17202a;
      --muted: #5d6b7a;
      --line: #d8dee8;
      --panel: #ffffff;
      --surface: #f6f8fb;
      --blue: #315fbb;
      --green: #167a5b;
      --red: #b24040;
      --amber: #8a6100;
      --focus: #ecb22e;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--surface);
      color: var(--ink);
    }
    .app {
      min-height: 100vh;
      display: grid;
      grid-template-rows: auto 1fr;
    }
    header {
      border-bottom: 1px solid var(--line);
      background: #fbfcfe;
    }
    .topbar {
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
      min-height: 72px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }
    h1 {
      margin: 0;
      font-size: 22px;
      line-height: 1.2;
      font-weight: 720;
    }
    .status {
      display: flex;
      align-items: center;
      gap: 10px;
      color: var(--muted);
      font-size: 14px;
      min-width: 0;
    }
    .dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--green);
      flex: 0 0 auto;
    }
    main {
      width: min(1180px, calc(100% - 32px));
      margin: 24px auto 40px;
      display: grid;
      grid-template-columns: minmax(0, 1.35fr) minmax(280px, 0.65fr);
      gap: 20px;
      align-items: start;
    }
    .workspace, .side {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }
    .section {
      padding: 22px;
      border-bottom: 1px solid var(--line);
    }
    .section:last-child { border-bottom: 0; }
    .label {
      margin: 0 0 8px;
      color: var(--muted);
      font-size: 13px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0;
    }
    .meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: 0 0 14px;
    }
    .chip {
      display: inline-flex;
      min-height: 28px;
      align-items: center;
      padding: 4px 9px;
      border: 1px solid #cfd7e5;
      border-radius: 999px;
      color: #26364c;
      background: #f8fafc;
      font-size: 13px;
      line-height: 1.2;
    }
    .prompt {
      white-space: pre-wrap;
      font-size: 19px;
      line-height: 1.55;
      margin: 0;
    }
    textarea {
      width: 100%;
      min-height: 220px;
      resize: vertical;
      border: 1px solid #bfc9d8;
      border-radius: 8px;
      padding: 14px;
      font: 16px/1.45 ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
      color: var(--ink);
      background: #fff;
    }
    textarea:focus, button:focus {
      outline: 3px solid color-mix(in srgb, var(--focus) 55%, transparent);
      outline-offset: 2px;
    }
    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
      margin-top: 14px;
    }
    button {
      min-height: 40px;
      border: 1px solid #244d9e;
      border-radius: 7px;
      background: var(--blue);
      color: #fff;
      padding: 8px 14px;
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
    }
    button.secondary {
      background: #fff;
      color: #253449;
      border-color: #aeb9c8;
    }
    button:disabled {
      cursor: not-allowed;
      opacity: 0.65;
    }
    .feedback {
      display: grid;
      gap: 14px;
    }
    .scoreline {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 12px;
    }
    .score {
      font-size: 34px;
      font-weight: 760;
      line-height: 1;
      color: var(--blue);
    }
    .result {
      margin: 0;
      font-size: 16px;
      line-height: 1.5;
    }
    .list {
      margin: 0;
      padding-left: 18px;
      color: var(--muted);
      line-height: 1.45;
    }
    .empty {
      margin: 0;
      color: var(--muted);
      line-height: 1.5;
    }
    .error {
      color: var(--red);
      background: #fff5f5;
      border: 1px solid #f1b8b8;
      border-radius: 8px;
      padding: 12px;
      white-space: pre-wrap;
    }
    .logpath {
      overflow-wrap: anywhere;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.4;
    }
    .spinner {
      width: 16px;
      height: 16px;
      border: 2px solid #c7d1e0;
      border-top-color: var(--blue);
      border-radius: 50%;
      animation: spin 0.75s linear infinite;
      display: none;
    }
    .busy .spinner { display: inline-block; }
    @keyframes spin { to { transform: rotate(360deg); } }
    @media (max-width: 840px) {
      main { grid-template-columns: 1fr; }
      .topbar { align-items: flex-start; flex-direction: column; padding: 16px 0; }
      .section { padding: 18px; }
      .prompt { font-size: 17px; }
    }
  </style>
</head>
<body>
  <div class="app">
    <header>
      <div class="topbar">
        <h1>Linear Algebra Practice</h1>
        <div class="status" id="status"><span class="dot"></span><span>Starting</span><span class="spinner"></span></div>
      </div>
    </header>
    <main>
      <section class="workspace">
        <div class="section">
          <p class="label">Exercise</p>
          <div class="meta" id="meta"></div>
          <p class="prompt" id="prompt">Loading...</p>
        </div>
        <div class="section">
          <p class="label">Your Answer</p>
          <textarea id="answer" spellcheck="false" placeholder="Write in plain text or LaTeX."></textarea>
          <div class="actions">
            <button id="submit">Submit Solution</button>
            <button class="secondary" id="reset">Reset</button>
          </div>
        </div>
      </section>
      <aside class="side">
        <div class="section">
          <p class="label">Evaluation</p>
          <div id="feedback"><p class="empty">Submit a solution to see feedback here.</p></div>
        </div>
        <div class="section">
          <p class="label">Student Log</p>
          <p class="logpath" id="logpath"></p>
        </div>
      </aside>
    </main>
  </div>
  <script>
    const els = {
      status: document.getElementById('status'),
      meta: document.getElementById('meta'),
      prompt: document.getElementById('prompt'),
      answer: document.getElementById('answer'),
      submit: document.getElementById('submit'),
      reset: document.getElementById('reset'),
      feedback: document.getElementById('feedback'),
      logpath: document.getElementById('logpath')
    };

    let currentExercise = null;

    function setBusy(message, busy = true) {
      document.body.classList.toggle('busy', busy);
      els.status.querySelector('span:nth-child(2)').textContent = message;
      els.submit.disabled = busy;
      els.reset.disabled = busy;
    }

    function chip(text) {
      const item = document.createElement('span');
      item.className = 'chip';
      item.textContent = text;
      return item;
    }

    function renderExercise(data) {
      currentExercise = data.current_exercise;
      els.meta.replaceChildren();
      if (currentExercise.topic) els.meta.appendChild(chip(currentExercise.topic));
      if (currentExercise.difficulty) els.meta.appendChild(chip(`Difficulty ${currentExercise.difficulty}`));
      if (currentExercise.question_id) els.meta.appendChild(chip(currentExercise.question_id));
      els.prompt.textContent = currentExercise.prompt || 'No exercise available.';
      els.logpath.textContent = data.log_file || '';
    }

    function renderFeedback(event) {
      const grading = event.grading_result || {};
      const score = typeof grading.score === 'number' ? Math.round(grading.score * 100) : null;
      const weaknesses = Array.isArray(grading.weaknesses) ? grading.weaknesses : [];
      const updates = Array.isArray(grading.topic_level_updates) ? grading.topic_level_updates : [];
      const feedback = grading.feedback_to_student || event.feedback_to_student || 'Evaluation appended to the log.';

      const wrap = document.createElement('div');
      wrap.className = 'feedback';
      wrap.innerHTML = `
        <div class="scoreline">
          <div class="score">${score === null ? '-' : `${score}%`}</div>
          <div>${grading.is_correct ? 'Correct' : 'Needs work'}</div>
        </div>
        <p class="result"></p>
      `;
      wrap.querySelector('.result').textContent = feedback;
      if (weaknesses.length) {
        const list = document.createElement('ul');
        list.className = 'list';
        weaknesses.forEach((text) => {
          const li = document.createElement('li');
          li.textContent = text;
          list.appendChild(li);
        });
        wrap.appendChild(list);
      }
      if (updates.length) {
        const list = document.createElement('ul');
        list.className = 'list';
        updates.forEach((update) => {
          const li = document.createElement('li');
          li.textContent = `${update.topic}: ${update.previous_level} -> ${update.new_level}`;
          list.appendChild(li);
        });
        wrap.appendChild(list);
      }
      els.feedback.replaceChildren(wrap);
    }

    function renderError(message) {
      const node = document.createElement('div');
      node.className = 'error';
      node.textContent = message;
      els.feedback.replaceChildren(node);
    }

    async function requestJson(path, options) {
      const response = await fetch(path, options);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || data.message || 'Request failed');
      return data;
    }

    async function loadState() {
      setBusy('Generating exercise');
      try {
        const data = await requestJson('/api/state');
        renderExercise(data);
        setBusy('Ready', false);
      } catch (error) {
        renderError(error.message);
        setBusy('Error', false);
      }
    }

    async function submitAnswer() {
      const solution = els.answer.value.trim();
      if (!solution) {
        renderError('Write a solution before submitting.');
        return;
      }
      setBusy('Evaluating answer');
      try {
        const data = await requestJson('/api/submit', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({solution})
        });
        renderFeedback(data.evaluation);
        renderExercise(data);
        els.answer.value = '';
        setBusy('Ready', false);
      } catch (error) {
        renderError(error.message);
        setBusy('Error', false);
      }
    }

    async function resetApp() {
      setBusy('Resetting');
      try {
        const data = await requestJson('/api/reset', {method: 'POST'});
        renderExercise(data);
        els.answer.value = '';
        els.feedback.innerHTML = '<p class="empty">Submit a solution to see feedback here.</p>';
        setBusy('Ready', false);
      } catch (error) {
        renderError(error.message);
        setBusy('Error', false);
      }
    }

    els.submit.addEventListener('click', submitAnswer);
    els.reset.addEventListener('click', resetApp);
    loadState();
  </script>
</body>
</html>
"""


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return default or {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def compact_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=True, separators=(",", ":"))


def parse_json_text(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.DOTALL)
    if fenced:
        cleaned = fenced.group(1).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise


def load_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def ensure_runtime_log() -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    if not LOG_PATH.exists():
        shutil.copyfile(BASELINE_LOG, LOG_PATH)


def reset_runtime() -> dict[str, Any]:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(BASELINE_LOG, LOG_PATH)
    state = {"current_exercise": None}
    save_json(STATE_PATH, state)
    return state


def student_id_from_log() -> str:
    events = load_events(LOG_PATH)
    for event in reversed(events):
        if event.get("student_id"):
            return str(event["student_id"])
    return "student-web-001"


def append_event(event: dict[str, Any]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(compact_json(event) + "\n")


def call_gemini_json(prompt: str, system_instruction: str) -> dict[str, Any]:
    generator.load_dotenv(ROOT / ".env")
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set in .env.")
    model = os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash"
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        + urllib.parse.quote(model, safe="")
        + ":generateContent?key="
        + urllib.parse.quote(api_key, safe="")
    )
    payload = {
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    context = ssl.create_default_context()
    if os.environ.get("ALLOW_INSECURE_LOCAL_TLS", "1") == "1":
        context = ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(request, timeout=90, context=context) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini request failed: HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Gemini request failed: {exc.reason}") from exc

    data = json.loads(raw)
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Gemini response did not include JSON text: {raw}") from exc
    return parse_json_text(text)


def generate_exercise() -> dict[str, Any]:
    ensure_runtime_log()
    events, warnings = generator.load_jsonl(LOG_PATH)
    student_id = str(events[-1].get("student_id", "student-web-001"))
    profile = generator.latest_profile(events) or generator.derive_profile_from_events(events)
    performance = generator.summarize_performance(events)
    topic_plan = generator.build_topic_plan(profile)
    prompt = generator.build_prompt(
        student_id=student_id,
        log_path=LOG_PATH.relative_to(ROOT),
        profile=profile,
        topic_plan=topic_plan,
        performance=performance,
        include_solutions=False,
    )
    try:
        result = call_gemini_json(
            prompt,
            "You are a careful Linear Algebra 1 exercise generator. Return only valid JSON and match the requested schema.",
        )
    except Exception as exc:
        return local_generated_exercise(topic_plan, len(events), str(exc))
    questions = result.get("exercise_set", {}).get("questions", [])
    if not questions:
        raise RuntimeError("The generator returned no questions.")
    graded_count = len([event for event in events if event.get("event_type") == "exercise_attempt_graded"])
    question = questions[graded_count % len(questions)]
    exercise_id = f"web-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{question.get('question_id', 'q')}"
    return {
        "id": exercise_id,
        "question_id": str(question.get("question_id", exercise_id)),
        "topic": str(question.get("topic", "Linear Algebra 1")),
        "difficulty": int(question.get("difficulty", 5)),
        "prompt": str(question.get("prompt", "")),
        "generated_set": result,
        "warnings": warnings,
    }


def local_generated_exercise(topic_plan: list[dict[str, Any]], event_count: int, reason: str) -> dict[str, Any]:
    plan_item = topic_plan[event_count % len(topic_plan)] if topic_plan else {
        "topic": "Determinants and their algebraic and geometric meanings",
        "target_difficulty": 4,
    }
    topic = str(plan_item["topic"])
    difficulty = int(plan_item.get("target_difficulty", 4))
    prompt, expected = local_template(topic)
    exercise_id = f"local-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{event_count + 1:04d}"
    return {
        "id": exercise_id,
        "question_id": f"local-{event_count + 1:04d}",
        "topic": topic,
        "difficulty": difficulty,
        "prompt": prompt,
        "expected_answer": expected,
        "generated_set": {
            "schema_version": "1.0",
            "course": COURSE,
            "rationale": "Generated locally from generate_exercise_from_log.py topic planning because the model API was unavailable.",
        },
        "warnings": [reason],
    }


def local_template(topic: str) -> tuple[str, str]:
    templates = {
        "Systems of linear equations and Gaussian elimination": (
            "Solve the system using row reduction:\n\nx + 2y = 5\n3x - y = 4",
            "x=13/7, y=11/7",
        ),
        "Matrix operations, inverses, and elementary matrices": (
            "Let A = [[1, 2], [3, 7]]. Compute A^{-1}.",
            "[[7,-2],[-3,1]]",
        ),
        "Vectors, linear combinations, span, and geometric interpretation": (
            "Decide whether v = (5, 1) is in span{(1, 2), (3, -1)}. If yes, find coefficients.",
            "v=1*(1,2)+? no, solve gives a=8/7, b=9/7",
        ),
        "Linear independence, bases, coordinates, and dimension": (
            "Determine whether {(1,0,1), (0,1,1), (1,1,2)} is linearly independent in R^3.",
            "dependent, third vector is sum of first two",
        ),
        "Subspaces, including column space, null space, row space, and their bases": (
            "Find a basis for the null space of A = [[1, 2, -1], [0, 1, 3]].",
            "span{(7,-3,1)}",
        ),
        "Rank, nullity, the rank-nullity theorem, and consistency criteria": (
            "A 4 x 6 matrix has rank 3. What is the nullity of the corresponding linear map R^6 -> R^4?",
            "nullity 3",
        ),
        "Linear transformations, kernels, images, standard matrices, and composition": (
            "Let T(x,y) = (x+2y, 3x-y). Find the standard matrix of T and decide whether T is invertible.",
            "[[1,2],[3,-1]], invertible because determinant -7",
        ),
        "Change of basis and coordinate representations": (
            "Let B = {(1,1), (1,-1)}. Find the B-coordinates of v = (4,2).",
            "[v]_B = (3,1)",
        ),
        "Determinants and their algebraic and geometric meanings": (
            "Compute det([[2, 1, 0], [0, 3, 1], [0, 0, 4]]) and state what it says about invertibility.",
            "24, invertible",
        ),
        "Eigenvalues, eigenvectors, eigenspaces, diagonalization, and powers of matrices": (
            "Find the eigenvalues of A = [[2, 0], [0, 5]] and give one eigenvector for each.",
            "eigenvalues 2 and 5 with eigenvectors (1,0) and (0,1)",
        ),
        "Orthogonality, projections, Gram-Schmidt, and least squares when included in the course": (
            "Project v = (3,4) onto the line spanned by u = (1,0).",
            "(3,0)",
        ),
        "Proof skills: definitions, counterexamples, theorem application, and abstraction": (
            "Give a counterexample to the claim: if u and v are nonzero vectors, then {u, v} is linearly independent.",
            "u=v=(1,0), dependent",
        ),
    }
    return templates.get(topic, templates["Determinants and their algebraic and geometric meanings"])


def current_or_new_exercise() -> dict[str, Any]:
    state = load_json(STATE_PATH, {"current_exercise": None})
    current = state.get("current_exercise")
    if not isinstance(current, dict) or not current.get("prompt"):
        current = generate_exercise()
        state["current_exercise"] = current
        save_json(STATE_PATH, state)
    return current


def assessment_prompt(exercise: dict[str, Any], solution: str) -> str:
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    pair = {
        "id": exercise["id"],
        "exercise": exercise["prompt"],
        "solution": solution,
        "time_submitted": now,
    }
    envelope = {
        "student_id": student_id_from_log(),
        "log_file": str(LOG_PATH.relative_to(ROOT)),
        "exercise_answer_pair": pair,
    }
    recent_events = load_events(LOG_PATH)[-8:]
    return f"""
Execute the local Codex skill below for this request. You cannot write files from the model response; instead return exactly the JSONL event object the server must append. The server will append your returned compact JSON object to the log file.

Skill:
{read_text(SKILL_PATH)}

Repository AGENTS.md:
{read_text(AGENTS_PATH)}

Current exercise metadata:
{json.dumps(exercise, indent=2)}

Recent log events:
{json.dumps(recent_events, indent=2)}

Request envelope:
{json.dumps(envelope, indent=2)}

Return only one JSON object. It must be an exercise_attempt_graded event compatible with generate_exercise_from_log.py and with the skill's JSONL Event Format. Set exercise.difficulty and exercise.topics from the current exercise metadata. Include grading_result.feedback_to_student.
""".strip()


def validate_event(event: dict[str, Any], exercise: dict[str, Any], solution: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    events = load_events(LOG_PATH)
    student_id = student_id_from_log()
    event["schema_version"] = "1.0"
    event["event_type"] = "exercise_attempt_graded"
    event["student_id"] = student_id
    event["exercise_id"] = exercise["id"]
    event.setdefault("timestamp", now)
    event.setdefault("attempt_id", next_attempt_id(events, event["timestamp"]))
    event["exercise_answer_pair"] = {
        "id": exercise["id"],
        "exercise": exercise["prompt"],
        "solution": solution,
        "time_submitted": event.get("exercise_answer_pair", {}).get("time_submitted", now),
    }
    event["exercise"] = {
        "difficulty": int(exercise.get("difficulty", 5)),
        "topics": [slugify_topic(str(exercise.get("topic", "linear-algebra")))],
        "prompt": exercise["prompt"],
    }
    event["submission"] = {
        "answer_text_hash": "sha256:" + hashlib.sha256(solution.encode("utf-8")).hexdigest(),
        "answer_text_ref": None,
    }
    grading = event.setdefault("grading_result", {})
    grading.setdefault("score", 0.0)
    grading.setdefault("max_score", 1.0)
    grading.setdefault("is_correct", False)
    grading.setdefault("weaknesses", [])
    grading.setdefault("topic_level_updates", [])
    grading.setdefault("feedback_to_student", "Your answer was evaluated and added to the practice log.")
    event["student_profile_after_attempt"] = normalize_profile(event, events)
    return event


def next_attempt_id(events: list[dict[str, Any]], timestamp: str) -> str:
    date = timestamp[:10].replace("-", "")
    pattern = re.compile(rf"^attempt-{re.escape(date)}-(\d+)$")
    highest = 0
    for event in events:
        match = pattern.match(str(event.get("attempt_id", "")))
        if match:
            highest = max(highest, int(match.group(1)))
    return f"attempt-{date}-{highest + 1:04d}"


def slugify_topic(topic: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")
    return slug or "linear-algebra"


def normalize_profile(event: dict[str, Any], prior_events: list[dict[str, Any]]) -> dict[str, Any]:
    profile = None
    for prior in reversed(prior_events):
        if isinstance(prior.get("student_profile_after_attempt"), dict):
            profile = json.loads(json.dumps(prior["student_profile_after_attempt"]))
            break
    if profile is None:
        profile = generator.derive_profile_from_events(prior_events)

    topics = {
        item.get("topic"): item
        for item in profile.get("topics", [])
        if isinstance(item, dict) and item.get("topic")
    }
    for update in event.get("grading_result", {}).get("topic_level_updates", []) or []:
        topic = update.get("topic")
        if not topic:
            continue
        topics[topic] = {
            "topic": topic,
            "level": float(update.get("new_level", update.get("previous_level", 3.0))),
            "confidence": float(update.get("confidence", 0.35)),
            "last_assessed": event["timestamp"],
        }
    profile["topics"] = list(topics.values())
    if profile["topics"]:
        profile["overall_level"] = round(sum(float(item.get("level", 3.0)) for item in profile["topics"]) / len(profile["topics"]), 2)
    else:
        profile["overall_level"] = 3.0
    return profile


def assess_solution(exercise: dict[str, Any], solution: str) -> dict[str, Any]:
    prompt = assessment_prompt(exercise, solution)
    try:
        event = call_gemini_json(
            prompt,
            "You are a careful Linear Algebra 1 assessor. Return only one valid JSON object.",
        )
    except Exception as exc:
        event = local_assessment_event(exercise, solution, str(exc))
    return validate_event(event, exercise, solution)


def local_assessment_event(exercise: dict[str, Any], solution: str, reason: str) -> dict[str, Any]:
    expected = str(exercise.get("expected_answer", "")).lower()
    normalized = solution.lower().replace(" ", "")
    hints = [part.strip().replace(" ", "") for part in re.split(r"[,;]", expected) if part.strip()]
    matched = sum(1 for hint in hints if hint and hint in normalized)
    score = 0.75 if hints and matched >= max(1, len(hints) // 2) else 0.35
    if any(word in normalized for word in ["because", "therefore", "so", "rank", "det", "basis"]):
        score = min(1.0, score + 0.1)
    is_correct = score >= 0.75
    topic = str(exercise.get("topic", "Determinants and their algebraic and geometric meanings"))
    prior = prior_topic_level(topic)
    delta = 0.25 if is_correct else 0.05
    timestamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    return {
        "schema_version": "1.0",
        "event_type": "exercise_attempt_graded",
        "student_id": student_id_from_log(),
        "exercise_id": exercise["id"],
        "timestamp": timestamp,
        "exercise": {
            "difficulty": int(exercise.get("difficulty", 5)),
            "topics": [slugify_topic(topic)],
            "prompt": exercise["prompt"],
        },
        "grading_result": {
            "score": round(score, 2),
            "max_score": 1.0,
            "is_correct": is_correct,
            "weaknesses": [] if is_correct else ["check the final result and justify each step"],
            "topic_level_updates": [
                {
                    "topic": topic,
                    "previous_level": prior,
                    "new_level": round(min(10.0, prior + delta), 2),
                    "confidence": 0.42,
                }
            ],
            "rubric": [
                {
                    "criterion": "local fallback assessment",
                    "score": round(score, 2),
                    "max_score": 1.0,
                    "feedback": "The live model assessor was unavailable, so this conservative local check compared the answer with the expected result.",
                }
            ],
            "feedback_to_student": (
                "This was graded by the local fallback because the Gemini API was unavailable. "
                + ("Your answer appears to match the expected result." if is_correct else "Recheck the computation and include the final result clearly.")
            ),
            "assessor_warning": reason,
        },
    }


def prior_topic_level(topic: str) -> float:
    for event in reversed(load_events(LOG_PATH)):
        profile = event.get("student_profile_after_attempt")
        if not isinstance(profile, dict):
            continue
        for item in profile.get("topics", []) or []:
            if isinstance(item, dict) and item.get("topic") == topic:
                return float(item.get("level", 3.0))
    return 3.0


def response_payload(evaluation: dict[str, Any] | None = None) -> dict[str, Any]:
    current = current_or_new_exercise()
    payload: dict[str, Any] = {
        "student_id": student_id_from_log(),
        "log_file": str(LOG_PATH),
        "current_exercise": {
            "id": current["id"],
            "question_id": current.get("question_id"),
            "topic": current.get("topic"),
            "difficulty": current.get("difficulty"),
            "prompt": current.get("prompt"),
        },
    }
    if evaluation is not None:
        payload["evaluation"] = evaluation
    return payload


class AppHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        print("%s - %s" % (self.address_string(), format % args))

    def do_GET(self) -> None:
        if self.path == "/" or self.path.startswith("/?"):
            self.send_bytes(HTML.encode("utf-8"), HTTPStatus.OK, {"Content-Type": "text/html; charset=utf-8"})
            return
        if self.path == "/api/state":
            self.handle_json(lambda: response_payload())
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if self.path == "/api/reset":
            self.handle_json(self.handle_reset)
            return
        if self.path == "/api/submit":
            self.handle_json(self.handle_submit)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def handle_reset(self) -> dict[str, Any]:
        with STATE_LOCK:
            reset_runtime()
            return response_payload()

    def handle_submit(self) -> dict[str, Any]:
        body = self.read_json_body()
        solution = str(body.get("solution", "")).strip()
        if not solution:
            raise ValueError("Write a solution before submitting.")
        with STATE_LOCK:
            exercise = current_or_new_exercise()
            evaluation = assess_solution(exercise, solution)
            append_event(evaluation)
            state = load_json(STATE_PATH, {})
            state["current_exercise"] = generate_exercise()
            save_json(STATE_PATH, state)
            return response_payload(evaluation)

    def read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw or "{}")

    def handle_json(self, callback: Any) -> None:
        try:
            data = callback()
            self.send_json(data, HTTPStatus.OK)
        except Exception as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def send_json(self, data: dict[str, Any], status: HTTPStatus) -> None:
        self.send_bytes(json.dumps(data).encode("utf-8"), status, JSON_HEADERS)

    def send_bytes(self, data: bytes, status: HTTPStatus, headers: dict[str, str]) -> None:
        self.send_response(status)
        for key, value in headers.items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local Linear Algebra practice web app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_runtime_log()
    server = ThreadingHTTPServer((args.host, args.port), AppHandler)
    print(f"Serving Linear Algebra Practice at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
