


from typing import List

from simless.runs_frame import RunsFrame
from simless.simulation import Simulation


class Runner:
    """
    Manages and executes a list of simulations.

    The `Runner` class is responsible for taking a list of `Simulation` objects, 
    collecting their dataframes, and executing them. It consolidates the simulation 
    runs and ensures they are executed in the desired order or configuration.

    The actual implementation of the simulations and their execution logic is left 
    to the user, allowing flexibility in defining how the simulations are run and 
    how their results are handled.
    """
    
    def __init__(self, simulations = []):
        self.simulation: List[Simulation] = simulations
        self.runs_frame = RunsFrame()
    
    def prepare_runs_frame(self):
        for sim in self.simulation:
            self.runs_frame.add(sim.runs_frame.frame)
    
    def run(self):
        pass


