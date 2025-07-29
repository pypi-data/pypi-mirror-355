import pandas as pd


class RunsFrame:
    """
    Represents a collection of simulation runs.

    The `RunsFrame` class holds all the simulation runs in a dataframe, 
    organizing them for later execution. It stores the necessary information 
    required to execute each simulation, as well as any additional metadata 
    or information the user wants to associate with each simulation run.
    """

    def __init__(self):
        self.frame = pd.DataFrame()
    
    def init_from_dict(self, details: dict):
        """
        Initializes the dataframe from a given dictionary.
    
        The `init_from_dict` method creates a dataframe using the provided Python 
        dictionary. Each key in the dictionary represents a column, and the values 
        are used as the data for the corresponding column in the dataframe.
        """
        self.frame = pd.DataFrame(details)
    
    def set_column(self, col_name, value):
        """
        Sets the value of an entire column in the dataframe.
    
        The `set_column` method updates or creates a column in the dataframe with 
        the specified values. If the column already exists, its values are replaced; 
        otherwise, a new column is added to the dataframe.
        """
        self.frame[col_name] = value

    def add(self, sub_frame):
        """
        Concatenates dataframes.
    
        The `add` method appends new data to the existing dataframe by concatenating 
        it with another dataframe. The input can be a single dataframe or a list of 
        dataframes, and the resulting dataframe will include all rows from both 
        the original and the new data.
        """
        if sub_frame is None:
            return
        self.frame = pd.concat([self.frame, sub_frame], ignore_index=True) 

    def to_csv(self, name):
        """
        Exports the dataframe to a CSV file.
    
        The `to_csv` method saves the current dataframe to a CSV file at the specified 
        file path. This allows the simulation runs and their associated data to be 
        stored in a structured, easily accessible format for further analysis or execution.
        """
        self.frame.to_csv(name, index=False)