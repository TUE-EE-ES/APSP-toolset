from itertools import combinations

def get_actors_dict(data):
    ACTORS = {}

    for actor in data["actors"]:
        ACTORS[actor["Actor Name"]] = {}

        for exec in data["execution_times"]:
            if exec["Actor"] == actor["Actor Name"]:
                ACTORS[actor["Actor Name"]][exec["Processor"]] = exec["Execution Time"]

    return ACTORS

def get_channels_dict(data):
    CHANNELS = {}

    for channel in data["channels"]:
        CHANNELS[channel["Source Actor"], channel["Destination Actor"]] = channel["Initial Tokens"]

    return CHANNELS

def get_nr_processors(data):
    return len(data["processors"])

def get_nr_actors(data):
    return len(data["actors"])

def get_allocation_overlap_dict(data):
    ALLOCATION_OVERLAP = {}

    ACTORS = get_actors_dict(data)
    CHANNELS = get_channels_dict(data)

    # Get all unique actor pairs
    for a1, a2 in combinations([a for a in ACTORS], 2):
        # Find common machines
        machines_a1 = set(ACTORS[a1].keys())
        machines_a2 = set(ACTORS[a2].keys())
        common_machines = machines_a1.intersection(machines_a2)

        if common_machines:
            ALLOCATION_OVERLAP[(a1, a2)] = common_machines
            ALLOCATION_OVERLAP[(a2, a1)] = common_machines

    return ALLOCATION_OVERLAP

def get_all_data(data):
    ACTORS = get_actors_dict(data)
    CHANNELS = get_channels_dict(data)
    ALLOCATION_OVERLAP = get_allocation_overlap_dict(data)
    NR_PROCESSORS = get_nr_processors(data)
    NR_ACTORS = get_nr_actors(data)

    return [ACTORS, CHANNELS, ALLOCATION_OVERLAP, NR_PROCESSORS, NR_ACTORS]
