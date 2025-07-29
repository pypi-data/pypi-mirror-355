import nox

VERSIONS = ["3.9", "3.10", "3.11", "3.12", "3.13"]


@nox.session(venv_backend="uv", tags=["lint"])
def flake8(session):
    """Run flake8 linting"""
    session.install("flake8")

    session.run(
        "flake8",
        ".",
        "--count",
        "--select=E9,F63,F7,F82",
        "--show-source",
        "--statistics",
        "--exclude=.venv,.nox",
    )

    session.run(
        "flake8",
        ".",
        "--count",
        "--exit-zero",
        "--max-complexity=10",
        "--max-line-length=127",
        "--statistics",
        "--exclude=.venv,.nox",
    )


@nox.session(venv_backend="uv", tags=["lint"])
def isort(session):
    """Check import sorting with isort"""
    session.install("isort")
    session.run(
        "isort",
        ".",
        "--check-only",
        "--diff",
        "--skip",
        ".venv",
        "--skip",
        ".nox",
        "--line-length",
        "120",
    )


@nox.session(venv_backend="uv", tags=["lint"])
def black(session):
    """Check formatting with black"""
    session.install("black")
    session.run(
        "black",
        ".",
        "--check",
        "--diff",
        "--extend-exclude=.venv|.nox",
        "-l",
        "120",
    )


@nox.session(python=VERSIONS, venv_backend="uv")
def test_all_tests(session):
    session.install("-e", ".")
    session.install("pytest")
    session.run("pytest")
