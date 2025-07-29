import os

from typing import Dict, List, Optional

from clipped.utils.cmd import run_command


def git_init(repo_path: str):
    run_command(
        cmd="git init {}".format(repo_path), data=None, location=repo_path, chw=True
    )


def update_submodules(repo_path: str):
    run_command(
        cmd="git submodule update --init --recursive --rebase --force",
        data=None,
        location=repo_path,
        chw=True,
    )


def git_fetch(repo_path: str, revision: str, flags: Optional[List[str]], env=None):
    flags = flags or []
    fetch_cmd = "git fetch {} origin".format(" ".join(flags))
    if revision:
        fetch_cmd = "{} {}".format(fetch_cmd, revision)
    fetch_cmd = "{} --update-head-ok --force".format(fetch_cmd)
    run_command(cmd=fetch_cmd, data=None, location=repo_path, chw=True, env=env)
    run_command(cmd="git checkout FETCH_HEAD", data=None, location=repo_path, chw=True)


def checkout_revision(repo_path: str, revision: str):
    """Checkout to a specific revision.

    If commit is None then checkout to master.
    """
    revision = revision or "master"
    run_command(
        cmd="git checkout {}".format(revision), data=None, location=repo_path, chw=True
    )


def add_remote(repo_path: str, url: str):
    run_command(
        cmd="git remote add origin {}".format(url),
        data=None,
        location=repo_path,
        chw=True,
    )


def set_remote(repo_path: str, url: str):
    run_command(
        cmd="git remote set-url origin {}".format(url),
        data=None,
        location=repo_path,
        chw=True,
    )


def get_status(repo_path: str):
    return run_command(cmd="git status -s", data=None, location=repo_path, chw=True)


def get_committed_files(repo_path: str, commit_hash: str):
    files_committed = run_command(
        cmd="git diff-tree --no-commit-id --name-only -r {}".format(commit_hash),
        data=None,
        location=repo_path,
        chw=True,
    ).split("\n")
    return [f for f in files_committed if f]


def git_undo(repo_path: str):
    run_command(cmd="git reset --hard", data=None, location=repo_path, chw=True)
    run_command(cmd="git clean -fd", data=None, location=repo_path, chw=True)


def git_commit(
    repo_path: str = ".",
    user_email: Optional[str] = None,
    user_name: Optional[str] = None,
    message: Optional[str] = None,
):
    message = message or "updated"
    run_command(cmd="git add -A", data=None, location=repo_path, chw=True)
    git_auth = "-c user.email=<{}> -c user.name={}".format(user_email, user_name)
    run_command(
        cmd='git {} commit -m "{}"'.format(git_auth, message),
        data=None,
        location=repo_path,
        chw=True,
    )


def is_git_initialized(path: str = ".") -> bool:
    return bool(
        run_command(
            cmd="git rev-parse --is-inside-work-tree",
            data=None,
            location=path,
            chw=True,
        ).split("\n")[0]
    )


def get_commit(path: str = ".") -> str:
    return run_command(
        cmd="git --no-pager log --pretty=oneline -1", data=None, location=path, chw=True
    ).split(" ")[0]


def get_head(path: str = ".") -> str:
    return run_command(
        cmd="git rev-parse HEAD", data=None, location=path, chw=True
    ).split("\n")[0]


def get_remote(repo_path: str = "."):
    current_remote = run_command(
        cmd="git config --get remote.origin.url",
        data=None,
        location=repo_path,
        chw=True,
    )
    return current_remote.strip("\n")


def get_repo_name(path: str = ".") -> str:
    repo = run_command(
        cmd="git rev-parse --show-toplevel", data=None, location=path, chw=True
    ).split("\n")[0]

    return os.path.basename(repo)


def get_branch_name(path: str = ".") -> str:
    return run_command(
        cmd="git rev-parse --abbrev-ref HEAD", data=None, location=path, chw=True
    ).split("\n")[0]


def is_dirty(path: str = ".") -> bool:
    return bool(run_command(cmd="git diff --stat", data=None, location=path, chw=True))


def get_code_reference(path: str = ".", url: Optional[str] = None) -> Dict:
    if not is_git_initialized(path):
        return {}

    url = url or get_remote(path)
    if "git@" in url:
        url = url.split("git@")[1]
        url = url.split(".git")[0]
        url = url.replace(":", "/")
        url = "https://" + url
    return {"commit": get_commit(path), "branch": get_branch_name(path), "url": url}


def get_code_reference_all(path: str = ".") -> Dict:
    if not is_git_initialized(path):
        return {}

    return {
        "commit": get_commit(path),
        "head": get_head(path),
        "branch": get_branch_name(path),
        "url": get_remote(path),
        "is_dirty": is_dirty(path),
    }
