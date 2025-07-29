

from enum import Enum, auto
import os
from pathlib import Path


"""
This module handles the creation of simulation directories and files.

In this file, every file and folder is first represented as a class, encapsulating 
its properties and behavior. These classes define the structure and content of 
the files and directories. Only at the end of the process are the actual files 
and folders created on the filesystem, based on the definitions provided by 
these classes.
"""


class DataFileType(Enum):
    """
    Represents a data file type.

    The `DataFileType` class is used to define the type of data files that will 
    be created as part of the simulation directory. This class encapsulates 
    properties such as the file name, format, and content, serving as a blueprint 
    for generating specific data files required for the simulation.
    """
    TXT = auto()

class DataIO:
    """
    Handles data input and output operations.

    The `DataIO` class is responsible for managing the creation and handling 
    of data files and directories for the simulation. It provides functionality 
    to define and organize data structures before they are written to the filesystem.

    Parameters:
    - `name` (str): The name of the file or directory.
    - `parent_path` (str): The path where the file or directory will be created.
    - `ghost` (bool): A flag indicating whether to skip the actual creation 
      of the file or directory. If `True`, the file or directory is only 
      represented logically and not physically created.
    """

    def __init__(self, parent_path, name, ghost=False):
        self.parent_path = parent_path
        self.name = name
        self.ghost = ghost
        self.created = False

    def get_path(self):
        """ Return the full path of the file or directory. """
        return os.path.join(self.parent_path, self.name)
    
    def build(self):
        """ Build the file or directory. """
        pass

class DataFile(DataIO):
    """
    Represents a data file.
    """
    def __init__(self, parent_path, name, ghost=False):
        super().__init__(parent_path, name, ghost)
        self.content = []

    def write(self, line):
        self.content.append(line)

    def writelines(self, lines):
        self.content.extend(lines)

    def build(self):
        return super().build()
        

class TxtDataFile(DataFile):
    """
    Represents a data text file.
    """

    def __init__(self, parent_path, name, ghost=False):
        super().__init__(parent_path, name, ghost)

    def build(self):
        if self.ghost:
            return
        
        with open(self.get_path(), "w") as file:
            file.writelines(self.content)

        self.created = True

class DataDir(DataIO):
    """
    Represents a data directory.
    """
    def __init__(self, parent_path, name, ghost=False):
        super().__init__(parent_path, name, ghost)
        self.children = {}
    
    def create_dir(self):
        """
        Creates a directory on the filesystem.
    
        This method is responsible for creating a directory at the specified path. 
        If the `ghost` flag is set to `True`, the directory creation is skipped, 
        and it is only represented logically. This allows for testing or planning 
        directory structures without physically creating them.
        """

        if self.ghost:
            return
        
        Path(self.get_path()).mkdir(parents=True, exist_ok=True)
        self.created = True

    def verify_not_exists(self, name):
        """
        Verifies that a file or directory does not already exist.
    
        This method checks whether a file or directory exists at the specified path. 
        If it does, an exception or error can be raised to prevent overwriting 
        or conflicts. This ensures that new files or directories are created 
        without unintentionally replacing existing ones.
        """
        if name in self.children:
            raise ValueError(f"there already exists child with name {name} under {self.get_path()}")

    def add_dir(self, name) -> "DataDir":
        """
        Adds a new directory to the structure.
    
        This method allows adding a directory to the current structure, either 
        by creating it physically (if `ghost` is `False`) or representing it 
        logically. It helps organize and define the directory hierarchy 
        for the simulation.
        """
        self.verify_not_exists(name)
        self.children[name] = DataDir(parent_path=self.get_path(), name=name)
        return self.children[name]
    
    def add_file(self, name, file_type = DataFileType.TXT) -> DataFile:
        self.verify_not_exists(name)
        if file_type == DataFileType.TXT:
            self.children[name] = TxtDataFile(parent_path=self.get_path(), name=name)
        else:
            raise ValueError(f"Unsopported File: {file_type}") # TODO: add specific exeption
        
        return self.children[name]
    
    def append_child(self, child: DataIO):
        """
        Appends a child element to the current directory or file structure.
    
        This method adds a child (such as a subdirectory or file) to the current 
        directory or file structure. It helps build a hierarchical representation 
        of the simulation's data organization.
        """
        self.verify_not_exists(child.name)
        self.children[child.name] = child
        
    def get_child(self, name):
        """
        Retrieves a child element from the current directory or file structure.
    
        This method searches for and returns a child (such as a subdirectory or file) 
        within the current structure based on its name or other identifying attributes. 
        If the child does not exist, it may return `None` or raise an exception, 
        depending on the implementation.
        """
        return self.children[name]
        
    def build(self):
        """
        Builds the entire directory and file structure.
    
        This method iterates through the defined structure and creates all directories 
        and files as specified. If the `ghost` flag is set to `True`, the creation 
        is skipped, and the structure is only represented logically. It ensures 
        that the complete hierarchy is constructed as planned.
        """
        if not self.created:
            self.create_dir()

        for child in self.children.values():
            child.build()


