import pandas as pd
import xml.etree.ElementTree as ET


def parse_sdf3_xml(file_path):
    """ Parses the SDF3 XML file, extracting actors, channels, execution times, and processor mappings. """

    # Load XML file
    tree = ET.parse(file_path)
    root = tree.getroot()

    return root


def parse_application_graph_from_root(root):
    """ Parses the SDF3 XML file, extracting actors, channels, execution times, and processor mappings. """

    # Ensure correct SDF3 format
    if root.tag != "sdf3":
        raise ValueError("Invalid SDF3 file format")

    data = {
        "graphs": [],
        "actors": [],
        "channels": [],
        "execution_times": [],
        "processors": []
    }

    # Extract Application Graph
    application = root.find("applicationGraph")
    if application is not None:
        _parse_application_graph(application, data)

    return data


def parse_application_graph_from_xml(file_path):
    """ Parses the SDF3 XML file, extracting actors, channels, execution times, and processor mappings. """

    # Load XML file
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Ensure correct SDF3 format
    if root.tag != "sdf3":
        raise ValueError("Invalid SDF3 file format")

    data = {
        "graphs": [],
        "actors": [],
        "channels": [],
        "execution_times": [],
        "processors": []
    }

    # Extract Application Graph
    application = root.find("applicationGraph")
    if application is not None:
        _parse_application_graph(application, data)

    return data


def _parse_application_graph(app, data):
    """ Extracts application graph (actors, channels, execution times) from SDF3 XML. """
    for graph in app.findall("sdf"):
        graph_name = graph.get("name", "unnamed_graph")
        actors = graph.findall("actor")
        channels = graph.findall("channel")

        # Store graph metadata
        data["graphs"].append({"Graph Name": graph_name, "Number of Actors": len(actors)})

        # Extract actors
        for actor in actors:
            actor_name = actor.get("name")
            data["actors"].append({
                "Graph Name": graph_name,
                "Actor Name": actor_name,
                "Type": actor.get("type", "unknown"),
            })

        # Extract channels
        for channel in channels:
            src = channel.get("srcActor")
            dst = channel.get("dstActor")
            initial_tokens = channel.get("initialTokens", "0")
            data["channels"].append({
                "Graph Name": graph_name,
                "Source Actor": src,
                "Destination Actor": dst,
                "Initial Tokens": int(initial_tokens),
            })

    # Extract execution times from sdfProperties
    sdf_properties = app.find("sdfProperties")
    if sdf_properties is not None:
        for actor_properties in sdf_properties.findall("actorProperties"):
            actor_name = actor_properties.get("actor")
            for processor_data in actor_properties.findall("processor"):
                processor_type = processor_data.get("type", "unknown")
                execution_time = processor_data.find("executionTime")
                if execution_time is not None:
                    exec_time = float(execution_time.get("time", 0))
                    data["execution_times"].append({
                        "Actor": actor_name,
                        "Processor": processor_type,
                        "Execution Time": exec_time
                    })
                    # Collect unique processors
                    if processor_type not in [entry["Processor"] for entry in data["processors"]]:
                        data["processors"].append({"Processor": processor_type})



if __name__ == "__main__":
    # Example usage

    file_path = "graph.xml"  # Replace with actual SDF3 file path
    sdf_data = parse_application_graph_from_xml(file_path)
    #
    # Convert to DataFrames
    df_graphs = pd.DataFrame(sdf_data["graphs"])
    df_actors = pd.DataFrame(sdf_data["actors"])
    df_channels = pd.DataFrame(sdf_data["channels"])
    df_execution_times = pd.DataFrame(sdf_data["execution_times"])
    df_processors = pd.DataFrame(sdf_data["processors"])

    # Display DataFrames
    print("\n--- Graphs Overview ---")
    print(df_graphs)

    print("\n--- Actors Overview ---")
    print(df_actors)

    print("\n--- Channels Overview ---")
    print(df_channels)

    print("\n--- Execution Times Overview ---")
    print(df_execution_times)

    print("\n--- Processors Overview ---")
    print(df_processors)

    actor_name = "motion_estimation"  # Replace with the actor you're looking for
    processor_name = "p"  # Replace with the processor name

    execution_time = df_execution_times[
        (df_execution_times["Actor"] == actor_name) &
        (df_execution_times["Processor"] == processor_name)
    ]["Execution Time"].values

    if len(execution_time) > 0:
        print(f"Execution time of {actor_name} on {processor_name}: {execution_time[0]}")
    else:
        print("No execution time found for this actor on the specified processor.")
