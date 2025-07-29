import subprocess
from pathlib import Path


def git_root():
    """Return the root directory of the git repository."""
    output = subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).strip()
    return Path(output.decode("utf-8"))


def git_ls_files(path):
    """Yield files in the git repository one at a time."""
    process = subprocess.Popen(
        [
            "git",
            "ls-files",
            "--cached",
            "--deleted",
            "--others",
            "--exclude-standard",
        ],
        cwd=path,
        stdout=subprocess.PIPE,
        text=True,
    )

    for line in process.stdout:
        yield line.strip()

    process.stdout.close()
    process.wait()


def git_ls_changes(path):
    process = subprocess.Popen(
        [
            "git",
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ],
        cwd=path,
        stdout=subprocess.PIPE,
        text=True,
    )

    for line in process.stdout:
        yield line.strip().split(" ", 1)[1]

    process.stdout.close()
    process.wait()


def git_diff_stream(path, *diff_args):
    process = subprocess.Popen(
        ["git", "diff", "--no-ext-diff"] + list(diff_args),
        cwd=path,
        stdout=subprocess.PIPE,
        text=True,
    )

    yield from process.stdout

    process.stdout.close()
    process.wait()
