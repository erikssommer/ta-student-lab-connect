import json
import logging
import paho.mqtt.client as mqtt

# MQTT broker address
MQTT_BROKER = 'mqtt20.iik.ntnu.no'
MQTT_PORT = 1883

# MQTT topics
MQTT_TOPIC_TASKS = 'ttm4115/project/team10/api/v1/tasks'
MQTT_TOPIC_TASKS_LATE = 'ttm4115/project/team10/api/v1/tasks/late'

MQTT_TOPIC_REQUEST_HELP = 'ttm4115/project/team10/api/v1/request/#'
MQTT_TOPIC_GROUP_PRESENT = 'ttm4115/project/team10/api/v1/present/#'
MQTT_TOPIC_GROUP_DONE = 'ttm4115/project/team10/api/v1/done/#'
MQTT_TOPIC_PROGRESS = 'ttm4115/project/team10/api/v1/progress/#'

MQTT_TOPIC_QUEUE_NUMBER = 'ttm4115/project/team10/api/v1/queue_number'
MQTT_TOPIC_GETTING_HELP = 'ttm4115/project/team10/api/v1/getting_help'
MQTT_TOPIC_RECEIVED_HELP = 'ttm4115/project/team10/api/v1/received_help'

MQTT_TOPIC_TA_UPDATE = 'ttm4115/project/team10/api/v1/ta_update'
MQTT_TOPIC_TA = 'ttm4115/project/team10/api/v1/ta'

MQTT_TOPIC_TA_READY_REQUEST = 'ttm4115/project/team10/api/v1/ta_ready/request'
MQTT_TOPIC_TA_READY_RESPONSE = 'ttm4115/project/team10/api/v1/ta_ready/response'
MQTT_TOPIC_TA_READY_RESPONSE_ALL = 'ttm4115/project/team10/api/v1/ta_ready/response/all'


