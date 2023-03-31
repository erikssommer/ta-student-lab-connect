# Status light state machine
import stmpy
import logging


class StatusLight:

    def __init__(self, name, component):
        self.green_light_off = open("../assets/green_off.png", "rb").read()
        self.green_light_on = open("../assets/green_light.png", "rb").read()
        self.red_light_on = open("../assets/red_light.png", "rb").read()
        self.yellow_light_on = open("../assets/yellow_light.png", "rb").read()

        self._logger = logging.getLogger(__name__)
        self.name = name
        self.component = component

    def create_machine(team, component):
        """ Create a state machine for the status light"""
        status_light = StatusLight(name=team, component=component)

        # Define the transitions
        transitions = [
            {'source': 'initial', 'trigger': 't', 'target': 'GREEN'},
            {'source': 'GREEN', 'trigger': 't', 'target': 'YELLOW'},
            {'source': 'YELLOW', 'trigger': 't', 'target': 'RED'},
            {'source': 'RED', 'trigger': 't', 'target': 'GREEN'},
        ]

        # Define the state machine
        status_light_stm = stmpy.Machine(
            name=team,
            transitions=transitions,
            obj=status_light
        )

        status_light.stm = status_light_stm

        return status_light_stm
