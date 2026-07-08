import pytest
from cubesat_thermal.controls import HysteresisThermostat

def test_thermostat_hysteresis():
    # ON below 5.0 C, OFF above 10.0 C
    thermostat = HysteresisThermostat(t_on_c=5.0, t_off_c=10.0, initial_state=False)
    
    # Starts OFF
    assert thermostat.is_on is False
    
    # 8 C (in-between): should remain OFF
    thermostat.update_state(8.0)
    assert thermostat.is_on is False
    
    # 4.9 C (below ON threshold): should turn ON
    thermostat.update_state(4.9)
    assert thermostat.is_on is True
    
    # 7 C (in-between): should remain ON
    thermostat.update_state(7.0)
    assert thermostat.is_on is True
    
    # 10.1 C (above OFF threshold): should turn OFF
    thermostat.update_state(10.1)
    assert thermostat.is_on is False
    
    # 9 C (in-between): should remain OFF
    thermostat.update_state(9.0)
    assert thermostat.is_on is False
    
    # Boundary values check
    thermostat.update_state(5.0) # exactly t_on
    assert thermostat.is_on is True
    
    thermostat.update_state(10.0) # exactly t_off
    assert thermostat.is_on is False
