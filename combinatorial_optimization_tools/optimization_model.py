import json
from abc import ABC, abstractmethod
from enum import Enum
from docplex.mp.model import *
from .model_data import *
from dataclasses import dataclass
import docplex.mp.conflict_refiner as cr
import matplotlib.pyplot as plt


@dataclass
class Transfer:
    endNode: int
    startingTime: int
    deadlineTime: int

class ProblemType(Enum):
    OPTIMIZATION_PROBLEM = 1
    FEASIBILITY_PROBLEM = 2

@dataclass
class DecisionVariables(ABC):
    pass

class OptimizationModel(ABC):
    def __init__(self, model_data, problem_type):
        # Shared optimization model state used by all formulations.
        self.problem_type = problem_type
        self.decision_vars = DecisionVariables()
        self.model = None
        self.res = None

        if not isinstance(model_data, ModelData):
            raise TypeError('model_data must be an instance of ModelData')

        self.data = model_data

    def setup_model(self, data):
        # Two-phase build: first declare variables, then add constraints.
        self.setup_variables()
        self.setup_constraints(data)
        pass

    @abstractmethod
    def setup_variables(self):
        pass

    @abstractmethod
    def setup_constraints(self, *data):
        pass

    @abstractmethod
    def solve(self, print_output):
        pass

    def print_figure(self):
        visu = self.__build_figure()

        visu.show()

    def save_figure(self, destination, filename):
        visu = self.__build_figure()
        if visu is not None:
            with Show(destination + filename + ".pdf"):
                visu.show()
            visu.close('all')

    def build_figure(self):
        pass

    def additional_output_information(self):
        pass

    @abstractmethod
    def get_objective(self):
        pass

    @abstractmethod
    def write_solution(self, destination, filename):
        pass


class CplexModel(OptimizationModel, ABC):
    def __init__(self, model_name, model_data, problem_type=ProblemType.OPTIMIZATION_PROBLEM):
        super().__init__(model_data, problem_type)

        # Backing docplex model instance.
        self.model = Model(model_name)
        # Time limit used for conflict refiner fallback when solve fails.
        self.conflict_ref_time_limit = 180

    def solve(self, print_output, time_limit = 1e+75):
        # Primary solve call.
        self.model.set_time_limit(time_limit)
        self.res = self.model.solve(log_output=print_output)

        if print_output:
            self.model.print_information()
            print(str(self.model.solve_details))
            print(self.res)

            try:
                self._OptimizationModel__additional_output_information()
            except:
                pass
        if self.res is None:
            # If no solution is found, run conflict refiner to explain infeasibility.
            self.model.set_time_limit(self.conflict_ref_time_limit)
            cref = cr.ConflictRefiner()
            print('Conflict refining')
            self.crefres = cref.refine_conflict(self.model, display=print_output)  # display flag is to show the conflicts
            self.model.set_time_limit(time_limit)

            if print_output:
                self.crefres.display()
        pass

    def get_objective(self):
        if hasattr(self.res, 'objective_value'):
            if self.res.objective_value is not None:
                return self.res.objective_value
            else:
                return ''
        else:
            return ''

    def get_status(self):
        if hasattr(self.res, 'solve_status'):
            if self.res.solve_status is not None:
                return self.res.solve_details.status
            else:
                return ''
        else:
            return self.model.solve_details.status

    def get_solve_time(self):
        if hasattr(self.res, 'solve_details'):
            if self.res.solve_details is not None:
                return self.res.solve_details.time
            else:
                return ''
        else:
            return ''

    def write_solution(self, destination, filename):
        # Write plain text solution for quick inspection.
        f = open(destination + filename + ".txt", "w")
        f.write(str(self.res))
        f.close()

        # Always export LP model for reproducibility/debugging.
        self.model.export_as_lp(destination + filename + ".lp")

        if self.model.solution is not None:
            # Export JSON and pretty-print for readability.
            self.model.solution.export(destination + filename + ".json")

            # Load the one-line JSON solution
            with open(destination + filename + ".json", 'r') as infile:
                result = json.load(infile)

            # Write it back with indentation
            with open(destination + filename + ".json", 'w') as outfile:
                json.dump(result, outfile, indent=4)


# Obtained via StackOverflow - Author: Daniel Junglas
class Show:
    '''Simple context manager to temporarily reroute plt.show().

    This context manager temporarily reroutes the plt.show() function to
    plt.savefig() in order to save the figure to the file specified in the
    constructor rather than displaying it on the screen.'''
    def __init__(self, name):
        self._name = name
        self._orig = None
    def _save(self):
        plt.savefig(self._name)
        if False:
            # Here we could show the figure as well
            self._orig()
    def __enter__(self):
        # Monkey patch plt.show so callers can reuse existing plotting code.
        self._orig = plt.show
        plt.show = lambda: self._save()
        return self
    def __exit__(self, type, value, traceback):
        if self._orig is not None:
            plt.show = self._orig
            self._orig = None
