# TA state machine
import stmpy
import logging

class TaSTM:
    def __init__(self, name, component, logger):
        self._logger: logging.Logger = logger
        self.name = name
        self.component = component
    
    def create_machine(ta, component, logger):
        ta_stm = TaSTM(name=ta, component=component, logger=logger)

        # Define the transitions
        init = {'source': 'initial', 'target': 'not_helping_group', 'effect': 'started()'}

        # Define the transitions to helping a group
        helping_group1 = {'trigger': 'help_group', 'source': 'not_helping_group', 'target': 'helping_group', 'effect': 'help_group()'}
        helping_group2 = {'trigger': 'help_group', 'source': 'helping_group', 'target': 'helping_group', 'effect': 'help_group()'}

        # Define the transitions to not helping a group
        not_helping_group1 = {'trigger': 'help_recieved', 'source': 'helping_group', 'target': 'not_helping_group', 'effect': 'help_recieved()'}

        # Define the state machine
        ta_stm = stmpy.Machine(
            name=ta,
            transitions=[init, helping_group1, helping_group2, not_helping_group1],
            obj=ta_stm,
        )

        ta_stm.stm = ta_stm

        return ta_stm

    def started(self):
        self._logger.info(f'TA {self.name} started')
        self.stm.start()
    
    def help_group(self):
        self._logger.info(f'TA {self.name} is helping a group')
        # Updating the queue number for the groups when a TA is helping a group
        self.component.send_new_queue_number_to_groups()
    
    def help_recieved(self):
        self._logger.info(f'TA {self.name} recieved a group help')
    