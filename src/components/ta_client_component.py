import logging
from threading import Thread
import paho.mqtt.client as mqtt
import stmpy
from appJar import gui
from datetime import datetime

# TA client component

# MQTT broker address
MQTT_BROKER = 'mqtt20.iik.ntnu.no'
MQTT_PORT = 1883

# MQTT topics
MQTT_TOPIC_INPUT = 'ttm4115/project/team_10/input'
MQTT_TOPIC_TASKS = 'ttm4115/project/team_10/tasks'
MQTT_TOPIC_OUTPUT = 'ttm4115/project/team_10/output'

class TaClientComponent:
    def on_connect(self, client, userdata, flags, rc):
        # Only log that we are connected if the connection was successful
        self._logger.debug('MQTT connected to {}'.format(client))

    def on_message(self, client, userdata, msg):
        # Log the message received
        self._logger.debug('MQTT received message: {}'.format(msg.payload))

    def __init__(self):
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

        # Start the MQTT client in a separate thread to avoid blocking
        try:
            thread = Thread(target=self.mqtt_client.loop_start())
            thread.start()
        except KeyboardInterrupt:
            print("Interrupted")
            self.mqtt_client.disconnect()

        # Setting up the drivers for the state machines
        # Start the stmpy driver for the group component, without any state machines for now
        self.ta_stm_driver = stmpy.Driver()
        self.ta_stm_driver.start(keep_active=True)

        # Setting up the drivers for the status light
        self.light_stm_driver = stmpy.Driver()
        self.light_stm_driver.start(keep_active=True)

        self._logger.debug('Component initialization finished')

        # Settup the GUI
        self.setup_gui()

    def setup_gui(self):
        self.app = gui()

        # set the background color of the window to light blue
        self.app.setBg("light blue")
        # Set the size of the GUI window and primary elements
        self.app.setSize(800, 600)  # Set the size of the GUI window
        self.app.setTitle("TA client")  # Set the title of the GUI window
        # Set the label in the upper right corner
        self.app.addLabel("upper_right_label_date",
                          f"Date: {datetime.now().strftime('%d/%m/%Y')}")
        self.app.addLabel("upper_right_label", "TA name")
        self.app.setLabelSticky("upper_right_label_date", "ne")
        self.app.setLabelSticky("upper_right_label", "ne")

        self.app.addLabel("title", "Welcome to the lab").config(
            font="Helvetica 25")

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
        self.ta_stm_driver.stop()
        self.light_stm_driver.stop()

        # Log the shutdown
        self._logger.info('Shutting down TA client component')
        exit()

    def init_popup(self):
        # Make TA enter name
        self.app.startSubWindow("Enter TA name", modal=True)
        self.app.setSize(300, 200)
        self.app.addLabelEntry("Your name:")
        self.app.addButton("Submit", self.submit_name)
        self.app.setStopFunction(self.sub_window_closed)
        self.app.stopSubWindow()

        self.app.showSubWindow("Enter TA name")
    
    def submit_name(self):
        name = self.app.getEntry("Your name:")
        self.app.hideSubWindow("Enter TA name")

        # Set the label in the upper right corner
        self.app.setLabel("upper_right_label", f"TA name: {name}")

    def sub_window_closed(self):
        """ Close the application if the popup window is closed """
        # Close the application if the popup window is closed
        self.app.popUp("Info", "Application will stop", kind="info")
        self._logger.info('Application will stop')
        self.app.stop()

