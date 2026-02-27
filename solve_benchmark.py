import json
import os
import pandas as pd

import models.bounded.bounded_monolithic as bounded_monolithic
import models.bounded.bounded_Benders as bounded_Benders
import models.Quinton.Quinton_monolithic as Quinton_monolithic
import models.Quinton.Quinton_Benders as Quinton_Benders
import models.bounded.bounded_Quinton_monolithic as bounded_Quinton_monolithic
import models.bounded.bounded_Quinton_Benders as bounded_Quinton_Benders
from models.configuration import *
from models.utilities import *

# Benchmark configuration.
experiments_folder = "/benchmark_full/" # or "/benchmark_shortened/"
timeout = 3600
iterations = 1000000

# Create benchmark input and results folders.
experiments_path = os.path.abspath(os.getcwd()) + experiments_folder
if not os.path.isdir(experiments_path):
    raise OSError("No experiment folder named '" + experiments_path + "'")

graph_path = os.path.abspath(os.getcwd()) + experiments_folder + "graphs/"
if not os.path.isdir(graph_path):
    raise OSError("Experiments has no graphs")


results_path = os.path.abspath(os.getcwd()) + experiments_folder + "results/"
if not os.path.isdir(results_path):
    os.makedirs(results_path)


figures_path = os.path.abspath(os.getcwd()) + experiments_folder + "figures/"
if not os.path.isdir(figures_path):
    os.makedirs(figures_path)

# Unified benchmark result table.
RESULTS = pd.DataFrame(columns=[
    "Quinton Monolithic Time",  "Quinton Monolithic Objective", "Quinton Monolithic Status",
    "Bounded Monolithic Time", "Bounded Monolithic Objective", "Bounded Monolithic Status",
    "Bounded Quinton Monolithic Time", "Bounded Quinton Monolithic Objective", "Bounded Quinton Monolithic Status",
    "Quinton Benders Time", "Quinton Benders Iterations", "Quinton Benders Objective", "Quinton Benders Status",
    "Bounded Benders Time", "Bounded Benders Iterations","Bounded Benders Objective", "Bounded Benders Status",
    "Bounded Quinton Benders Time", "Bounded Quinton Benders Iterations", "Bounded Quinton Benders Objective", "Bounded Quinton Benders Status",
                                ])
RESULTS.index.names = ['Experiment']

