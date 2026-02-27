from models.configuration import *
import matplotlib.pyplot as plt
import re

class BoundedMonolithic(CplexModel):

    def setup_variables(self, *args):
        """
        Setup decision variables and solver parameters
        """
        mdl = self.model
        # Set solver parameters
        APSPParameters(mdl)
        # Set solver precision
        mdl.parameters.simplex.tolerances.optimality = 1e-6

        # Define bound from Theorem 1
        self.data.BOUND = self.data.NR_RESOURCES + self.data.NR_TASKS

        # Create decision vars
        self.decision_vars.s = mdl.continuous_var_dict([(t) for t in self.data.TASKS.keys()], name='s', lb=0) # Start time of each task
        self.decision_vars.mu = mdl.continuous_var(name='mu') # Period to minimize
        self.decision_vars.x = mdl.binary_var_dict([(t, r) for t in self.data.TASKS.keys() for r in self.data.TASKS[t]], name='x') # Task t is on resource r
        self.decision_vars.y = mdl.binary_var_dict([(t1, t2, k) for t1 in self.data.TASKS.keys() for t2 in self.data.TASKS.keys() if t1 != t2 for k in range(self.data.BOUND + 1)], name='y') # Repeition 1 of task t1 is before repetition m of t2


        pass

    def setup_constraints(self, *args):
        """
        Setup constraints for solving
        """
        mdl = self.model

        s = self.decision_vars.s
        mu = self.decision_vars.mu
        x = self.decision_vars.x
        y = self.decision_vars.y

        M = max([self.data.TASKS[t][r] for t in self.data.TASKS for r in self.data.TASKS[t]]) * self.data.NR_TASKS * self.data.BOUND

        # Begin constraints
        for d in self.data.DEPENDENCIES:
            # Add task dependencies constraints
            mdl.add_constraint(
                s[d[1]] >= s[d[0]] - self.data.DEPENDENCIES[d] * mu + mdl.sum(x[d[0], r] * self.data.TASKS[d[0]][r] for r in self.data.TASKS[d[0]]))

        # Add resource allocation constraint
        mdl.add_constraints(mdl.sum(x[t, p] for p in self.data.TASKS[t]) == 1 for t in self.data.TASKS)

        for t1 in self.data.TASKS.keys():
            if 0 not in self.data.TASKS[t1].values():
                # Add no-overlap constraint of t single tasks with another repetition.
                mdl.add(s[t1] + mdl.sum(x[t1, r] * self.data.TASKS[t1][r] for r in self.data.TASKS[t1]) <= s[t1] + mu)
            # Add start time bound
            mdl.add(s[t1] <= self.data.BOUND * mu)

            # Add no-overlap constraints between various tasks and various repetitions
            for t2 in self.data.TASKS:
                if t1 != t2:
                    if (t1, t2) in self.data.ALLOCATION_OVERLAP:
                        for r in self.data.ALLOCATION_OVERLAP[(t1, t2)]:
                            for m1 in range(self.data.BOUND + 1):
                                mdl.add_constraint(
                                    s[t1] + self.data.TASKS[t1][r] + m1 * mu <= s[t2] + M * (
                                            3 - x[(t1, r)] - x[(t2, r)] - y[(t1, t2, m1)]),
                                )
                                mdl.add_constraint(
                                    s[t2] + self.data.TASKS[t2][r] <= s[t1] + m1 * mu + M * (
                                            2 - x[(t1, r)] - x[(t2, r)] + y[(t1, t2, m1)]),
                                )

        # Minimize mu
        mdl.minimize(mu)

    def _OptimizationModel__build_figure(self):
        res = self.res
        config = APSPConfigure()

        # Check if solution is available
        if res is not None:
            gantt_data = []

            # Build Gantt dataset
            for rep in range(config.figure_repetitions):
                for task, start_time in self.decision_vars.s.items():
                    assigned_resources = [
                        r for r in self.data.TASKS[task]
                        if self.decision_vars.x[(task, r)].solution_value > 0.5
                    ]
                    # if not assigned_resources:
                    #     continue
                    resource = assigned_resources[0]
                    duration = self.data.TASKS[task][resource]
                    start_time_val = start_time.solution_value + rep * self.decision_vars.mu.solution_value
                    gantt_data.append((resource, task, start_time_val, duration, rep))

            # Sort tasks by start time within each resource
            gantt_data.sort(key=lambda x: (x[0], x[2]))

            if config.mode is not APSPConfigure.APSPConfig.PAPER:
                # Create plot
                fig, ax = plt.subplots(figsize=(10, 6))

                yticks = []
                ylabels = []
                colors = plt.cm.tab20.colors

                task_color_map = {task: colors[i % len(colors)] for i, task in enumerate(self.data.TASKS)}

                # Draw bars
                for i, (resource, task, start, duration, rep) in enumerate(gantt_data):
                    y = resource
                    ax.barh(y, duration, left=start, height=0.3, color=task_color_map[task], edgecolor='black')
                    ax.text(start + duration / 2, y, f"{task}", ha='center', va='center', color='white', fontsize=8,
                                weight='bold')

                    if y not in yticks:
                        yticks.append(y)
                        # Change y label to custom naming
                        if config.mode is APSPConfigure.APSPConfig.SDF3:
                            ylabels.append(f"Processor {y}")
                        elif config.mode is APSPConfigure.APSPConfig.CUSTOM:
                            ylabels.append(str(y))

                # Plot settings
                ax.set_xlabel(r"Time " + config.time_units)
                # Change y label to custom naming
                if config.mode is APSPConfigure.APSPConfig.SDF3:
                    ax.set_ylabel("Processor")
                elif config.mode is APSPConfigure.APSPConfig.CUSTOM:
                    ax.set_ylabel(config.custom_resource_name.capitalize())
                ax.set_yticks(yticks)
                ax.set_yticklabels(ylabels)
                ax.grid(True)
                plt.tight_layout()

                return plt
            else:
                # Set plot to Latex Font
                plt.rcParams.update({
                    "text.usetex": True,
                    "font.family": "serif",
                    "font.sans-serif": "Computer Modern Roman",
                })

                # Create plot
                fig, ax = plt.subplots(figsize=(9, 2.5), constrained_layout=True)
                plt.rcParams.update({
                    "axes.labelsize": 30,
                    "xtick.labelsize": 30,
                    "ytick.labelsize": 30,
                    "legend.fontsize": 13,
                })

                # Apply custom bar colors
                colors = [
                    '#1393A0',  # Teal
                    '#F4843A',  # Orange
                    '#2F8C6B',  # Green
                    '#C85A5A',  # Soft red
                    '#7B66C7',  # Indigo
                    '#8A6F5A',  # Warm brown
                    '#C45FA1',  # Pink-magenta
                    '#7F8C8D',  # Neutral gray
                    '#B9C55B',  # Yellow-green
                    '#74C7D2',  # Cyan-blue
                    '#7BC4A8'   # Light green
                ]

                # Map tasks to colors
                task_color_map = {
                    actor: colors[i % len(colors)] for i, actor in enumerate(self.data.TASKS)
                }

                # Set bar height
                BAR_HEIGHT = 0.85

                # Set repetition patterns
                HATCHES = ['', '//', '..']

                resource_positions = {}
                ylabels = []

                # Draw bars
                for resource, task, start, duration, rep_idx in gantt_data:
                    if resource not in resource_positions:
                        resource_positions[resource] = len(resource_positions)
                        ylabels.append(r"$r_{" + str(int(re.findall(r'\d+', resource)[0]) + 1) + "}$")

                    y = resource_positions[resource]

                    # Make horizontal bar
                    ax.barh(
                        y,
                        duration,
                        left=start,
                        height=BAR_HEIGHT,
                        color=task_color_map[task],
                        edgecolor='black',
                        hatch=HATCHES[rep_idx % len(HATCHES)],
                    )

                # Build legends
                from matplotlib.patches import Patch

                # Create patch for all tasks
                task_legend_handles = [
                    Patch(facecolor=task_color_map[task], edgecolor='black',
                          label=r"$t_{" + str(task[1:]) + "}$")  # ,alpha = 0.85)
                    for task in self.data.TASKS
                ]

                # Create patch for all repetitions
                repetition_legend_handles = [
                    Patch(facecolor='white', edgecolor='black',
                          hatch=HATCHES[r % len(HATCHES)], label=f"{r + 1}")
                    for r in range(config.figure_repetitions)
                ]

                # Create legend for tasks
                legend_tasks = ax.legend(
                    handles=task_legend_handles,
                    title="Tasks",
                    loc='lower left',
                    bbox_to_anchor=(0.0, 1.00),  # just above the plot
                    bbox_transform=ax.transAxes,
                    frameon=False,
                    fancybox=False,
                    framealpha=0.9,
                    ncol=len(task_legend_handles),  # horizontal
                    handlelength=1.4,  # compact glyph width
                    handletextpad=0.4,  # smaller gap
                    borderpad=0.3,  # tighter box padding
                    labelspacing=0.2,  # tighter vertical
                    columnspacing=0.6,  # tighter horizontal
                )
                ax.add_artist(legend_tasks)
                legend_tasks.get_title().set_fontsize(13)

                # Create legend for repetitions
                legend_reps = ax.legend(
                    handles=repetition_legend_handles,
                    title="Repetitions",
                    loc='lower right',  # anchor on right
                    bbox_to_anchor=(1.00, 1.00),  # top-right above axes
                    bbox_transform=ax.transAxes,
                    frameon=False,
                    fancybox=False,
                    framealpha=0.9,
                    ncol=len(repetition_legend_handles),
                    handlelength=1.3,
                    handletextpad=0.4,
                    borderpad=0.3,
                    labelspacing=0.2,
                    columnspacing=0.6,
                )
                legend_reps.get_title().set_fontsize(13)

                # Other plot settings
                ax.set_yticks(list(resource_positions.values()))
                ax.set_yticklabels(ylabels)

                ax.set_xlabel(r"Time " + config.time_units)
                ax.set_ylabel("Resource")
                ax.grid(True, axis='x', linewidth=0.5, alpha=0.6)
                ax.tick_params(axis='both', which='major', labelsize=13)
                ax.xaxis.label.set_size(13)
                ax.yaxis.label.set_size(13)
                ax.margins(x=0.01, y=0.06)

                return plt
