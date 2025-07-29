

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class BaseParameter:

    """
    This module defines the basic parameters used in an INI section.

    Each parameter is represented by a key-value pair and includes an `export` 
    function to generate its representation in the INI file format. The module 
    provides the foundational `BaseParameter` class, which can be extended to 
    create more complex parameter types as needed.

    Key Features:
    - Each parameter has a `key`, `value`, and an optional `comment`.
    - Includes functionality to export the parameter in INI format.
    - Provides a base structure for defining additional, more complex parameters.
    """

    def __init__(self, key=None, value=None, comment=None, add_to_details=False):     
        """
        Initializes a new parameter.
    
        Parameters:
        - `key` (str): The key or name of the parameter.
        - `value` (any): The value associated with the parameter.
        - `comment` (str, optional): A comment to add for the parameter, which will 
          be written in the INI section itself.
        - `add_to_details` (bool, optional): A flag indicating whether to include this parameter 
          in the `RunsFrame` description of the simulation.
        """  
        self.key: str = key
        self.value = value
        self.comment: Optional[str] = comment
        self.add_to_details: Optional[bool] = add_to_details

    def as_detail(self):
        """
        Returns the parameter as a dictionary.
    
        The `as_detail` method converts the parameter into a dictionary format, 
        making it suitable for inclusion in the `RunsFrame` description of the simulation.
        The dictionary typically contains the parameter's key and value.
        """
        return {self.key: self.get_value()}
    
    def get_value(self):
        """
        Retrieves the value of the parameter.
    
        The `get_value` method returns the value associated with the parameter. 
        This can be used to access the parameter's value for processing or exporting.
        """
        return self.value

    def export(self):
        """
        Exports the parameter in INI file format.
    
        The `export` method generates a string representation of the parameter 
        in the INI file format. This includes the key, value, and an optional 
        comment if provided.
        """
        return f"{self.key} = {self.get_value()}"

    def __str__(self):
        prm = self.export()
        if self.comment is not None:
            prm += f"   # {self.comment}"
        return prm


class NativeParameter(BaseParameter):
    """
    Represents a native parameter.

    The `NativeParameter` class is a specialized type of parameter that is 
    expected to be in a native format. It extends the `BaseParameter` class 
    and ensures that the value is properly handled and exported in the INI 
    file format.
    """
    def __init__(self, key, value, comment=None, add_to_details=False):
        super().__init__(key, value, comment, add_to_details)

class StrParameter(BaseParameter):
    """
    Represents a string parameter.

    The `StrParameter` class is a specialized type of parameter where the value 
    is expected to be a string. It extends the `BaseParameter` class and ensures 
    that the value is properly handled and exported as a string in the INI file format.
    """

    def __init__(self, key, value, comment=None, add_to_details=False):
        super().__init__(key, value, comment, add_to_details)

    def get_value(self):
        return f"\"{self.value}\""


class IntegerParameter(BaseParameter):
    """
    Represents an integer parameter.

    The `IntegerParameter` class is a specialized type of parameter where the value 
    is expected to be an integer. It extends the `BaseParameter` class and ensures 
    that the value is properly handled and exported as an integer in the INI file format.
    """
    def __init__(self, key, value, comment=None, add_to_details=False):
        super().__init__(key, value, comment, add_to_details)


class BooleanParameter(BaseParameter):
    """
    Represents a boolean parameter.

    The `BooleanParameter` class is a specialized type of parameter where the value 
    is expected to be a boolean (`True` or `False`). It extends the `BaseParameter` 
    class and ensures that the value is properly handled and exported as a boolean 
    in the INI file format, typically represented as `true` or `false`.
    """
    def __init__(self, key, value, comment=None, add_to_details=False):
        super().__init__(key, value, comment, add_to_details)

    def get_value(self):
        return "true" if self.value else "false"
    

class FloutParameter(BaseParameter):
    """
    Represents a float parameter.

    The `FloatParameter` class is a specialized type of parameter where the value 
    is expected to be a floating-point number. It extends the `BaseParameter` class 
    and ensures that the value is properly handled and exported as a float in the 
    INI file format.
    """
    def __init__(self, key, value, comment=None, add_to_details=False):
        super().__init__(key, value, comment, add_to_details)
        

