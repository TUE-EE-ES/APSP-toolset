import models.bounded.bounded_monolithic as bounded_monolithic
import models.bounded.bounded_Benders as bounded_Benders
import models.Quinton.Quinton_monolithic as Quinton_monolithic
import models.Quinton.Quinton_Benders as Quinton_Benders
import models.bounded.bounded_Quinton_monolithic as bounded_Quinton_monolithic
import models.bounded.bounded_Quinton_Benders as bounded_Quinton_Benders
from models.utilities import *
import pandas as pd

# Path to one graph instance used for manual runs.
filepath = os.path.abspath(os.getcwd()) + "/benchmark/graphs/"
filename = "graph__10-1000-0.10-02_0.xml"

# Global solve settings.
timeout = 3600
iterations = 1000000

# Unified result table for all formulations.
RESULTS = pd.DataFrame(columns=[
    "Quinton Monolithic Time",  "Quinton Monolithic Objective", "Quinton Monolithic Status",
    "Bounded Monolithic Time", "Bounded Monolithic Objective", "Bounded Monolithic Status",
    "Bounded Quinton Monolithic Time", "Bounded Quinton Monolithic Objective", "Bounded Quinton Monolithic Status",
    "Quinton Benders Time", "Quinton Benders Iterations", "Quinton Benders Objective", "Quinton Benders Status",
    "Bounded Benders Time", "Bounded Benders Iterations","Bounded Benders Objective", "Bounded Benders Status",
    "Bounded Quinton Benders Time", "Bounded Quinton Benders Iterations", "Bounded Quinton Benders Objective", "Bounded Quinton Benders Status",
                                ])

# Parse instance data from XML.
data = APSPModelData(filepath, filename)

# Initialize placeholders to keep schema stable even when runs are disabled.
qm_time, qm_objective, qm_status = [1, 1, "NaN"]
om_time, om_objective, om_status = [1, 1, "NaN"]
qmb_time, qmb_objective, qmb_status = [1, 1, "NaN"]
qb_time, qb_it, qb_objective, qb_status = [1, 0, 1, "NaN"]
ob_time, ob_it, ob_objective, ob_status = [1, 0, 1, "NaN"]
qbb_time, qbb_it, qbb_objective, qbb_status = [1, 0, 1, "NaN"]

# Toggle guide:
# - To ENABLE a technique, uncomment the full block under its header.
# - To DISABLE a technique, keep that full block commented.


# [ENABLED] comment this full block to disable
print('Quinton Monolithic')
model = Quinton_monolithic.QuintonMonolithic('Quinton Monolithic', data)
model.setup_model("")
model.solve(False, time_limit=timeout)

qm_time = model.get_solve_time()
qm_objective = 1 / model.get_objective()
qm_status = model.get_status()
model.print_figure()
model.additional_output_information()
model.print_figure()
# ----------------------------


# [ENABLED] comment this full block to disable
print('Bounded Monolithic')
model = bounded_monolithic.BoundedMonolithic('Bounded Monolithic', data)
model.setup_model("")
model.solve(True, time_limit=timeout)

om_time = model.get_solve_time()
om_objective = model.get_objective()
om_status = model.get_status()
model.print_figure()
# ----------------------------


# [ENABLED] comment this full block to disable
print('Bounded Quinton Monolithic')
model = bounded_Quinton_monolithic.BoundedQuintonMonolithic('Bounded Quinton Monolithic', data)
model.setup_model("")
model.solve(True, time_limit=timeout)

qmb_time = model.get_solve_time()
qmb_objective = 1 / model.get_objective()
qmb_status = model.get_status()
model.print_figure()
# ----------------------------


# [DISABLED] uncomment this full block to enable
print('Quinton Benders')
model = Quinton_Benders.QuintonMagnantiWongBenders('Quinton Benders', data)
model.set_iterations(iterations)
model.solve(True, log_verbosity=1, time_out=timeout)

qb_time = model.get_solve_time()
qb_it = model.iteration
qb_objective = 1 / model.get_objective()
qb_status = model.get_status()
model.additional_output_information()
model.print_figure()
# ----------------------------


# [ENABLED] comment this full block to disable
print('Bounded Benders')
model = bounded_Benders.BoundedMagnantiWongBenders('Bounded Benders', data)
model.set_iterations(iterations)
model.solve(True, log_verbosity=2, time_out=timeout)

ob_time = model.get_solve_time()
ob_it = model.iteration
ob_objective = model.get_objective()
ob_status = model.get_status()
model.print_figure()
# ----------------------------


# [ENABLED] comment this full block to disable
print('Bounded Quinton Benders')
model = bounded_Quinton_Benders.BoundedQuintonMagnantiWongBenders('Bounded Quinton Benders', data)
model.set_iterations(iterations)
model.solve(True, log_verbosity=1, time_out=timeout)

qbb_time = model.get_solve_time()
qbb_it = model.iteration
qbb_objective = 1/model.get_objective()
qbb_status = model.get_status()
model.additional_output_information()
model.print_figure()
# ----------------------------

# Store one row per instance using the fixed RESULTS schema.
RESULTS.loc[filename[:-4]] = [qm_time, qm_objective, qm_status,
                              om_time, om_objective, om_status,
                              qmb_time, qmb_objective, qmb_status,
                              qb_time, qb_it, qb_objective, qb_status,
                              ob_time, ob_it, ob_objective, ob_status,
                              qbb_time, qbb_it, qbb_objective, qbb_status,
                              ]

# Print full dataframe
pd.set_option('display.max_columns', None)
pd.set_option('display.width',1000)

print(RESULTS)
