from combinatorial_optimization_tools import *
from models.configuration import *

class BoundedQuintonMagnantiWongSub(CplexModel):

    def setup_variables(self):
        """
        Setup decision variables and solver parameters
        """
        mdl = self.model
        # Set solver parameters
        APSPParameters(mdl)
        # Set solver precision

        mdl.parameters.simplex.tolerances.optimality = 1e-9

        # Create dual decision vars
        self.decision_vars.pi_nr = mdl.continuous_var_dict([(i) for i in self.data.TASKS], name='pi_nr', lb=0)
        self.decision_vars.pi_p = mdl.continuous_var_dict([(c[0], c[1]) for c in self.data.DEPENDENCIES], name='pi_p', lb=0)
        self.decision_vars.pi_d = mdl.continuous_var_dict(
            [
                (ij[0], ij[1], r)
                for ij in self.data.ALLOCATION_OVERLAP.keys()
                for r in self.data.ALLOCATION_OVERLAP[ij]
            ], name='pi_d', lb=0
        )
        self.decision_vars.pi_y1 = mdl.continuous_var_dict([(i) for i in self.data.TASKS], name='pi_y1', lb=-mdl.infinity)
        self.decision_vars.pi_y2 = mdl.continuous_var_dict([(i, r) for i in self.data.TASKS for r in self.data.TASKS[i]], name='pi_y2', lb=0)
        self.decision_vars.tau = mdl.continuous_var(name='tau')#, lb=1e-9)  # Linearized period to minimize

        pass

    def setup_constraints(self, *data):
        """
        Setup constraints for solving
        """
        mdl = self.model

        pi_nr = self.decision_vars.pi_nr
        pi_p = self.decision_vars.pi_p
        pi_d  = self.decision_vars.pi_d
        pi_y1 = self.decision_vars.pi_y1
        pi_y2 = self.decision_vars.pi_y2
        tau = self.decision_vars.tau

        # Get previous subproblem solutions
        m_bar = data[0].m
        K_bar = data[0].K

        m_core = data[1].m
        K_core = data[1].K

        z_star = data[2]

        # P1 as in Quinton et al. 2020
        P1 = max([self.data.TASKS[a][r] for a in self.data.TASKS for r in self.data.TASKS[a]])

        # Constraint (11a) in Quinton et al. 2020
        mdl.add(
            (mdl.sum(pi_nr[i] * mdl.sum(m_bar[(i, r)] / self.data.TASKS[i][r] for r in self.data.TASKS[i]) for i in
                     self.data.TASKS) +
             mdl.sum(
                pi_d[(ij[0], ij[1], r)] * (P1 * (2 - m_bar[(ij[0], r)] - m_bar[(ij[1], r)]) + K_bar[(ij[0], ij[1])]) for
                ij in self.data.ALLOCATION_OVERLAP.keys() for r in self.data.ALLOCATION_OVERLAP[ij]) +
             mdl.sum(pi_p[c] * self.data.DEPENDENCIES[c] for c in self.data.DEPENDENCIES) +
             mdl.sum(pi_y2[(i, r)] * m_bar[(i, r)] for i in self.data.TASKS for r in self.data.TASKS[i])) == z_star
        )

        # Constraint (10a) in Quinton et al. 2020
        mdl.add(mdl.sum(pi_nr[i] - pi_y1[i] for i in self.data.TASKS) >= 1)

        for i in self.data.TASKS:
            # Constraint (10b) in Quinton et al. 2020
            mdl.add(
                mdl.sum(pi_p[c] for c in self.data.DEPENDENCIES if c[0] == i) -
                mdl.sum(pi_p[c] for c in self.data.DEPENDENCIES if c[1] == i) +
                mdl.sum(pi_d[(ij[0], ij[1], r)] for ij in self.data.ALLOCATION_OVERLAP.keys() if ij[0] == i for r in self.data.ALLOCATION_OVERLAP[ij]) -
                mdl.sum(pi_d[(ij[0], ij[1], r)] for ij in self.data.ALLOCATION_OVERLAP.keys() if ij[1] == i for r in self.data.ALLOCATION_OVERLAP[ij]) >= 0
            )

            for r in self.data.TASKS[i]:
                # Constraint (10c) in Quinton et al. 2020
                mdl.add(
                    mdl.sum(pi_p[c] * self.data.TASKS[i][r] for c in self.data.DEPENDENCIES if c[0] == i) +
                    mdl.sum(pi_d[(ij[0], ij[1], r)] * self.data.TASKS[i][r] for ij in self.data.ALLOCATION_OVERLAP.keys() if ij[0] == i and r in self.data.ALLOCATION_OVERLAP[ij]) +
                    pi_y2[i,r] + pi_y1[i]
                    >= 0
                )

        # Constraint (11) in Quinton et al. 2020
        mdl.minimize(
            mdl.sum(pi_nr[i] * mdl.sum(m_core[(i,r)] / self.data.TASKS[i][r] for r in self.data.TASKS[i]) for i in self.data.TASKS) +
            mdl.sum(pi_d[(ij[0], ij[1], r)]*(P1*(2 - m_core[(ij[0], r)] - m_core[(ij[1], r)]) + K_core[(ij[0], ij[1])]) for ij in self.data.ALLOCATION_OVERLAP.keys() for r in self.data.ALLOCATION_OVERLAP[ij]) +
            mdl.sum(pi_p[c] * self.data.DEPENDENCIES[c] for c in self.data.DEPENDENCIES) +
            mdl.sum(pi_y2[(i, r)] * m_core[(i, r)] for i in self.data.TASKS for r in self.data.TASKS[i])
        )




