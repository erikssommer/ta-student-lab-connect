# TA state machine
import stmpy
import logging


class TaSTM:
    def __init__(self, name, component, logger):
        self._logger: logging.Logger = logger
        self.name = name
        self.component = component
        self.help_duration_timer = 10000

    def create_machine(ta, component, logger):
        """ Create the state machine for a TA client """
        ta_obj = TaSTM(name=ta, component=component, logger=logger)

        # Define the states
        logged_on = {
            'name': 'logged_on'
            }
        
        helping_group = {
            'name': 'helping_group',
            'entry': 'help_group()', 
            'exit': 'help_recieved()'
            }
        
        not_helping_group = {
            'name': 'not_helping_group'
            }

        # Define the transitions
        init = {
            'source': 'initial',
            'target': 'logged_on', 
            'effect': 'started()'
            }

        t_publish_tasks = {
            'trigger': 'publish_tasks',
            'source': 'logged_on', 
            'target': 'not_helping_group'
            }

        # Define the transitions to helping a group
        t_helping_group = {
            'trigger': 'help_group',
            'source': 'not_helping_group',
            'target': 'helping_group', 
            'effect': 'start_giving_help_timer()'
            }

        t_helping_group_timer_expired = {
            'trigger': 't',
            'source': 'helping_group',
            'target': 'helping_group', 
            'effect': 'notify_ta_helping_timer_expired()'
            }

        # Define the transitions to not helping a group
        t_not_helping_group = {
            'trigger': 'help_recieved', 
            'source': 'helping_group',
            'target': 'not_helping_group', 
            'effect': 'stop_giving_help_timer()'
            }

        # Define the state machine
        ta_stm = stmpy.Machine(
            name=ta,
            states=[logged_on, helping_group, not_helping_group],
            transitions=[init, t_publish_tasks, t_helping_group, t_helping_group_timer_expired, t_not_helping_group],
            obj=ta_obj,
        )

        ta_obj.stm = ta_stm
gi
        return ta_stm
    
    def started(self):
        self._logger.info(f'TA {self.name} has started')

    def help_group(self):
        self._logger.info(f'TA {self.name} is helping a group')
        # Updating the queue number for the groups when a TA is helping a group
        self.component.set_helping_group(True)
        self.component.send_new_queue_number_to_groups()

    def start_giving_help_timer(self):
        self._logger.info(f'TA {self.name} is starting the help timer')
        self.stm.start_timer('t', self.help_duration_timer)

    def stop_giving_help_timer(self):
        self._logger.info(f'TA {self.name} is stopping the help timer')
        self.stm.stop_timer('t')

    def notify_ta_helping_timer_expired(self):
        self._logger.info(
            f'TA {self.name} is notifying the group that help is on the way')
        self.component.notify_ta_to_finish_helping()

    def help_recieved(self):
        self.component.set_helping_group(False)
        self._logger.info(f'TA {self.name} recieved a group help')
