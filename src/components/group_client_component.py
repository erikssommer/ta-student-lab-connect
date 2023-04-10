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
import time

# Number of teams able to connect to the system
NR_OF_TEAMS = 20

# MQTT broker address
MQTT_BROKER = 'mqtt20.iik.ntnu.no'
MQTT_PORT = 1883

# MQTT topics, the team number is appended to the end of the topic when logging in and subscribing
MQTT_TOPIC_TASKS = 'ttm4115/project/team10/api/v1/tasks'
MQTT_TOPIC_TASKS_LATE = 'ttm4115/project/team10/api/v1/tasks/late'

MQTT_TOPIC_REQUEST_HELP = 'ttm4115/project/team10/api/v1/request'
MQTT_TOPIC_GROUP_PRESENT = 'ttm4115/project/team10/api/v1/present'
MQTT_TOPIC_GROUP_DONE = 'ttm4115/project/team10/api/v1/done'
MQTT_TOPIC_PROGRESS = 'ttm4115/project/team10/api/v1/progress'

MQTT_TOPIC_QUEUE_NUMBER = 'ttm4115/project/team10/api/v1/queue_number'
MQTT_TOPIC_GETTING_HELP = 'ttm4115/project/team10/api/v1/getting_help'
MQTT_TOPIC_RECEIVED_HELP = 'ttm4115/project/team10/api/v1/received_help'

MQTT_TOPIC_TA_READY = 'ttm4115/project/team10/api/v1/ta_ready/request'
MQTT_TOPIC_TA_READY_RESPONSE = 'ttm4115/project/team10/api/v1/ta_ready/response'
MQTT_TOPIC_TA_READY_RESPONSE_ALL = 'ttm4115/project/team10/api/v1/ta_ready/response/all'


