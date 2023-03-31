# Group client component
import paho.mqtt.client as mqtt
from appJar import gui
from datetime import datetime
import logging
import json

# MQTT broker address
MQTT_BROKER = 'mqtt20.iik.ntnu.no'
MQTT_PORT = 1883

# MQTT topics
MQTT_TOPIC_INPUT = 'ttm4115/project/team10/request'
MQTT_TOPIC_OUTPUT = 'ttm4115/project/team10/response'


class GroupClientComponent:

    def on_connect(self, client, userdata, flags, rc):
        # Only log that we are connected if the connection was successful
        self._logger.debug('MQTT connected to {}'.format(client))

    def on_message(self, client, userdata, msg):
        pass

    def publish_message(self, message):
        payload = json.dumps(message)
        self._logger.info('Publishing message: {}'.format(payload))
        self.mqtt_client.publish(MQTT_TOPIC_INPUT, payload=payload, qos=2)

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
        # start the internal loop to process MQTT messages
        self.mqtt_client.loop_start()

        self.tasks = ["Task 1: Implement a linked list. Duration: 30min", "Task 2: Implement a stack. Duration: 30min",
                      "Task 3: Implement a queue. Duration: 30min", "Task 4: Implement a binary search tree. Duration: 30min", "Task 5: Implement a hash table. Duration: 30min"]
        self.teams = ['Select a team'] + [team for team in range(1, 21)]
        self.image_path = '../../assets/green_light.png'

        # Settup the GUI
        self.setup_gui()

    def setup_gui(self):
        self.app = gui()

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
        # Add all tasks to the listbox
        for task in self.tasks:
            self.app.addCheckBox(task)

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

        # Start the GUI
        self.app.go()

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

    def sub_window_closed(self):
        """ Close the application if the popup window is closed """
        # Close the application if the popup window is closed
        self.app.popUp("Info", "Application will stop", kind="info")
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
            print(help_request)

            self.app.setPollTime(1000)
            self.app.registerEvent(self.update_queue_number)
        except Exception as e:
            self.app.popUp("Error", e, kind="error")
            self.app.setLabel("Request feedback", "Request failed!")
            self.app.setLabelFg("Request feedback", "red")
            return

    def stop(self):
        """
        Stop the component.
        """
        # stop the MQTT client
        self.mqtt_client.loop_stop()

    def update_queue_number(self):
        """ Update the queue number """
        self.app.setLabel("Help Queue", f"Queue Number: {self.queue_number}")


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
 