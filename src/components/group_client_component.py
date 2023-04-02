# Group client component
import paho.mqtt.client as mqtt
from appJar import gui
from datetime import datetime
import json
import stmpy
from threading import Thread
from state_machines.status_light_stm import StatusLight
from state_machines.group_stm import GroupLogic
import logging

NR_OF_TEAMS = 20

# MQTT broker address
MQTT_BROKER = 'mqtt20.iik.ntnu.no'
MQTT_PORT = 1883

# MQTT topics
MQTT_TOPIC_TASKS = 'ttm4115/project/team10/tasks'
MQTT_TOPIC_REQUEST_HELP = 'ttm4115/project/team10/request'
MQTT_TOPIC_OUTPUT = 'ttm4115/project/team10/response'
MQTT_TOPIC_PROGRESS = 'ttm4115/project/team10/progress'
MQTT_TOPIC_GROUP_PRESENT = 'ttm4115/project/team10/present'
MQTT_TOPIC_GROUP_DONE = 'ttm4115/project/team10/done'
MQTT_TOPIC_QUEUE_NUMBER = 'ttm4115/project/team10/queue_number'
MQTT_TOPIC_GETTING_HELP = 'ttm4115/project/team10/getting_help'
MQTT_TOPIC_RECEIVED_HELP = 'ttm4115/project/team10/received_help'


