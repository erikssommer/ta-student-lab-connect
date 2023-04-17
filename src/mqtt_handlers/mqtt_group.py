import paho.mqtt.client as mqtt
import json
import logging

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


class MqttGroup:

    def __init__(self, component, logger):
        # Setting the reference to the component
        self.component = component
        # Setting the logger
        self.logger: logging.Logger = logger
         # create a new MQTT client
        self.logger.debug(
            f'Connecting to MQTT broker {MQTT_BROKER} at port {MQTT_PORT}')
        self.mqtt_client = mqtt.Client()
        # callback methods
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        # Setting the name of the team to none (will be set when logging in)
        self.team_mqtt_endpoint = None
        self.team_text = None

        # Connect to the broker (subscribe to topics when logged on)
        self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
    
    def set_topics(self):
        """ Set the topics for the group client component """
        self.logger.debug('Setting topics')
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
        self.logger.debug('Subscribing to topics')
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
        self.logger.debug(f'MQTT connected to {client}')

    def on_message(self, client, userdata, msg):
        # Retrieving the topic and payload
        topic = msg.topic

        self.logger.debug(
            f'Received message on topic {topic}, with payload {msg.payload}')

        # Unwrap JSON-encoded payload
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
        except json.JSONDecodeError:
            self.logger.error(
                f'Could not decode JSON from message {msg.payload}')
            return

        # Get the payload attributes
        command = payload.get('command')
        header = payload.get('header')
        body = payload.get('body')

        # Handle the different commands
        if command == "submit_tasks":
            # Update the listbox with the tasks
            self.component.handle_recieve_tasks(body)

        if command == "submit_tasks_late":
            # Update the listbox with the late tasks
            self.component.handle_recieve_tasks(body)

        if command == "queue_number":
            self.component.handle_update_queue_number(body)

        if command == "getting_help":
            self.component.handle_getting_help(body)

        if command == "received_help":
            self.component.handle_received_help(body)

        if command == "ta_present":
            self.component.handle_ta_present()

        if command == "ta_present_all":
            self.component.handle_ta_present(all=True)

    def publish_message(self, topic, message):
        """Publish a message to the MQTT broker.

        Args:
            topic (str): The topic to publish to.
            message (str): The message to publish.
        """
        payload = json.dumps(message)
        self.logger.info(f'Publishing message: {payload}')
        self.mqtt_client.publish(topic, payload=payload, qos=2)

    # MQTT message creation logic
    def create_payload(self, command, header, body):
        """ Create a payload for the MQTT message """
        return {"command": command, "header": header, "body": body}
    
    # Handle the different commands
    def handle_group_present(self):
        body = {
            "group": self.team_text
        }

        payload = self.create_payload(
            command="group_present", header=self.team_mqtt_endpoint, body=body)

        # Notify the TAs that the group is ready
        self.publish_message(self.MQTT_TOPIC_GROUP_PRESENT, payload)

    def handle_request_help(self, task_dict):
        payload = self.create_payload(
                command="request_help", header=self.team_mqtt_endpoint, body=task_dict)

        self.publish_message(self.MQTT_TOPIC_REQUEST_HELP, payload)

    def handle_task_done(self, body):
        payload = self.create_payload(
                    command="report_current_task", header=self.team_mqtt_endpoint, body=body)

        self.publish_message(self.MQTT_TOPIC_PROGRESS, payload)
    
    def handle_all_tasks_done(self, body):
        payload = self.create_payload(
                command="tasks_done", header=self.team_mqtt_endpoint, body=body)

        self.publish_message(self.MQTT_TOPIC_GROUP_DONE, payload)