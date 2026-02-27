"""Stacked bar chart of solution outcomes per benchmark set and technique."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

# Keep the exact plot typography settings used in the original scripts.
plt.rcParams.update(
    {
        "text.usetex": True,
        "font.family": "serif",
        "font.sans-serif": "Computer Modern Roman",
    }
)


def _ordered_status_columns(df: pd.DataFrame) -> list[str]:
    """Return status columns in the same fixed order as the original figure code."""
    status_columns = [col for col in df.columns if "Status" in col]
    return [
        status_columns[1],
        status_columns[4],
        status_columns[0],
        status_columns[3],
        status_columns[2],
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


def _build_long_form_outcome_table(
    results_csv: str = "results.csv",
    verification_csv: str = "verification_results.csv",
) -> tuple[pd.DataFrame, list[str], list[str], list[str], dict[str, str]]:
    """
    Rebuild the same long-form table used by the original stacked outcomes plot.
    This intentionally preserves filtering/order behavior from the old script.
    """
    df = pd.read_csv(results_csv)
    dfv = pd.read_csv(verification_csv)

    status_columns = _ordered_status_columns(df)
    objective_columns = [col.replace("Status", "Objective") for col in status_columns]
    verification_columns = [col.replace(" Status", "") for col in status_columns]
    _normalize_status_labels(df, status_columns)

    # Objective values are compared as rounded integers, exactly as before.
    df[objective_columns] = (
        df[objective_columns].apply(pd.to_numeric, errors="coerce").round().astype("Int64")
    )

    benchmark_sets = ["10-04", "10-03", "10-02", "15-04", "15-03", "15-02"]
    deviations_list: list[tuple[str, list[str]]] = []

    # Update statuses based on verification outcomes and objective agreement.
    for idx, row in df.iterrows():
        objectives = row[objective_columns].dropna().astype(int)
        status = row[status_columns]
        verification_row = dfv[dfv["Experiment"] == row["Experiment"]]

        for col in objectives.index:
            idx_obj = objective_columns.index(col)
            technique_key = col[:-10]  # drop " Objective"

            if "constraint violation" in verification_row[technique_key].to_string():
                df.at[idx, status_columns[idx_obj]] = "constraint violation"

            if (
                status[status_columns[idx_obj]] != "optimal solution"
                or "verification successful | matching objectives"
                not in verification_row[technique_key].to_string()
            ):
                objectives = objectives.drop(col)

        if not objectives.empty and len(objectives) > 2:
            mode_value = objectives.min()
            deviations = objectives[objectives != mode_value]

            for col in deviations.index:
                idx_obj = objective_columns.index(col)
                if status[status_columns[idx_obj]] == "optimal solution":
                    df.at[idx, status_columns[idx_obj]] = "deviating objective"

            if not deviations.empty:
                deviations_list.append((row["Experiment"], deviations.index.tolist()))

    infeasible_sets: dict[str, tuple[int, ...]] = {}
    deviating_objective_sets: dict[str, tuple[int, ...]] = {}
    constraint_violation_sets: dict[str, tuple[int, ...]] = {}
    timeout_sets: dict[str, tuple[int, ...]] = {}
    optimal_sets: dict[str, tuple[int, ...]] = {}

    for benchmark_set in benchmark_sets:
        pattern = benchmark_set[:2] + "-1000-0.10" + benchmark_set[2:]
        df_filtered = df[df["Experiment"].str.contains(pattern, na=False)]
        dfv_filtered = dfv[dfv["Experiment"].str.contains(pattern, na=False)]

        infeasible_sets[benchmark_set] = tuple(
            df_filtered[col].str.count("infeas|unbound").sum() for col in status_columns
        )
        deviating_objective_sets[benchmark_set] = tuple(
            df_filtered[col].str.count("deviating").sum() for col in status_columns
        )
        timeout_sets[benchmark_set] = tuple(
            df_filtered[col].str.count("time limit").sum() for col in status_columns
        )
        constraint_violation_sets[benchmark_set] = tuple(
            dfv_filtered[col].str.count("constraint violation").sum()
            for col in verification_columns
        )
        optimal_sets[benchmark_set] = tuple(
            df_filtered[col].str.count("optimal solution").sum() for col in status_columns
        )

    # Preserve the original console output side-effects.
    for instance, deviating_techniques in deviations_list:
        print(f"Instance: {instance}, Deviating Techniques: {', '.join(deviating_techniques)}")
    print(infeasible_sets)

    techniques = [
        "Bounded Monolithic",
        "Bounded Benders",
        "Quinton Monolithic",
        "Quinton Benders",
        "Bounded Quinton Monolithic",
        "Bounded Quinton Benders",
    ]
    outcomes = [
        "Optimal",
        "Time Limit",
        "Constraint Violation",
        "Deviating Objective",
        "Solving Error",
    ]

    # Keep the exact outcome palette from the original chart.
    custom_colors = ["#FBE2E5", "#F29AA3", "#B5283B", "#C5CAD1", "#BEE5D6"]
    outcome_colors = {outcome: custom_colors[i] for i, outcome in enumerate(reversed(outcomes))}

    # Convert tuple aggregates into one long-form table for plotting.
    records: list[dict[str, int | str]] = []
    for benchmark_set in benchmark_sets:
        infeas_vals = infeasible_sets.get(benchmark_set, ())
        dev_vals = deviating_objective_sets.get(benchmark_set, ())
        cons_vals = constraint_violation_sets.get(benchmark_set, ())
        time_vals = timeout_sets.get(benchmark_set, ())
        opt_vals = optimal_sets.get(benchmark_set, ())

        max_len = (
            max(
                len(infeas_vals),
                len(dev_vals),
                len(cons_vals),
                len(time_vals),
                len(opt_vals),
            )
            if techniques
            else 0
        )
        for idx in range(max_len):
            records.append(
                {
                    "Benchmark set": benchmark_set,
                    "Technique": (
                        techniques[idx] if idx < len(techniques) else f"Tech {idx + 1}"
                    ),
                    "Solving Error": int(infeas_vals[idx]) if idx < len(infeas_vals) else 0,
                    "Deviating Objective": int(dev_vals[idx]) if idx < len(dev_vals) else 0,
                    "Constraint Violation": int(cons_vals[idx]) if idx < len(cons_vals) else 0,
                    "Time Limit": int(time_vals[idx]) if idx < len(time_vals) else 0,
                    "Optimal": int(opt_vals[idx]) if idx < len(opt_vals) else 0,
                }
            )

    long_df = pd.DataFrame.from_records(records)
    return long_df, benchmark_sets, techniques, outcomes, outcome_colors


def main() -> None:
    long_df, benchmark_sets, techniques, outcomes, outcome_colors = _build_long_form_outcome_table()

    # Grouped + stacked layout:
    # x-groups are techniques, each group contains one bar per benchmark set.
    plt.close("all")
    x = np.arange(len(techniques))
    bar_width = 0.8 / max(1, len(benchmark_sets))
    _, ax = plt.subplots(figsize=(6, 4))

    for benchmark_index, benchmark_set in enumerate(benchmark_sets):
        xpos = x + (benchmark_index * bar_width) - 0.4 + (bar_width / 2)
        bottom = np.zeros(len(techniques), dtype=float)
        for outcome in reversed(outcomes):
            measurement = np.array(
                [
                    long_df[
                        (long_df["Benchmark set"] == benchmark_set)
                        & (long_df["Technique"] == technique)
                    ][outcome].sum()
                    for technique in techniques
                ],
                dtype=float,
            )
            rects = ax.bar(
                xpos,
                measurement,
                bar_width,
                bottom=bottom,
                color=outcome_colors[outcome],
                edgecolor="black",
                linewidth=0.4,
                label=outcome if benchmark_index == 0 else None,
            )
            ax.bar_label(
                rects,
                labels=[r"\textbf{" + str(int(v)) + r"}" if v > 0 else "" for v in measurement],
                label_type="center",
                color="black",
                fontsize=7,
                fontweight="bold",
            )
            bottom += measurement

    # Bottom axis: techniques.
    ax.set_xticks(x)
    wrapped_labels = [technique.replace(" ", "\n", 2) for technique in techniques]
    ax.set_xticklabels(wrapped_labels, rotation=0, ha="center")
    ax.set_xlabel("Model", labelpad=12)

    # Top axis: benchmark set label per individual bar.
    ax_top = ax.secondary_xaxis("top")
    all_xpos = []
    all_labels = []
    for benchmark_index, benchmark_set in enumerate(benchmark_sets):
        xpos = x + (benchmark_index * bar_width) - 0.4 + (bar_width / 2)
        all_xpos.extend(list(xpos))
        all_labels.extend([benchmark_set] * len(xpos))
    ax_top.set_xticks(all_xpos)
    ax_top.set_xticklabels(all_labels, rotation=90, fontsize=9)
    ax_top.set_xlabel("Benchmark sets", labelpad=10)
    ax.set_ylabel("Number of Benchmark Instances")

    # Keep legend ordering and 2/3 column split exactly as before.
    handles, labels = ax.get_legend_handles_labels()
    label_to_handle = dict(zip(labels, handles))
    desired_order = [
        "Optimal",
        "Time Limit",
        "Constraint Violation",
        "Deviating Objective",
        "Solving Error",
    ]
    ordered_labels = [label for label in desired_order if label in label_to_handle]
    ordered_handles = [label_to_handle[label] for label in ordered_labels]
    spacer = Patch(facecolor="none", edgecolor="none", linewidth=0)
    ordered_handles = [
        ordered_handles[0],
        ordered_handles[1],
        spacer,
        ordered_handles[2],
        ordered_handles[3],
        ordered_handles[4],
    ]
    ordered_labels = [
        ordered_labels[0],
        ordered_labels[1],
        "",
        ordered_labels[2],
        ordered_labels[3],
        ordered_labels[4],
    ]
    ax.legend(
        ordered_handles,
        ordered_labels,
        title="Outcome",
        loc="upper left",
        frameon=True,
        fontsize=8,
        title_fontsize=9,
        ncol=2,
    )

    plt.tight_layout()
    plt.subplots_adjust(left=0.12, right=0.98, bottom=0.30, top=0.92)
    plt.yticks(range(0, 21, 2))
    ax.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.7)
    plt.show()


if __name__ == "__main__":
    main()
