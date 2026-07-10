import pathlib

MANAGED_FIELDS: tuple[str, ...] = ("user_feedback", "log")

# Static handoff files for the process-user-feedback-on-deck pipeline. One run at a
# time: extract.py overwrites EDIT_INPUT_PATH, edit.py overwrites
# EDIT_OUTPUT_PATH. apply.py reads EDIT_OUTPUT_PATH and prints its results to stdout
# for the orchestrator — no third file, nothing downstream reads it from disk.
#
# They live in the skill's own `.artifacts/` dir (resolved from this module's path so
# it works regardless of cwd), NOT under /tmp. Writes therefore stay inside the
# workspace and never trigger an out-of-tree write confirmation. `.artifacts/` is
# gitignored, so the files never show up in `git status`.
_ARTIFACTS_DIR = (
    pathlib.Path(__file__).resolve().parent.parent
    / "skills"
    / "process-user-feedback-on-deck"
    / ".artifacts"
)
EDIT_INPUT_PATH = _ARTIFACTS_DIR / "feedback-edit-input.json"
EDIT_OUTPUT_PATH = _ARTIFACTS_DIR / "feedback-edit-output.json"
