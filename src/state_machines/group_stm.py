# Student group state machine
import stmpy
import logging


class GroupSTM:
    """ State machine for a group client """

    def __init__(self, name, component, logger):
        self._logger: logging.Logger = logger
        self.name = name
        self.component = component
        self.waiting_for_help_timer = 10000

    def create_machine(team, component, logger):
        """ Create the state machine for a group client """
        group_obj = GroupSTM(name=team, component=component, logger=logger)

        # Define the states
        logged_on = {
            'name': 'logged_on'
        }

        not_working_on_task = {
            'name': 'not_working_on_task'
        }

        working_on_task = {
            'name': 'working_on_task'
        }

        waiting_for_help = {
            'name': 'waiting_for_help',
            'entry': 'start_waiting_for_help_timer()', 
            'exit': 'stop_waiting_for_help_timer()'
        }

        # Define the transitions
        init = {
            'source': 'initial',
            'target': 'logged_on'
        }

        # Define the transitions where the task is started
        tasks_recieved = {
            'trigger': 'tasks_received',
            'source': 'logged_on',
            'target': 'working_on_task'
        }

        task_start1 = {
            'trigger': 'task_start',
            'source': 'not_working_on_task',
            'target': 'working_on_task',
            'effect': 'task_start()'
        }

        task_start2 = {
            'trigger': 'task_start',
            'source': 'working_on_task',
            'target': 'working_on_task',
            'effect': 'task_start()'
        }

        # Define the transitions where group is waiting for help
        waiting_for_help1 = {
            'trigger': 'request_help',
            'source': 'working_on_task',
            'target': 'waiting_for_help',
            'effect': 'request_help()'
        }

        waiting_for_help2 = {
            'trigger': 'request_help',
            'source': 'not_working_on_task',
            'target': 'waiting_for_help',
            'effect': 'request_help()'
        }
        
        t_waiting_for_help = {
            'trigger': 't', 'source':
            'waiting_for_help', 'target':
            'waiting_for_help',
            'effect': 'report_timer()'
        }

        # Define the transitions where group is receiving help
        receiving_help1 = {
            'trigger': 'receive_help',
            'source': 'waiting_for_help',
            'target': 'receiving_help',
            'effect': 'receiving_help()'
        }

        # Define the transitions where group has recieved help and is working on next task
        received_help1 = {
            'trigger': 'received_help',
            'source': 'receiving_help',
            'target': 'working_on_task', 
            'effect': 'recieved_help()'
        }

        # Define the transitions where all the tasks is finished
        tasks_done1 = {
            'trigger': 'tasks_done',
            'source': 'working_on_task',
            'target': 'finished', 
            'effect': 'finished()'
        }

        # Define the state machine
        group_stm = stmpy.Machine(
            name=team,
            states=[logged_on, not_working_on_task, working_on_task, waiting_for_help],
            transitions=[init, tasks_recieved, task_start1, task_start2, waiting_for_help1,
                         waiting_for_help2, t_waiting_for_help, receiving_help1, received_help1, tasks_done1],
            obj=group_obj,
        )

        group_obj.stm = group_stm

        return group_stm

    def task_start(self):
        self._logger.info(f'Group {self.name} is working on a new task')

    def request_help(self):
        self._logger.info(f'Group {self.name} is requesting help')
        self.component.request_help()

    def start_waiting_for_help_timer(self):
        self._logger.info(f'Group {self.name} is waiting for help')
        self.stm.start_timer('t', self.waiting_for_help_timer)

    def report_timer(self):
        self._logger.info(f'Group {self.name} is still waiting for help after {self.waiting_for_help_timer / 1000} seconds')

    def receiving_help(self):
        self._logger.info(f'Group {self.name} is receiving help')
        self.component.receiving_help()
    
    def stop_waiting_for_help_timer(self):
        self._logger.info(f'Group {self.name} is no longer waiting for help')
        self.stm.stop_timer('t')

    def recieved_help(self):
        self._logger.info(f'Group {self.name} recieved help')
        self.component.received_help()

    def finished(self):
        self._logger.info(f'Group {self.name} finished')
        self.stm.terminate()
