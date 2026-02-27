from models.configuration import *

class BoundedMaster(CplexModel):

    def setup_variables(self, *args):
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
        self.decision_vars.x = mdl.binary_var_dict([(a, p) for a in self.data.TASKS.keys() for p in self.data.TASKS[a]], name='x') # Actor is on processor p
        self.decision_vars.y = mdl.binary_var_dict([(a1, a2, m1) for a1 in self.data.TASKS.keys() for a2 in self.data.TASKS.keys() if a1 != a2 for m1 in range(self.data.BOUND + 1)], name='y') # Actor a1 is before a2 in period m
        self.decision_vars.w = mdl.continuous_var_dict([a for a in self.data.TASKS], name='w', lb=0)
        self.decision_vars.mu = mdl.continuous_var(name='mu', lb=0)

        pass

    def setup_constraints(self, data):
        """
        Setup constraints for solving
        """
        mdl = self.model

        x = self.decision_vars.x
        y = self.decision_vars.y
        mu = self.decision_vars.mu
        w = self.decision_vars.w

        mu_ub = sum(max(self.data.TASKS[i][r] for r in self.data.TASKS[i]) for i in self.data.TASKS) #/self.data.NR_ACTORS*100

        M = max([self.data.TASKS[a][r] for a in self.data.TASKS for r in self.data.TASKS[a]]) * self.data.NR_TASKS * self.data.BOUND

        # Constraint (20)
        mdl.add_constraints(mdl.sum(x[a, p] for p in self.data.TASKS[a]) == 1 for a in self.data.TASKS)


        # Constraint (21)
        for c in self.data.DEPENDENCIES:
            mdl.add_constraint(
                w[c[1]] >= w[c[0]] - self.data.DEPENDENCIES[c] * mu_ub + mdl.sum(x[c[0], p] * self.data.TASKS[c[0]][p] for p in self.data.TASKS[c[0]]))

        # Constraints (22) & (23)
        for ij in self.data.ALLOCATION_OVERLAP.keys():
            for p in self.data.ALLOCATION_OVERLAP[ij]:
                for m1 in range(self.data.BOUND + 1):
                        mdl.add_constraint(
                            w[ij[0]] + self.data.TASKS[ij[0]][p] + m1 * mu_ub <= w[ij[1]] + M * (
                                    3 - x[(ij[0], p)] - x[(ij[1], p)] - y[(ij[0], ij[1], m1)]),
                        )
                        mdl.add_constraint(
                            w[ij[1]] + self.data.TASKS[ij[1]][p] <= w[ij[0]] + m1 * mu_ub + M * (
                                    2 - x[(ij[0], p)] - x[(ij[1], p)] + y[(ij[0], ij[1], m1)]),
                        )

        # Constraint (25)
        for t1 in self.data.TASKS.keys():
            mdl.add(
                w[t1] + mdl.sum(x[t1, p] * self.data.TASKS[t1][p] for p in self.data.TASKS[t1]) <= w[t1] + mu_ub)

        mdl.minimize(mu)

        pass