class GroupClientComponent:

    # MQTT connection logic
    def on_connect(self, client, userdata, flags, rc):
        # Only log that we are connected if the connection was successful
        self._logger.debug('MQTT connected to {}'.format(client))

    def on_message(self, client, userdata, msg):
        # Retrieving the topic and payload
        topic = msg.topic

        self._logger.debug('Received message on topic {}, with payload {}'.format(
            topic, msg.payload))

        # Unwrap JSON-encoded payload
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
        except json.JSONDecodeError:
            self._logger.error(
                'Could not decode JSON from message {}'.format(msg.payload))
            return

        # Handle the different topics
        if topic == MQTT_TOPIC_TASKS:
            self.app.setLabel("listbox_tasks_label", "")
            # Keep track of the task durations for the status light stm
            duration_list = []
            # Populate the listbox with tasks
            for i, task in enumerate(payload):
                # set the status for the first row to "in progress"
                if i == 0:
                    status = "In progress"
                else:
                    status = "Not done"
                self.app.addTableRow(
                    "table_tasks", [task['task'], task['description'], task['duration'], status])
                duration_list.append(task['duration'])

            # Set the status of the first task to "in progress"
            # Report the task as done to the TAs
            message = [{"group": self.team_text, "current_task": "1"}]
            self.report_current_task(message)

            # Cange state to "working on task"
            self.group_stm_driver.send('task_start', self.team_text)

            self.create_status_light_stm(durations=duration_list)

        if topic == MQTT_TOPIC_QUEUE_NUMBER:
            self.queue_number = payload[0]['queue_number']
            self.app.setLabel("queue_number_label", f"Number in queue: {self.queue_number}")

        if topic == MQTT_TOPIC_GETTING_HELP:
            # Update the queue number label to inform the user that they are getting help
            self.app.setLabel("queue_number_label", "Getting help!")
            # Change state to "receive_help"
            self.group_stm_driver.send('receive_help', self.team_text)

        if topic == MQTT_TOPIC_RECEIVED_HELP:
            # Update the queue number label to inform the user that they have received help
            self.app.setLabel("queue_number_label", "Received help!")
            # Change state to "receive_help"
            self.group_stm_driver.send('received_help', self.team_text)

    def publish_message(self, topic, message):
        payload = json.dumps(message)
        self._logger.info('Publishing message: {}'.format(payload))
        self.mqtt_client.publish(topic, payload=payload, qos=2)

    def retrieve_message(self):
        self.mqtt_client.subscribe(MQTT_TOPIC_OUTPUT)
        self.mqtt_client.on_message = self.on_message

    # Creation on state machines logic
    def create_status_light_stm(self, durations: list[str]):
        """ Create a new status light state machine """
        # Create a new status light state machine
        status_light_stm = StatusLight.create_machine(team=self.team_text, durations=durations, component=self, logger=self._logger)
        # Add the state machine to the driver
        self.light_stm_driver.add_machine(status_light_stm)

    def create_group_stm(self):
        """ Create a new group state machine """
        # Create a new group state machine
        group_stm = GroupLogic.create_machine(team=self.team_text, component=self, logger=self._logger)
        # Add the state machine to the driver
        self.group_stm_driver.add_machine(group_stm)

    def set_status_light(self, light):
        """ Set the status light """
        self.app.setImage("light", light)

    def __init__(self, logger):
        self.queue_number = 0

        # get the logger object for the component
        self._logger: logging.Logger = logger
        print('logging under name {}.'.format(__name__))
        self._logger.info('Starting Component')

        # create a new MQTT client
        self._logger.debug(
            'Connecting to MQTT broker {} at port {}'.format(MQTT_BROKER, MQTT_PORT))
        self.mqtt_client = mqtt.Client()
        # callback methods
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        # Connect to the broker
        self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT)

        # Subscribe to the input topics
        self.mqtt_client.subscribe(MQTT_TOPIC_REQUEST_HELP)
        self.mqtt_client.subscribe(MQTT_TOPIC_TASKS)
        self.mqtt_client.subscribe(MQTT_TOPIC_GROUP_PRESENT)
        self.mqtt_client.subscribe(MQTT_TOPIC_QUEUE_NUMBER)
        self.mqtt_client.subscribe(MQTT_TOPIC_GETTING_HELP)
        self.mqtt_client.subscribe(MQTT_TOPIC_RECEIVED_HELP)

        # Start the MQTT client in a separate thread to avoid blocking
        try:
            thread = Thread(target=self.mqtt_client.loop_start())
            thread.start()
        except KeyboardInterrupt:
            print("Interrupted")
            self.mqtt_client.disconnect()

        # Setting up the drivers for the state machines
        # Start the stmpy driver for the group component, without any state machines for now
        self.group_stm_driver = stmpy.Driver()
        self.group_stm_driver.start(keep_active=True)

        # Setting up the drivers for the status light
        self.light_stm_driver = stmpy.Driver()
        self.light_stm_driver.start(keep_active=True)

        self._logger.debug('Component initialization finished')

        self.teams = ['Select a team'] + ["Team " +
                                          str(team) for team in range(1, NR_OF_TEAMS + 1)]

        # Set the initial image path
        self.image_path = "../assets/green_off.png"

        # Settup the GUI
        self.setup_gui()

    def setup_gui(self):
        self.app = gui()

        self.app.setBg("light blue")  # Set the background color of the GUI window

        # Set the size of the GUI window and primary elements
        self.app.setSize(800, 800)  # Set the size of the GUI window
        self.app.setTitle("Group Client")  # Set the title of the GUI window

        self.app.setResizable(canResize=False)

        # Set the font size of the buttons
        self.app.setButtonFont(size=15, family="Verdana", underline=False, slant="roman")


        self.app.addLabel("upper_right_label_date",
                          f"Date: {datetime.now().strftime('%d/%m/%Y')}").config(font="Helvetica 15")
        self.app.addLabel("upper_right_label", "Team Number").config(font="Helvetica 15")
        self.app.setLabelSticky("upper_right_label", "ne")
        self.app.setLabelSticky("upper_right_label_date", "ne")

        # Add image of school logo
        self.app.addImage("logo", "../assets/ntnu_logo.png")

        self.app.addLabel("title", "Welcome to the lab").config(
            font="Helvetica 25")
        self.app.addLabel("subtitle", "Tasks for this lab session:").config(
            font="Helvetica 15")
        self.app.setLabelSticky("subtitle", "w")
        self.app.addButton("Show Instructions", self.show_message)
        self.app.setButtonSticky("Show Instructions", "w")

        # Add empty label for spacing
        self.app.addEmptyLabel("empty_label")

        # Task elements
        self.app.addLabel("listbox_tasks_label",
                          "Waiting for TAs to assign tasks...")
        self.app.setLabelSticky("listbox_tasks_label", "w")
        # Add a listbox to host the tasks
        self.app.addTable(
            "table_tasks", [["Task", "Description", "Duration", "Status"]])

        # Add button to registre that a task is done
        self.app.addButton("Mark next task as done", self.mark_task_done)
        self.app.setButtonSticky("Mark next task as done", "w")

        # Add lable for tasks done
        self.app.addLabel("all_tasks_done_label",
                          "").config(font="Helvetica 15")
        self.app.setLabelSticky("all_tasks_done_label", "w")

        # Request help elements
        self.app.addLabel("description_label",
                          "Need help? - Ask TAs for help!")
        self.app.addLabelEntry("Description:").config(font="Helvetica 15")
        self.app.addButton("Request Help", self.on_request_help)
        self.app.addLabel("Request feedback", "")
        self.app.addLabel("queue_number_label", "")

        # Add a horizontal separator
        self.app.addHorizontalSeparator(16,0,4,colour="black")

        # Light status elements
        self.app.addLabel("light_label", "Light status:")
        self.app.addImage("light", self.image_path)
        self.init_popup()

        self.app.setStopFunction(self.stop)

        # Start the GUI
        self.app.go()

    def stop(self):
        """
        Stop the component.
        """
        # stop the MQTT client
        self.mqtt_client.loop_stop()

        # stop the stmpy drivers
        self.group_stm_driver.stop()
        self.light_stm_driver.stop()

        # Log the shutdown
        self._logger.info('Shutting down Component')
        exit()

    def show_message(self):
        """ Show the instructions for the lab session """
        self.app.infoBox(title="Instructions",
                         message="Use the checkboxes to mark the tasks you have completed. \
                         When you are ready to request help, enter a description of the help you need in the text \
                          field below and click the 'Request Help' button. The TAs will then come to your group and \
                          help you with your tasks. Good luck!")

    def init_popup(self):
        """ Initialize the popup window """
        # Define the popup window
        self.app.startSubWindow("Enter Group Number", modal=True)
        self.app.setSize(300, 200)
        self.app.addOptionBox("team_dropdown", self.teams, height=3)
        self.app.addButton("Submit", self.submit_message)
        self.app.setStopFunction(self.sub_window_closed)
        self.app.stopSubWindow()

        # Show the popup window
        self.app.showSubWindow("Enter Group Number")

    def submit_message(self):
        """ Submit the message from the input field """
        # Retrieve the message from the input field
        message = self.app.getOptionBox("team_dropdown")

        # Test if the message is empty
        if message == "Select a team":
            self.app.popUp("Error", "Please choose a team", kind="error")
            return

        self.team_text = message
        # Close the popup window
        self.app.hideSubWindow("Enter Group Number")
        # Set the label in the upper right corner
        self.app.setSticky("ne")
        self.app.setLabel("upper_right_label", self.team_text)

        # Logging the team number
        self._logger.info(f'Team number: {self.team_text}')

        # Notify the TAs that the group is ready
        data_object = [{"group": self.team_text,
                        "current_task": "Waiting for TAs to assign tasks..."}]
        self.publish_message(MQTT_TOPIC_GROUP_PRESENT, data_object)

        # Start the group state machine
        self.create_group_stm()

    def sub_window_closed(self):
        """ Close the application if the popup window is closed """
        # Close the application if the popup window is closed
        self.app.popUp("Info", "Application will stop", kind="info")
        self._logger.info('Application will stop')
        self.app.stop()

    def on_request_help(self):
        help_request = self.app.getEntry("Description:")
        # Test if the help request is empty
        if help_request == "":
            self.app.popUp(
                "Error", "Please enter a description of the help you need", kind="error")
            return
        self.app.clearEntry("Description:")
        try:
            # Create the help request message
            help_request = [self.team_text, help_request,
                            datetime.now().strftime('%H:%M:%S')]
            output_list = []

            task_dict = {
                "group": help_request[0],
                "description": help_request[1],
                "time": help_request[2]
            }

            output_list.append(task_dict)

            self.publish_message(MQTT_TOPIC_REQUEST_HELP, output_list)
            self.app.setLabel("Request feedback", "Request successfully sent!")
            self.app.setLabelFg("Request feedback", "green")

            # Change state to "waiting_for_help"
            self.group_stm_driver.send("request_help", self.team_text)

        except Exception as e:
            self.app.popUp("Error", e, kind="error")
            self.app.setLabel("Request feedback", "Request failed!")
            self.app.setLabelFg("Request feedback", "red")
            return

    def update_queue_number(self):
        """ Update the queue number """
        self.app.setLabel("Help Queue", f"Queue Number: {self.queue_number}")

    def mark_task_done(self):
        """ Mark the first tast with status 'not done' as 'done' and the next task as 'in progress' """
        duration = None
        # If there are no tasks, do nothing
        if self.app.getTableRowCount("table_tasks") == 0:
            self.app.setLabel("all_tasks_done_label",
                              "There are no tasks to mark as done")
            self._logger.info("There are no tasks to mark as done")
            return

        # Find the first task with status 'not done'
        for row in range(self.app.getTableRowCount("table_tasks")):
            if self.app.getTableRow("table_tasks", row)[3] == "In progress":
                # Mark the task as 'done'
                data = self.app.getTableRow("table_tasks", row)
                data[3] = "Done"
                duration = data[2]
                self.app.replaceTableRow("table_tasks", row, data)
                # Mark the next task as 'in progress'
                if row < self.app.getTableRowCount("table_tasks") - 1:
                    data = self.app.getTableRow("table_tasks", row + 1)
                    data[3] = "In progress"
                    self.app.replaceTableRow("table_tasks", row + 1, data)

                # Report the task as done to the TAs
                message = [{"group": self.team_text, "current_task": data[0]}]
                self.report_current_task(message)
                break

        # Report to the light stm that the task is done
        if duration is not None:
            self.light_stm_driver.send('task_start', self.team_text)

        # Check if all tasks are done
        if self.app.getTableRow("table_tasks", self.app.getTableRowCount("table_tasks") - 1)[3] == "Done":
            self.app.popUp("Info", "All tasks are done", kind="info")
            self.app.setLabel("all_tasks_done_label",
                              "All tasks are done! Good job!")
            self.light_stm_driver.send('tasks_done', self.team_text)

            # Report the task as done to the TAs
            message = [{"group": self.team_text}]
            self.publish_message(MQTT_TOPIC_GROUP_DONE, message)

            # Change state to "tasks_done"
            self.group_stm_driver.send("tasks_done", self.team_text)

    def report_current_task(self, message):
        self.publish_message(MQTT_TOPIC_PROGRESS, message)
