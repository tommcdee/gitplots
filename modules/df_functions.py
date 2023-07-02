import os
from git import Repo
from git.objects.commit import Commit
from git.exc import GitCommandError, NoSuchPathError, InvalidGitRepositoryError
import pandas as pd
from typing import Literal
from dateutil import parser
import datetime


def get_repo(
    path: str,
    branch: str = None,
    start: int | str | datetime.date = None,
    end: int | str | datetime.date = None,
    penalties: list[tuple[str, float]] | tuple[str, float] = None,
    group: Literal["day", "month", "year"] = "day",
    all_dates: bool = False,
    full_info: bool = False,
) -> pd.DataFrame:
    """
    Get a human readable dataframe about a git repo.
    """
    try:
        repo, repo_name = get_repo_from_source(path)
    except (InvalidGitRepositoryError, NoSuchPathError, GitCommandError):
        print("Path not recognized as a git repo.")
        return

    # get only commits of certain branch
    if branch:
        if branch == "--all":
            commits_full = list(repo.iter_commits("--all"))
        else:
            commits_full = list(repo.iter_commits(branch))
    else:
        commits_full = list(repo.iter_commits())

    # full dataframe with all commits
    commits_full.reverse()
    df_commits = get_df(commits_full)
    df_commits["net_change"] = df_commits["insertions"] - df_commits["deletions"]
    df_commits["total_code"] = (df_commits["net_change"]).cumsum()

    # reduced dataframe with penalties and grouping by date
    df = df_commits.copy()
    if isinstance(start, int):
        df = df[start:].reset_index(drop=True)
        start = None
    elif isinstance(start, str):
        start = parser.parse(start).date()
    if isinstance(end, int):
        df = df[:end].reset_index(drop=True)
        end = None
    elif isinstance(end, str):
        end = parser.parse(end).date()

    if penalties:
        df = penalize(df, penalties=penalties)
    df = group_by_time(df, group=group.lower(), start=start, end=end)
    df.title = repo_name

    if full_info:
        return df, df_commits
    else:
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
    df_commits = pd.DataFrame(commits_full).rename(columns={0: "id"})
    df_commits["date"] = df_commits["id"].apply(
        lambda commit: commit.authored_datetime.date()
    )
    df_commits["message"] = df_commits["id"].apply(
        lambda commit: commit.message.replace("\n", "")
    )
    df_commits["stats"] = df_commits["id"].apply(lambda commit: commit.stats.total)
    df_commits["insertions"] = df_commits["stats"].apply(
        lambda stats: stats["insertions"]
    )
    df_commits["deletions"] = df_commits["stats"].apply(
        lambda stats: stats["deletions"]
    )
    df_commits["net_change"] = df_commits["insertions"] - df_commits["deletions"]
    df_commits.drop("stats", axis=1, inplace=True)

    return df_commits


def penalize(
    df_input: pd.DataFrame, penalties: list[tuple[str, float]] | tuple[str, float]
) -> pd.DataFrame:
    """
    Give a penalty to commits with certain messages in them.

    penalty
      list of tuples, each tuple is (penalty_string, multiplication_factor)
    """
    df = df_input.copy()
    if isinstance(penalties, tuple):
        penalties = [penalties]
    for penalty in penalties:
        penalty_string, multiplication_factor = penalty
        mask = df["message"].str.contains(penalty_string, case=False)
        for key in ["insertions", "deletions"]:
            df.loc[mask, key] = df.loc[mask, key] * multiplication_factor
    return df


def group_by_time(
    df_commits: pd.DataFrame,
    group: Literal["day", "month", "year"] = "day",
    start: datetime.date = None,
    end: datetime.date = None,
) -> pd.DataFrame:
    """At the moment only supports grouping by day but can be extended."""
    if group == "year":
        df_commits["date"] = pd.to_datetime(df_commits["date"]).dt.to_period("Y")
    elif group == "month":
        df_commits["date"] = pd.to_datetime(df_commits["date"]).dt.to_period("M")
    elif group != "day":
        print("group should be 'day', 'month' or 'year'")
        return
    df = (
        df_commits.groupby("date")
        .agg(
            {
                "insertions": "sum",
                "deletions": "sum",
                "date": "size",
            }
        )
        .rename(columns={"date": "commits"})
        .sort_values(by="date")
        .reset_index()
    )
    df["net_change"] = df["insertions"] - df["deletions"]
    df["total_code"] = (df["net_change"]).cumsum()
    if start:
        df = df[df.date > start].reset_index(drop=True)
    if end:
        df = df[df.date < end].reset_index(drop=True)

    return df
