#!/usr/bin/env python3
"""Prepare static site for deployment to GitHub pages."""

import shutil
from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).parents[2]
SITE_ROOT = REPO_ROOT / "_site"


def main():
    """Main function to build the static site."""
    if not (REPO_ROOT / ".git").is_dir():
        raise AssertionError("Repo root is not a git repository")

    print("Building static site at ", SITE_ROOT.absolute())

    if SITE_ROOT.exists():
        print("Removing existing static site directory")
        shutil.rmtree(SITE_ROOT)

    SITE_ROOT.mkdir(parents=True)

    copy_worktree(SITE_ROOT / "tree")

    print("Done.")


def copy_worktree(dest: Path):
    """Copy the worktree to the static site directory."""
    print("Copying worktree to ", dest.absolute())
    git_archive_unpack(dest)


def git_archive_unpack(output_dir: Path):
    """Create a git archive and unpack it to the specified directory."""
    output_dir = output_dir.resolve()
    if not output_dir.exists():
        output_dir.mkdir(parents=True)

    # Create the git archive and unpack it
    try:
        ga = subprocess.Popen(
            ["git", "archive", "--format=tar", "HEAD"],
            stdout=subprocess.PIPE,
        )
        subprocess.check_output(
            ["tar", "-x", "-C", str(output_dir)],
            stdin=ga.stdout,
        )
        print(f"Repository contents unpacked to: {output_dir}")
    except subprocess.CalledProcessError as e:
        print(f"Error during git archive or unpacking: {e}")
        raise


if __name__ == "__main__":
    main()
