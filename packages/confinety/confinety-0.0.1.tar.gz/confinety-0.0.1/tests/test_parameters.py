from confinety.sections import *
from confinety.parameters import *
from confinety.configurations import *

# PYTHONPATH=. python3 tests/test_parameters.py

def test_speed_rate_parameters():

    speed_section = ConfigSection(name="SpeedRateSection1", group="SpeedRateSection")
    speed_section.add(
        [       
            BitsPerSecSpeedRateParameter("**.rate", 10.7),
            KiloBitsPerSecSpeedRateParameter("**.rate", 10.6),
            BitDataSizeParameter("**.size", 100),

        ]
    )
    
    speed_section2 = ConfigSection(name="SpeedRateSection2", group="SpeedRateSection")
    speed_section2.add(
        [       
            BitsPerSecSpeedRateParameter("**.rate", 15.6),
            KiloBitsPerSecSpeedRateParameter("**.rate", 11.6),
            BitDataSizeParameter("**.size", 150),
        ]
    )
    

    conf_file = Configurations(
        sections=[
            speed_section,
            speed_section2
        ]
    )
    
    ini = conf_file.export()
    print(ini)

test_speed_rate_parameters()