class TimeParameter(BaseParameter):
    """
    Represents a time parameter.

    The `TimeParameter` class is a specialized type of parameter where the value 
    is expected to represent a time duration. It extends the `BaseParameter` class 
    and ensures that the value is properly handled and exported in the INI file 
    format, typically using a time-specific representation (e.g., seconds, milliseconds).
    """
    class Type(Enum):
        NANO_SEC = "ns"
        MICRO_SEC = "us"
        MILI_SEC = "ms"
        SEC = "s"

    def __init__(self, key, value, time_type, comment=None, add_to_details=False):
        super().__init__(key, value, comment, add_to_details)
        self.time_type = time_type

    def get_value(self):
        return f"{self.value}{self.time_type.value}"


class SecTimeParameter(TimeParameter):
    """
    Represents a time parameter in seconds.

    The `SecTimeParameter` class is a specialized type of time parameter where the 
    value is expected to represent a duration in seconds. It extends the `TimeParameter` 
    class and ensures
    """

    def __init__(self, key, value, comment=None, add_to_details=False):
        super().__init__(key, value, TimeParameter.Type.SEC, comment, add_to_details)

class MicroSecTimeParameter(TimeParameter):
    """
    Represents a time parameter in microseconds.

    The `MicroSecTimeParameter` class is a specialized type of time parameter where 
    the value is expected to represent a duration in microseconds. It extends the 
    `TimeParameter` class and ensures that the value is properly handled and exported 
    in the INI file format.
    """
    def __init__(self, key, value, comment=None, add_to_details=False):
        super().__init__(key, value, TimeParameter.Type.MICRO_SEC, comment, add_to_details)


class MiliSecTimeParameter(TimeParameter):
    """
    Represents a time parameter in milliseconds.

    The `MiliSecTimeParameter` class is a specialized type of time parameter where 
    the value is expected to represent a duration in milliseconds. It extends the 
    `TimeParameter` class and ensures that the value is properly handled and exported 
    in the INI file format.
    """
    def __init__(self, key, value, comment=None, add_to_details=False):
        super().__init__(key, value, TimeParameter.Type.MILI_SEC, comment, add_to_details)


class NanoSecTimeParameter(TimeParameter):
    """
    Represents a time parameter in nanoseconds.

    The `NanoSecTimeParameter` class is a specialized type of time parameter where 
    the value is expected to represent a duration in nanoseconds. It extends the 
    `TimeParameter` class and ensures that the value is properly handled and exported 
    in the INI file format.
    """
    def __init__(self, key, value, comment=None, add_to_details=False):
        super().__init__(key, value, TimeParameter.Type.NANO_SEC, comment, add_to_details)




class DataSizeParameter(BaseParameter):

    class Type(Enum):
        bit = "b" # 1 bit
        byte = "B" # 8 bits
        kilobit = "kb" # 1000 bits
        kibibit = "kib" # 1,024 bits
        kilobyte = "kB" # 1,000 bytes
        kibibyte = "KiB" # 1,024 bytes
        megabit = "Mb" # 1000 bytes
        mebibit = "Mib" # 1024^2 bits
        mebibyte = "MiB" # 1024^2 bits
        gigabit = "Gb" # 1000^3 bits
        gibibit = "GiB" # 1024^3 bits


    def __init__(self, key, value, data_size_type, comment=None, add_to_details=False):
        super().__init__(key, value, comment, add_to_details)
        self.data_size_type = data_size_type

    def get_value(self):
        return f"{self.value}{self.data_size_type.value}"


class BitDataSizeParameter(DataSizeParameter):

    def __init__(self, key, value, comment=None, add_to_details=False):
        super().__init__(key, value, DataSizeParameter.Type.bit, comment, add_to_details)

class KibiBitDataSizeParameter(DataSizeParameter):

    def __init__(self, key, value, comment=None, add_to_details=False):
        super().__init__(key, value, DataSizeParameter.Type.kibibit, comment, add_to_details)


