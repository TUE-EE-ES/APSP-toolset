from fontTools.designspaceLib import posixpath_property
from fontTools.misc.cython import returns

from combinatorial_optimization_tools import *
from .bounded_quinton_master import *
from .bounded_quinton_dual_sub import *
from .bounded_quinton_primal_sub import *
from .bounded_quinton_auxilary_sub import *
import copy
from dataclasses import replace

class BoundedQuintonMagnantiWongBenders(MagnantiWongPapadakosBendersDecomposition):
    def   __init__(self, name, model_data):
        # Store the model data
        self.data = model_data

        # Initialize master problem
        master_problem = BoundedQuintonMaster(name + "_master", model_data)
        primal_sub_problem = BoundedQuintonPrimalSub(name + "_primal_sub", model_data)
        dual_sub_problem = BoundedQuintonDualSub(name + "_dual_sub", model_data)
        auxiliary_sub_problem = BoundedQuintonMagnantiWongSub(name + "_auxiliary_sub", model_data)

        super().__init__(name, master_problem, primal_sub_problem, dual_sub_problem, auxiliary_sub_problem)

    def _MagnantiWongPapadakosBendersDecomposition__extract_master_problem_results(self):
        """
        Extracts the relevant trail values from the master problem solution
        """

        self.master_problem_extract = copy.copy(self.master_problem.decision_vars)

        self.master_problem_extract.K = {x: round(y.solution_value)  for x, y in self.master_problem_extract.K.items()}
        self.master_problem_extract.m = {x: round(y.solution_value)  for x, y in self.master_problem_extract.m.items()}

        self.master_problem_extract.z = self.master_problem_extract.z.solution_value

    def _MagnantiWongPapadakosBendersDecomposition__calculate_core_point(self, iteration):
        """
        Obtains the core point for auxiliary sub problems
        """
        self.core_point = copy.copy(self.master_problem_extract)

        if iteration == 0:
            self.previous_core_point = copy.copy(self.core_point)

            self.core_point.K = {x: 0.5 * y for x, y in self.core_point.K.items()}
            self.core_point.m = {x: 0.5 * y for x, y in self.core_point.m.items()}
            self.core_point.z = 0.5 * self.core_point.z
        else:
            self.previous_core_point.K = copy.deepcopy(self.core_point.K)
            self.previous_core_point.m = copy.deepcopy(self.core_point.m)
            self.previous_core_point.z = copy.deepcopy(self.core_point.z)

            self.core_point.K = {x: 0.5 * self.previous_core_point.K[x] + 0.5 * self.core_point.K[x] for x in self.core_point.K.keys()}
            self.core_point.m = {x: 0.5 * self.previous_core_point.m[x] + 0.5 * self.core_point.m[x]  for x in self.core_point.m.keys()}
            self.core_point.z = 0.5 + self.previous_core_point.z + 0.5 * self.core_point.z


    def _MagnantiWongPapadakosBendersDecomposition__apply_cuts(self):
        """
        Construct and apply Benders Cuts
        """
        mdl = self.master_problem.model

        # Obtain variable solutions
        sub_problem_extract = copy.copy(self.auxiliary_sub_problem.decision_vars)

        pi_d = {x: y.solution_value for x, y in sub_problem_extract.pi_d.items()}
        pi_nr = {x: y.solution_value for x, y in sub_problem_extract.pi_nr.items()}
        pi_p = {x: y.solution_value for x, y in sub_problem_extract.pi_p.items()}
        pi_y1 = {x: y.solution_value for x, y in sub_problem_extract.pi_y1.items()}
        pi_y2 = {x: y.solution_value for x, y in sub_problem_extract.pi_y2.items()}


        K = self.master_problem.decision_vars.K
        m = self.master_problem.decision_vars.m
        z = self.master_problem.decision_vars.z

        # P1 as in Quinton et al. 2020
        P1 = max([self.master_problem.data.TASKS[a][r] for a in self.data.TASKS for r in self.data.TASKS[a]])

        # Traditional Benders optimality cut
        cut = (
                z <= (mdl.sum(pi_nr[i] * mdl.sum(m[(i, r)] / self.data.TASKS[i][r] for r in self.data.TASKS[i]) for i in
                              self.data.TASKS) +
                      mdl.sum(
                    pi_d[(ij[0], ij[1], r)] * (P1 * (2 - m[(ij[0], r)] - m[(ij[1], r)]) + K[(ij[0], ij[1])])
                    for ij in self.data.ALLOCATION_OVERLAP.keys() for r in self.data.ALLOCATION_OVERLAP[ij]) +
                      mdl.sum(pi_p[c] * self.data.DEPENDENCIES[c] for c in self.data.DEPENDENCIES) +
                      mdl.sum(pi_y2[(i, r)] * m[(i, r)] for i in self.data.TASKS for r in self.data.TASKS[i]))
        )

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