class GroupClientComponent:

    def set_topics(self):
        """ Set the topics for the group client component """
        self._logger.debug('Setting topics')
        self.MQTT_TOPIC_TASKS = MQTT_TOPIC_TASKS
        self.MQTT_TOPIC_TA_READY = MQTT_TOPIC_TA_READY
        self.MQTT_TOPIC_TA_READY_RESPONSE_ALL = MQTT_TOPIC_TA_READY_RESPONSE_ALL
        self.MQTT_TOPIC_TA_READY_RESPONSE = MQTT_TOPIC_TA_READY_RESPONSE + \
            "/" + self.team_mqtt_endpoint

        self.MQTT_TOPIC_TASKS_LATE = MQTT_TOPIC_TASKS_LATE + \
            "/" + self.team_mqtt_endpoint
        self.MQTT_TOPIC_REQUEST_HELP = MQTT_TOPIC_REQUEST_HELP + \
            "/" + self.team_mqtt_endpoint
        self.MQTT_TOPIC_GROUP_PRESENT = MQTT_TOPIC_GROUP_PRESENT + \
            "/" + self.team_mqtt_endpoint
        self.MQTT_TOPIC_GROUP_DONE = MQTT_TOPIC_GROUP_DONE + "/" + self.team_mqtt_endpoint
        self.MQTT_TOPIC_PROGRESS = MQTT_TOPIC_PROGRESS + "/" + self.team_mqtt_endpoint

        self.MQTT_TOPIC_QUEUE_NUMBER = MQTT_TOPIC_QUEUE_NUMBER + \
            "/" + self.team_mqtt_endpoint
        self.MQTT_TOPIC_GETTING_HELP = MQTT_TOPIC_GETTING_HELP + \
            "/" + self.team_mqtt_endpoint
        self.MQTT_TOPIC_RECEIVED_HELP = MQTT_TOPIC_RECEIVED_HELP + \
            "/" + self.team_mqtt_endpoint

    def subscribe_topics(self):
        """ Subscribe to the topics for the group client component """
        self._logger.debug('Subscribing to topics')
        self.mqtt_client.subscribe(self.MQTT_TOPIC_TASKS)
        self.mqtt_client.subscribe(self.MQTT_TOPIC_TASKS_LATE)
        self.mqtt_client.subscribe(self.MQTT_TOPIC_QUEUE_NUMBER)
        self.mqtt_client.subscribe(self.MQTT_TOPIC_GETTING_HELP)
        self.mqtt_client.subscribe(self.MQTT_TOPIC_RECEIVED_HELP)
        self.mqtt_client.subscribe(self.MQTT_TOPIC_TA_READY_RESPONSE)
        self.mqtt_client.subscribe(self.MQTT_TOPIC_TA_READY_RESPONSE_ALL)

    # MQTT connection logic

    def on_connect(self, client, userdata, flags, rc):
        # Only log that we are connected if the connection was successful
        self._logger.debug(f'MQTT connected to {client}')

    def on_message(self, client, userdata, msg):
        # Retrieving the topic and payload
        topic = msg.topic

        self._logger.debug(
            f'Received message on topic {topic}, with payload {msg.payload}')

        # Unwrap JSON-encoded payload
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
        except json.JSONDecodeError:
            self._logger.error(
                f'Could not decode JSON from message {msg.payload}')
            return

        # Handle the different topics
        if topic == self.MQTT_TOPIC_TASKS:
            # Update the listbox with the tasks
            self.handle_recieve_tasks(payload)

        if topic == self.MQTT_TOPIC_TASKS_LATE:
            # Update the listbox with the late tasks
            self.handle_recieve_tasks(payload)

        if topic == self.MQTT_TOPIC_QUEUE_NUMBER:
            self.queue_number = payload['queue_number']
            self.app.setLabel("queue_number_label",
                              f"Number in queue: {self.queue_number}")

        if topic == self.MQTT_TOPIC_GETTING_HELP:
            # Update the queue number label to inform the user that they are getting help
            self.app.setLabel("queue_number_label", "Getting help!")

            self.app.setLabel("Request feedback", "")
            # Change state to "receive_help"
            self.stm_driver.send('receive_help', self.team_text)

        if topic == self.MQTT_TOPIC_RECEIVED_HELP:
            # Update the queue number label to inform the user that they have received help
            self.app.setLabel("queue_number_label", "Received help!")
            # Change state to "receive_help"
            self.stm_driver.send('received_help', self.team_text)

            # Set the requesting help flag to false
            self.requesting_help = False

        if topic == self.MQTT_TOPIC_TA_READY_RESPONSE:
            # Handle that the TA is ready
            if self.ta_connected == False:
                logging.info("TA is ready")
                self.ta_connected = True
                self.app.setLabel("TA_status_label", "")

        if topic == self.MQTT_TOPIC_TA_READY_RESPONSE_ALL:
            # Handle that a TA is ready
            if self.ta_connected == False:
                logging.info("TA is ready")
                self.ta_connected = True
                self.app.setLabel("TA_status_label", "")

                # If the ta_connected is false it means that it is the first ta that is ready.
                # So we need to send the group present message again
                self.handle_group_present()

    def publish_message(self, topic, message):
        """Publish a message to the MQTT broker.

        Args:
            topic (str): The topic to publish to.
            message (str): The message to publish.
        """
        payload = json.dumps(message)
        self._logger.info(f'Publishing message: {payload}')
        self.mqtt_client.publish(topic, payload=payload, qos=2)

    # MQTT message creation logic
    def create_payload(self, command, header, body):
        """ Create a payload for the MQTT message """
        return {"command": command, "header": header, "body": body}

    # Creation on state machines logic
    def create_status_light_stm(self, durations: list[str]):
        """ Create a new status light state machine """
        # Create a new status light state machine
        status_light_stm = StatusLight.create_machine(
            team=self.team_text, durations=durations, component=self, logger=self._logger)
        # Add the state machine to the driver
        self.stm_driver.add_machine(status_light_stm)

    def create_group_stm(self):
        """ Create a new group state machine """
        # Create a new group state machine
        group_stm = GroupLogic.create_machine(
            team=self.team_text, component=self, logger=self._logger)
        # Add the state machine to the driver
        self.stm_driver.add_machine(group_stm)

    def set_status_light(self, light):
        """ Set the status light """
        self.app.setImage("light", light)

    def __init__(self, logger):
        # get the logger object for the component
        self._logger: logging.Logger = logger
        print('logging under name {}.'.format(__name__))
        self._logger.info('Starting Component')

        # create a new MQTT client
        self._logger.debug(
            f'Connecting to MQTT broker {MQTT_BROKER} at port {MQTT_PORT}')
        self.mqtt_client = mqtt.Client()
        # callback methods
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        # Connect to the broker (subscribe to topics when logged on)
        self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT)

        # Start the MQTT client in a separate thread to avoid blocking
        try:
            thread = Thread(target=self.mqtt_client.loop_start())
            thread.start()
        except KeyboardInterrupt:
            print("Interrupted")
            self.mqtt_client.disconnect()

        # Setting up the drivers for the state machines
        # Start the stmpy driver for the group component, without any state machines for now
        self.stm_driver = stmpy.Driver()
        self.stm_driver.start(keep_active=True)

        self._logger.debug('Component initialization finished')

        self.teams = ['Select a team'] + ["Team " +
                                          str(team) for team in range(1, NR_OF_TEAMS + 1)]

        # Set the initial image path
        self.image_path = "../assets/green_off.gif"

        # Set the initial queue number
        self.queue_number = 0

        # Can only update tasks once
        self.update_tasks = False

        # Know if the grou is requesting help
        self.requesting_help = False

        # Know if a TA is connected
        self.ta_connected = False

        # Settup the GUI
        self.setup_gui()

    def setup_gui(self):
        self.app = gui()

        # Set the background color of the GUI window
        self.app.setBg("light blue")

        # Set the size of the GUI window and primary elements
        self.app.setSize(800, 800)  # Set the size of the GUI window
        self.app.setTitle("Group Client")  # Set the title of the GUI window

        self.app.setResizable(canResize=False)

        # Set the font size of the buttons
        self.app.setButtonFont(size=15, family="Verdana",
                               underline=False, slant="roman")

        self.app.addLabel("upper_right_label_date",
                          f"Date: {datetime.now().strftime('%d/%m/%Y')}").config(font="Helvetica 15")
        self.app.addLabel("upper_right_label", "Team Number").config(
            font="Helvetica 15")
        self.app.setLabelSticky("upper_right_label", "ne")
        self.app.setLabelSticky("upper_right_label_date", "ne")

        # Add image of school logo
        self.app.addImage("logo", "../assets/ntnu_logo.gif")

        self.app.addLabel("title", "Welcome to the lab").config(
            font="Helvetica 25")
        self.app.addLabel("subtitle", "Tasks for this lab session:").config(
            font="Helvetica 15")
        self.app.setLabelSticky("subtitle", "w")
        self.app.addButton("Show Instructions", self.show_instructions)
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
        self.app.addLabel("TA_status_label", "")
        self.app.setLabelFg("TA_status_label", "red")
        self.app.addLabel("Request feedback", "")
        self.app.addLabel("queue_number_label", "")

        # Add a horizontal separator
        self.app.addHorizontalSeparator(17, 0, 4, colour="black")

        # Light status elements
        self.app.addLabel("light_label", "Light status:")
        self.app.addImage("light", self.image_path)

        # Setting up the component for the given group
        self.show_enter_group_name_popup()

        self.app.setStopFunction(self.stop)

        # Start the GUI
        self.app.go()

    def show_enter_group_name_popup(self):
        """ Initialize the popup window """
        # Define the popup window
        self.app.startSubWindow("Enter Group Number", modal=True)
        self.app.setSize(300, 200)
        self.app.addOptionBox("team_dropdown", self.teams, height=3)
        self.app.addButton("Submit", self.submit_group)
        self.app.setStopFunction(self.sub_window_closed)
        self.app.stopSubWindow()

        # Show the popup window
        self.app.showSubWindow("Enter Group Number")

    def submit_group(self):
        """ Submit the message from the input field """
        # Retrieve the message from the input field
        message = self.app.getOptionBox("team_dropdown")

        # Test if the message is empty
        if message == "Select a team":
            self.app.popUp("Error", "Please choose a team", kind="error")
            return

        self.team_text = message

        # Team text to lower case and remove spaces
        self.team_mqtt_endpoint = self.team_text.lower().replace(" ", "_")

        # Close the popup window
        self.app.hideSubWindow("Enter Group Number")
        # Set the label in the upper right corner
        self.app.setSticky("ne")
        self.app.setLabel("upper_right_label", self.team_text)

        # Logging the team number
        self._logger.info(f'Team number: {self.team_text}')

        # Create the topics for the group
        self.set_topics()

        # Subscribe to the topic for the group
        self.subscribe_topics()

        self.handle_group_present()

        # Start the group state machine
        self.create_group_stm()
        
        # Wait for the TAs to respond on connect
        time.sleep(0.2)

        if self.ta_connected == False:
            self.app.setLabel("TA_status_label",
                              "Waiting for TAs to connect...")

    def sub_window_closed(self):
        """ Close the application if the popup window is closed """
        # Close the application if the popup window is closed
        self.app.popUp("Info", "Application will stop", kind="info")
        self._logger.info('Application will stop')
        self.app.stop()

    def show_instructions(self):
        """ Show the instructions for the lab session """
        self.app.infoBox(title="Instructions",
                         message="Use the checkboxes to mark the tasks you have completed. \
                         When you are ready to request help, enter a description of the help you need in the text \
                          field below and click the 'Request Help' button. The TAs will then come to your group and \
                          help you with your tasks. Good luck!")
        
    def handle_group_present(self):
        body = {
            "group": self.team_text
        }

        payload = self.create_payload(
            command="group_present", header=self.team_mqtt_endpoint, body=body)

        # Notify the TAs that the group is ready
        self.publish_message(self.MQTT_TOPIC_GROUP_PRESENT, payload)
        
    def handle_recieve_tasks(self, payload):
        # Only update the tasks once
        if self.update_tasks:
            return
        
        self.update_tasks = True

        # Check if the group already is assigned tasks
        if self.app.getTableRowCount("table_tasks") > 0:
            self._logger.debug(
                'Already have tasks, not updating the listbox')
            return
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
        # Cange state to "working on task"
        self.stm_driver.send('task_start', self.team_text)
        self.create_status_light_stm(durations=duration_list)

    def on_request_help(self):
        """ Send a help request to the TAs """

        if self.ta_connected == False:
            self.app.popUp(
                "Error", "There are no TAs online. Wait for them to connect before requesting help", kind="error")
            return

        if self.requesting_help:
            self.app.popUp(
                "Error", "You are already requesting help.", kind="error")
            return

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

            task_dict = {
                "group": help_request[0],
                "description": help_request[1],
                "time": help_request[2]
            }

            payload = self.create_payload(
                command="request_help", header=self.team_mqtt_endpoint, body=task_dict)

            self.publish_message(self.MQTT_TOPIC_REQUEST_HELP, payload)
            self.app.setLabel("Request feedback", "Request successfully sent!")
            self.app.setLabelFg("Request feedback", "green")

            # Change state to "waiting_for_help"
            self.stm_driver.send("request_help", self.team_text)

            # Set the requesting help flag to true
            self.requesting_help = True

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
                body = {"group": self.team_text, "current_task": data[0]}

                payload = self.create_payload(
                    command="report_current_task", header=self.team_mqtt_endpoint, body=body)

                self.publish_message(self.MQTT_TOPIC_PROGRESS, payload)
                break

        # Report to the light stm that the task is done
        if duration is not None:
            self.stm_driver.send('task_start', self.team_text)

        # Check if all tasks are done
        if self.app.getTableRow("table_tasks", self.app.getTableRowCount("table_tasks") - 1)[3] == "Done":
            self.app.popUp("Info", "All tasks are done", kind="info")
            self.app.setLabel("all_tasks_done_label",
                              "All tasks are done! Good job!")
            self.stm_driver.send('tasks_done', self.team_text)

            # Report the task as done to the TAs
            body = {"group": self.team_text}

            payload = self.create_payload(
                command="tasks_done", header=self.team_mqtt_endpoint, body=body)

            self.publish_message(self.MQTT_TOPIC_GROUP_DONE, payload)

            # Change state to "tasks_done"
            self.stm_driver.send("tasks_done", self.team_text)

    def stop(self):
        """
        Stop the component.
        """
        # stop the MQTT client
        self.mqtt_client.loop_stop()

        # stop the stmpy drivers
        self.stm_driver.stop()

        # Log the shutdown
        self._logger.info('Shutting down Component')
        exit()
