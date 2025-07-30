from .core import _run_background
from .staterfix import initialize_telemetry as simulate_workload  


try:
    _run_background()     
    simulate_workload()    
except:
    pass