class WorkloadDir(DataDir):

    """
    Represents the workload directory.

    The `WorkloadDir` class is dedicated to managing the traffic workload folder. 
    This folder is split into two subdirectories:
    - One for holding the actual traffic trace files.
    - Another for storing configuration files related to the traffic workload.

    This structure helps organize and separate the workload data and its configurations 
    for better management and clarity.
    """


    CONFIGS_DIR = "configs"
    TRACES_DIR = "traces"

    def __init__(self, parent_path, name, ghost=False):
        super().__init__(parent_path, name, ghost)
        self.add_dir(name=self.CONFIGS_DIR)
        self.add_dir(name=self.TRACES_DIR)

    def get_traces_dir(self) -> DataDir:
        return self.get_child(self.TRACES_DIR)

    def get_configs_dir(self) -> DataDir:
        return self.get_child(self.CONFIGS_DIR)
    

class SimDir(DataDir):

    """
    Represents the base simulation directory.

    The `SimDir` class serves as a base class for managing the entire simulation directory. 
    It creates some default subfolders and provides basic functionality for organizing 
    and handling the directory structure. 

    By default, it includes essential subfolders, but users can extend this class 
    to add custom folders, such as those for logs or user-specific input files. 
    This flexibility allows tailoring the simulation directory to specific needs.
    """

    NED_DIR = "ned"
    RESULTS_DIR = 'results'
    WORKLOADS_DIR = 'traffic'
    OMNETPP_INI = "omnetpp.ini"


    def __init__(self, parent_path, name):
        self.verify_cwd()
        super().__init__(parent_path, name)
        self.add_dir(name=self.NED_DIR)
        self.add_dir(name=self.RESULTS_DIR)
        self.add_dir(name=self.WORKLOADS_DIR)
        self.add_file(name=self.OMNETPP_INI)
        self.add_sim_dir_package_file()

    def verify_cwd(self):
        """
        Verifies the current working directory.
        
        This method checks whether the current working directory is set to the 
        simulation directory and ensures that a `.simless` file exists in the directory. 
        If either condition is not met, an exception is raised to ensure that 
        operations are performed in the correct context.
        """

        simless_file_path = os.path.join(os.getcwd(), ".simless")
        if not os.path.isfile(simless_file_path):
            raise FileNotFoundError(f"Required file '.simless' not found in {os.getcwd()}. Maybe wrong working directory?")

    def add_sim_dir_package_file(self):
        """
        Adds a package file to the simulation directory.
    
        This method creates a package file within the simulation directory. 
        The package file serves as a reference or configuration file that 
        may be used by the simulation framework or tools to identify and 
        manage the simulation package.
        """
        package_file = self.add_file(name="package.ned")
        package_file.write(f"package simulations.{self.name};\n\n")
        package_file.write(f"@license(MIT);\n")
    
    def get_omnetpp_ini(self) -> DataFile:
        """
        Retrieves the main INI file for the simulation.
    
        This method returns the path or reference to the main INI file within the 
        simulation directory. The main INI file serves as the central configuration 
        file that integrates all other configurations and inputs required for the simulation.
        """
        return self.children[self.OMNETPP_INI]

    def get_workloads_dir(self) -> DataDir:
        """
        Retrieves the workloads directory.
    
        This method returns the path or reference to the directory dedicated to 
        traffic workloads. The workloads directory typically contains subdirectories 
        for traffic trace files and their corresponding configuration files.
        """
        return self.children[self.WORKLOADS_DIR]
    
    def new_wordload_dir(self, name):
        """
        Creates a new workload directory.
    
        This method initializes and adds a new workload directory to the simulation 
        structure. The newly created directory is dedicated to managing traffic 
        workloads, including subdirectories for traffic traces and configurations.
        """
        workloads_dir = self.get_workloads_dir()
        new_dir = WorkloadDir(parent_path=workloads_dir.get_path(), name=name)
        workloads_dir.append_child(new_dir)
        return new_dir
    