# TA state machine
import stmpy
import logging

class TaLogic:
    def __init__(self, name, component, logger):
        self._logger: logging.Logger = logger
        self.name = name
        self.component = component
    
    def create_machine(ta, component, logger):
        ta_logic = TaLogic(name=ta, component=component, logger=logger)

        # Define the transitions
        init = {'source': 'initial', 'target': 'not_helping_group'}

        # Define the transitions to helping a group
        helping_group1 = {'trigger': 'help_group', 'source': 'not_helping_group', 'target': 'helping_group'}
        helping_group2 = {'trigger': 'help_group', 'source': 'helping_group', 'target': 'helping_group'}

        # Define the transitions to not helping a group
        not_helping_group1 = {'trigger': 'help_recieved', 'source': 'helping_group', 'target': 'not_helping_group'}

        # Define the state machine
        ta_stm = stmpy.Machine(
            name=ta,
            transitions=[init, helping_group1, helping_group2, not_helping_group1],
            obj=ta_logic,
        )

        ta_logic.stm = ta_stm

        return ta_stm
    

    