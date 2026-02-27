import os
from combinatorial_optimization_tools import *
from models.utilities import APSPModelData

def verify_solution(identifier, graph_path, graph_name, results_path, reference_objective=None):
    # Reconstructed solution components from exported solver artifacts.
    objective = None
    binding = {}
    order = {}
    start_times = {}

    model_data = APSPModelData(graph_path, graph_name + ".xml")

    # Parse monolithic JSON exports.
    if "Monolithic" in identifier:
        path = results_path + graph_name + "/" + graph_name + "_" + identifier + ".json"


        with open(path, 'r') as file:
            data = json.load(file)
        result_data = data

        if "Quinton" in identifier:
            # Quinton variants use inverse objective scaling in saved solutions.
            objective = round(1 / float(result_data['CPLEXSolution']['header']['objectiveValue']))

            for v in result_data['CPLEXSolution']['variables']:
                if v['name'][0] == 'm' and round(float(v['value'])) == 1:
                    pattern_m = r'^(m)_a(\d{1,2}|100)_proc_(\d{1,2}|10)$'

                    match_m = re.match(pattern_m, v['name'])
                    name, actor, proc = match_m.groups()
                    binding[f"a{actor}"] = f"proc_{proc}"

                if v['name'][0] == 'K':
                    pattern_K = r'^(K)_a(\d{1,2}|100)_a(\d{1,2}|100)$'
                    match_K = re.match(pattern_K, v['name'])
                    name, actor0, actor1 = match_K.groups()

                    order[(f"a{actor0}", f"a{actor1}")] = round(float(v['value']))

                    for t1 in model_data.TASKS:
                        for t2 in model_data.TASKS:
                            if t1 != t2:
                                if (t1, t2) not in order:
                                    order[(t1, t2)] = 0
                            if t1 == t2:
                                order[(t1, t2)] = 1

                if v['name'][0] == 'u':
                    # Normalize start times with objective for Quinton format.
                    start_times[v['name'][2:]] = round(
                        float(v['value']) / float(result_data['CPLEXSolution']['header']['objectiveValue']))

                    for t in model_data.TASKS:
                        if t not in start_times:
                            start_times[t] = 0

        if "VanOs" in identifier:
            # VanOs variants keep objective and starts directly in absolute values.
            objective = round(float(result_data['CPLEXSolution']['header']['objectiveValue']))

            for v in result_data['CPLEXSolution']['variables']:
                if v['name'][0] == 'x' and round(float(v['value'])) == 1:
                    pattern_x = r'^(x)_a(\d{1,2}|100)_proc_(\d{1,2}|10)$'

                    match_x = re.match(pattern_x, v['name'])
                    name, actor, proc = match_x.groups()
                    binding[f"a{actor}"] = f"proc_{proc}"


                if v['name'][0] == 'z' and round(float(v['value'])) == 1:
                    pattern_z = r'^(z)_a(\d{1,2}|100)_a(\d{1,2}|100)_(\d{1,2}|100000)$'
                    match_z = re.match(pattern_z, v['name'])
                    name, actor0, actor1, distance = match_z.groups()

                    order[(f"a{actor1}", f"a{actor0}")] = round(float(distance) + 1)
                    order[(f"a{actor0}", f"a{actor1}")] = -round(float(distance))

                    for t1 in model_data.TASKS:
                        for t2 in model_data.TASKS:
                            if (t1, t2) not in order:
                                if t1 != t2:
                                    order[(t1, t2)] = 0
                                if t1 == t2:
                                    order[(t1, t2)] = 1

                if v['name'][0] == 's':
                    start_times[v['name'][2:]] = round(float(v['value']))

                    for t in model_data.TASKS:
                        if t not in start_times:
                            start_times[t] = 0
    try:
        # Parse Benders exports: master (assignment/order) + primal sub (timings/objective).
        if "Benders" in identifier:
            master_path = results_path + graph_name + "/" + graph_name + "_" + identifier + "_master" + ".json"
            master_path_txt = results_path + graph_name + "/" + graph_name + "_" + identifier + "_master" + ".txt"
            sub_path = results_path + graph_name + "/" + graph_name + "_" + identifier + "_primal_sub" + ".json"

            with open(master_path, 'r') as file:
                data = json.load(file)
            master_result_data = data

            with open(sub_path, 'r') as file:
                data = json.load(file)
            sub_result_data = data



            data = {}
            with open(master_path_txt, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if not line or '=' not in line:
                        continue  # skip blank lines or malformed ones
                    key, value = line.split('=', 1)
                    data[key.strip()] = value.strip()
            master_result_txt_data = data


            if "Quinton" in identifier:
                objective = round(1/float(sub_result_data['CPLEXSolution']['header']['objectiveValue']))

                for v in master_result_txt_data.keys():
                    if v[0] == 'm' and round(float(master_result_txt_data[v])) == 1:
                        pattern_m = r'^(m)_a(\d{1,2}|100)_proc_(\d{1,2}|10)$'

                        match_m = re.match(pattern_m, v)
                        name, actor, proc = match_m.groups()
                        binding[f"a{actor}"] = f"proc_{proc}"

                    if v[0] == 'K':
                        pattern_K = r'^(K)_a(\d{1,2}|100)_a(\d{1,2}|100)$'
                        match_K = re.match(pattern_K, v)
                        name, actor0, actor1 = match_K.groups()

                        order[(f"a{actor0}", f"a{actor1}")] = round(float(master_result_txt_data[v]))

                        for t1 in model_data.TASKS:
                            for t2 in model_data.TASKS:
                                if t1 != t2:
                                    if (t1, t2) not in order:
                                        order[(t1, t2)] = 0
                                if t1 == t2:
                                    order[(t1, t2)] = 1

                for v in sub_result_data['CPLEXSolution']['variables']:
                    if v['name'][0] == 'u':
                        start_times[v['name'][2:]] = round(float(v['value'])/float(sub_result_data['CPLEXSolution']['header']['objectiveValue']))

                        for t in model_data.TASKS:
                            if t not in start_times:
                                start_times[t] = 0

            if "VanOs" in identifier:
                objective = round(float(sub_result_data['CPLEXSolution']['header']['objectiveValue']))

                for v in master_result_txt_data.keys():
                    if v[0] == 'x' and round(float(master_result_txt_data[v])) == 1:
                        pattern_x = r'^(x)_a(\d{1,2}|100)_proc_(\d{1,2}|10)$'

                        match_x = re.match(pattern_x, v)
                        name, actor, proc = match_x.groups()
                        binding[f"a{actor}"] = f"proc_{proc}"

                    if v[0] == 'z' and round(float(master_result_txt_data[v])) == 1:
                        pattern_z = r'^(z)_a(\d{1,2}|100)_a(\d{1,2}|100)_(\d{1,2}|100000)$'
                        match_z = re.match(pattern_z, v)
                        name, actor0, actor1, distance = match_z.groups()

                        order[(f"a{actor1}",f"a{actor0}")] = round(float(distance) + 1)
                        order[(f"a{actor0}",f"a{actor1}")] = -round(float(distance))

                        for t1 in model_data.TASKS:
                            for t2 in model_data.TASKS:
                                if (t1, t2) not in order:
                                    if t1 != t2:
                                        order[(t1, t2)] = 0
                                    if t1 == t2:
                                        order[(t1, t2)] = 1


                for v in sub_result_data['CPLEXSolution']['variables']:
                    if v['name'][0] == 's':
                        start_times[v['name'][2:]] = round(float(v['value']))

                        for t in model_data.TASKS:
                            if t not in start_times:
                                start_times[t] = 0
    except:
        # Any missing/malformed artifact is treated as verification failure.
        return 'Verification failed'
    # Optional suffix indicating whether reconstructed objective matches the benchmark table.
    ref_postscript = ""

    if reference_objective != None:
        if round(reference_objective) == round(objective):
            ref_postscript = " | matching objectives"
        else:
            ref_postscript = " | !mismatching objectives!"

    # Validate reconstructed solution components against precedence and no-overlap constraints.
    verification_result = verify(model_data, identifier, objective, binding, order, start_times)
    print(verification_result + ref_postscript)
    return verification_result + ref_postscript

def verify(model_data, identifier, *args):
    # Unpack reconstructed values: objective, binding map, order matrix, start times.
    mu = args[0]
    b = args[1]
    m = args[2]
    s = args[3]

    mdl = Model(f"Verify {identifier}")
    mdl.context.cplex_parameters.preprocessing.presolve = 0

    # Channel precedence constraints.
    for c in model_data.DEPENDENCIES:
        try:
            mdl.add_constraint(
                s[c[1]] >= s[c[0]] - model_data.DEPENDENCIES[c] * mu + model_data.TASKS[c[0]][b[c[0]]]
            )
        except DOcplexException:
            return f"Channel constraint violation between {c[0]} ({s[c[0]]}-{s[c[0]] + round(model_data.TASKS[c[0]][b[c[0]]])}) and {c[1]} ({s[c[1]]}-{s[c[1]] + round(model_data.TASKS[c[1]][b[c[1]]])})"

    # No-overlap constraints for tasks mapped to the same processor.
    for t1 in model_data.TASKS.keys():
        for t2 in model_data.TASKS.keys():
            if b[t1] == b[t2]:
                try:
                    mdl.add(
                        s[t2] >= s[t1] - m[(t1, t2)] * mu + model_data.TASKS[t1][b[t1]]
                    )
                except DOcplexException:
                    return f"No-overlap constraint violation between {t1} ({s[t1]}-{s[t1] + round(model_data.TASKS[t1][b[t1]])}) and {t2} ({s[t2]}-{s[t2] + round(model_data.TASKS[t2][b[t2]])})"

    # A feasible solve means all reconstructed constraints are simultaneously satisfiable.
    res = mdl.solve()

    # Keep the original success/failure string convention used by CSV post-processing.
    if hasattr(res, 'solve_status'):
        if res.solve_status is not None:
            return "verification successful"
            # return res.solve_details.status
        else:
            return 'Verification Failed'
    else:
        return mdl.solve_details.status