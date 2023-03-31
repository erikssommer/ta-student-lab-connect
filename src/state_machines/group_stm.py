# Student group state machine
import stmpy
import logging

MQTT_TOPIC_INPUT = 'input'

class GroupLogic:
    """ State machine for a group client """
    def __init__(self, name, stage, component):
        self._logger = logging.getLogger(__name__)
        self.name = name
        self.stage = stage
        self.component = component


    def create_machine(team, stage, component):
        """ Create the state machine for a group client """
        group_logic = GroupLogic(name=team, stage=stage, component=component)

        # TODO: Define the states
        states = [
            {'name': 'INIT', 'entry': 'init'},
            {'name': 'WAITING', 'entry': 'waiting'},
            {'name': 'WORKING', 'entry': 'working'},
            {'name': 'DONE', 'entry': 'done'},
            {'name': 'FINISHED', 'entry': 'finished'},
        ]

        # TODO: Define the transitions
        transitions = [
            {'source': 'INIT', 'target': 'WAITING'},
            {'source': 'WAITING', 'target': 'WORKING'},
            {'source': 'WORKING', 'target': 'DONE'},
            {'source': 'DONE', 'target': 'FINISHED'},
            {'source': 'FINISHED', 'target': 'INIT'},
        ]

        # Define the state machine
        group_stm = stmpy.Machine(
            name=team,
            transitions=transitions,
            obj=group_stm,
            states=states,
        )

        group_logic.stm = group_stm

        return group_stm
    
    def started(self):
        self._logger.info('Group {} started'.format(self.name))
        self.stm.start()

    def finished(self):
        self._logger.info('Group {} finished'.format(self.name))
        self.stm.stop()

    def report_status(self, status):
        self._logger.info('Group {} reported status {}'.format(self.name, status))
        message = {'group': self.name, 'status': status}
        self.component.mqtt_client.publish_message(MQTT_TOPIC_INPUT, message)