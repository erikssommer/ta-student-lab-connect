# Student group state machine
import stmpy
import logging

MQTT_TOPIC_INPUT = 'input'

class GroupLogic:
    """ State machine for a group client """
    def __init__(self, name, component, logger):
        self._logger: logging.Logger = logger
        self.name = name
        self.component = component


    def create_machine(team, component, logger):
        """ Create the state machine for a group client """
        group_logic = GroupLogic(name=team, component=component, logger=logger)

        # Define the transitions
        init = {'source': 'initial', 'target': 'not_working_on_task'}

        # Define the transitions where the task is started
        task_start1 = {'trigger': 'task_start', 'source': 'not_working_on_task', 'target': 'working_on_task'}
        task_start2 = {'trigger': 'task_start', 'source': 'working_on_task', 'target': 'working_on_task'}

        # Define the transitions where group is waiting for help
        waiting_for_help1 = {'trigger': 'request_help', 'source': 'working_on_task', 'target': 'waiting_for_help'}

        # Define the transitions where group is receiving help
        receiving_help1 = {'trigger': 'receive_help', 'source': 'waiting_for_help', 'target': 'receiving_help'}

        # Define the transitions where group has recieved help and is working on next task
        received_help1 = {'trigger': 'received_help', 'source': 'receiving_help', 'target': 'working_on_task'}

        # Define the transitions where all the tasks is finished
        tasks_done1 = {'trigger': 'tasks_done', 'source': 'working_on_task', 'target': 'finished', 'effect': 'finished()'}

        # Define the state machine
        group_stm = stmpy.Machine(
            name=team,
            transitions=[init, task_start1, task_start2, waiting_for_help1, receiving_help1, received_help1, tasks_done1],
            obj=group_logic,
        )

        group_logic.stm = group_stm

        return group_stm
    
    def started(self):
        self._logger.info('Group {} started'.format(self.name))
        self.stm.start()

    def finished(self):
        self._logger.info('Group {} finished'.format(self.name))
        self.stm.terminate()

    def report_status(self, status):
        self._logger.info('Group {} reported status {}'.format(self.name, status))
        message = {'group': self.name, 'status': status}
        self.component.mqtt_client.publish_message(MQTT_TOPIC_INPUT, message)