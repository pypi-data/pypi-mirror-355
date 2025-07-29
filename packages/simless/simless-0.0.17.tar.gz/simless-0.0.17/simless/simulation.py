from simless.configurations import Configurations
from simless.runs_frame import RunsFrame
from simless.sim_dir import SimDir
from simless.topology import Topology
from simless.workloads import WorkloadManager



class Simulation:
    """
    The Simulation class encapsulates the logic for managing and running a simulation.

    Attributes:
        sim_dir (SimDir): Represents the directory where simulation data is stored.
        topology (Topology): Defines the network or system topology for the simulation.
        configuration (Configurations): Stores configuration details for the simulation.
        workload_mgr (WorkloadManager): Manages workloads associated with the simulation.
        runs_frame (RunsFrame): Stores simulation results in a structured format.

    """

    SIM_DIR_MODEL = SimDir # This is the model for the simulation directory
    
    def __init__(self, sim_dir_name, topology, configuration=None, workload_mgr=None, runs_frame=None):
        self.sim_dir: SimDir =self.SIM_DIR_MODEL(name=sim_dir_name, parent_path="./simulations")
        self.topology: Topology = topology
        self.configuration: Configurations = configuration or Configurations()
        self.workload_mgr: WorkloadManager = workload_mgr or WorkloadManager()
        self.runs_frame: RunsFrame = runs_frame or RunsFrame()
        self.workload_mgr.set_sim_dir(self.sim_dir)


    def build_topology(self):
        """
        Builds the topology for the simulation by generating any required input files
        and adds the relevant configuration section to the configuration manager.

        This method uses the `Topology` instance to create the necessary topology
        files in the simulation directory and updates the `Configurations` instance
        with the generated topology configuration.
        """
        topology_section = self.topology.build(self.sim_dir)
        self.configuration.add_config(topology_section)

    def build_workloads(self):
        """
        Allocates nodes for each workload based on the topology, generates any 
        required input files, and adds the relevant configurations to the 
        configuration manager.

        This method uses the `WorkloadManager` to:
        1. Allocate nodes for workloads using the provided topology.
        2. Create any necessary input files for the workloads.
        3. Update the `Configurations` instance with the generated workload configurations.
        """
        self.workload_mgr.allocate(self.topology)
        workload_sections = self.workload_mgr.build()
        self.configuration.add_config(workload_sections)
    
    def build_configuration(self):
        """
        Creates the `omnetpp.ini` file for the simulation.

        This method generates the main configuration file (`Main.ini`) by 
        consolidating all the configuration sections managed by the 
        `Configurations` instance and writes it to the simulation directory.
        """
        omnetpp_ini = self.sim_dir.get_omnetpp_ini()
        omnetpp_ini.writelines(self.configuration.export())
    
    def init_runs_frame(self):
        """
        Initializes the runs dataframe with the details provided by the user 
        in the configuration sections.

        This method extracts relevant information from the `Configurations` 
        instance and uses it to populate the `RunsFrame` instance, which 
        organizes simulation runs in a structured format.
        """
        runs_details = self.configuration.get_runs_details()
        self.runs_frame.init_from_dict(runs_details)

    def add_fields_to_frame(self):
        """
        Adds "top-level" data to all the records in the runs dataframe.

        This method allows the user to specify additional fields and their 
        corresponding values, which will be applied to all records in the 
        `RunsFrame` instance. It is useful for adding metadata or global 
        attributes to the simulation runs.

        Args:
            fields (dict): A dictionary where keys are field names and values 
                           are the data to be added to all records.
        """
        pass

    def build_runs_frame(self):
        self.init_runs_frame()
        self.add_fields_to_frame()
    
    def build_sim_dir(self):
        """
        Creates the directory and file structure for the simulation.

        This method is responsible for setting up the simulation directory 
        and generating the necessary file tree. It ensures that all required 
        directories and files are created in the specified simulation directory.
        """
        self.sim_dir.build()

    def build(self):
        """
        Executes the complete simulation setup process.

        This method orchestrates the entire simulation setup by performing the 
        following steps in sequence:
        1. Builds the simulation directory and file structure.
        2. Generates the topology and updates the configuration manager.
        3. Allocates and builds workloads, adding their configurations.
        4. Creates the main configuration file (`Main.ini`).
        5. Initializes the runs dataframe with user-provided configuration details.

        It ensures that all necessary components are prepared for running the simulation.
        """
        self.build_topology()
        self.build_workloads()
        self.build_configuration()
        self.build_runs_frame()
        self.build_sim_dir()

    def to_csv(self, csv_name: str =None):
        """
        Exports the runs dataframe to a CSV file.

        This method saves the contents of the `RunsFrame` instance to a CSV file 
        at the specified file path. It allows the user to persist simulation run 
        details in a tabular format for further analysis or record-keeping.

        Args:
            file_path (str): The path where the CSV file will be saved.
        """
        csv_name = csv_name.strip()
        csv_name = csv_name if csv_name is not None else self.sim_dir.name
        if not csv_name.endswith(".csv"):
            csv_name += ".csv"
        self.runs_frame.to_csv(csv_name)


