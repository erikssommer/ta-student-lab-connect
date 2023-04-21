# TA state machine
import stmpy
import logging


class TaSTM:
    def __init__(self, name, component, logger):
        self._logger: logging.Logger = logger
        self.name = name
        self.component = component

    def create_machine(ta, component, logger):
        """ Create the state machine for a TA client """
        ta_stm = TaSTM(name=ta, component=component, logger=logger)

        # Define the states
        logged_on = {'name': 'logged_on'}
        helping_group = {'name': 'helping_group',
                         'entry': 'help_group()', 'exit': 'help_recieved()'}
        not_helping_group = {'name': 'not_helping_group'}

        # Define the transitions
        init = {'source': 'initial', 'target': 'logged_on'}

        publish_tasks = {'trigger': 'publish_tasks',
                         'source': 'logged_on', 'target': 'not_helping_group'}

        # Define the transitions to helping a group
        helping_group1 = {'trigger': 'help_group', 'source': 'not_helping_group',
                          'target': 'helping_group'}
        helping_group2 = {'trigger': 'help_group', 'source': 'helping_group',
                          'target': 'helping_group'}

        # Define the transitions to not helping a group
        not_helping_group1 = {'trigger': 'help_recieved', 'source': 'helping_group',
                              'target': 'not_helping_group'}

        # Define the state machine
        ta_stm = stmpy.Machine(
            name=ta,
            states=[logged_on, helping_group, not_helping_group],
            transitions=[init, publish_tasks, helping_group1,
                         helping_group2, not_helping_group1],
            obj=ta_stm,
        )

        ta_stm.stm = ta_stm

        return ta_stm

    def help_group(self):
        self._logger.info(f'TA {self.name} is helping a group')
        # Updating the queue number for the groups when a TA is helping a group
        self.component.set_helping_group(True)
        self.component.send_new_queue_number_to_groups()

    def help_recieved(self):
        self.component.set_helping_group(False)
        self._logger.info(f'TA {self.name} recieved a group help')
