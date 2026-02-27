import pandas as pd
from verifiy_instance import *

# Experiment folder and solver defaults used for verification runs.
experiments_folder = "/benchmark_full/"
timeout = 3600
iterations = 1000000

# Show the full verification table in terminal output.
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

# Resolve and validate expected benchmark folder structure.
experiments_path = os.path.abspath(os.getcwd()) + experiments_folder
if not os.path.isdir(experiments_path):
    raise OSError("No experiment folder named '" + experiments_path + "'")

graph_path = os.path.abspath(os.getcwd()) + experiments_folder + "graphs/"
if not os.path.isdir(graph_path):
    raise OSError("Experiments has no graphs")


results_path = os.path.abspath(os.getcwd()) + experiments_folder + "results/"
if not os.path.isdir(results_path):
    raise OSError("Experiments has no results")

verification_results_path = os.path.abspath(os.getcwd()) + experiments_folder + "verification-results/"
if not os.path.isdir(verification_results_path):
    os.makedirs(verification_results_path)

# Output schema: one verification verdict column per technique.
RESULTS = pd.DataFrame(columns=["Quinton Monolithic", "Bounded Monolithic", "Quinton Bounded Monolithic", "Quinton Benders",
                                "Bounded Benders", "Quinton Bounded Benders",
                                ])
RESULTS.index.names = ['Experiment']

# Input benchmark summary table used for reference objectives.
df = pd.read_csv(experiments_path + 'results.csv')

# Verify every graph in the experiment set.
for i, filename in enumerate(sorted(os.listdir(graph_path))):
    graph = filename[:-4]
    print(graph)
    print("---------------------------------------------------")

    row = df[df['Experiment'].str.contains(graph)]

    # Load model data
    model_data = APSPModelData(graph_path, filename)

    # Default values make missing outputs visible in the final CSV.
    qm = 'Verification Failed'
    om = 'Verification Failed'
    qbm = 'Verification Failed'
    qb = 'Verification Failed'
    ob = 'Verification Failed'
    qbb = 'Verification Failed'

    # Run per-technique verification and attach objective consistency check.
    qm = verify_solution("Quinton_Monolithic", graph_path, graph, results_path, row["Quinton Monolithic Objective"].tolist()[0])
    om = verify_solution("VanOs_Monolithic", graph_path, graph, results_path, row["Our Monolithic Objective"].tolist()[0])
    qbm = verify_solution("QuintonOs_Monolithic", graph_path, graph, results_path, row["Quinton Bounded Monolithic Objective"].tolist()[0])
    qb = verify_solution("Quinton_Benders", graph_path, graph, results_path, row["Quinton Benders Objective"].tolist()[0])
    ob = verify_solution("VanOs_Benders", graph_path, graph, results_path, row["Our Benders Objective"].tolist()[0])
    qbb = verify_solution("QuintonOs_Benders", graph_path, graph, results_path, row["Quinton Bounded Benders Objective"].tolist()[0])


    # Write results into csv line
    RESULTS.loc[filename[:-4]] = [qm, om, qbm, qb, ob, qbb]

    RESULTS.to_csv(experiments_path + "verification_results.csv")

print(RESULTS)
