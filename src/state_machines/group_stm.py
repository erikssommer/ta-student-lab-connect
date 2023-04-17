# Student group state machine
import stmpy
import logging

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
        init = {'source': 'initial', 'target': 'not_working_on_task', 'effect': 'started()'}

        # Define the transitions where the task is started
        task_start1 = {'trigger': 'task_start', 'source': 'not_working_on_task', 'target': 'working_on_task', 'effect': 'task_start()'}
        task_start2 = {'trigger': 'task_start', 'source': 'working_on_task', 'target': 'working_on_task', 'effect': 'task_start()'}

        # Define the transitions where group is waiting for help
        waiting_for_help1 = {'trigger': 'request_help', 'source': 'working_on_task', 'target': 'waiting_for_help', 'effect': 'request_help()'}
        waiting_for_help2 = {'trigger': 'request_help', 'source': 'not_working_on_task', 'target': 'waiting_for_help', 'effect': 'request_help()'}

        # Define the transitions where group is receiving help
        receiving_help1 = {'trigger': 'receive_help', 'source': 'waiting_for_help', 'target': 'receiving_help', 'effect': 'receiving_help()'}

        # Define the transitions where group has recieved help and is working on next task
        received_help1 = {'trigger': 'received_help', 'source': 'receiving_help', 'target': 'working_on_task', 'effect': 'recieved_help()'}

        # Define the transitions where all the tasks is finished
        tasks_done1 = {'trigger': 'tasks_done', 'source': 'working_on_task', 'target': 'finished', 'effect': 'finished()'}

        # Define the state machine
        group_stm = stmpy.Machine(
            name=team,
            transitions=[init, task_start1, task_start2, waiting_for_help1, waiting_for_help2, receiving_help1, received_help1, tasks_done1],
            obj=group_logic,
        )

        group_logic.stm = group_stm

        return group_stm
    
    def started(self):
        self._logger.info(f'Group {self.name} started')
        self.stm.start()

    def task_start(self):
        self._logger.info(f'Group {self.name} is working on a new task')

    def request_help(self):
        self._logger.info(f'Group {self.name} is requesting help')
        self.component.request_help()

    def receiving_help(self):
        self._logger.info(f'Group {self.name} is receiving help')
        self.component.receiving_help()

    def recieved_help(self):
        self._logger.info(f'Group {self.name} recieved help')
        self.component.received_help()

    def finished(self):
        self._logger.info(f'Group {self.name} finished')
        self.stm.terminate()
