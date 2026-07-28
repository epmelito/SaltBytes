from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIRECTORY = (
    REPOSITORY_ROOT
    / "skills"
    / "forecast-failure-review"
)


def test_skill_instructions_exist() -> None:
    skill_file = SKILL_DIRECTORY / "SKILL.md"

    assert skill_file.is_file()


def test_skill_instructions_define_required_metadata() -> None:
    skill_content = (
        SKILL_DIRECTORY
        / "SKILL.md"
    ).read_text(encoding="utf-8")

    assert "name: forecast-failure-review" in skill_content
    assert "description:" in skill_content
    assert "## Workflow" in skill_content
    assert "## Failure categories" in skill_content
    assert "## Output format" in skill_content
    assert "## Rules" in skill_content


def test_skill_examples_exist() -> None:
    examples_directory = SKILL_DIRECTORY / "examples"

    assert (
        examples_directory
        / "failed-quality-check.md"
    ).is_file()
    assert (
        examples_directory
        / "unknown-failure.md"
    ).is_file()


def test_unknown_failure_example_avoids_unsupported_conclusion() -> None:
    example_content = (
        SKILL_DIRECTORY
        / "examples"
        / "unknown-failure.md"
    ).read_text(encoding="utf-8")

    assert "failure category is `unknown`" in example_content
    assert "## Missing evidence" in example_content