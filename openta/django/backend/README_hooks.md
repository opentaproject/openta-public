# Git Hooks: Maintain backend/version.txt

This repository uses Git hooks to keep `backend/version.txt` in sync with the
current repository state.

Important limitation
- It is impossible to embed the hash of a commit inside that very commit, due to
  the hash depending on the file contents. Therefore:
  - Pre-commit cannot produce a `version.txt` that contains the new commit’s
    own hash.
  - We instead refresh `version.txt` after the commit, so your working tree
    reflects the just-created commit hash, but the file itself is not committed.

What the hooks do
- pre-commit: runs the Python generator (Git tag/hash/date) and updates
  `backend/version.txt` if needed. It does NOT stage/commit the file.
- post-commit: runs after a successful commit and regenerates
  `backend/version.txt` so it matches `HEAD`.

Enable the hooks (per clone)
- From the repository root, run:

  `git config core.hooksPath .githooks`

- After this, `git commit` will automatically run both hooks.

Hook details
- Paths: `.githooks/pre-commit` and `.githooks/post-commit` (repo root).
- Interpreter: prefers `python3`, falls back to `python`.
- Auto-detection: finds `**/backend/version.py` tracked in the repo.
- Safety: hooks are no-ops if the generator fails; they do not block commits.

Production/CI note
- In production images where `.git` is not present, the code falls back to
  reading `backend/version.txt` or the `OPENTA_VERSION` environment variable.
  For reproducible builds, prefer setting `OPENTA_VERSION` during CI/CD rather
  than committing `version.txt`.

Common tips
- Skip once: `git commit --no-verify` (not recommended in general).
- Disable globally for this clone: `git config --unset core.hooksPath`.
- Troubleshooting: ensure `python3` or `python` is available; verify the hook files exist under `.githooks/` in the repo root.
