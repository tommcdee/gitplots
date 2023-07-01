from git import Repo
from git.objects.commit import Commit
import pandas as pd
from tempfile import TemporaryDirectory


def get_repo(
    path: str,
    branch: str = None,
    start: int = None,
    end: int = None,
    penalties: list[tuple[str, float]] | tuple[str, float] = None,
) -> pd.DataFrame:
    """
    Get a human readable dataframe about a git repo.
    """
    commits_full = get_from_source(path=path, branch=branch)
    commits_full = commits_full[start:end]
    df_commits = get_df(commits_full)
    if penalties:
        df_commits = penalize(df_commits, penalties=penalties)
    df = group_by_time(df_commits)
    return df


def get_from_source(path: str, branch: str = None) -> list[Commit]:
    """
    Given a path to a git repo (either local or remote), return a list of gitpython commit objects.
    """
    if path.startswith("http"):
        # If the path is a URL, clone the repository to a temporary directory
        with TemporaryDirectory() as temp_dir:
            repo = Repo.clone_from(path, temp_dir)
            if branch:
                commits_full = list(repo.iter_commits(branch))
            else:
                commits_full = list(repo.iter_commits("--all"))
    else:
        # If the path is local, open the repository
        repo = Repo(path)
        if branch:
            commits_full = list(repo.iter_commits(branch))
        else:
            commits_full = list(repo.iter_commits("--all"))

    return commits_full


def get_df(commits_full: list[Commit]):
    """
    Take a full list of commits from gitpython and convert to human readable dataframe.
    """
    commits = []
    for commit in reversed(commits_full):
        commits.append(
            {
                "id": commit.hexsha,
                "date": commit.authored_datetime.date(),
                "message": commit.message.replace("\n", ""),
                "insertions": commit.stats.total["insertions"],
                "deletions": commit.stats.total["deletions"],
                "total_edits": commit.stats.total["lines"],
            }
        )
    df_commits = pd.DataFrame(commits)
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
        df_commits.loc[mask, "insertions"] = (
            df_commits.loc[mask, "insertions"] * multiplication_factor
        )
        df_commits.loc[mask, "deletions"] = (
            df_commits.loc[mask, "deletions"] * multiplication_factor
        )
        df_commits.loc[mask, "total_edits"] = (
            df_commits.loc[mask, "total_edits"] * multiplication_factor
        )
    return df_commits


def group_by_time(df_commits: pd.DataFrame) -> pd.DataFrame:
    """At the moment only supports grouping by day but can be extended."""
    df = (
        df_commits.groupby("date")
        .agg(
            {
                "insertions": "sum",
                "deletions": "sum",
                "total_edits": "sum",
                "total_code": "max",
                "date": "size",  # New line: count the number of occurrences of each date
            }
        )
        # Rename the "date" column to "commits"
        .rename(columns={"date": "commits"})
        .reset_index()
    )
    return df
