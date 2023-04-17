# Status light state machine
import stmpy
import logging


class StatusLight:

    def __init__(self, name, durations, component, logger):
        self.green_light_off = "../assets/green_off.gif"
        self.green_light_on = "../assets/green_light.gif"
        self.red_light_on = "../assets/red_light.gif"
        self.yellow_light_on = "../assets/yellow_light.gif"

        self._logger: logging.Logger = logger
        self.name = name

        # Convert durations to milliseconds
        self.durations = self.convert_durations_to_milliseconds(durations)
        self.light_duration = self.set_all_light_intervals(self.durations)
        self.current_duration = 0

        self.component = component

    def create_machine(team, durations: list[str], component, logger):
        """ Create a state machine for the status light"""
        status_light = StatusLight(
            name=team, durations=durations, component=component, logger=logger)

        # Define the transitions

        # Initial transition
        init = {'source': 'initial', 'target': 'green',
                'effect': 'on_enter_green(True); start_light_timer()'}

        # Define the transitions where the task is started
        task_start1 = {'trigger': 'task_start', 'source': 'green',
                       'target': 'green', 'effect': 'on_enter_green()'}
        task_start2 = {'trigger': 'task_start', 'source': 'yellow',
                       'target': 'green', 'effect': 'on_enter_green()'}
        task_start3 = {'trigger': 'task_start', 'source': 'red',
                       'target': 'green', 'effect': 'on_enter_green()'}

        # Define the transitions where the time is up
        t0 = {'trigger': 't', 'source': 'green', 'target': 'yellow',
              'effect': 'on_enter_yellow(); stop_light_timer(); start_light_timer()'}
        t1 = {'trigger': 't', 'source': 'yellow', 'target': 'red',
              'effect': 'on_enter_red(); stop_light_timer(); start_light_timer()'}

        tasks_done1 = {'trigger': 'tasks_done', 'source': 'green', 'target': 'off',
                       'effect': 'turn_off(); stop_light_timer(); terminate_stm()'}
        tasks_done2 = {'trigger': 'tasks_done', 'source': 'yellow', 'target': 'off',
                       'effect': 'turn_off(); stop_light_timer(); terminate_stm()'}
        tasks_done3 = {'trigger': 'tasks_done', 'source': 'red', 'target': 'off',
                       'effect': 'turn_off(); stop_light_timer(); terminate_stm()'}

        # Define the state machine
        status_light_stm = stmpy.Machine(
            name=team,
            transitions=[init, task_start1, task_start2, task_start3,
                         t0, t1, tasks_done1, tasks_done2, tasks_done3],
            obj=status_light
        )

        status_light.stm = status_light_stm

        return status_light_stm

    def convert_durations_to_milliseconds(self, durations: list[str]):
        duration_in_milliseconds = []
        for duration in durations:
            # Convert duration into integer
            duration_in_minutes = int(duration)
            # Convert duration to milliseconds and append to list
            duration_in_milliseconds.append(duration_in_minutes * 60 * 1000)
        return duration_in_milliseconds

    def set_all_light_intervals(self, durations: list[str]):
        intervals = []
        for duration in durations:
            intervals.append(duration / 2)
        return intervals

    def start_light_timer(self):
        self._logger.info(
            f'Starting timer for {self.light_duration[self.current_duration]}')
        self.stm.start_timer("t", self.light_duration[self.current_duration])

    def stop_light_timer(self):
        self._logger.info("Stopping timer")
        self.stm.stop_timer("t")

    def on_enter_green(self, init=False):
        self._logger.info("Entering GREEN state")
        self.component.set_status_light(self.green_light_on)
        if init is False:
            self.current_duration += 1

    def on_enter_yellow(self):
        self._logger.info("Entering YELLOW state")
        self.component.set_status_light(self.yellow_light_on)

    def on_enter_red(self):
        self._logger.info("Entering RED state")
        self.component.set_status_light(self.red_light_on)

    def on_exit_green(self):
        self._logger.info("Exiting GREEN state")
        self.component.set_status_light(self.green_light_off)

    def turn_off(self):
        self._logger.info("Turning off")
        self.component.set_status_light(self.green_light_off)

    def terminate_stm(self):
        """ The timer has completed """
        self._logger.info(f'Team {self.name} completed')
        self.stm.terminate()
