import subprocess
from pathlib import Path

from bobleesj.utils.io import config


def prompt_for_issue():
    title = input("Enter the title for the new issue: ")
    body = input("Enter the body for the new issue: ")
    return title, body


def find_git_repos(root_dir):
    return [p.parent for p in Path(root_dir).rglob(".git")]


def create_issue(repo_path, title, body):
    print(f"\nProcessing repository: {repo_path}")
    try:
        subprocess.run(
            ["gh", "issue", "create", "--title", title, "--body", body],
            cwd=repo_path,
            check=True,
        )
        print("✅ Issue created.")
    except subprocess.CalledProcessError:
        print("❌ Failed to create issue.")


def issues(args):
    root_dir = config.value("~/.bobrc", "dev_dir_path")
    if not root_dir or not Path(root_dir).is_dir():
        print(f"Error: '{root_dir}' is not a valid directory.")
        return
    title, body = prompt_for_issue()
    repos = find_git_repos(root_dir)
    if not repos:
        print("No Git repositories found.")
        return

    for repo in repos:
        create_issue(repo, title, body)
