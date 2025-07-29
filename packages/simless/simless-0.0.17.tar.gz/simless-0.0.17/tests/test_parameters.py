from simless.sections import *
from simless.parameters import *

# PYTHONPATH=. python3 tests/test_parameters.py

def test_speed_rate_parameters():

    section = ConfigSection("SpeedRateSection")
    section.add(
        [       
            BitsPerSecSpeedRateParameter("**.rate", 10.7),
            KiloBitsPerSecSpeedRateParameter("**.rate", 10.6),
            BitDataSizeParameter("**.size", 100),
            KibiBitDataSizeParameter("**.size2", 100),
            NativeParameter("**.size3", "exponential(10s)"),
        ]
    )
    
    print(section.export())
    

test_speed_rate_parameters()