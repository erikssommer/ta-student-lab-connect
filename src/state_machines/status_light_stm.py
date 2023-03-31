# Status light state machine
import stmpy
import logging


class StatusLight:

    def __init__(self, name, component):
        self.green_light_off = "../assets/green_off.png"
        self.green_light_on = "../assets/green_light.png"
        self.red_light_on = "../assets/red_light.png"
        self.yellow_light_on = "../assets/yellow_light.png"

        self._logger = logging.getLogger(__name__)
        self.name = name
        self.component = component

    def create_machine(team, component):
        """ Create a state machine for the status light"""
        status_light = StatusLight(name=team, component=component)

        # Define the transitions
        transitions = [
            {'source': 'initial', 'trigger': 't', 'target': 'GREEN', 'effect': 'on_enter_GREEN'},
            {'source': 'GREEN', 'trigger': 't', 'target': 'YELLOW', 'effect': 'on_enter_YELLOW'},
            {'source': 'YELLOW', 'trigger': 't', 'target': 'RED', 'effect': 'on_enter_RED'},
            {'source': 'RED', 'trigger': 't', 'target': 'GREEN', 'effect': 'on_enter_GREEN'},
            {'source': 'GREEN', 'trigger': 'tasks_done', 'target': 'initial', 'effect': 'turn_off'},
        ]

        # Define the state machine
        status_light_stm = stmpy.Machine(
            name=team,
            transitions=transitions,
            obj=status_light
        )

        status_light.stm = status_light_stm

        return status_light_stm
    
    def start_timer(self, time):
        self.stm.start_timer('t', time)
    
    def on_enter_GREEN(self):
        self._logger.debug("Entering GREEN state")
        self.component.set_status_light(self.green_light_on)

    def on_enter_YELLOW(self):
        self._logger.debug("Entering YELLOW state")
        self.component.set_status_light(self.yellow_light_on)

    def on_enter_RED(self):
        self._logger.debug("Entering RED state")
        self.component.set_status_light(self.red_light_on)

    def on_exit_GREEN(self):
        self._logger.debug("Exiting GREEN state")
        self.component.set_status_light(self.green_light_off)

    def turn_off(self):
        self.component.set_status_light(self.green_light_off)
