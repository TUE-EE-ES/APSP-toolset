import os
import re
import json
from collections import defaultdict

def parse_solution_file(filepath):
    """
    Parse a solver text export (.txt) into a key/value dictionary.
    """
    data = {}
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("solution for:"):
                continue
            # Parse "key: value" records.
            if ':' in line:
                key, val = line.split(':', 1)
                data[key.strip()] = val.strip()
            # Parse "var = value" records.
            elif '=' in line:
                key, val = line.split('=', 1)
                try:
                    data[key.strip()] = float(val.strip())
                except ValueError:
                    data[key.strip()] = val.strip()
    return data

def collect_graph_data(folder_path, graph_name):
    """
    Group parsed result files per model and formulation type for one graph instance.
    """
    grouped_data = defaultdict(lambda: {'master': None, 'sub': None, 'monolithic': None})

    for filename in os.listdir(folder_path):
        if not re.match(rf"^{re.escape(graph_name)}(_|$)", filename):
            continue

        if filename.endswith(".txt"):
            base_name = filename.replace(graph_name + "_", "").replace(".txt", "")
            key_match = re.match(r"(.+?)_(Benders|Monolithic)", base_name)

            if not key_match:
                continue

            model_name, model_type = key_match.groups()
            model_key = model_name.strip()

            filepath = os.path.join(folder_path, filename)
            parsed_data = parse_solution_file(filepath)

            # Store each file in its formulation slot.
            if "Benders" in model_type:
                if "master" in base_name:
                    grouped_data[model_key]['master'] = parsed_data
                elif "sub" in base_name:
                    grouped_data[model_key]['sub'] = parsed_data
            elif "Monolithic" in model_type:
                grouped_data[model_key]['monolithic'] = parsed_data

    return grouped_data

def parse_json(folder_path, graph_name):
    """
    Parse a JSON solution export file.
    """
    return json.loads(folder_path + graph_name + ".json")
