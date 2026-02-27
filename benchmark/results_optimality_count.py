"""Optimality count chart per technique."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

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
) -> tuple[pd.DataFrame, list[str]]:
    """
    Rebuild the same long-form table used by the original results-sets script.
    This keeps preprocessing behavior aligned with the accuracy-issues chart.
    """
    df = pd.read_csv(results_csv)
    dfv = pd.read_csv(verification_csv)

    status_columns = _ordered_status_columns(df)
    objective_columns = [col.replace("Status", "Objective") for col in status_columns]
    verification_columns = [col.replace(" Status", "") for col in status_columns]
    _normalize_status_labels(df, status_columns)
    df[objective_columns] = (
        df[objective_columns].apply(pd.to_numeric, errors="coerce").round().astype("Int64")
    )

    benchmark_sets = ["10-04", "10-03", "10-02", "15-04", "15-03", "15-02"]
    deviations_list: list[tuple[str, list[str]]] = []

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

    return pd.DataFrame.from_records(records), techniques


def main() -> None:
    long_df, techniques = _build_long_form_outcome_table()

    # Sum optimal outcomes over all benchmark sets, per technique.
    opt_sums = long_df.groupby("Technique")["Optimal"].sum().reindex(techniques).fillna(0)

    _, ax = plt.subplots()
    plt.gcf().set_size_inches(5.2, 2.8)

    x = np.arange(len(opt_sums))
    bar_width = 0.6
    max_total = 120

    # Preserve the same stacked "optimal vs not optimal up to 120" design.
    not_opt_sums = np.maximum(0, max_total - opt_sums.values.astype(float))
    opt_colors = ["#2C4AA0", "#2C4AA0", "#3F6FD8", "#3F6FD8", "#8FB0F0", "#8FB0F0"]

    rects_opt = ax.bar(
        x,
        opt_sums.values.astype(float),
        bar_width,
        color=opt_colors,
        edgecolor="black",
        linewidth=0.4,
        label="Optimal",
    )
    rects_not = ax.bar(
        x,
        not_opt_sums,
        bar_width,
        bottom=opt_sums.values.astype(float),
        color="#D9D9D9",
        edgecolor="black",
        linewidth=0.4,
        label="Not Optimal",
    )

    wrapped_labels = [technique.replace(" ", "\n", 2) for technique in techniques]
    ax.set_xticks(x)
    ax.set_xticklabels(wrapped_labels, rotation=0, ha="center")
    ax.set_ylabel("Optimality Count")
    ax.set_xlabel("Model", labelpad=8)
    ax.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.7)

    opt_labels = [f"{int(v)}" if v > 0 else "" for v in opt_sums.values.astype(float)]
    not_labels = [f"{int(v)}" if v > 0 else "" for v in not_opt_sums]
    ax.bar_label(rects_opt, labels=opt_labels, label_type="center", fontsize=8, fontweight="bold")
    ax.bar_label(rects_not, labels=not_labels, label_type="center", fontsize=8, fontweight="bold")

    ax.set_ylim(0, max_total)
    plt.yticks(range(0, max_total + 1, 20))
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