# Run all configured formulations for each graph instance.
for i, filename in enumerate(sorted(os.listdir(graph_path))):
    print(  filename[:-4])

    # Per-instance output folders.
    instance_results_path = os.path.abspath(os.getcwd()) + experiments_folder + "results/" + filename[:-4] + "/"
    if not os.path.isdir(instance_results_path):
        os.makedirs(instance_results_path)
    instance_figure_path = os.path.abspath(os.getcwd()) + experiments_folder + "figures/" + filename[:-4] + "/"
    if not os.path.isdir(instance_figure_path):
        os.makedirs(instance_figure_path)

    # Parse APSP instance from XML graph file.
    data = APSPModelData(graph_path, filename)

    # Initialize placeholders to keep a complete row in RESULTS.
    qm_time, qm_objective, qm_status = [1, 1, "NaN"]
    om_time, om_objective, om_status = [1, 1, "NaN"]
    qmb_time, qmb_objective, qmb_status = [1, 1, "NaN"]
    qb_time, qb_it, qb_objective, qb_status = [1, 0, 1, "NaN"]
    ob_time, ob_it, ob_objective, ob_status = [1, 0, 1, "NaN"]
    qbb_time, qbb_it, qbb_objective, qbb_status = [1, 0, 1, "NaN"]

    # 1) Quinton monolithic model.
    print('Quinton Monolithic')
    model = Quinton_monolithic.QuintonMonolithic('Quinton Monolithic', data)
    model.setup_model("")
    model.solve(False, time_limit=timeout)

    qm_time = model.get_solve_time()
    qm_objective = 1 / model.get_objective()
    qm_status = model.get_status()

    model.write_solution(instance_results_path, filename[:-4] + '_Quinton_Monolithic')
    model.save_figure(instance_figure_path, filename[:-4] + '_Quinton_Monolithic')

    # 2) Bounded monolithic model.
    print('Bounded Monolithic')
    model = bounded_monolithic.BoundedMonolithic('Bounded Monolithic', data)
    model.setup_model("")
    model.solve(False, time_limit=timeout)

    om_time = model.get_solve_time()
    om_objective = model.get_objective()
    om_status = model.get_status()

    model.write_solution(instance_results_path, filename[:-4] + '_Bounded_Monolithic')
    model.save_figure(instance_figure_path, filename[:-4] + '_Bounded_Monolithic')

    # 3) Bounded Quinton monolithic model.
    print('Bounded Quinton Monolithic')
    model = bounded_Quinton_monolithic.BoundedQuintonMonolithic('Bounded Quinton Monolithic', data)
    model.setup_model("")
    model.solve(False, time_limit=timeout)

    qmb_time = model.get_solve_time()
    qmb_objective = 1 / model.get_objective()
    qmb_status = model.get_status()

    model.write_solution(instance_results_path, filename[:-4] + '_Bounded_Quinton_Monolithic')
    model.save_figure(instance_figure_path, filename[:-4] + '_Bounded_Quinton_Monolithic')

    # 4) Quinton Benders decomposition.
    print('Quinton Benders')
    model = Quinton_Benders.QuintonMagnantiWongBenders('Quinton Benders', data)
    model.set_iterations(iterations)
    model.solve(True, log_verbosity=1, time_out=timeout, log_destination=instance_results_path, log_file_name=filename[:-4] + "_Quinton_Benders")

    qb_time = model.get_solve_time()
    qb_it = model.iteration
    qb_objective = 1 / model.get_objective()
    qb_status = model.get_status()

    model.write_solution(instance_results_path, filename[:-4] + '_Quinton_Benders')
    model.save_figure(instance_figure_path, filename[:-4] + '_Quinton_Benders')

    # 5) Bounded Benders decomposition.
    print('Bounded Benders')
    model = bounded_Benders.BoundedMagnantiWongBenders('Bounded Benders', data)
    model.set_iterations(iterations)
    model.solve(True, log_verbosity=1, time_out=timeout, log_destination=instance_results_path, log_file_name=filename[:-4] + "_Bounded_Benders")

    ob_time = model.get_solve_time()
    ob_it = model.iteration
    ob_objective = model.get_objective()
    ob_status = model.get_status()

    model.write_solution(instance_results_path, filename[:-4] + '_Bounded_Benders')
    model.save_figure(instance_figure_path, filename[:-4] + '_Bounded_Benders')

    # 6) Bounded Quinton Benders decomposition.
    print('Bounded Quinton Benders')
    model = bounded_Quinton_Benders.BoundedQuintonMagnantiWongBenders('Bounded Quinton Benders', data)
    model.set_iterations(iterations)
    model.solve(True, log_verbosity=1, time_out=timeout, log_destination=instance_results_path, log_file_name=filename[:-4] + "_QuintonOs_Benders")
    qbb_time = model.get_solve_time()
    qbb_it = model.iteration
    qbb_objective = 1/model.get_objective()
    qbb_status = model.get_status()

    model.write_solution(instance_results_path, filename[:-4] + '_Bounded_Quinton_Benders')
    model.save_figure(instance_figure_path, filename[:-4] + '_Bounded_Quinton_Benders')

    # Persist benchmark row and write intermediate CSV after each instance.
    RESULTS.loc[filename[:-4]] = [qm_time, qm_objective, qm_status,
                                  om_time, om_objective, om_status,
                                  qmb_time, qmb_objective, qmb_status,
                                  qb_time, qb_it, qb_objective, qb_status,
                                  ob_time, ob_it, ob_objective, ob_status,
                                  qbb_time, qbb_it, qbb_objective, qbb_status,
                                  ]

    RESULTS.to_csv(experiments_path + "results.csv")

# Final console summary.
print(RESULTS)
