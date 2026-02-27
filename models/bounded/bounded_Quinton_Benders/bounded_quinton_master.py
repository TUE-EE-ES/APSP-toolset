from combinatorial_optimization_tools import *
from models.configuration import *

class BoundedQuintonMaster(CplexModel):

    def setup_variables(self):
        """
        Setup decision variables and solver parameters
        """
        mdl = self.model
        # Set solver parameters
        APSPParameters(mdl)
        # Set solver precision
        mdl.parameters.simplex.tolerances.optimality = 1e-9

        # Define bound from Theorem 1
        self.data.BOUND = self.data.NR_RESOURCES + self.data.NR_TASKS

        # Create decision vars
        self.decision_vars.K = mdl.integer_var_dict([(a1, a2) for a1 in self.data.TASKS for a2 in self.data.TASKS if a1 != a2], name='K',
                                                    lb=-self.data.BOUND, ub=self.data.BOUND)  # Repetition distance between two tasks
        self.decision_vars.m = mdl.binary_var_dict([(a, r) for a in self.data.TASKS for r in self.data.TASKS[a]], name='m')  # Task allocated on a resource
        self.decision_vars.z = mdl.continuous_var(name='z') # Upper bound on tau
        self.decision_vars.w = mdl.continuous_var_dict([i for i in self.data.TASKS], name='w', lb=0) # Linearized feasible start time of each task
        pass

    def setup_constraints(self, data):
        """
        Setup constraints for solving
        """
        mdl = self.model


        K = self.decision_vars.K
        m = self.decision_vars.m
        z = self.decision_vars.z
        w = self.decision_vars.w


        for a in self.data.TASKS:
            # Constraint (7a) in Quinton et al. 2020
            mdl.add(mdl.sum(m[(a, r)] for r in self.data.TASKS[a]) == 1)

        for ij in self.data.ALLOCATION_OVERLAP.keys():
            # Constraint (7b) in Quinton et al. 2020
            mdl.add(K[ij[0], ij[1]] + K[ij[1], ij[0]] == 1)

        # Limit z to a finite domain for the first iteration
        mdl.add(z <= (1e+20) - 1e10)

        # T_lb and P1 as in Quinton et al. 2020
        T_lb = 1/sum(max(self.data.TASKS[i][r] for r in self.data.TASKS[i]) for i in self.data.TASKS)
        P1 = max([self.data.TASKS[a][r] for a in self.data.TASKS for r in self.data.TASKS[a]])

        for i in self.data.TASKS:
            for r in self.data.TASKS[i]:
                # Constraint (8a) in Quinton et al. 2020
                mdl.add(P1 * (1 - m[(i,r)]) + w[c[1]] + self.data.DEPENDENCIES[c] >= w[c[0]] + T_lb * self.data.TASKS[i][r] for c in self.data.DEPENDENCIES if c[0] == i)
                # Constraint (8b) in Quinton et al. 2020
                mdl.add(P1*(2 - m[(i,r2)] - m[(ij[1],r2)]) + w[ij[1]] + K[ij] >= w[ij[0]] + T_lb*self.data.TASKS[i][r]
                        for ij in self.data.ALLOCATION_OVERLAP.keys() if ij[0] == i
                        for r2 in self.data.ALLOCATION_OVERLAP[ij] if r2 == r
                        )
        # Objective function as in Quinton et al. 2020
        mdl.maximize(z)
        pass
