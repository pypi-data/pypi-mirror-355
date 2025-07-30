#!/usr/bin/env python3

from pathlib import Path
import subprocess


def _git(path, *args):
    path = Path(path).expanduser().resolve()
    path = path.is_dir() and path or path.parent
    cmd = ("git", "-C", path) + args
    return subprocess.run(cmd, capture_output=True)


def find_repo_path(path):
    path = Path(path).resolve()
    if path.is_dir():
        git_subdir = path / ".git"
        if git_subdir.exists() and git_subdir.is_dir():
            # Found the applicable git repo root.
            return path
    if len(path.parents) > 0:
        return find_repo_path(path.parent)


def find_gitignore_path(path):
    if repo_path := find_repo_path(path):
        return repo_path / ".gitignore"


def get_gitignore_rules(path):
    gitignore_path = find_gitignore_path(path)
    if gitignore_path.exists():
        with gitignore_path.open("r") as f:
            return list(filter(bool, f.read().split("\n")))
    return []


def add_gitignore_rule(path, rule):
    rules = get_gitignore_rules(path) + [
        rule,
    ]
    with find_gitignore_path(path).open("w") as f:
        f.write("\n".join(rules))


def is_file_matched_by_gitignore_rule(path):
    path = Path(path).resolve()
    if repo_root := find_repo_path(path):
        for rule in get_gitignore_rules(path):
            if path.relative_to(repo_root).match(rule):
                return True
        return False
    return None
