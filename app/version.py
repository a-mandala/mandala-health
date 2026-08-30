"""App version: git hash injected at build time (Docker ARG -> APP_VERSION env).

Falls back to `git describe` when running from a repo, then to "dev".
"""

import os
import subprocess
from pathlib import Path


def _git_describe() -> str | None:
    try:
        out = subprocess.run(
            ["git", "describe", "--tags", "--always", "--dirty"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0 or not out.stdout.strip():
        return None
    return out.stdout.strip()


def version_info() -> dict:
    env_version = os.environ.get("APP_VERSION")
    env_hash = os.environ.get("APP_GIT_HASH")
    git = _git_describe()
    version = env_version or git or "dev"
    git_hash = env_hash or (git[-7:] if git else "dev")
    return {
        "version": version,
        "git_hash": git_hash,
        "build_date": os.environ.get("APP_BUILD_DATE") or "dev",
    }
