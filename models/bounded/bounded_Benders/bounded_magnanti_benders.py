from .bounded_master import *
from .bounded_dual_sub import *
from .bounded_primal_sub import *
from .bounded_auxilary_sub import *
import copy

class BoundedMagnantiWongBenders(MagnantiWongPapadakosBendersDecomposition):
    def   __init__(self, name, model_data):
        # Store the model data
        self.data = model_data

        # Initialize master problem
        master_problem = BoundedMaster(name + "_master", model_data)
        primal_sub_problem = BoundedPrimalSub(name + "_primal_sub", model_data)
        dual_sub_problem = BoundedDualSub(name + "_dual_sub", model_data)
        auxiliary_sub_problem = BoundedMagnantiWongSub(name + "_auxiliary_sub", model_data)

        super().__init__(name, master_problem, primal_sub_problem, dual_sub_problem, auxiliary_sub_problem)

    def _MagnantiWongPapadakosBendersDecomposition__extract_master_problem_results(self):
        """
        Extracts the relevant trail values from the master problem solution
        """

        # List to hold sequence of transfers for each vehicle
        self.master_problem_extract = copy.copy(self.master_problem.decision_vars)

        self.master_problem_extract.x = {x: round(y.solution_value) for x, y in self.master_problem_extract.x.items()}
        self.master_problem_extract.y = {x: round(y.solution_value) for x, y in self.master_problem_extract.y.items()}

        self.master_problem_extract.mu = self.master_problem_extract.mu.solution_value

    def _MagnantiWongPapadakosBendersDecomposition__calculate_core_point(self, iteration):
        """
        Obtains the core point for auxiliary sub problems
        """

        self.core_point = copy.copy(self.master_problem_extract)

        if iteration == 0:
            self.previous_core_point = copy.copy(self.core_point)

            self.core_point.x = {x: 0.5 * y for x, y in self.core_point.x.items()}
            self.core_point.y = {x: 0.5 * y for x, y in self.core_point.y.items()}
            self.core_point.mu = 0.5 * self.core_point.mu
        else:
            self.previous_core_point.x = copy.deepcopy(self.core_point.x)
            self.previous_core_point.y = copy.deepcopy(self.core_point.y)
            self.previous_core_point.mu = copy.deepcopy(self.core_point.mu)

            self.core_point.x = {i: 0.5 * self.previous_core_point.x[i] + 0.5 * self.core_point.x[i] for i in self.core_point.x.keys()}
            self.core_point.y = {i: 0.5 * self.previous_core_point.y[i] + 0.5 * self.core_point.y[i]  for i in self.core_point.y.keys()}
            self.core_point.mu = 0.5 + self.previous_core_point.mu + 0.5 * self.core_point.mu


    def _MagnantiWongPapadakosBendersDecomposition__apply_cuts(self):
        """
        Construct and apply Benders Cuts
        """
        mdl = self.master_problem.model

        # Obtain variable solutions
        sub_problem_extract = copy.copy(self.auxiliary_sub_problem.decision_vars)

        pi_p = {x: y.solution_value for x, y in sub_problem_extract.pi_p.items()}
        pi_nr = {x: y.solution_value for x, y in sub_problem_extract.pi_nr.items()}
        pi_nl = {x: y.solution_value for x, y in sub_problem_extract.pi_nl.items()}
        pi_nd = {x: y.solution_value for x, y in sub_problem_extract.pi_nd.items()}
        pi_s = {x: y.solution_value for x, y in sub_problem_extract.pi_s.items()}

        x = self.master_problem.decision_vars.x
        y = self.master_problem.decision_vars.y
        mu = self.master_problem.decision_vars.mu

        M = max([self.data.TASKS[a][r] for a in self.data.TASKS for r in
                 self.data.TASKS[a]]) * self.data.NR_TASKS * self.data.BOUND

        # Benders cut as described by constraints (21) and (35)
        cut = (mu >= (
                mdl.sum(pi_p[(c[0], self.data.DEPENDENCIES[c], c[1])] * mdl.sum(
                    x[(c[0], p)] * self.data.TASKS[c[0]][p] for p in self.data.TASKS[c[0]]) for c in
                        self.data.DEPENDENCIES) +
                mdl.sum(pi_nl[(ij[0], ij[1], p, m)] * (
                        self.data.TASKS[ij[0]][p] - M * (3 - x[(ij[0], p)] - x[(ij[1], p)] - y[(ij[0], ij[1], m)]))
                        for ij in self.data.ALLOCATION_OVERLAP.keys()
                        for p in self.data.ALLOCATION_OVERLAP[ij]
                        for m in range(self.data.BOUND + 1)) +
                mdl.sum(pi_nr[(ij[0], ij[1], p, m)] * (
                        self.data.TASKS[ij[1]][p] - M * (2 - x[(ij[0], p)] - x[(ij[1], p)] + y[(ij[0], ij[1], m)]))
                        for ij in self.data.ALLOCATION_OVERLAP.keys()
                        for p in self.data.ALLOCATION_OVERLAP[ij]
                        for m in range(self.data.BOUND + 1)) +
                mdl.sum(pi_nd[a] * mdl.sum(x[(a, p)] * self.data.TASKS[a][p] for p in self.data.TASKS[a]) for a in
                        self.data.TASKS if 0 not in self.data.TASKS[a].values())
        ))

        # Add cut to master problem
        self.master_problem.model.add(cut)

    def build_figure(self):
        """
        Build figure of final solution
        """

        # Use primal sub problem to obtain final schedule
        self.primal_sub_problem.setup_constraints(self.best_master_problem_extract)
        self.primal_sub_problem.solve(False)

        return self.primal_sub_problem.build_figure()


