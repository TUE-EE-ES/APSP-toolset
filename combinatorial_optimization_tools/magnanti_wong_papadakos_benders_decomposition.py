import copy

from cplex import CplexError

from .optimization_model import *
from enum import Enum
import time
from interruptingcow import timeout

class MagnantiWongPapadakosBendersDecomposition(ABC):
    def __init__(self, name, master_problem, primal_sub_problem, dual_sub_problem, auxiliary_sub_problem, epsilon=1e-9):
        """
        Initialize Magnanti-Wong Benders Decomposition variables with the core point definition by Papadakos
        """
        self.name = name
        self.print_output = False

        # Global LB/UB bounds for Benders convergence checks.
        self.upper_bound = float('inf')
        self.lower_bound = float('-inf')
        self.epsilon = epsilon

        self.status = "optimal solution"

        self.master_problem_extract = None

        self.iteration = None
        self.iterations = 1000 # Default maximum number of iterations

        if not isinstance(master_problem, CplexModel):
            raise TypeError('Master problem must be an instance of CplexModel')
        if not isinstance(dual_sub_problem, CplexModel):
            raise TypeError('Sub-problem must be an instance of CplexModel')
        if not isinstance(primal_sub_problem, CplexModel) :
            raise TypeError('Sub-problem must be an instance of CplexModel')
        if not isinstance(auxiliary_sub_problem, CplexModel) :
            raise TypeError('Sub-problem must be an instance of CplexModel')


        self.master_problem = master_problem
        self.dual_sub_problem = dual_sub_problem
        self.best_master_problem = None
        self.best_master_problem_extract = None
        self.best_dual_sub_problem = None

        self.primal_sub_problem = primal_sub_problem
        self.auxiliary_sub_problem = auxiliary_sub_problem

        # Create fresh model instances for master/primal templates.
        self.master_problem.model = Model(self.master_problem.model.name)
        self.primal_sub_problem.model = Model(self.primal_sub_problem.model.name)

        self.master_problem.setup_variables()
        self.primal_sub_problem.setup_variables()

        self.master_problem.setup_constraints(0)

        self.core_point = None
        self.previous_core_point = None

        self.solve_time = None
        self.iteration_count = 0

        self.log_verbosity = 2



    def set_iterations(self, iterations):
        """
        Specify max number of iterations before solving terminates
        """
        self.iterations = iterations

    def solve(self, print_output, log_verbosity=0, time_out=None, log_destination = "", log_file_name = "log"):
        self.log_verbosity = log_verbosity

        if not print_output:
            self.log_verbosity = 0

        """
        Solves the LBBD procedure
        """
        start_time = time.time()
        self.print_output = print_output

        # Start iterative LBBD procedure.
        try:
            if time_out is None:
                self.__solve(print_output, log_verbosity, start_time, time_out)
            else:
                self.__solve(print_output, log_verbosity, start_time, time_out)
        except RuntimeError:
            self.status =  "time limit exceeded"
        except CplexError:
            self.status = "solver error"
            self.write_error_log(log_destination, log_file_name)
        except Exception as e:
            print(f"Error during solve: {e}")
            self.write_error_log(log_destination, log_file_name)

        end_time = time.time()
        self.solve_time = end_time - start_time

    def __solve(self, print_output, log_verbosity, start_time, time_out):
        for iteration in range(self.iterations):

            # Global timeout check for the full decomposition loop.
            if (time_out - (time.time() - start_time)) <= 0:
                 raise RuntimeError("Timeout exceeded")

            self.iteration = iteration

            # Build and solve master, then evaluate subproblems for current trial point.
            if self.log_verbosity == 2:
                print(
                    "________________________________________________________ "
                    + "BENDERS "
                    + self.name
                    + " ITERATION "
                    + str(iteration)
                    + " ________________________________________________________"
                )

                print("Adding cuts to " + self.name + "...")

            # Add all Benders cuts (none are available in iteration 0).
            if iteration > 0:
                self.__apply_cuts()

            if self.log_verbosity == 2:
                print(
                    "Master "
                    + self.name
                    + " ITERATION "
                    + str(iteration)
                    + " ________________________________________________________"
                )

            # Solve master problem for current iteration.
            if time_out is not None:
                self.master_problem.solve(print_output=self.log_verbosity == 2, time_limit= max(1, time_out - (time.time() - start_time)))
            else:
                self.master_problem.solve(print_output=self.log_verbosity == 2)

            self.status = "master problem " + self.master_problem.get_status()

            # Optional per-iteration exports can be enabled for debugging.
            # self.master_problem.write_solution('benders/benders-new/test/', 'iteration' + str(iteration))

            # Extract trial values from master solution.
            self.__extract_master_problem_results()

            # Rebuild dual subproblem with fixed master trial values.
            if isinstance(self.dual_sub_problem, OptimizationModel):
                self.dual_sub_problem.model = Model(self.dual_sub_problem.model.name)
                self.dual_sub_problem.setup_variables()
                self.dual_sub_problem.setup_constraints(self.master_problem_extract)

            # Solve dual subproblem.
            if isinstance(self.dual_sub_problem, OptimizationModel):
                if self.log_verbosity == 2:
                    print(
                        "Sub "
                        + self.name
                        + " ITERATION "
                        + str(iteration)
                        + " ________________________________________________________"
                    )
                if (time_out - (time.time() - start_time)) <= 0:
                    raise RuntimeError("Timeout exceeded")

                if time_out is not None:
                    self.dual_sub_problem.solve(print_output=self.log_verbosity == 2, time_limit= max(1, time_out - (time.time() - start_time)))
                else:
                    self.dual_sub_problem.solve(print_output=self.log_verbosity == 2)

                self.status = "dual sub problem " + self.dual_sub_problem.get_status()

            # Update core point after solving the dual subproblem.
            self.__calculate_core_point(iteration)

            # Rebuild auxiliary Magnanti-Wong subproblem.
            if isinstance(self.dual_sub_problem, OptimizationModel):
                self.auxiliary_sub_problem.model = Model(self.auxiliary_sub_problem.model.name)
                self.auxiliary_sub_problem.setup_variables()
                self.auxiliary_sub_problem.setup_constraints(self.master_problem_extract, self.core_point,
                                                             self.dual_sub_problem.get_objective())

            # Solve auxiliary subproblem to obtain stronger cut multipliers.
            if isinstance(self.auxiliary_sub_problem, OptimizationModel):
                if self.log_verbosity == 2:
                    print(
                        "Magnanti Sub "
                        + self.name
                        + " ITERATION "
                        + str(iteration)
                        + " ________________________________________________________"
                    )
                if (time_out - (time.time() - start_time)) <= 0:
                    raise RuntimeError("Timeout exceeded")

                if time_out is not None:
                    self.auxiliary_sub_problem.solve(print_output=self.log_verbosity == 2, time_limit= max(1, time_out - (time.time() - start_time)))
                else:
                    self.auxiliary_sub_problem.solve(print_output=self.log_verbosity == 2)

                self.status = "aux sub problem " + self.auxiliary_sub_problem.get_status()


            if self.master_problem.model.objective_sense == ObjectiveSense.Maximize:
                # Master gives UB, dual sub gives LB for maximization.
                self.upper_bound = self.master_problem.get_objective()
                current_lb = self.lower_bound
                self.lower_bound = max(self.lower_bound, self.dual_sub_problem.get_objective())

                if self.lower_bound == self.dual_sub_problem.get_objective():
                    self.best_dual_sub_problem = copy.copy(self.dual_sub_problem)
                    self.best_master_problem = copy.copy(self.master_problem)
                    self.best_master_problem_extract = copy.copy(self.master_problem_extract)

            elif self.master_problem.model.objective_sense == ObjectiveSense.Minimize:
                # Mirror of above for minimization.
                self.upper_bound = min(self.upper_bound, self.dual_sub_problem.get_objective())
                self.lower_bound = self.master_problem.get_objective()

                if self.upper_bound == self.dual_sub_problem.get_objective():
                    self.best_dual_sub_problem = copy.copy(self.dual_sub_problem)
                    self.best_master_problem = copy.copy(self.master_problem)
                    self.best_master_problem_extract = copy.copy(self.master_problem_extract)


            if self.log_verbosity == 1:
                print("Iteration: " + str(iteration))
                print("Elapsed time: " + str(round(time.time() - start_time, 2)) + " seconds\n")
                print("Upperbound: " + str(self.upper_bound))
                print("Lowerbound: " + str(self.lower_bound))
                print("Completion: " + str(self.__check_completion(iteration)))
                print("--------------------------\n")


            if (time_out - (time.time() - start_time)) <= 0:
                raise RuntimeError("Timeout exceeded")

            if self.__check_completion(iteration):
                self.iteration_count = iteration
                break

        if self.iteration >= self.iterations - 1:
            self.status = "iteration limit exceeded"

    def __check_completion(self, i):
        """
        Check if LBBD procedure can finish
        """
        # Stop when optimality gap is within epsilon.
        if self.upper_bound - self.lower_bound < self.epsilon:
            self.status = "optimal solution"
            return True
        else:
            return False

    @abstractmethod
    def __extract_master_problem_results(self):
        """
         Extracts the relevant trail values from the mater problem solution results
        """
        pass

    @abstractmethod
    def __apply_cuts(self):
        """
        Applies logic based benders cuts
        """
        pass

    @abstractmethod
    def __calculate_core_point(self, iteration):
        pass

    def print_figure(self):
        """
        Prints figure of solution
        """
        visu = self.build_figure()

        visu.show()

    def save_figure(self, destination, filename):
        """
        Saves figure of solution at /destination/filename.pdf
        """
        visu = self.build_figure()

        if visu is not None:
            with Show(destination + filename + ".pdf"):
                visu.show()
            visu.close('all')

    @abstractmethod
    def build_figure(self):
        """
        Creates a figure of solution
        """
        pass

    def get_status(self):
        return self.status

    def get_objective(self):
        """
        Returns the objective value of master problem solution
        """
        if self.master_problem.model.objective_sense == ObjectiveSense.Maximize:
            return self.lower_bound
        elif self.master_problem.model.objective_sense == ObjectiveSense.Minimize:
            return self.upper_bound

    def get_solve_time(self):
        """
        Returns the solve time
        """
        return self.solve_time

    def get_iteration_count(self):
        """
        Returns the iteration count
        """
        return self.iteration_count

    def write_solution(self, destination, filename):
        """
        Writes a textual solution to /destination/filename(_master/_sub).txt
        """
        self.best_master_problem.write_solution(destination, filename + '_master')
        self.best_dual_sub_problem.write_solution(destination, filename + '_sub')
        self.auxiliary_sub_problem.write_solution(destination, filename + '_aux')

        self.primal_sub_problem.setup_constraints(self.best_master_problem_extract)
        self.primal_sub_problem.solve(True)

        self.primal_sub_problem.write_solution(destination, filename + '_primal_sub')

    def write_error_log(self, destination, filename):
        """
        Writes a textual solution to /destination/filename(_master/_sub).txt
        """
        error_log_destination = destination + "error_log/"

        if not os.path.isdir(error_log_destination):
            os.makedirs(error_log_destination)

        self.master_problem.write_solution(error_log_destination, filename + '_master_ERRORLOG')
        self.dual_sub_problem.write_solution(error_log_destination, filename + '_sub_ERRORLOG')
        self.auxiliary_sub_problem.write_solution(error_log_destination, filename + '_aux_ERRORLOG')
        self.primal_sub_problem.setup_constraints(self.best_master_problem_extract)
        self.primal_sub_problem.solve(False)
        self.primal_sub_problem.write_solution(error_log_destination, filename + '_primal_sub_ERRORLOG')