class TaMqttClient:
    def set_topics(self):
        # Set the topics for the specific TA
        self.MQTT_TOPIC_TA = MQTT_TOPIC_TA + "/" + self.ta_mqtt_endpoint

    def subscribe_topics(self):
        # Subscribe to the input topics
        self.mqtt_client.subscribe(MQTT_TOPIC_REQUEST_HELP)
        self.mqtt_client.subscribe(MQTT_TOPIC_GROUP_PRESENT)
        self.mqtt_client.subscribe(MQTT_TOPIC_GROUP_DONE)
        self.mqtt_client.subscribe(MQTT_TOPIC_PROGRESS)
        self.mqtt_client.subscribe(MQTT_TOPIC_TA_UPDATE)
        self.mqtt_client.subscribe(self.MQTT_TOPIC_TA)
        self.mqtt_client.subscribe(MQTT_TOPIC_TA_READY_REQUEST)

    # MQTT communication methods
    def on_connect(self, client, userdata, flags, rc):
        # Log that we are connected if the connection was successful
        self._logger.debug(f'MQTT connected to {client}')

    def on_message(self, client, userdata, msg):
        # Get the topic
        topic = msg.topic
        # Log the message received
        self._logger.debug(
            f'MQTT received message on topic {topic}, with payload {msg.payload}')

        # Unwrap the message
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
        except json.JSONDecodeError:
            self._logger.error(
                f'Could not decode JSON from message {msg.payload}')
            return

        # Get the command
        command = payload.get('command')
        header = payload.get('header')
        body = payload.get('body')

        self._logger.debug(f'Received command {command}')

        # Handle the different topics
        if command == "request_help":
            # Handle the request for help
            self.component.handle_request_help(header, body)
        elif command == "group_present":
            # Handle the group present message
            self.component.handle_group_present(header, body)
        elif command == "tasks_done":
            # Handle the group done message
            self.component.handle_group_done(header, body)
        elif command == "report_current_task":
            # Handle the progress message
            self.component.handle_group_progress(header, body)
        elif command == "ta_update_tasks":
            # Handle the ta update message
            self.component.handle_ta_update_tasks(header, body)
        elif command == "ta_update_receiving_help":
            # Handle the ta update message
            self.component.handle_ta_update_receiving_help(header, body)
        elif command == "ta_update_received_help":
            # Handle the ta update message
            self.component.handle_ta_update_received_help(header, body)
        elif command == "request_update_of_tables":
            # Handle the ta request for table updates
            self.component.handle_request_update_of_tables(header, body)
        elif command == "ta_update_tables":
            # Handle the ta update message
            self.component.handle_ta_update_tables(header, body)

    def publish_message(self, topic, message):
        """Publish a message to the MQTT broker.

        Args:
            topic (str): The topic to publish to.
            message (str): The message to publish.
        """
        payload = json.dumps(message)
        self._logger.debug(f'Publishing message to topic {topic}: {payload}')
        self.mqtt_client.publish(topic, payload, qos=2)

    # MQTT message creation logic
    def create_payload(self, command, header, body):
        """ Create a payload for the MQTT message """
        return {"command": command, "header": header, "body": body}

    def __init__(self, component, logger):
        self.component = component
        self._logger: logging.Logger = logger

        self._logger.debug('Initializing MQTT client')

        # create a new MQTT client
        self._logger.debug(
            f'Connecting to MQTT broker {MQTT_BROKER} at port {MQTT_PORT}')
        self.mqtt_client = mqtt.Client()
        # callback methods
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        # Setting the name of the ta to none (will be set when logging in)
        self.ta_mqtt_endpoint = None
        self.ta_name = None

        # Connect to the broker
        self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT)

    def request_update_of_tables(self):
        # Request the tables to be updated
        self._logger.info('Requesting update of tables')

        payload = self.create_payload(
            command="request_update_of_tables", header=self.ta_name, body="")

        self.publish_message(MQTT_TOPIC_TA_UPDATE, payload)

    def notify_student_groups_of_ta(self):
        payload = self.create_payload(
            command="ta_present_all", header=self.ta_name, body={})

        # Report that TA is ready
        self.publish_message(MQTT_TOPIC_TA_READY_RESPONSE_ALL, payload)

    def report_queue_number(self, group, queue_number):
        # Wrap the queue number in a list
        message = {"queue_number": f"{queue_number}"}

        mqtt_topic_endpoint = group.lower().replace(" ", "_")

        payload = self.create_payload(
            command="queue_number", header=self.ta_name, body=message)

        # Send the queue number to the group
        self.publish_message(MQTT_TOPIC_QUEUE_NUMBER +
                             "/" + mqtt_topic_endpoint, payload)

    def notify_other_tas_getting_help(self, body):
        payload = self.create_payload(
            command="ta_update_receiving_help", header=self.ta_name, body=body)

        self.publish_message(MQTT_TOPIC_TA_UPDATE, payload)

    def report_getting_help(self, group):
        # Wrap the group name in a list
        message = {"group": group}

        mqtt_topic_endpoint = group.lower().replace(" ", "_")

        payload = self.create_payload(
            command="getting_help", header=self.ta_name, body=message)

        # Send the group name to the group
        self.publish_message(MQTT_TOPIC_GETTING_HELP +
                             "/" + mqtt_topic_endpoint, payload)

    def report_received_help(self, group):
        # Wrap the group name in a list
        message = {"group": group}

        mqtt_topic_endpoint = group.lower().replace(" ", "_")

        payload = self.create_payload(
            command="received_help", header=self.ta_name, body=message)

        # Send the group name to the group
        self.publish_message(MQTT_TOPIC_RECEIVED_HELP +
                             "/" + mqtt_topic_endpoint, payload)

    def notify_other_tas_got_help(self, row):

        body = {
            "row": row
        }

        payload = self.create_payload(
            command="ta_update_received_help", header=self.ta_name, body=body)

        self.publish_message(MQTT_TOPIC_TA_UPDATE, payload)

    def report_ta_present(self, group):
        # Wrap the group name in a list
        message = {"ta": self.ta_name}

        mqtt_topic_endpoint = group.lower().replace(" ", "_")

        payload = self.create_payload(
            command="ta_present", header=self.ta_name, body=message)

        # Send the group name to the group
        self.publish_message(MQTT_TOPIC_TA_READY_RESPONSE +
                             "/" + mqtt_topic_endpoint, payload)

    def send_tasks_to_group(self, header, body):
        mqtt_topic_endpoint = header.lower().replace(" ", "_")

        payload = self.create_payload(
            command="submit_tasks_late", header=self.ta_name, body=body)

        # Send the tasks to the group
        self.publish_message(MQTT_TOPIC_TASKS_LATE + "/" +
                             mqtt_topic_endpoint, payload)

    def submit_tasks_to_groups(self, body):
        payload = self.create_payload(
            command="submit_tasks", header=self.ta_name, body=body)

        # Publish the tasks to the MQTT broker
        self.publish_message(MQTT_TOPIC_TASKS, payload)

    def submit_tasks_to_tas(self, body):
        payload = self.create_payload(
            command="ta_update_tasks", header=self.ta_name, body=body)

        # Send the tasks to the other TAs
        self.publish_message(MQTT_TOPIC_TA_UPDATE, payload)

    def send_tables_to_ta(self, header, body):
        payload = self.create_payload(
            command="ta_update_tables", header=self.ta_name, body=body)

        ta_endpoint = header.lower().replace(" ", "_")

        # Send the tasks to the TA that requested the update
        self.publish_message(MQTT_TOPIC_TA + "/" + ta_endpoint, payload)
