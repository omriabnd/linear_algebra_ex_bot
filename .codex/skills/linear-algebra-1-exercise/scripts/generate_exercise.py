#!/usr/bin/env python3
"""Generate a Linear Algebra 1 exercise for a difficulty level from 1 to 10."""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Exercise:
    difficulty: int
    topic: str
    statement: str
    techniques: str
    solution: str


EXERCISES: dict[int, list[Exercise]] = {
    1: [
        Exercise(
            1,
            "Vector arithmetic in R^2",
            "Let u = (2, -1) and v = (-3, 4). Compute 3u - 2v.",
            "Scalar multiplication and vector addition.",
            "3u - 2v = (6, -3) - (-6, 8) = (12, -11).",
        ),
        Exercise(
            1,
            "Matrix-vector multiplication",
            "Compute A x for A = [[1, 2], [0, -3]] and x = (4, -1).",
            "Basic matrix-vector multiplication.",
            "A x = (1*4 + 2*(-1), 0*4 + (-3)*(-1)) = (2, 3).",
        ),
    ],
    2: [
        Exercise(
            2,
            "Solving a 2x2 linear system",
            "Solve the system x + 2y = 5, 3x - y = 4.",
            "Elimination or substitution.",
            "From x = 5 - 2y. Substitute: 15 - 6y - y = 4, so y = 11/7 and x = 13/7.",
        ),
        Exercise(
            2,
            "Linear combinations",
            "Decide whether b = (7, 1) is a linear combination of v1 = (1, 2) and v2 = (3, -1).",
            "Set up and solve a 2x2 system for coefficients.",
            "Solve c1 + 3c2 = 7 and 2c1 - c2 = 1. This gives c2 = 13/7 and c1 = 10/7, so yes.",
        ),
    ],
    3: [
        Exercise(
            3,
            "Span in R^3",
            "Determine whether b = (1, 4, 2) lies in span{(1, 0, 2), (0, 1, -1)}.",
            "Translate span membership into a linear system.",
            "Need a(1,0,2)+b(0,1,-1)=(1,4,2). Then a=1, b=4, but 2a-b=-2, not 2. No.",
        ),
        Exercise(
            3,
            "Matrix multiplication",
            "Let A = [[1, 0, 2], [-1, 3, 1]] and B = [[2, 1], [0, -2], [4, 3]]. Compute AB.",
            "Row-column products and matrix dimensions.",
            "AB = [[10, 7], [2, -4]].",
        ),
    ],
    4: [
        Exercise(
            4,
            "Linear independence",
            "Determine whether the vectors (1, 2, 0), (0, 1, 1), and (2, 5, 1) are linearly independent.",
            "Solve a homogeneous system or compare one vector to a combination of the others.",
            "The third vector equals 2(1,2,0) + (0,1,1), so the set is dependent.",
        ),
        Exercise(
            4,
            "Inverse matrix",
            "Find A^{-1}, if it exists, for A = [[2, 1], [5, 3]].",
            "Use the 2x2 inverse formula and determinant.",
            "det(A)=1, so A^{-1} = [[3, -1], [-5, 2]].",
        ),
    ],
    5: [
        Exercise(
            5,
            "Basis and dimension",
            "Let W = {(x, y, z) in R^3 : x - 2y + z = 0}. Find a basis for W and compute dim(W).",
            "Parametrize a subspace and extract basis vectors.",
            "x=2y-z, so (x,y,z)=y(2,1,0)+z(-1,0,1). A basis is {(2,1,0),(-1,0,1)} and dim(W)=2.",
        ),
        Exercise(
            5,
            "Rank and null space",
            "Find a basis for the null space of A = [[1, 2, -1], [2, 4, -2], [0, 1, 3]].",
            "Row reduction and solving a homogeneous system.",
            "Equations reduce to x + 2y - z = 0 and y + 3z = 0. Let z=t, then y=-3t and x=7t. Basis: {(7,-3,1)}.",
        ),
    ],
    6: [
        Exercise(
            6,
            "Linear transformations",
            "Let T: R^3 -> R^2 be defined by T(x, y, z) = (x + 2y - z, 3x + y). Find the standard matrix of T and determine whether T is onto.",
            "Build a standard matrix and use rank.",
            "The matrix is [[1,2,-1],[3,1,0]]. Its two rows are independent, so rank is 2 and T is onto R^2.",
        ),
        Exercise(
            6,
            "Coordinates in a basis",
            "Let B = {(1, 1), (2, -1)}. Find the coordinate vector [v]_B for v = (7, 1).",
            "Solve for coefficients in a nonstandard basis.",
            "Solve c1(1,1)+c2(2,-1)=(7,1). Then c1+2c2=7 and c1-c2=1, so c2=2 and c1=3. [v]_B=(3,2).",
        ),
    ],
    7: [
        Exercise(
            7,
            "Eigenvalues and eigenvectors",
            "Find the eigenvalues and eigenspaces of A = [[4, 1], [2, 3]].",
            "Characteristic polynomial and null spaces of A - lambda I.",
            "The characteristic polynomial is lambda^2 - 7lambda + 10, so lambda=5,2. E_5=span{(1,1)}, E_2=span{(1,-2)}.",
        ),
        Exercise(
            7,
            "Diagonalization",
            "Determine whether A = [[1, 1, 0], [0, 1, 0], [0, 0, 2]] is diagonalizable over R.",
            "Compare algebraic and geometric multiplicities.",
            "For lambda=1, A-I has nullity 1 while algebraic multiplicity is 2. Therefore A is not diagonalizable.",
        ),
    ],
    8: [
        Exercise(
            8,
            "Change of basis",
            "Let B = {(1, 0), (1, 1)} and C = {(2, 1), (1, -1)} be bases of R^2. Find the change-of-basis matrix that sends [v]_B to [v]_C.",
            "Use P_C^{-1} P_B.",
            "P_B=[[1,1],[0,1]], P_C=[[2,1],[1,-1]]. P_C^{-1}P_B = [[1/3, 2/3], [1/3, -1/3]].",
        ),
        Exercise(
            8,
            "Rank-nullity and transformations",
            "Let T: P_2 -> P_2 be T(p) = p' + p(0). Find ker(T), im(T), and decide whether T is invertible.",
            "Represent polynomials by coefficients and apply rank-nullity.",
            "For p=a+bt+ct^2, T(p)=a+b+2ct. Kernel needs a+b=0 and c=0, so span{1-t}. Image is span{1,t}. Not invertible.",
        ),
    ],
    9: [
        Exercise(
            9,
            "Parameter-dependent systems",
            "For which real values of a does the system x + y + z = 1, x + ay + z = 2, x + y + az = 3 have no solution, one solution, or infinitely many solutions?",
            "Row reduction with parameters and consistency cases.",
            "Subtract the first equation from the second and third: (a-1)y=1 and (a-1)z=2. If a!=1, unique solution. If a=1, inconsistent, so no solution. No value gives infinitely many solutions.",
        ),
        Exercise(
            9,
            "Proof and computation with subspaces",
            "Let U and W be subspaces of a finite-dimensional vector space V. Prove that dim(U + W) = dim(U) + dim(W) - dim(U intersection W), then verify it for U = span{(1,0,1),(0,1,1)} and W = span{(1,1,2),(1,-1,0)} in R^3.",
            "Basis extension, dimension formula, and concrete span computation.",
            "Proof: extend a basis of U intersection W to bases of U and W, then show the combined extended list is a basis of U+W. Here U=W=span{(1,0,1),(0,1,1)}, so dimensions are 2,2,2 and dim(U+W)=2.",
        ),
    ],
    10: [
        Exercise(
            10,
            "Synthesis: diagonalization and recurrence",
            "Let A = [[2, 1, 0], [0, 2, 0], [0, 0, 3]]. Decide whether A is diagonalizable. Then compute A^n for all n >= 1 or explain why diagonalization alone is insufficient.",
            "Jordan-type reasoning within a Linear Algebra 1 vocabulary, powers of block matrices, eigenstructure.",
            "A is not diagonalizable because lambda=2 has algebraic multiplicity 2 but eigenspace dimension 1. The 2x2 block satisfies [[2,1],[0,2]]^n = [[2^n, n*2^(n-1)],[0,2^n]], so A^n has that block and 3^n in the last diagonal entry.",
        ),
        Exercise(
            10,
            "Synthesis: linear maps, bases, and constraints",
            "Let T: R^3 -> R^3 be linear with T(1,0,1)=(2,1,0), T(0,1,1)=(1,0,1), and T(1,1,2)=(3,1,1). Determine whether T is uniquely defined. If not, describe all such transformations and compute their possible ranks.",
            "Detect dependent input data, consistency of linear-map definitions, degrees of freedom, rank analysis.",
            "The third input is the sum of the first two, and its image is also the sum of the first two images, so the data are consistent but span only a 2D subspace. Choose T on one complementary vector freely. Possible ranks are 2 or 3, depending on whether the free image lies in the span of the two specified images.",
        ),
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("difficulty", type=int, help="difficulty level from 1 to 10")
    parser.add_argument("--seed", type=int, help="optional seed for repeatable selection")
    parser.add_argument("--include-solution", action="store_true", help="include the solution")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    return parser.parse_args()


def choose_exercise(difficulty: int, seed: int | None) -> Exercise:
    if difficulty < 1 or difficulty > 10:
        raise ValueError("difficulty must be between 1 and 10")
    rng = random.Random(seed)
    return rng.choice(EXERCISES[difficulty])


def as_markdown(exercise: Exercise, include_solution: bool) -> str:
    parts = [
        f"Difficulty: {exercise.difficulty}/10",
        f"Topic: {exercise.topic}",
        "",
        "Exercise:",
        exercise.statement,
        "",
        f"Expected techniques: {exercise.techniques}",
    ]
    if include_solution:
        parts.extend(["", "Solution:", exercise.solution])
    return "\n".join(parts)


def main() -> int:
    args = parse_args()
    try:
        exercise = choose_exercise(args.difficulty, args.seed)
    except ValueError as exc:
        raise SystemExit(str(exc))

    if args.json:
        payload = {
            "difficulty": exercise.difficulty,
            "topic": exercise.topic,
            "statement": exercise.statement,
            "techniques": exercise.techniques,
        }
        if args.include_solution:
            payload["solution"] = exercise.solution
        print(json.dumps(payload, indent=2))
    else:
        print(as_markdown(exercise, args.include_solution))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
