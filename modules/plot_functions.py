import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import pandas as pd


def plot(df):
    """Plots git repo information as a function of time."""
    insertion_color = "#88c999"  # green
    deletion_color = "#ff8c8c"  # red
    commit_color = "#ffaf5f"  # orange
    total_color = "#5c5c5c"  # grey
    label_color = "#5c5c5c"  # grey

    dates = [date.strftime("%d/%m") for date in df["date"]]
    # extended_dates = dates.copy().append("")
    # final_code_count = df_days["total_code"].iloc[-1]

    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Bar plot for insertions and deletions
    ax1.bar(
        dates,
        df["insertions"],
        label="additions",
        width=0.7,
        color=insertion_color,
    )
    ax1.bar(
        dates,
        df["deletions"],
        label="deletions",
        width=0.7,
        color=deletion_color,
        bottom=df["insertions"],
    )

    # Create a secondary y-axis for the number of commits
    ax2 = ax1.twinx()
    ax2.plot(
        dates,
        df["commits"],
        color=commit_color,
        marker="o",
        markersize=8,
        linewidth=3,
        label="commits",
    )

    # plot total amount of code
    ax3 = ax1.twinx()
    ax3.plot(
        dates,
        df["total_code"],
        label="total lines of code",
        color=total_color,
        alpha=0.6,
    )
    ax3.fill_between(dates, df["total_code"], color=total_color, alpha=0.1)
    ax3.set_yticks([])
    ax3.set_yticklabels([])

    # Set axis labels and title
    ax1.set_title("cityalarms.com reboot", fontsize=13, color=label_color)
    ax1.set_xlabel("date", fontsize=13, color=label_color)
    ax1.set_ylabel("code edits", fontsize=13, color=label_color)
    ax2.set_ylabel("commits", fontsize=13, color=label_color)

    # Rotate and align x-axis tick labels for both subplots
    ax1.tick_params(axis="x", rotation=45, colors=label_color)
    ax2.tick_params(axis="x", rotation=45, colors=label_color)

    # Make y=0 aligned with bottom of plot
    ax1.set_ylim(bottom=0, top=1.2 * df["total_edits"].max())
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
        text.set_color(label_color)
    for text in legend_combined.get_texts():
        text.set_color(label_color)

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
        ax.tick_params(color=label_color, labelcolor=label_color)
        for spine in ax.spines.values():
            spine.set_edgecolor(label_color)
            spine.set_visible(False)

    # Reduce the x-axis margins
    margin = 1  # Adjust the margin size as needed
    ax.set_xlim(-margin, len(dates) - 1 + margin)

    # Annotations
    font_properties = fm.FontProperties(size=11)
    ax1.annotate(
        "6134 total lines",
        xy=(0, 0),
        xytext=(len(dates) - 4.7, 1900),
        fontproperties=font_properties,
        color=label_color,
    )

    plt.tight_layout()
    plt.show()
