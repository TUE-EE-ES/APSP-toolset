from models.configuration import *

class BoundedMagnantiWongSub(CplexModel):

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

        # Create dual decision vars
        lb = 0
        self.decision_vars.pi_p = mdl.continuous_var_dict([(c[0], self.data.DEPENDENCIES[c], c[1]) for c in self.data.DEPENDENCIES], name='pi_p', lb=lb)
        self.decision_vars.pi_nl = mdl.continuous_var_dict([(ij[0], ij[1], p, m)
                                                       for ij in self.data.ALLOCATION_OVERLAP.keys()
                                                       for p in self.data.ALLOCATION_OVERLAP[ij]
                                                       for m in range(self.data.BOUND + 1)
                                                        ], name='pi_nl', lb=lb)
        self.decision_vars.pi_nr = mdl.continuous_var_dict([(ij[0], ij[1], p, m)
                                                       for ij in self.data.ALLOCATION_OVERLAP.keys()
                                                       for p in self.data.ALLOCATION_OVERLAP[ij]
                                                       for m in range(self.data.BOUND + 1)
                                                       ], name='pi_nr', lb=lb)
        self.decision_vars.pi_nd = mdl.continuous_var_dict([a for a in self.data.TASKS if 0 not in self.data.TASKS[a].values()], name='pi_nd', lb=lb)
        self.decision_vars.pi_s = mdl.continuous_var_dict([a for a in self.data.TASKS], name='pi_s', lb=lb)

    def setup_constraints(self, *data):
        """
        Setup constraints for solving
        """
        mdl = self.model

        pi_p = self.decision_vars.pi_p
        pi_nl = self.decision_vars.pi_nl
        pi_nr = self.decision_vars.pi_nr
        pi_nd = self.decision_vars.pi_nd
        pi_s = self.decision_vars.pi_s

        # Get previous subproblem solutions
        x_bar = data[0].x
        y_bar = data[0].y

        x_core = data[1].x
        y_core = data[1].y

        ob_bar = data[2]

        M = max([self.data.TASKS[a][r] for a in self.data.TASKS for r in self.data.TASKS[a]]) * self.data.NR_TASKS * self.data.BOUND

        # Constraint (33)
        mdl.add(
            mdl.sum(self.data.DEPENDENCIES[c] * pi_p[(c[0], self.data.DEPENDENCIES[c], c[1])] for c in
                    self.data.DEPENDENCIES) -
            mdl.sum(m * pi_nl[(ij[0], ij[1], p, m)]
                    for ij in self.data.ALLOCATION_OVERLAP.keys()
                    for p in self.data.ALLOCATION_OVERLAP[ij]
                    for m in range(self.data.BOUND + 1)) +
            mdl.sum(m * pi_nr[(ij[0], ij[1], p, m)]
                    for ij in self.data.ALLOCATION_OVERLAP.keys()
                    for p in self.data.ALLOCATION_OVERLAP[ij]
                    for m in range(self.data.BOUND + 1)) +
            mdl.sum(pi_nd[a] for a in self.data.TASKS if 0 not in self.data.TASKS[a].values()) +
            mdl.sum(self.data.BOUND * pi_s[a] for a in self.data.TASKS) <= 1
        )

        # Constraint (34)
        for a1 in self.data.TASKS:
            mdl.add(
                mdl.sum(pi_p[(c[0], self.data.DEPENDENCIES[c], c[1])] for c in
                        self.data.DEPENDENCIES if c[1] == a1) -
                mdl.sum(pi_p[(c[0], self.data.DEPENDENCIES[c], c[1])] for c in
                        self.data.DEPENDENCIES if c[0] == a1) +
                mdl.sum(pi_nl[(ij[0], ij[1], p, m)]
                        for ij in self.data.ALLOCATION_OVERLAP.keys() if ij[1] == a1
                        for p in self.data.ALLOCATION_OVERLAP[ij]
                        for m in range(self.data.BOUND + 1)) -
                mdl.sum(pi_nl[(ij[0], ij[1], p, m)]
                        for ij in self.data.ALLOCATION_OVERLAP.keys() if ij[0] == a1
                        for p in self.data.ALLOCATION_OVERLAP[ij]
                        for m in range(self.data.BOUND + 1)) +
                mdl.sum(pi_nr[(ij[0], ij[1], p, m)]
                        for ij in self.data.ALLOCATION_OVERLAP.keys() if ij[0] == a1
                        for p in self.data.ALLOCATION_OVERLAP[ij]
                        for m in range(self.data.BOUND + 1)) -
                mdl.sum(pi_nr[(ij[0], ij[1], p, m)]
                        for ij in self.data.ALLOCATION_OVERLAP.keys() if ij[1] == a1
                        for p in self.data.ALLOCATION_OVERLAP[ij]
                        for m in range(self.data.BOUND + 1)) -
                pi_s[a1] <= 0
            )

        # Constraint (37)
        mdl.add((
                        mdl.sum(pi_p[(c[0], self.data.DEPENDENCIES[c], c[1])] * mdl.sum(
                x_bar[(c[0], p)] * self.data.TASKS[c[0]][p] for p in self.data.TASKS[c[0]]) for c in
                                self.data.DEPENDENCIES) +
                        mdl.sum(pi_nl[(ij[0], ij[1], p, m)] * (self.data.TASKS[ij[0]][p] - M * (
                    3 - x_bar[(ij[0], p)] - x_bar[(ij[1], p)] - y_bar[(ij[0], ij[1], m)]))
                    for ij in self.data.ALLOCATION_OVERLAP.keys()
                    for p in self.data.ALLOCATION_OVERLAP[ij]
                    for m in range(self.data.BOUND + 1)) +
                        mdl.sum(pi_nr[(ij[0], ij[1], p, m)] * (self.data.TASKS[ij[1]][p] - M * (
                    2 - x_bar[(ij[0], p)] - x_bar[(ij[1], p)] + y_bar[(ij[0], ij[1], m)]))
                    for ij in self.data.ALLOCATION_OVERLAP.keys()
                    for p in self.data.ALLOCATION_OVERLAP[ij]
                    for m in range(self.data.BOUND + 1)) +
                        mdl.sum(
                pi_nd[a] * mdl.sum(x_bar[(a, p)] * self.data.TASKS[a][p] for p in self.data.TASKS[a]) for
                a in
                self.data.TASKS if 0 not in self.data.TASKS[a].values())) == ob_bar
                )

        # Constraint (36)
        mdl.maximize(
            mdl.sum(pi_p[(c[0], self.data.DEPENDENCIES[c], c[1])] * mdl.sum(
                x_core[(c[0], p)] * self.data.TASKS[c[0]][p] for p in self.data.TASKS[c[0]]) for c in
                    self.data.DEPENDENCIES) +
            mdl.sum(pi_nl[(ij[0], ij[1], p, m)] * (self.data.TASKS[ij[0]][p] - M * (3 - x_core[(ij[0], p)] - x_core[(ij[1], p)] - y_core[(ij[0], ij[1], m)]))
                    for ij in self.data.ALLOCATION_OVERLAP.keys()
                    for p in self.data.ALLOCATION_OVERLAP[ij]
                    for m in range(self.data.BOUND + 1)) +
            mdl.sum(pi_nr[(ij[0], ij[1], p, m)] * (self.data.TASKS[ij[1]][p] - M * (2 - x_core[(ij[0], p)] - x_core[(ij[1], p)] + y_core[(ij[0], ij[1], m)]))
                    for ij in self.data.ALLOCATION_OVERLAP.keys()
                    for p in self.data.ALLOCATION_OVERLAP[ij]
                    for m in range(self.data.BOUND + 1)) +
            mdl.sum(pi_nd[a] * mdl.sum(x_core[(a,p)] * self.data.TASKS[a][p] for p in self.data.TASKS[a]) for a in self.data.TASKS if 0 not in self.data.TASKS[a].values())
        )

        pass
