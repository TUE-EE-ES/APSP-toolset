from combinatorial_optimization_tools import *

class APSPParameters():
    ''' Choose solver settings'''
    def __init__(self, mdl):
        mdl.context.cplex_parameters.emphasis.mip = 2 # Focus on optimality
        mdl.parameters.emphasis.numerical = 1 # Numerical precision




