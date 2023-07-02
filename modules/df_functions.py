import os
from git import Repo
from git.objects.commit import Commit
from git.exc import GitCommandError, NoSuchPathError, InvalidGitRepositoryError
import pandas as pd
from typing import Literal


def get_repo(
    path: str,
    branch: str = None,
    start: int = None,
    end: int = None,
    penalties: list[tuple[str, float]] | tuple[str, float] = None,
    group: Literal["day", "month", "year"] = "day",
) -> pd.DataFrame:
    """
    Get a human readable dataframe about a git repo.
    """
    try:
        repo, repo_name = get_repo_from_source(path)
    except (InvalidGitRepositoryError, NoSuchPathError, GitCommandError):
        print("Path not recognized as a git repo.")
        return

    if branch:
        if branch == "--all":
            commits_full = list(repo.iter_commits("--all"))
        else:
            commits_full = list(repo.iter_commits(branch))
    else:
        commits_full = list(repo.iter_commits())

    commits_full.reverse()
    commits_full = commits_full[start:end]
    df_commits = get_df(commits_full)

    if penalties:
        df_commits = penalize(df_commits, penalties=penalties)
    df = group_by_time(df_commits, group=group)

    df.title = repo_name
    return df


def get_repo_from_source(path: str):
    """Get repo from the source using gitpython."""
    if not os.path.isdir("cloned_repos"):
        os.mkdir("cloned_repos")
    if path.startswith("http"):
        repo_name = os.path.splitext(os.path.basename(path))[0]
        save_path = os.path.join("cloned_repos", repo_name)
        if os.path.isdir(save_path):
            repo = Repo(save_path)
        else:
            repo = Repo.clone_from(path, save_path, no_checkout=True)
    else:
        repo = Repo(path)
        repo_path = repo.git.rev_parse("--show-toplevel")
        repo_name = os.path.basename(repo_path)

    return repo, repo_name


def get_df(commits_full: list[Commit]):
    """Take a full list of commits from gitpython and convert to human readable dataframe."""
    commit_generator = (
        {
            "id": commit.hexsha,
            "date": commit.authored_datetime.date(),
            "message": commit.message.replace("\n", ""),
            "insertions": commit.stats.total["insertions"],
            "deletions": commit.stats.total["deletions"],
            "total_edits": commit.stats.total["lines"],
        }
        for commit in commits_full
    )
    df_commits = pd.DataFrame(commit_generator)
    net_code_added = df_commits["insertions"] - df_commits["deletions"]
    df_commits["total_code"] = net_code_added.cumsum()
    return df_commits


def penalize(
    df_commits: pd.DataFrame, penalties: list[tuple[str, float]] | tuple[str, float]
) -> pd.DataFrame:
    """
    Give a penalty to commits with certain messages in them.

    penalty
      list of tuples, each tuple is (penalty_string, multiplication_factor)
    """
    if isinstance(penalties, tuple):
        penalties = [penalties]
    for penalty in penalties:
        penalty_string, multiplication_factor = penalty
        mask = df_commits["message"].str.contains(penalty_string, case=False)
        for key in ["insertions", "deletions", "total_edits"]:
            df_commits.loc[mask, key] = (
                df_commits.loc[mask, key] * multiplication_factor
            )
    return df_commits


def group_by_time(
    df_commits: pd.DataFrame, group: Literal["day", "month", "year"] = "day"
) -> pd.DataFrame:
    """At the moment only supports grouping by day but can be extended."""

    if group.lower() == "month":
        df_commits["date"] = df_commits["date"].apply(lambda x: x.strftime("%m/%Y"))
        new_key = "month/year"
    elif group.lower() == "year":
        df_commits["date"] = df_commits["date"].apply(lambda x: x.strftime("%Y"))
        new_key = "year"
    elif group.lower() == "day":
        new_key = "date"
    else:
        print("group should be 'day', 'month' or 'year'")
        return

    df = (
        df_commits.groupby("date")
        .agg(
            {
                "insertions": "sum",
                "deletions": "sum",
                "total_edits": "sum",
                "total_code": "max",
                "date": "size",
            }
        )
        .rename(columns={"date": "commits"})
        .reset_index()
    )
    return df.rename(columns={"date": new_key})
