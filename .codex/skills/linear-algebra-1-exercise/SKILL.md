---
name: linear-algebra-1-exercise
description: Generate a Linear Algebra 1 exercise from a requested difficulty level between 1 and 10. Use when the user asks for a linear algebra exercise, practice problem, homework-style question, quiz item, or exam-style problem calibrated by difficulty.
---

# Linear Algebra 1 Exercise

## Overview

Generate one Linear Algebra 1 exercise calibrated to a difficulty level from 1 to 10, where 1 is easy and 10 is difficult.

## Quick Start

Use `scripts/generate_exercise.py` when the user gives a numeric difficulty and wants an exercise:

```bash
python3 scripts/generate_exercise.py 6
```

Use `--seed` to make a repeatable variant:

```bash
python3 scripts/generate_exercise.py 6 --seed 42
```

Use `--include-solution` only when the user asks for a solution, answer key, or worked example.

## Difficulty Calibration

Treat the levels as a smooth progression:

- `1-2`: direct computation with small vectors or 2x2 matrices.
- `3-4`: systems, span, independence, matrix products, inverse checks.
- `5-6`: subspaces, bases, rank-nullity, coordinates, linear transformations.
- `7-8`: eigenvalues/eigenvectors, diagonalization, abstract proof plus computation.
- `9-10`: multi-concept synthesis, parameter cases, proofs, change of basis, diagonalization limits.

If the user gives a value outside `1-10`, ask for a valid difficulty or clamp only if the user explicitly permits approximation.

## Response Style

Return the exercise in clear mathematical notation. Include:

- Difficulty level.
- Topic.
- Exercise statement.
- Expected techniques or learning goal.

Do not include a solution unless requested. If a user asks for a different language, formatting, or course convention, adapt the generated exercise while preserving the requested difficulty.