class SpeedRateParameter(BaseParameter):
    """
    Represents a speed rate parameter.

    The `SpeedRateParameter` class is a specialized type of parameter where the value 
    is expected to represent a data transfer rate. It extends the `BaseParameter` class 
    and ensures that the value is properly handled and exported in the INI file format 
    with a specific rate type (e.g., bps, kbps, mbps, gbps).

    Key Features:
    - Supports multiple rate types through the `Type` enum.
    - Ensures the value is formatted with the appropriate rate type suffix.
    - Can be extended to create more specific speed rate parameters.

    Attributes:
    - `rate_type` (SpeedRateParameter.Type): The type of speed rate (e.g., bps, kbps, mbps, gbps).

    Methods:
    - `get_value()`: Returns the value of the parameter formatted with the rate type suffix.
    """
    
    class Type(Enum):
        bps = "bps"
        kbps = "kbps"
        mbps = "mbps"
        gbps = "gbps"

    def __init__(self, key, value, rate_type, comment=None, add_to_details=False):
        super().__init__(key, value, comment, add_to_details)
        self.rate_type = rate_type

    def get_value(self):
        return f"{self.value}{self.rate_type.value}"


class BitsPerSecSpeedRateParameter(SpeedRateParameter):

    """Represents a speed rate parameter in bits per second."""

    def __init__(self, key, value, comment=None, add_to_details=False):
        super().__init__(key, value, SpeedRateParameter.Type.bps, comment, add_to_details)

class KiloBitsPerSecSpeedRateParameter(SpeedRateParameter):

    """Represents a speed rate parameter in kilobits per second."""

    def __init__(self, key, value, comment=None, add_to_details=False):
        super().__init__(key, value, SpeedRateParameter.Type.kbps, comment, add_to_details)


class MegaBitsPerSecSpeedRateParameter(SpeedRateParameter):

    """Represents a speed rate parameter in megabits per second."""

    def __init__(self, key, value, comment=None, add_to_details=False):
        super().__init__(key, value, SpeedRateParameter.Type.mbps, comment, add_to_details)


class GigaBitsPerSecSpeedRateParameter(SpeedRateParameter):

    """Represents a speed rate parameter in gigabits per second."""

    def __init__(self, key, value, comment=None, add_to_details=False):
        super().__init__(key, value, SpeedRateParameter.Type.gbps, comment, add_to_details)


class IncludeIniParameter(BaseParameter):
    """
    Represents an include INI parameter.

    The `IncludeIniParameter` class is a specialized type of parameter used to 
    include external INI files within the current configuration. It extends the 
    `BaseParameter` class and ensures that the value is properly handled and 
    exported in the INI file format, typically as an `include` directive.
    """
    def __init__(self, value, comment=None):
        super().__init__("include", comment)
        self.value = value

    def export(self):
        return f"include {self.value}"
    

class ParameterSweeperBase:
    """
    Represents the base class for parameter sweeping.

    The `ParameterSweeperBase` class is used for simulating multiple different 
    values for the same parameter. It provides the foundational structure for 
    defining parameter sweeps, allowing users to explore the impact of varying 
    parameter values on the simulation.

    This is a base class, and users should utilize specific sweep parameter 
    classes that extend this base class to define the desired sweeping behavior.
    """
    def __init__(self, key, values, add_to_details=False):
        self.key = key
        self.values = values
        self.add_to_details=add_to_details

    def build(self):
        pass

class IntegerParameterSweeper(ParameterSweeperBase):
    """
    Represents a parameter sweeper for integer values.

    The `IntegerParameterSweeper` class is a specialized type of parameter sweeper 
    designed to simulate multiple integer values for a parameter. It extends the 
    `ParameterSweeperBase` class and allows users to define a range or set of 
    integer values to be tested in the simulation.
    """
    def __init__(self, key, values, add_to_details=False):
        super().__init__(key, values, add_to_details)
    
    def to_list(self):
        params = []
        for v in self.values:
            params.append(IntegerParameter(key=self.key, value=v, add_to_details=self.add_to_details))
        
        return params


class NativeParameterSweeper(ParameterSweeperBase):

    def __init__(self, key, values, add_to_details=False):
        super().__init__(key, values, add_to_details)
    
    def to_list(self):
        params = []
        for v in self.values:
            params.append(NativeParameter(key=self.key, value=v, add_to_details=self.add_to_details))
        
        return params