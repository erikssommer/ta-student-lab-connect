# Group client component
import paho.mqtt.client as mqtt
from appJar import gui
from datetime import datetime
import logging
import json
import stmpy
from threading import Thread

# MQTT broker address
MQTT_BROKER = 'mqtt20.iik.ntnu.no'
MQTT_PORT = 1883

# MQTT topics
MQTT_TOPIC_TASKS = 'ttm4115/project/team10/tasks'
MQTT_TOPIC_INPUT = 'ttm4115/project/team10/request'
MQTT_TOPIC_OUTPUT = 'ttm4115/project/team10/response'


class GroupClientComponent:

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

        # Handle the different commands
        if topic == MQTT_TOPIC_TASKS:
            self.app.setLabel("listbox_tasks_label", "")

            # Populate the listbox with tasks
            for i, task in enumerate(payload):
                # set the status for the first row to "in progress"
                if i == 0:
                    status = "In progress"
                else:
                    status = "Not done"
                self.app.addTableRow(
                    "table_tasks", [task['task'], task['description'], task['duration'], status])

    def publish_message(self, message):
        payload = json.dumps(message)
        self._logger.info('Publishing message: {}'.format(payload))
        self.mqtt_client.publish(MQTT_TOPIC_INPUT, payload=payload, qos=2)

    def retrieve_message(self):
        self.mqtt_client.subscribe(MQTT_TOPIC_OUTPUT)
        self.mqtt_client.on_message = self.on_message

    def __init__(self):
        self.queue_number = 0

        # get the logger object for the component
        self._logger = logging.getLogger(__name__)
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
        # Subscribe to the input topic
        self.mqtt_client.subscribe(MQTT_TOPIC_INPUT)
        self.mqtt_client.subscribe(MQTT_TOPIC_TASKS)
        # Start the internal loop to process MQTT messages
        self.mqtt_client.loop_start()

        # Setting up the drivers for the state machines
        # Start the stmpy driver for the group component, without any state machines for now
        self.group_stm_driver = stmpy.Driver()
        self.group_stm_driver.start(keep_active=True)

        # Setting up the drivers for the status light
        self.light_stm_driver = stmpy.Driver()
        self.light_stm_driver.start(keep_active=True)

        self._logger.debug('Component initialization finished')

        # TODO removed later
        self.nr_of_tasks = 5
        self.teams = ['Select a team'] + [team for team in range(1, 21)]
        self.image_path = '../../assets/green_light.png'

        # Settup the GUI
        self.setup_gui()

    def setup_gui(self):
        self.app = gui()
        # set the background color of the window to light blue
        self.app.setBg("light blue")
        # Set the size of the GUI window and primary elements
        self.app.setSize(800, 600)  # Set the size of the GUI window
        self.app.setTitle("Group Client")  # Set the title of the GUI window
        self.app.addLabel("upper_right_label_date",
                          f"Date: {datetime.now().strftime('%d/%m/%Y')}")
        self.app.addLabel("upper_right_label", "Team Number")
        self.app.setLabelSticky("upper_right_label", "ne")
        self.app.setLabelSticky("upper_right_label_date", "ne")
        self.app.addLabel("title", "Welcome to the lab").config(
            font="Helvetica 25")
        self.app.addLabel("subtitle", "Tasks for this lab session:").config(
            font="Helvetica 15")
        self.app.setLabelSticky("subtitle", "w")
        self.app.addButton("Show Instructions", self.show_message)
        self.app.setButtonSticky("Show Instructions", "w")

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
        self.app.addLabelEntry("Description:")
        self.app.addButton("Request Help", self.on_request_help)
        self.app.addLabel("Request feedback", "")
        self.app.addLabel("Help Queue", "")

        # Add a horizontal separator
        self.app.addHorizontalSeparator(colour="black")

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

        # Test if message is a number
        try:
            int(message)
        except ValueError:
            self.app.popUp("Error", "Please enter a number", kind="error")
            return

        self.group_nr = message
        self.team_text = "Team " + self.group_nr
        # Close the popup window
        self.app.hideSubWindow("Enter Group Number")
        # Set the label in the upper right corner
        self.app.setSticky("ne")
        self.app.setLabel("upper_right_label", self.team_text)

        # Logging the team number
        self._logger.info(f'Team number: {self.group_nr}')

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
            self.publish_message(help_request)
            self.app.setLabel("Request feedback", "Request successfully sent!")
            self.app.setLabelFg("Request feedback", "green")

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
        # If there are no tasks, do nothing
        if self.app.getTableRowCount("table_tasks") == 0:
            self.app.setLabel("all_tasks_done_label", "There are no tasks to mark as done")
            self._logger.info("There are no tasks to mark as done")
            return

        # Find the first task with status 'not done'
        for row in range(self.app.getTableRowCount("table_tasks")):
            if self.app.getTableRow("table_tasks", row)[3] == "In progress":
                # Mark the task as 'done'
                data = self.app.getTableRow("table_tasks", row)
                data[3] = "Done"
                self.app.replaceTableRow("table_tasks", row, data)
                # Mark the next task as 'in progress'
                if row < self.app.getTableRowCount("table_tasks") - 1:
                    data = self.app.getTableRow("table_tasks", row + 1)
                    data[3] = "In progress"
                    self.app.replaceTableRow("table_tasks", row + 1, data)
                break

        # Check if all tasks are done
        if self.app.getTableRow("table_tasks", self.app.getTableRowCount("table_tasks") - 1)[3] == "Done":
            self.app.popUp("Info", "All tasks are done", kind="info")
            self.app.setLabel("all_tasks_done_label", "All tasks are done! Good job!")


if __name__ == '__main__':
    # logging.DEBUG: Most fine-grained logging, printing everything
    # logging.INFO:  Only the most important informational log items
    # logging.WARN:  Show only warnings and errors.
    # logging.ERROR: Show only error messages.
    debug_level = logging.DEBUG
    logger = logging.getLogger(__name__)
    logger.setLevel(debug_level)
    ch = logging.StreamHandler()
    ch.setLevel(debug_level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)-12s - %(levelname)-8s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Create a new instance of the GroupClientComponent
    client = GroupClientComponent()
