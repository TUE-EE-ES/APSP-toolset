import sdf3_python_utilities as sdf3
from models.configuration.apsp_configure import *


class APSPModelData(ModelData):
    def __init__(self, filepath, filename):
        """
        Specify a data file for parsing and setting up model data

        :param filepath: Path to the sdf3 graph file
        :param filename: Name of the graph
        """
        super().__init__(filepath, filename)

        self.FILENAME = filename

        data = sdf3.parse_application_graph_from_xml(filepath + filename)

        # Model Data
        self.TASKS, self.DEPENDENCIES, self.ALLOCATION_OVERLAP, self.NR_RESOURCES, self.NR_TASKS = sdf3.get_all_data(data)

        config = APSPConfigure()


        if config.mode is APSPConfigure.APSPConfig.SDF3:
            pass
        else:
            new_task_config = {}
            for tkey, tvalue in self.TASKS.items():
                if config.mode is APSPConfigure.APSPConfig.PAPER:
                    new_tkey = tkey.replace("a", "t")
                elif config.mode is APSPConfigure.APSPConfig.CUSTOM:
                    new_tkey = tkey.replace("a", config.custom_task_name)

                new_resource_config = {}
                for rkey, rvalue in self.TASKS[tkey].items():
                    if config.mode is APSPConfigure.APSPConfig.PAPER:
                        new_rkey = rkey.replace("proc_", "r")
                    elif config.mode is APSPConfigure.APSPConfig.CUSTOM:
                        new_rkey = rkey.replace("proc_", config.custom_resource_name)
                    new_resource_config[new_rkey] = rvalue
                new_task_config[new_tkey] = new_resource_config
            self.TASKS = new_task_config

            new_dependencies_config = {}
            for dkey, dvalue in self.DEPENDENCIES.items():
                new_dkey = ('', '')
                if config.mode is APSPConfigure.APSPConfig.PAPER:
                    new_dkey = (
                        dkey[0].replace("a", "t"),
                        dkey[1].replace("a", "t"),
                    )
                elif config.mode is APSPConfigure.APSPConfig.CUSTOM:
                    new_dkey = (
                        dkey[0].replace("a", config.custom_task_name),
                        dkey[1].replace("a", config.custom_task_name),
                    )
                new_dependencies_config[new_dkey] = dvalue
            self.DEPENDENCIES = new_dependencies_config

            new_allocation_overlap_config = {}
            for okey, ovalue in self.ALLOCATION_OVERLAP.items():
                new_okey = ('', '')
                if config.mode is APSPConfigure.APSPConfig.PAPER:
                    new_okey = (
                        okey[0].replace("a", "t"),
                        okey[1].replace("a", "t"),
                    )
                elif config.mode is APSPConfigure.APSPConfig.CUSTOM:
                    new_okey = (
                        okey[0].replace("a", config.custom_task_name),
                        okey[1].replace("a", config.custom_task_name),
                    )

                new_resource_set = set()
                for r in self.ALLOCATION_OVERLAP[okey]:
                    if config.mode is APSPConfigure.APSPConfig.PAPER:
                        new_r = r.replace("proc_", "r")
                    elif config.mode is APSPConfigure.APSPConfig.CUSTOM:
                        new_r = r.replace("proc_", config.custom_resource_name)
                    new_resource_set.add(new_r)
                new_allocation_overlap_config[new_okey] = new_resource_set
            self.ALLOCATION_OVERLAP = new_allocation_overlap_config