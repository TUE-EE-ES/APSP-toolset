"""Solve-time boxplot figure using the same filtering and styling as the original code."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.cbook import _reshape_2D
from matplotlib.patches import Polygon

# Keep the exact plot typography settings used in the original scripts.
plt.rcParams.update(
    {
        "text.usetex": True,
        "font.family": "serif",
        "font.sans-serif": "Computer Modern Roman",
    }
)

# Percentiles used for the box body and whiskers.
UNDER_PERCENTILE = 20
UPPER_PERCENTILE = 80
UNDER_WHISKER_PERCENTILE = 10
UPPER_WHISKER_PERCENTILE = 90

# Display order of model variants on the x-axis.
TECHNIQUES = [
    "Bounded Monolithic",
    "Quinton Monolithic",
    "Bounded Quinton Monolithic",
    "Bounded Benders",
    "Quinton Benders",
    "Bounded Quinton Benders",
]


TIME_COLUMN_TO_SUBSCRIPT = {
    "Quinton Monolithic Time": "Quinton Monolithic",
    "Our Monolithic Time": "Bounded Monolithic",
    "Quinton Bounded Monolithic Time": "Quinton Bounded Monolithic",
    "Quinton Benders Time": "Quinton Benders",
    "Our Benders Time": "Our Benders",
    "Quinton Bounded Benders Time": "Quinton Bounded Benders",
}


def _ordered_status_columns(df: pd.DataFrame) -> list[str]:
    """Return status columns in the same fixed order as the original script."""
    status_columns = [col for col in df.columns if "Status" in col]
    return [
        status_columns[1],
        status_columns[0],
        status_columns[2],
        status_columns[4],
        status_columns[3],
        status_columns[5],
    ]


def _normalize_status_labels(df: pd.DataFrame, status_columns: list[str]) -> None:
    """Collapse equivalent status strings into one canonical label."""
    for col in status_columns:
        df[col] = df[col].replace(
            {
                "integer optimal solution": "optimal solution",
                "integer optimal, tolerance": "optimal solution",
                "optimal solution": "optimal solution",
            }
        )


def _drop_non_optimal_rows(df: pd.DataFrame, status_columns: list[str]) -> pd.DataFrame:
    """Keep only rows where every tracked technique status is optimal."""
    filtered = df.copy()
    for idx, row in df.iterrows():
        for col in status_columns:
            if "optimal solution" not in row[col]:
                print(row[col])
                filtered = filtered.drop(idx)
                break
    return filtered


def _drop_failed_verification_or_deviation_rows(
    df: pd.DataFrame,
    dfv: pd.DataFrame,
    status_columns: list[str],
    objective_columns: list[str],
) -> pd.DataFrame:
    """Remove rows that fail verification matching or have deviating objectives."""
    filtered = df.copy()

    for idx, row in df.iterrows():
        objectives = row[objective_columns].dropna().astype(int)
        status = row[status_columns]
        verification_row = dfv[dfv["Experiment"] == row["Experiment"]]

        drop_row = False
        for col in objectives.index:
            technique_key = col[:-10]  # drop " Objective"
            if (
                "verification successful | matching objectives"
                not in verification_row[technique_key].to_string()
            ):
                filtered = filtered.drop(idx)
                drop_row = True
                break
        if drop_row:
            continue

        if not objectives.empty and len(objectives) > 2:
            mode_value = objectives.min()
            deviations = objectives[objectives != mode_value]
            for col in deviations.index:
                idx_obj = objective_columns.index(col)
                if status[status_columns[idx_obj]] == "optimal solution":
                    filtered = filtered.drop(idx)
                    break

    return filtered


def _ordered_time_columns(df: pd.DataFrame) -> list[str]:
    """Return time columns in the same display order as the original script."""
    time_columns = [col for col in df.columns if "Time" in col]
    return [
        time_columns[1],
        time_columns[0],
        time_columns[2],
        time_columns[4],
        time_columns[3],
        time_columns[5],
    ]


# Function adapted from matplotlib.cbook to support custom percentile box ranges.
def my_boxplot_stats(X, whis=1.5, bootstrap=None, labels=None, autorange=False, percents=[25, 75]):
    def _bootstrap_median(data, N=5000):
        M = len(data)
        percentiles = [2.5, 97.5]
        bs_index = np.random.randint(M, size=(N, M))
        bs_data = data[bs_index]
        estimate = np.median(bs_data, axis=1, overwrite_input=True)
        return np.percentile(estimate, percentiles)

    def _compute_conf_interval(data, med, iqr, bootstrap_value):
        if bootstrap_value is not None:
            ci = _bootstrap_median(data, N=bootstrap_value)
            notch_min = ci[0]
            notch_max = ci[1]
        else:
            n_values = len(data)
            notch_min = med - 1.57 * iqr / np.sqrt(n_values)
            notch_max = med + 1.57 * iqr / np.sqrt(n_values)
        return notch_min, notch_max

    bxpstats = []
    X = _reshape_2D(X, "X")
    input_whis = whis

    for x, label in zip(X, labels):
        stats = {}
        if label is not None:
            stats["label"] = labels

        whis = input_whis
        bxpstats.append(stats)

        if len(x) == 0:
            stats["fliers"] = np.array([])
            stats["mean"] = np.nan
            stats["med"] = np.nan
            stats["q1"] = np.nan
            stats["q3"] = np.nan
            stats["cilo"] = np.nan
            stats["cihi"] = np.nan
            stats["whislo"] = np.nan
            stats["whishi"] = np.nan
            stats["med"] = np.nan
            continue

        x = np.asarray(x)
        stats["mean"] = np.mean(x)
        med = np.percentile(x, 50)
        q1, q3 = np.percentile(x, (percents[0], percents[1]))

        stats["iqr"] = q3 - q1
        if stats["iqr"] == 0 and autorange:
            whis = "range"

        stats["cilo"], stats["cihi"] = _compute_conf_interval(x, med, stats["iqr"], bootstrap)

        if np.isscalar(whis):
            if np.isreal(whis):
                loval = q1 - whis * stats["iqr"]
                hival = q3 + whis * stats["iqr"]
            elif whis in ["range", "limit", "limits", "min/max"]:
                loval = np.min(x)
                hival = np.max(x)
            else:
                raise ValueError("whis must be a float, valid string, or list of percentiles")
        else:
            loval = np.percentile(x, whis[0])
            hival = np.percentile(x, whis[1])

        wiskhi = np.compress(x <= hival, x)
        stats["whishi"] = q3 if len(wiskhi) == 0 or np.max(wiskhi) < q3 else np.max(wiskhi)

        wisklo = np.compress(x >= loval, x)
        stats["whislo"] = q1 if len(wisklo) == 0 or np.min(wisklo) > q1 else np.min(wisklo)

        stats["fliers"] = np.hstack(
            [
                np.compress(x < stats["whislo"], x),
                np.compress(x > stats["whishi"], x),
            ]
        )
        stats["q1"], stats["med"], stats["q3"] = q1, med, q3

    return bxpstats


def _build_boxplot_stats(df: pd.DataFrame, time_columns: list[str]) -> dict[str, dict]:
    """Compute custom boxplot stats for each ordered timing column."""
    stats: dict[str, dict] = {}
    for time_column in time_columns:
        stats[time_column] = my_boxplot_stats(
            df[time_column],
            labels=TIME_COLUMN_TO_SUBSCRIPT[time_column],
            percents=[UNDER_PERCENTILE, UPPER_PERCENTILE],
            whis=[UNDER_WHISKER_PERCENTILE, UPPER_WHISKER_PERCENTILE],
        )[0]
    return stats


def _plot_timing_boxplot(stats: dict[str, dict], time_columns: list[str], sample_count: int) -> None:
    """Render the final solve-time boxplot with the original colors and formatting."""
    # Preserve original debug prints.
    print("test")
    print(sample_count)

    _, ax = plt.subplots(1, 1, figsize=(6, 3))
    bp = ax.bxp([stats[column] for column in time_columns], positions=range(6))

    wrapped_labels = [technique.replace(" ", "\n", 2) for technique in TECHNIQUES]
    ax.set_xticklabels(wrapped_labels, rotation=0, ha="center")

    for element in bp.keys():
        plt.setp(bp[element], color="#000000")

    face_colors = ["#2C4AA0", "#3F6FD8", "#8FB0F0", "#2C4AA0", "#3F6FD8", "#8FB0F0"]
    for box_line, face_color in zip(bp["boxes"], face_colors):
        verts = box_line.get_path().vertices
        patch = Polygon(
            verts,
            closed=True,
            facecolor=face_color,
            edgecolor=box_line.get_color(),
        )
        ax.add_patch(patch)
        box_line.set_visible(False)

    plt.suptitle("")
    plt.xlabel("Model")
    plt.ylabel("Solve Time")
    plt.yscale("log")
    plt.tight_layout()
    ax.grid(linestyle=":", linewidth=0.6, alpha=0.7)
    plt.show()


def main() -> None:
    """Load data, filter to valid comparable rows, then plot solve-time distribution."""
    df = pd.read_csv("results.csv")
    dfv = pd.read_csv("verification_results.csv")

    status_columns = _ordered_status_columns(df)
    objective_columns = [col.replace("Status", "Objective") for col in status_columns]

    _normalize_status_labels(df, status_columns)
    df = _drop_non_optimal_rows(df, status_columns)
    df[objective_columns] = (
        df[objective_columns].apply(pd.to_numeric, errors="coerce").round().astype("Int64")
    )
    df = _drop_failed_verification_or_deviation_rows(df, dfv, status_columns, objective_columns)

    time_columns = _ordered_time_columns(df)
    stats = _build_boxplot_stats(df, time_columns)
    _plot_timing_boxplot(stats, time_columns, len(df[time_columns[0]]))


if __name__ == "__main__":
    main()
