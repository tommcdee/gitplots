import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import numpy as np
import pandas as pd
import os
from PIL import Image


def plot(df, save: str = None, title: str = None):
    """Plots git repo information as a function of time."""
    colors = {
        "insertions": "#88c999",  # green
        "deletions": "#ff8c8c",  # red
        "commits": "#ffaf5f",  # orange
        "total_code": "#5c5c5c",  # grey
        "labels": "#5c5c5c",  # grey
    }

    date_format = {
        "object": "%d/%m",  # days
        "period[M]": "%m/%Y",  # months
        "period[A-DEC]": "%Y",  # years
    }

    date_formatter = date_format.get(df["date"].dtype.name)
    dates = [date.strftime(date_formatter) for date in df["date"]]

    # add extra dummy data points before and after
    num_dates = len(dates)
    dates = ["before"] + dates + ["after"]
    dummy_spacing = 0.666
    x_positions = (
        [0 - dummy_spacing] + list(range(num_dates)) + [num_dates - 1 + dummy_spacing]
    )

    # Bar plot for insertions and deletions
    fig, ax1 = plt.subplots(figsize=(12, 6))
    df_extended_I = [0] + df["insertions"].tolist() + [0]
    ax1.bar(
        x_positions,
        df_extended_I,
        label="additions",
        width=0.666,
        color=colors["insertions"],
    )
    df_extended_D = [0] + df["deletions"].tolist() + [0]
    ax1.bar(
        x_positions,
        df_extended_D,
        label="deletions",
        width=0.666,
        color=colors["deletions"],
        bottom=df_extended_I,
    )

    # Create a secondary y-axis for the number of commits
    ax2 = ax1.twinx()
    df_extended = [np.nan] + df["commits"].tolist() + [np.nan]
    ax2.plot(
        x_positions,
        df_extended,
        color=colors["commits"],
        marker="o",
        markersize=8,
        linewidth=3,
        label="commits",
    )

    # Plot total amount of code
    ax3 = ax1.twinx()
    df_extended = [0] + df["total_code"].tolist() + [df["total_code"].iloc[-1]]
    ax3.plot(
        x_positions,
        df_extended,
        label=f"total lines added = {df['total_code'].iloc[-1]}",
        color=colors["total_code"],
        alpha=0.6,
    )
    ax3.fill_between(x_positions, df_extended, color=colors["total_code"], alpha=0.1)
    ax3.set_yticks([])
    ax3.set_yticklabels([])

    # Set axis labels and title
    ax1.set_title(
        title or df.title or "git history", fontsize=13, color=colors["labels"]
    )
    ax1.set_xlabel("date", fontsize=13, color=colors["labels"])
    ax1.set_ylabel("code edits", fontsize=13, color=colors["labels"])
    ax2.set_ylabel("commits", fontsize=13, color=colors["labels"])

    # Rotate and align x-axis tick labels for both subplots
    ax1.tick_params(axis="x", rotation=45, colors=colors["labels"])
    ax2.tick_params(axis="x", rotation=45, colors=colors["labels"])
    ax1.set_xticks(x_positions, dates)
    ax1.set_xticks(ax1.get_xticks()[1:-1])

    # Make y=0 aligned with bottom of plot
    ax1.set_ylim(bottom=0, top=1.2 * (df["insertions"] + df["deletions"]).max())
    ax2.set_ylim(bottom=0, top=1.2 * df["commits"].max())
    ax3.set_ylim(bottom=0, top=1.2 * df["total_code"].max())

    # Display legends
    legend_ax1 = ax1.legend(loc="upper left", fontsize=11)
    legend_ax2 = ax2.legend(loc="upper right", fontsize=11)

    # Create a separate legend for ax3
    legend_ax3 = ax3.legend(loc="center right", fontsize=11)
    legend_ax3.remove()

    # Combine the handles and labels from both legends
    handles = legend_ax3.legend_handles + legend_ax2.legend_handles
    labels = [text.get_text() for text in legend_ax3.get_texts()] + [
        text.get_text() for text in legend_ax2.get_texts()
    ]

    # Create a new legend with the combined handles and labels
    legend_combined = ax2.legend(handles, labels, loc="upper right", fontsize=11)

    # Add the combined legend to the plot
    ax2.add_artist(legend_combined)

    # Color the font in the legends
    for text in legend_ax1.get_texts():
        text.set_color(colors["labels"])
    for text in legend_combined.get_texts():
        text.set_color(colors["labels"])

    # Background color
    ax1.set_facecolor("pink")
    ax1.patch.set_alpha(0.05)
    ax1.patch.set_zorder(0)

    # Adjust the layering of the plots using zorder
    ax1.set_zorder(2)
    ax2.set_zorder(3)
    ax3.set_zorder(1)

    # Frame colours
    for ax in [ax1, ax2, ax3]:
        ax.tick_params(color=colors["labels"], labelcolor=colors["labels"])
        for spine in ax.spines.values():
            spine.set_edgecolor(colors["labels"])
            spine.set_visible(False)

    # Reduce the x-axis margins
    margin = 0.3  # Adjust the margin size as needed
    ax.set_xlim(x_positions[0] - margin, x_positions[-1] + margin)

    plt.tight_layout()
    if save:
        file_name, extension = os.path.splitext(save)
        if extension.lower() == ".webp":
            save = file_name + ".png"
            plt.savefig(save, dpi=300)
            image = Image.open(save)
            image.save(file_name + ".webp", "WEBP")
        else:
            plt.savefig(save, dpi=300)
    plt.show()
