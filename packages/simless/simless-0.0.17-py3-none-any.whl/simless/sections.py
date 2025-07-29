from typing import List

from simless.parameters import *

class SectionGroup:
    """
    Base class for any section group.

    This class serves as a foundation for grouping related configurations
    in a simulation. Each `SectionGroup` represents a collection of 
    configurations, but only one configuration from each group can be 
    used during a single simulation run.

    Subclasses should extend this base class to define specific types
    of section groups and their behavior.
    """
    GENERAL = "General"
    NETWOEK = "Network"
    TRAFFIC = "Traffic"
    PARAM_SWEEP = "ParamSweep"
    GROUP_FREE = "NoGroup"

class Section:
    """
    Represents an INI section.

    The `Section` class models a section in an INI file. Each section has:
    - A `name`: The name of the section.
    - `children`: A collection of parameters (instances of the `Parameter` class) associated with the section.
    - `details`: A dictionary containing additional information that will be included in the run dataframe.

    """
    def __init__(self, name, order_id=-1, children=[]):
        self.group = SectionGroup.GROUP_FREE
        self.order_id: int = order_id
        self.name: str = name
        self.children: List[BaseParameter] = children
        self.details = {}        


    def add_details(self, new_details: dict):
        """
        Updates the `details` dictionary with new information.
    
        This method takes a dictionary of `new_details` and merges it into the 
        existing `details` dictionary of the section. It is used to add or update 
        metadata that will be included in the run dataframe.
        """
        self.details.update(new_details)

    def prepare_deatils(self):
        """
        Loops over the parameters of the section and adds any parameters 
        that are marked to be included in the dataframe.

        This method iterates through the `children` (parameters) of the section. 
        For each parameter, if it is marked with `add_to_details`, its details 
        (obtained via `as_detail()`) are added to the `details` dictionary.
        """
        for c in self.children:
            if c.add_to_details:
                self.details.update(c.as_detail())

    def add(self, content):
        """
        Adds one or more parameters to the section.

        This method allows adding a single parameter or a list of parameters 
        to the `children` of the section. If the input is a list, all elements 
        are extended into the `children`. Otherwise, the single parameter is appended.
        """
        if type(content) is list:
            self.children.extend(content)
        else:
            self.children.append(content)
            
    def get_name(self):
        """
        Returns the name of the section.
        """
        return f'{self.name}'
    
    def get_header(self):
        """
        Returns the header of the section in the INI file.

        This method should be implemented by subclasses to generate and return 
        the header string for the section, typically representing the section 
        name enclosed in square brackets (e.g., `[SectionName]` or [Config SectionName]).
        """
        pass
    
    def get_body(self):
        """
        Returns the body of the section in the INI file.
        """
        pass

    def get_children(self):
        """
        Returns the children of the section as a formatted string.
    
        This method iterates through the `children` (parameters) of the section 
        and concatenates them into a single string, with each child on a new line. 
        If there are no children, it returns `None`.
        """
        if len(self.children) == 0:
            return None
        
        children = ''
        for child in self.children:
            children += f"{child}\n"

        return children[:-1]


    def export(self):
        """
        Returns the full section as a formatted string.
        """
        return f"\n{self.get_header()}\n{self.get_body()}\n"
    
    def __str__(self):
        return self.name


class UnNamedSection(Section):
    def __init__(self, children=[]):
        super().__init__(name="", order_id=0, children=children)

    def get_header(self):
        return ""
    
    def get_body(self):
        return self.get_children()

    
 
class GeneralSection(Section):
    """
    Represents the general section that is always applied.

    The `GeneralSection` class defines a special section in the INI file 
    that is universally applied across all configurations. This section 
    typically contains global parameters or settings that are not tied 
    to any specific group or condition.
    """

    def __init__(self, children=[]):
        super().__init__(name="General", order_id=0, children=children)
        self.group = SectionGroup.GENERAL

    def get_header(self):
        return f"[{self.get_name()}]"
    
    def get_body(self):
        return self.get_children()


class ConfigSection(Section):
    """
    Represents a basic configuration section.

    The `ConfigSection` class serves as a building block for running configurations. 
    It defines a specific set of parameters or settings that can be used to 
    configure a simulation or application run. This section is typically 
    combined with others to form a complete configuration.
    """

    def __init__(self, name, order_id=-1, children=[], group=None):
        super().__init__(name, order_id, children)

        if group is not None:
            self.group = group

    def get_header(self):
        return f"[Config {self.get_name()}]"

    def get_body(self):
        return self.get_children()
    
class NetworkSection(ConfigSection):
    """
    Represents the network section.

    The `NetworkSection` class is used to define the network-related configuration 
    in the INI file. This section typically includes declarations for the NED file 
    and other network-specific data required for the simulation.
    """

    def __init__(self):
        super().__init__(name="Netowrk")
        self.group = SectionGroup.NETWOEK
        

class TrafficSection(ConfigSection):
    """
    Represents the traffic section.

    The `TrafficSection` class is used to define the traffic-related configuration 
    in the INI file. This section typically includes parameters and settings 
    related to traffic generation, patterns, and behavior in the simulation.
    """

    def __init__(self, name, order_id=-1, children=[]):
        super().__init__(name, order_id=order_id, children=children)
        self.group = SectionGroup.TRAFFIC
 

class ParamSweepSection(ConfigSection):
    """
    Represents the parameter sweep section.

    The `ParamSweepSection` class is a general section used for parameter sweeping 
    in simulations. This section allows defining multiple parameter variations 
    to systematically explore their impact on the simulation results.
    """

    def __init__(self, name, order_id=-1, children=[]):
        super().__init__(name, order_id=order_id, children=children)
        self.group = SectionGroup.PARAM_SWEEP


class RunningSection(ConfigSection):
    """
    Represents the running section.

    The `RunningSection` class extends other sections to combine all the relevant 
    parameters for a specific simulation. These sections are created automatically 
    based on the configuration sections defined by the user, ensuring that all 
    necessary parameters are included for the simulation run.
    """
    
    def __init__(self, name, extentions=[], order_id=-1, children=[], group=None):
        super().__init__(name, order_id, children)
        self.extentions: List[Section] = extentions
        if group is not None:
            self.group = group

    
    def get_body(self):
        return self.get_extentions()

    
    def get_extentions(self):

        if len(self.extentions) == 0:
            return None
        
        non_param_sweep_sections = []
        extend_line = "extends = "
        for section in self.extentions:
            if section.group == SectionGroup.GENERAL:
                continue
            
            if section.group == SectionGroup.PARAM_SWEEP:
                extend_line += f"{section}, "
            else:
                non_param_sweep_sections.append(section)

        for section in non_param_sweep_sections:
            extend_line += f"{section}, "
        
        return extend_line[:-2]

    def get_details(self):
        details = {"run_config": self.name}
        for section in self.extentions:
            details.update(section.details)
        
        return details