# APSP Toolset
**Authors:** _Roel van Os, Marc Geilen, Martijn Hendriks, Twan Basten_ 

**Link to repository:** https://github.com/TUE-EE-ES/APSP-toolset

---
This repository includes software and benchmark assets for solving the Allocation and Periodic Scheduling Problem (APSP) as described in (`[APSP-2026]`). For any questions feel free to contact: Roel van Os (r.w.m.v.os@tue.nl). 

This repository includes:

- Precomputed benchmark results as seen in the paper 
- Solution models discussed in (`[APSP-2026]`)
- Solution models discussed in (`[QUINTON-2020]`)
- Scripts to run and verify solutions
- Scripts to generate figures

## System Requirements
There are no specific system requirements for running this software. The implementation is platform-independent and can be executed on any operating system (e.g., Linux, macOS, Windows) and hardware architecture, including both x86 and ARM-based systems.

## Repository Structure

- `solve_instance.py`: run selected models on a single graph instance.
- `solve_benchmark.py`: run all models on all instances in `benchmark/graphs/`.
- `verifiy_instance.py`: verify one saved solution instance against APSP constraints.
- `verify_benchmark.py`: verify all benchmark entries and write `benchmark/verification_results.csv`.
- `models/`: formulations and shared configuration classes.
- `models/configuration/apsp_parameters.py`: solver parameter defaults (applied to all models).
- `models/configuration/apsp_configure.py`: naming/visualization configuration used by model output.
- `benchmark/`: Precomputed results as seen in the paper
- `benchmark_full/`: skeleton folder for a full benchmark run.
- `benchmark_shortened/`: skeleton folder for a shortened benchmark run.

All default file settings correspond to those used for finding the results as reported in (`[APSP-2026]`)

## Python Requirements

Required: Python 3.10+ environment.

Core packages to run the optimization models:

- `docplex`: v2.29.241
- `cplex`: v22.1.1.0
- `pandas`: v2.2.3
- `matplotlib`: v3.10.1
- `interruptingcow`v0.8

Additional packages used by results evaluation plotting:

- `numpy`: v2.2.4
- `natsort`: v8.4.0
- `lxml`: v5.3.1

