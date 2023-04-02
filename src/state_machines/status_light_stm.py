# Status light state machine
import stmpy
import logging


class StatusLight:

    def __init__(self, name, duration, component, logger):
        self.green_light_off = "../assets/green_off.png"
        self.green_light_on = "../assets/green_light.png"
        self.red_light_on = "../assets/red_light.png"
        self.yellow_light_on = "../assets/yellow_light.png"

        self._logger = logger
        self.name = name
        self.duration = self.convert_duration_to_milliseconds(duration)
        self.light_duration = self.duration / 2

        self.component = component

    def create_machine(team, duration, component, logger):
        """ Create a state machine for the status light"""
        status_light = StatusLight(name=team, duration=duration, component=component, logger=logger)

        # Define the transitions
        transitions = [
            {'source': 'initial', 'target': 'green', 'effect': 'on_enter_green(); start_light_timer()'},
            {'trigger': 't', 'source': 'green', 'target': 'yellow', 'effect': 'on_enter_yellow(); stop_timer("t"); start_light_timer()'},
            {'trigger': 't', 'source': 'yellow', 'target': 'red', 'effect': 'on_enter_red'},
        ]

        # Define the state machine
        status_light_stm = stmpy.Machine(
            name=team,
            transitions=transitions,
            obj=status_light
        )

        status_light.stm = status_light_stm

        return status_light_stm
    
    def convert_duration_to_milliseconds(self, duration):
        # Convert duration into integer
        duration_in_minutes = int(duration)
        duration_in_milliseconds = duration_in_minutes * 60 * 1000
        return duration_in_milliseconds
    
    def start_light_timer(self):
        self.stm.start_timer("t", self.light_duration)

    def stop_light_timer(self):
        self.stm.stop_timer("t")
    
    def on_enter_green(self):
        self._logger.debug("Entering GREEN state")
        self.component.set_status_light(self.green_light_on)

    def on_enter_yellow(self):
        self._logger.debug("Entering YELLOW state")
        self.component.set_status_light(self.yellow_light_on)

    def on_enter_red(self):
        self._logger.debug("Entering RED state")
        self.component.set_status_light(self.red_light_on)

    def on_exit_green(self):
        self._logger.debug("Exiting GREEN state")
        self.component.set_status_light(self.green_light_off)

    def turn_off(self):
        self.component.set_status_light(self.green_light_off)
