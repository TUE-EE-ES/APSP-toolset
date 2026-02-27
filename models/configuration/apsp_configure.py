from combinatorial_optimization_tools import *

class APSPConfigure():
    '''
    Configurations settings

    - Set number of repetitions to visualize
    - Set optional time units to add to the x-axis label
    - Choose 1 of 3 different modes:
        1. SDF3
            - Naming matches SDF3
            - Variable naming
                Tasks (Actors): a0, a1, a2 .....
                Resources (Processors): proc_0, proc_1, proc_2 .....
            - Plain figure styling
        2. PAPER
            - Naming matches with terms introduced in the paper
            - Variable naming
                Tasks: t0, t1, t2 .....
                Processors: r0, r1, r2 .....
            - Figure styling matches with Figure 2 in the paper
        2. PAPER
            - Custom variable naming
                Tasks: custom_task_name0, custom_task_name1, custom_task_name2 .....
                Resources: custom_resource_name0, custom_resource_name1, custom_resource_name2 .....
            - Plain figure styling
    '''

    class APSPConfig(Enum):
        SDF3 = 1,
        PAPER = 2,
        CUSTOM = 3

    def __init__(self):
        self.figure_repetitions = 3
        self.time_units = "($\mu s$)" # optional

        self.mode = APSPConfigure.APSPConfig.PAPER # Set configuration mode
        self.custom_task_name = "tasks" # Set custom task name (if mode = CUSTOM)
        self.custom_resource_name = "resources" # Set custom task name (if mode = CUSTOM)



