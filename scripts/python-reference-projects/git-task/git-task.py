#!/usr/bin/env python3
"""git-task: create a local Git branch for a Jira ticket.

Written: 2026-06-13

What this script does:
- Runs from inside an existing Git repository.
- Reads the repository's `origin` remote and base branch.
- Optionally reads a Jira ticket summary and issue type.
- Builds a branch name like `feature/DEVOPS-123-add-terraform-validation`.
- Creates and checks out a local branch from `origin/<base-branch>`.
- Optionally moves the Jira ticket to the configured status.
- Optionally adds a Jira comment with the created branch name.
- Prints the push command, but does not push automatically.

Disclaimer:
This is a local workflow helper, not a production-grade release tool. Use it at
your own risk. Review the output before using it on important repositories or
real Jira tickets. The script can create local branches and can modify Jira
tickets when not run with `--dry-run`, `--no-jira`, `--no-transition`, or
`--no-comment`. The author and repository maintainers are not responsible for
incorrect branches, Jira transitions, comments, workflow disruption, data loss,
or other issues caused by using or modifying this script.

Example commands:
  git-task DEVOPS-123
  git-task DEVOPS-123 "add terraform validation"
  git-task --type docs DEVOPS-123
  git-task --dry-run DEVOPS-123
  git-task --no-jira DEVOPS-123 "add terraform validation"
  git-task --no-transition --no-comment DEVOPS-123
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from git import GitCommandError, InvalidGitRepositoryError, NoSuchPathError, Repo
except ImportError:
    print(
        "Error: missing Python package 'GitPython'. Install dependencies with: "
        "python3 -m pip install GitPython jira",
        file=sys.stderr,
    )
    sys.exit(1)


DEFAULT_TRANSITION = "In Progress"
DEFAULT_TYPE = "feature"

# Jira issue types are normalized to lowercase before lookup.
ISSUE_TYPE_TO_BRANCH_TYPE = {
    "bug": "bugfix",
    "story": "feature",
    "task": "feature",
    "improvement": "feature",
    "incident": "hotfix",
    "documentation": "docs",
}


@dataclass(frozen=True)
class Config:
    base_branch: str | None
    transition: str
    add_comment: bool
    default_type: str


@dataclass(frozen=True)
class IssueInfo:
    summary: str
    issue_type: str
    issue: Any | None = None


def die(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def warn(message: str) -> None:
    print(f"Warning: {message}", file=sys.stderr)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower())
    return slug.strip("-")


def branch_type_for(issue_type: str, default_type: str) -> str:
    return ISSUE_TYPE_TO_BRANCH_TYPE.get(issue_type.lower(), default_type)


def parse_bool(value: str | None, default: bool = True) -> bool:
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False

    warn(f"Invalid boolean Git config value '{value}', using {default}.")
    return default


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="git-task",
        description="A Jira-aware Git workflow helper to start work on a ticket.",
    )
    parser.add_argument("--type", dest="type_override", help="Override branch type.")
    parser.add_argument("--no-jira", action="store_true", help="Skip all Jira API calls.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would happen without mutating Git or Jira.",
    )
    parser.add_argument("--open", action="store_true", help="Open the Jira issue after processing.")
    parser.add_argument(
        "--no-transition",
        action="store_true",
        help="Read Jira but do not move the ticket.",
    )
    parser.add_argument(
        "--no-comment",
        action="store_true",
        help="Read Jira but do not add a comment.",
    )
    parser.add_argument("ticket", help="Jira ticket key, for example DEVOPS-123.")
    parser.add_argument("manual_title", nargs="?", help="Manual title override.")
    return parser.parse_args()


def load_repo() -> Repo:
    try:
        return Repo(search_parent_directories=True)
    except (InvalidGitRepositoryError, NoSuchPathError):
        die("Not inside a Git repository.")


def origin_remote(repo: Repo):
    for remote in repo.remotes:
        if remote.name == "origin":
            return remote
    die("No 'origin' remote exists.")


def config_value(repo: Repo, key: str) -> str | None:
    """Read a Git config value using keys such as task.defaultType.

    GitPython expects section and option separately. Splitting once preserves
    quoted sections like task "cloud".jiraTransition.
    """
    with repo.config_reader() as reader:
        try:
            return reader.get_value(*key.split(".", 1))
        except Exception:
            return None


def load_config(repo: Repo, repo_name: str) -> Config:
    default_type = config_value(repo, "task.defaultType") or DEFAULT_TYPE
    transition = config_value(repo, f'task "{repo_name}".jiraTransition') or DEFAULT_TRANSITION
    base_branch = config_value(repo, f'task "{repo_name}".baseBranch')
    add_comment_raw = config_value(repo, f'task "{repo_name}".addComment')

    return Config(
        base_branch=base_branch,
        transition=transition,
        add_comment=parse_bool(add_comment_raw, default=True),
        default_type=default_type,
    )


def remote_branch_exists(repo: Repo, branch_name: str) -> bool:
    ref_name = f"origin/{branch_name}"
    return any(ref.name == ref_name for ref in repo.remotes.origin.refs)


def detect_base_branch(repo: Repo, config: Config, repo_name: str) -> str:
    if config.base_branch:
        return config.base_branch

    # Prefer the remote's advertised default branch, then fall back to common
    # branch names so new repositories work without per-repo configuration.
    origin_head = next((ref for ref in repo.remotes.origin.refs if ref.name == "origin/HEAD"), None)
    if origin_head is not None:
        remote_name = getattr(origin_head.reference, "remote_head", "")
        if remote_name:
            return remote_name

    if remote_branch_exists(repo, "main"):
        return "main"
    if remote_branch_exists(repo, "master"):
        return "master"

    die(f"Could not detect base branch. Set one using: git config task.{repo_name}.baseBranch <branch>")


def load_jira_client() -> Any:
    base_url = os.environ.get("JIRA_BASE_URL")
    email = os.environ.get("JIRA_EMAIL")
    token = os.environ.get("JIRA_API_TOKEN")

    missing = [
        name
        for name, value in {
            "JIRA_BASE_URL": base_url,
            "JIRA_EMAIL": email,
            "JIRA_API_TOKEN": token,
        }.items()
        if not value
    ]
    if missing:
        die(f"Jira environment variables are not set. Missing: {', '.join(missing)}.")

    # Import Jira lazily so --no-jira can still work when the Jira package is
    # not installed. GitPython is always required because the command is Git-first.
    try:
        from jira import JIRA, JIRAError
    except ImportError:
        die(
            "Missing Python package 'jira'. Install dependencies with: "
            "python3 -m pip install GitPython jira"
        )

    try:
        return JIRA(server=base_url, basic_auth=(email, token))
    except JIRAError as exc:
        die(f"Failed to create Jira client: {jira_error_message(exc)}")


def jira_error_message(exc: Exception) -> str:
    """Return a compact message for jira.JIRAError and ordinary exceptions."""
    status = getattr(exc, "status_code", None)
    text = getattr(exc, "text", None)
    if status and text:
        return f"HTTP {status}: {text}"
    if status:
        return f"HTTP {status}"
    return str(exc)


def load_issue(jira_client: Any, ticket: str) -> IssueInfo:
    try:
        issue = jira_client.issue(ticket)
    except Exception as exc:
        die(f"Failed to fetch Jira ticket {ticket}: {jira_error_message(exc)}")

    summary = getattr(issue.fields, "summary", None)
    issue_type_obj = getattr(issue.fields, "issuetype", None)
    issue_type = getattr(issue_type_obj, "name", None)

    if not summary or not issue_type:
        die("Could not read Jira summary or issue type.")

    return IssueInfo(summary=summary, issue_type=issue_type, issue=issue)


def local_branch_exists(repo: Repo, branch_name: str) -> bool:
    return any(head.name == branch_name for head in repo.heads)


def create_branch(repo: Repo, branch_name: str, base_branch: str) -> None:
    if local_branch_exists(repo, branch_name):
        die(f"Local branch '{branch_name}' already exists.")

    base_ref_name = f"origin/{base_branch}"
    base_ref = next((ref for ref in repo.remotes.origin.refs if ref.name == base_ref_name), None)
    if base_ref is None:
        die(f"Base branch '{base_ref_name}' was not found.")

    try:
        new_branch = repo.create_head(branch_name, base_ref)
        new_branch.checkout()
    except GitCommandError as exc:
        die(f"Failed to create branch {branch_name} from {base_ref_name}: {exc}")


def find_transition(jira_client: Any, issue: Any, transition_name: str) -> dict[str, Any] | None:
    transitions = jira_client.transitions(issue)
    transition_name_lower = transition_name.lower()
    # Jira transition names are user-facing labels, so match them
    # case-insensitively to avoid needless workflow friction.
    for transition in transitions:
        if transition.get("name", "").lower() == transition_name_lower:
            return transition
    return None


def print_jira_manual_steps(ticket: str, transition: str, branch_name: str, need_transition: bool, need_comment: bool) -> None:
    print("")
    print("Manual Jira follow-up needed:")
    if need_transition:
        print(f"- Move {ticket} to '{transition}' manually.")
    if need_comment:
        print(f"- Add this comment manually: Started work on branch {branch_name}")


def transition_issue(jira_client: Any, issue: Any, ticket: str, transition_name: str, branch_name: str) -> bool:
    try:
        transition = find_transition(jira_client, issue, transition_name)
        if transition is None:
            print(f"Error: Transition '{transition_name}' not found for current issue state.", file=sys.stderr)
            print_jira_manual_steps(ticket, transition_name, branch_name, need_transition=True, need_comment=False)
            return False

        jira_client.transition_issue(issue, transition["id"])
        print(f"Jira ticket moved to '{transition_name}'.")
        return True
    except Exception as exc:
        # At this point the local branch may already exist. Do not roll it back;
        # report exactly what the user still needs to do in Jira.
        print(f"Error: Failed to transition Jira ticket: {jira_error_message(exc)}", file=sys.stderr)
        print_jira_manual_steps(ticket, transition_name, branch_name, need_transition=True, need_comment=False)
        return False


def add_comment(jira_client: Any, issue: Any, ticket: str, transition_name: str, branch_name: str) -> bool:
    comment = f"Started work on branch {branch_name}"
    try:
        jira_client.add_comment(issue, comment)
        print("Comment added to Jira ticket.")
        return True
    except Exception as exc:
        # Commenting is useful but not worth discarding a successfully created
        # local branch. Tell the user the exact comment to add manually.
        print(f"Error: Failed to add Jira comment: {jira_error_message(exc)}", file=sys.stderr)
        print_jira_manual_steps(ticket, transition_name, branch_name, need_transition=False, need_comment=True)
        return False


def print_summary(
    repo_name: str,
    ticket: str,
    summary: str,
    issue_type: str,
    base_branch: str,
    branch_name: str,
    jira_url: str | None,
) -> None:
    print("")
    print(f"Repository:  {repo_name}")
    print(f"Ticket:      {ticket}")
    print(f"Summary:     {summary}")
    print(f"Issue type:  {issue_type}")
    print(f"Base branch: {base_branch}")
    print(f"New branch:  {branch_name}")
    if jira_url:
        print(f"Jira URL:    {jira_url}")
    print("")


def print_dry_run(
    branch_name: str,
    base_branch: str,
    transition: str,
    should_transition: bool,
    should_comment: bool,
) -> None:
    print(f"[Dry Run] Would create branch {branch_name} from origin/{base_branch}")
    if should_transition:
        print(f"[Dry Run] Would transition ticket to '{transition}'")
    if should_comment:
        print("[Dry Run] Would add comment to ticket")
    print("[Dry Run] Final push command would be:")
    print(f"git push -u origin {branch_name}")
    print("[Dry Run] Browser will not be opened in dry-run mode.")
    print("[Dry Run] Finished.")


def main() -> int:
    args = parse_args()

    if args.no_jira and not args.manual_title:
        die("Manual title is required when using --no-jira mode.")

    repo = load_repo()
    origin = origin_remote(repo)
    repo_root = Path(repo.working_tree_dir or os.getcwd())
    repo_name = repo_root.name
    config = load_config(repo, repo_name)

    # A fetch updates remote-tracking refs, so it is intentionally skipped in
    # dry-run mode even though normal mode fetches before branch detection.
    if not args.dry_run:
        print("Fetching latest remote refs...")
        try:
            origin.fetch(prune=True)
        except GitCommandError as exc:
            die(f"Failed to fetch latest remote refs: {exc}")

    base_branch = detect_base_branch(repo, config, repo_name)

    jira_client = None
    issue_info: IssueInfo
    jira_url = None

    if args.no_jira:
        # In no-Jira mode the user supplies the branch title because there is no
        # issue lookup to provide a summary.
        issue_info = IssueInfo(summary=args.manual_title, issue_type="N/A")
        branch_type = args.type_override or config.default_type
    else:
        jira_client = load_jira_client()
        print(f"Fetching Jira issue {args.ticket}...")
        issue_info = load_issue(jira_client, args.ticket)
        issue_info = IssueInfo(
            summary=args.manual_title or issue_info.summary,
            issue_type=issue_info.issue_type,
            issue=issue_info.issue,
        )
        branch_type = args.type_override or branch_type_for(issue_info.issue_type, config.default_type)
        jira_url = f"{os.environ['JIRA_BASE_URL'].rstrip('/')}/browse/{args.ticket}"

    slug = slugify(issue_info.summary)
    if not slug:
        die("Generated branch title slug is empty.")

    branch_name = f"{branch_type}/{args.ticket}-{slug}"
    should_transition = not args.no_jira and not args.no_transition
    should_comment = not args.no_jira and not args.no_comment and config.add_comment

    print_summary(
        repo_name=repo_name,
        ticket=args.ticket,
        summary=issue_info.summary,
        issue_type=issue_info.issue_type,
        base_branch=base_branch,
        branch_name=branch_name,
        jira_url=jira_url,
    )

    if args.dry_run:
        # Nothing below this point is allowed in dry-run mode: no branch create,
        # no checkout, no Jira mutation, and no browser open.
        print_dry_run(
            branch_name=branch_name,
            base_branch=base_branch,
            transition=config.transition,
            should_transition=should_transition,
            should_comment=should_comment,
        )
        return 0

    print("Creating branch...")
    create_branch(repo, branch_name, base_branch)
    print("Branch created successfully.")

    jira_problem = False
    if jira_client and issue_info.issue:
        # Jira updates happen after branch creation. If they fail, keep the
        # branch and return a non-zero status with manual follow-up instructions.
        if should_transition:
            jira_problem = not transition_issue(
                jira_client, issue_info.issue, args.ticket, config.transition, branch_name
            )

        if should_comment:
            jira_problem = not add_comment(
                jira_client, issue_info.issue, args.ticket, config.transition, branch_name
            ) or jira_problem

        if args.open:
            print("Opening Jira issue...")
            webbrowser.open(jira_url)

    print("")
    print("Next:")
    print(f"git push -u origin {branch_name}")

    if jira_problem:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