Install with:

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install pandas matplotlib interruptingcow numpy natsort lxml
```

## CPLEX (Solver) Setup

The models are built with DOcplex (`docplex`) and require IBM CPLEX (`cplex`) for local solves.

### 1. Obtain CPLEX

- Download **IBM ILOG CPLEX Optimization Studio** from IBM.
- If you are a student/researcher, use the IBM academic initiative for access/licensing:
https://www.ibm.com/support/pages/ibm-ilog-optimization-academic-initiative

### 2. Install CPLEX and Python bindings


>**NOTE:** When installing CPLEX via pip, you obtain the community edition of the package. This edition only allows us to solve small problem instances. For the benchmark instances provided in this repository, we need to full version of the CPLEX package. The setup files for this package is provided after installing the IBM ILOG CPLEX Optimizaiton Studio.

- In your terminal application, browse to the CPLEX package install directory (i.e. `C:\Program Files\IBM\ILOG\CPLEX_StudioXXXX\python`)
- Run the `setup.py` script:
   - **Windows:** `py setup.py install`
   - **Linux (Ubuntu):** `python3 setup.py install`

Instructions to get the full CPLEX package, after we have installed IBM ILOG CPLEX Optimization Studio, can also be found here: https://www.ibm.com/docs/en/icos/20.1.0?topic=cplex-setting-up-python-api
### 3. Quick validation

```bash
python -c "import cplex, docplex; print('CPLEX + DOcplex OK')"
```

If this import fails, the solver will not run.

## Replicate Paper Results

>**NOTE:** To run the benchmark used in `[APSP-2026]`, the full version of CPLEX is required.

The following steps allow a full replication of the results. No changes are needed to the files, all default file settings correspond to those needed to replicate the results as seen in the paper.

#### Run instructions:
1. Run: `solve_benchmark.py`
```bash
python solve_benchmark.py
```
2. Run: `verify_benchmark.py`
```bash
python verify_benchmark.py
```
3. Open: `benchmark_full`
```bash
cd benchmark_full
```
4. Run figure generation scripts:
   - `results_optimality_count.py`: Bar chart of the optimality count for all modeling techniques (fig. 7 in paper)
   - `results_accuracy_issues.py`: Bar chart of the accuracy issues per benchmark set for all modeling techniques (fig. 8 in paper)
   - `results_solve_time.py`: Boxplot of solve time for all modeling techniques (fig. 9 in paper)


## Running Selected Models or Benchmarks

### Single instance run

`solve_instance.py` is intended for manual experiments on one graph.

1. Set:
   - `filepath` and `filename`
   - `timeout`
   - `iterations` (for Benders methods)
2. Enable/disable model blocks in the script.
3. Run:

```bash
python solve_instance.py
```

### Full benchmark run

`solve_benchmark.py` loops over all files in the selected folder and writes per-instance outputs.

Two folders are provided: 
- `benchmark_full/`: Contains the full set of benchmark graphs as reported in `[APSP-2026]`
- `benchmark_shortened/`: Contains a quarter of the set of benchmark graphs

_A full benchmark run takes roughly 8 days to complete. For the artifact evaluation we also provide a shortened benchmark with an expected runtime of approximately two days, that provides an indication of the trends reported in the paper._

#### Run instructions:
1. Set:
   - `timeout` (optional)
   - `iterations` (optional)
   - `experiments_folder`: to `"/benchmark_full/"` or `"/benchmark_shortened/"`
2. Run:

```bash
python solve_benchmark.py
```

Outputs are written to:

- `[benchmark_name]/results/<instance>/`
- `[benchmark_name]/figures/<instance>/`
- results table: `[benchmark_name]/results.csv`

### Verification runs

Upon completion of a benchmark run.
Use `verify_benchmark.py` to verify all benchmark outputs for correctness and accuracy issues.

```bash
python verify_benchmark.py
```

### Results Evaluation

Upon completion of a full benchmark run, and completed verification. The scripts in `benchmark_name/` can be used to figures. 
- `results_optimality_count.py`: Bar chart of the optimality count for all modeling techniques (fig. 7 in paper)
- `results_accuracy_issues.py`: Bar chart of the accuracy issues per benchmark set for all modeling techniques (fig. 8 in paper)
- `results_solve_time.py`: Boxplot of solve time for all modeling techniques (fig. 9 in paper)

## Configuring Parameters and Naming

### `models/configuration/apsp_parameters.py`

This class applies CPLEX defaults each time a model is built. Current defaults:

- `mdl.context.cplex_parameters.emphasis.mip = 2` (focus on optimality)
- `mdl.parameters.emphasis.numerical = 1` (numerical robustness)

Edit these values to tune solver behavior globally for all formulations.

### `models/configuration/apsp_configure.py`

This class controls naming and figure labeling:

- `mode`: 
  - `SDF3`: Default mode, uses the SDF3 naming configurations. This mode is also used for obtaining benchmark results.
  - `PAPER`: Applies the naming configuration as in the paper. Additionally, the figures have improved styling that matches the one of the illustrative example seen in Section II of the paper.
  - `CUSTOM`: Apply a custom naming configuration.
- `time_units`: x-axis label suffix
- `figure_repetitions`: visualization setting
- `custom_task_name`, `custom_resource_name`: used in `CUSTOM` mode

This affects model naming in parsed data and generated plots/text outputs.

## Benchmark Documentation

See the dedicated benchmark guide at:

- `BENCHMARK_README.md`

## References

Use either the number or the tag when referencing:

- `[APSP-2026]` (Conditionally Accept at RTAS 2026) van Os, R., Geilen, M., Hendriks, M., Basten, T., 2026. Optimal Resource Allocation and Periodic Scheduling.
- `[QUINTON-2020]` Quinton, F., Hamaz, I., Houssin, L., 2020. A mixed integer linear programming modelling for the flexible cyclic jobshop problem. Ann Oper Res 285, 335–352. https://doi.org/10.1007/s10479-019-03387-9
