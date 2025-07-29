

from typing import List


class JobDescription:
    """
    Represents a job description in a simulation.

    The `JobDescription` class serves as a base class for the user to describe 
    a job in a simulation. A simulation can have several jobs running together, 
    and this class provides the structure to define the details of one of those jobs.

    Users can extend this class to add custom attributes or behavior specific 
    to their simulation jobs.
    """
    def __init__(self):
        self.name = "job"

    def get_details(self):
        """
        Retrieves the details of the job.
    
        The `get_details` method returns the details of the job as a dictionary. 
        These details are used to include information about the job in the `RunsFrame`, 
        allowing the job's metadata to be tracked and analyzed as part of the simulation.
        """
        return {}


class WorkloadDescription:
    """
    Represents the workload description for a simulation.

    The `WorkloadDescription` class describes the entire traffic in a single simulation. 
    It encompasses all the jobs running together in the simulation, providing a 
    comprehensive view of the workload and its configuration.

    This class allows users to define and manage the traffic workload as a whole, 
    ensuring that all jobs are properly described and accounted for.
    """
    def __init__(self, name, job_descriptions = []):
        self.name = name # The name of the workload
        self.job_descriptions: List[JobDescription] = job_descriptions # The list of job descriptions in the workload
        
        self.workload_id = None # The workload ID, set bt the workload manager
        self.allocation_config_file = None # The allocation configuration file for the workload, set by the workload manager

        # Assign unique names to the job descriptions
        for idx, job_desc in enumerate(self.job_descriptions):
            job_desc.name += f"{idx}"