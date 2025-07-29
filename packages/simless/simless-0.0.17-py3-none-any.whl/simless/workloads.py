
from typing import List

from simless.runs_frame import RunsFrame
from simless.sections import Section, TrafficSection
from simless.sim_dir import DataDir, SimDir, WorkloadDir
from simless.topology import Topology

    

class JobAllocator:
    """
    Allocates hosts to jobs in a simulation.

    The `JobAllocator` class is responsible for taking a `WorkloadDescription` 
    and a `Topology` object and allocating actual hosts from the topology to 
    the jobs defined in the workload. 

    This is a base class, and the user must implement the allocation logic 
    by extending this class to suit their specific simulation requirements.
    """
        

    def allocate(self, workload_descriptor, topology):
        """
        Allocates hosts to jobs based on the workload and topology.
    
        The `allocate` method assigns actual hosts from the topology to the jobs 
        defined in the workload description. This method must be implemented by 
        subclasses to define the specific allocation logic for the simulation.
        """
        raise NotImplementedError()


class Job:
    """
    Represents a specific job in the simulation.

    The `Job` class takes a job descriptor and converts it into a specific job 
    object based on the descriptor's details. This object is responsible for 
    creating the actual trace files required for the job 
    to run in the simulation.
    """

    def __init__(self, job_descriptor):
        self.job_descriptor = job_descriptor

    def get_name(self):
        return self.job_descriptor.name
    
    def build(self, base_dir: DataDir):
        """
        Creates the necessary files for the job.
    
        The `build` function generates the actual trace files and configuration files 
        required for the job. This function ensures that all the resources needed 
        for the job to run in the simulation are properly created and stored.

        'base_dir' is the directory where the job files should be stored.
        """
        raise NotImplementedError()
        

class Workload:

    """
    Converts a workload description into files and configurations.

    The `Workload` class takes a `WorkloadDescription` object and generates 
    the actual trace files and configuration files needed for the simulation. 
    It ensures that all jobs described in the workload are properly represented 
    and prepared for execution.
    """

    JOB_MODEL = Job # The job model to use
    JOB_ALLOCATOR_MODEL = JobAllocator # The job allocator model to use

    def __init__(self, workload_dir, workload_description):
        self.workload_dir: WorkloadDir = workload_dir
        self.workload_description = workload_description  
    
    def build_traces(self):
        """
        Generates the trace files for the workload.
    
        The `build_traces` method creates the actual trace files for all the jobs 
        described in the workload. These trace files define the traffic patterns 
        and behaviors required for the simulation.
        """
        job_descriptors = self.workload_description.job_descriptions
        workload_dir = self.workload_dir
        for job_description in job_descriptors:
            job = self.JOB_MODEL(job_description)
            job.build(workload_dir.get_traces_dir())

    def build_configs(self):
        # create the config files needed for this workload (e.g., ini files for allocation)
        pass

    def build_traffic_section(self):
        # create the traffic section for this workload
        pass

    def add_traffic_details(self, traffic_section: TrafficSection):
        # add details to the traffic section to be included in the runs frame

        num_jobs = len(self.workload_description.job_descriptions)
        traffic_section.add_details({
            'num_jobs': len(self.workload_description.job_descriptions),
        })

        if num_jobs == 0:
            return
        else:
            for job_desc in self.workload_description.job_descriptions:
                details = job_desc.get_details()
                job_name = job_desc.name
                details = {job_name + "_" + key: value for key, value in details.items()}
                traffic_section.add_details(details)

    def build(self):
        # build the workload files, configurations, and traffic section.
        self.build_traces()
        self.build_configs()
        section = self.build_traffic_section()
        self.add_traffic_details(section)
        return section
    
    def allocate(self, topology):
        # allocate the jobs in the workload to the topology
        job_allocator = self.JOB_ALLOCATOR_MODEL()
        job_allocator.allocate(
                workload_descriptor=self.workload_description, 
                topology=topology
        )


class WorkloadManager:

    """
    Manages multiple workloads for a simulation.

    The `WorkloadManager` class allows handling multiple `Workload` objects 
    for the same `Simulation` object. Each workload runs in a separate simulation, 
    enabling the user to test different traffic patterns or configurations. 
    The `WorkloadManager` helps in creating and organizing these workloads 
    efficiently.
    """

    WORKLOAD_OBJECT_MODEL = Workload # The workload model to use

    def __init__(self):
        self.workloads: List[Workload] = []
        self.curr_workload_id = 0
        self.sim_dir: SimDir = None

    def set_sim_dir(self, sim_dir):
        """
        Sets the simulation directory for workloads.
    
        The `set_sim_dir` method specifies the directory where all workload-related 
        data, including trace files and configurations, should be stored. This ensures 
        that all generated files are organized in the appropriate location.
        """
        self.sim_dir = sim_dir

    def _update_descriptor_id(self, descriptor):
        """
        Updates the descriptor ID for workloads.
    
        The `_update_descriptor_id` method assigns or updates a unique identifier 
        for each workload descriptor. This ensures that each workload can be 
        uniquely identified and tracked within the simulation.
        """
        descriptor.workload_id = self.curr_workload_id
        self.curr_workload_id += 1

    def build(self):
        """
        Builds all workloads and collects their traffic sections.
    
        The `build` method generates the trace files and configurations for all 
        workloads managed by the `WorkloadManager`. It also collects the traffic 
        sections from each workload to be included in the simulation configuration.
        """
        workload_sections = [workload.build() for workload in self.workloads]
        return workload_sections
    

    def _create_and_store_workload(self, workload_dir, workload_descriptor):
        """
        Creates and stores a new workload.
    
        The `_create_and_store_workload` method initializes a new `Workload` object 
        based on the provided workload description, builds it, and stores it in 
        the `WorkloadManager`. This ensures the workload is properly prepared and 
        managed for the simulation.
        """
        workload = self.WORKLOAD_OBJECT_MODEL(
            workload_dir=workload_dir, 
            workload_description=workload_descriptor
        )
        self.workloads.append(workload)
        return workload
    
    def new_workload(self, workload_descriptor):
        """
        Creates and adds a new workload.
    
        The `new_workload` method generates a new workload based on the provided 
        workload description and adds it to the `WorkloadManager`. This allows 
        users to define and include additional workloads for the simulation.
        """

        self._update_descriptor_id(workload_descriptor)

        workload_dir = self.sim_dir.new_wordload_dir(name=workload_descriptor.name)
        workload = self._create_and_store_workload(workload_dir, workload_descriptor)

        return workload
    
    def allocate(self, topology: Topology):
        """
        Allocates hosts for all workloads.
    
        The `allocate` method assigns hosts from the topology to all workloads 
        managed by the `WorkloadManager`. This ensures that each job within the 
        workloads has the necessary resources allocated for the simulation.
        """
        for workload in self.workloads:
            workload.allocate(topology)


