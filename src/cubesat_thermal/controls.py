"""
Heater thermostat control logic with hysteresis.
"""

class HysteresisThermostat:
    def __init__(self, t_on_c: float, t_off_c: float, initial_state: bool = False):
        """
        Initializes the thermostat.
        t_on_c: Temperature below which heater turns ON [°C]
        t_off_c: Temperature above which heater turns OFF [°C]
        initial_state: Initial heater state (True = ON, False = OFF)
        """
        if t_on_c >= t_off_c:
            raise ValueError(f"Heater ON limit ({t_on_c} °C) must be less than OFF limit ({t_off_c} °C)")
        self.t_on_c = t_on_c
        self.t_off_c = t_off_c
        self.is_on = initial_state

    def update_state(self, current_temp_c: float) -> bool:
        """
        Updates the heater state based on current temperature in Celsius.
        The state is updated only after accepting the temperature state.
        
        Returns:
            bool: new heater state
        """
        if current_temp_c <= self.t_on_c:
            self.is_on = True
        elif current_temp_c >= self.t_off_c:
            self.is_on = False
        # If in-between, retain the previous state
        return self.is_on

    def get_power(self, heater_power_w: float) -> float:
        """
        Returns the power output [W] based on current state.
        """
        return heater_power_w if self.is_on else 0.0
