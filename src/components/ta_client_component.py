from threading import Thread
import paho.mqtt.client as mqtt
import stmpy
from appJar import gui
from datetime import datetime
import json
import logging
from state_machines.ta_stm import TaLogic

# TA client component

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


class TaClientComponent:

    def set_topics(self):
        self.MQTT_TOPIC_TA = MQTT_TOPIC_TA + "/" + self.ta_mqtt_endpoint

    def subscribe_topics(self):
        # Subscribe to the input topics
        self.mqtt_client.subscribe(MQTT_TOPIC_REQUEST_HELP)
        self.mqtt_client.subscribe(MQTT_TOPIC_GROUP_PRESENT)
        self.mqtt_client.subscribe(MQTT_TOPIC_GROUP_DONE)
        self.mqtt_client.subscribe(MQTT_TOPIC_PROGRESS)
        self.mqtt_client.subscribe(MQTT_TOPIC_TA_UPDATE)
        self.mqtt_client.subscribe(self.MQTT_TOPIC_TA)

    # MQTT communication methods
    def on_connect(self, client, userdata, flags, rc):
        # Only log that we are connected if the connection was successful
        self._logger.debug('MQTT connected to {}'.format(client))

    def on_message(self, client, userdata, msg):
        # Log the message received
        self._logger.debug('MQTT received message: {}'.format(msg.payload))

        # Unwrap the message
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
        except json.JSONDecodeError:
            self._logger.error(
                'Could not decode JSON from message {}'.format(msg.payload))
            return

        # Get the command
        command = payload.get('command')
        header = payload.get('header')
        body = payload.get('body')

        self._logger.debug(f'Received command {command}')

        # Handle the different topics
        if command == "request_help":
            # Handle the request for help
            self.handle_request_help(header, body)
        elif command == "group_present":
            # Handle the group present message
            self.handle_group_present(header, body)
        elif command == "tasks_done":
            # Handle the group done message
            self.handle_group_done(header, body)
        elif command == "report_current_task":
            # Handle the progress message
            self.handle_group_progress(header, body)
        elif command == "ta_update_tasks":
            # Handle the ta update message
            self.handle_ta_update_tasks(header, body)
        elif command == "ta_update_receiving_help":
            # Handle the ta update message
            self.handle_ta_update_receiving_help(header, body)
        elif command == "ta_update_received_help":
            # Handle the ta update message
            self.handle_ta_update_received_help(header, body)
        elif command == "request_update_of_tables":
            # Handle the ta request for table updates
            self.handle_request_update_of_tables(header, body)
        elif command == "ta_update_tables":
            # Handle the ta update message
            self.handle_ta_update_tables(header, body)

    def publish_message(self, topic, message):
        payload = json.dumps(message)
        self._logger.debug(
            'Publishing message to topic {}: {}'.format(topic, payload))
        self.mqtt_client.publish(topic, payload, qos=2)

    # MQTT message creation logic
    def create_payload(self, command, header, body):
        """ Create a payload for the MQTT message """
        return {"command": command, "header": header, "body": body}

    # State machine methods
    def create_ta_stm(self):
        """ Create a new ta state machine """
        # Create a new group state machine
        ta_stm = TaLogic.create_machine(
            ta=self.ta_name, component=self, logger=self._logger)
        # Add the state machine to the driver
        self.stm_driver.add_machine(ta_stm)

    def __init__(self, logger):
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

        # Start the MQTT client in a separate thread to avoid blocking
        try:
            thread = Thread(target=self.mqtt_client.loop_start())
            thread.start()
        except KeyboardInterrupt:
            print("Interrupted")
            self.mqtt_client.disconnect()

        # Start the stmpy driver, without any state machines for now
        self.stm_driver = stmpy.Driver()
        self.stm_driver.start(keep_active=True)

        self._logger.debug('Component initialization finished')

        self.tasks_submitted = False

        # Can only update tables once
        self.update_tabels = False

        # Settup the GUI
        self.setup_gui()

    def setup_gui(self):
        self.app = gui()

        # Set the background color of the GUI window
        self.app.setBg("light blue")

        # Set the size of the GUI window and primary elements
        self.app.setSize(800, 1050)  # Set the size of the GUI window

        self.app.setResizable(canResize=False)

        # Set the font size of the buttons
        self.app.setButtonFont(size=15, family="Verdana",
                               underline=False, slant="roman")

        self.app.setTitle("TA client")  # Set the title of the GUI window
        # Set the label in the upper right corner
        self.app.addLabel("upper_right_label_date",
                          f"Date: {datetime.now().strftime('%d/%m/%Y')}").config(font="Helvetica 15")
        self.app.addLabel("upper_right_label", "TA name").config(
            font="Helvetica 15")
        self.app.setLabelSticky("upper_right_label_date", "ne")
        self.app.setLabelSticky("upper_right_label", "ne")

        # Add image of school logo
        self.app.addImage("logo", "../assets/ntnu_logo.gif")

        self.app.addLabel("title", "Welcome to the lab").config(
            font="Helvetica 25")

        self.app.addLabel("subtitle", "Add tasks for the lab session:").config(
            font="Helvetica 15")
        self.app.setLabelSticky("subtitle", "w")

        self.app.addButton("Show Instructions", self.show_instructions)
        self.app.setButtonSticky("Show Instructions", "w")

        # Empty label to separate the tables
        self.app.addEmptyLabel("empty_label1")

        # Set up a table to contain the tasks
        self.app.addTable("assigned_tasks", [
                          ["Description", "Duration"]], addRow=self.add_task, addButton='Add task')

        # Add a button to submit the tasks
        self.app.addButton("Submit tasks", self.submit_tasks)
        self.app.setButtonSticky("Submit tasks", "w")

        # Empty label to separate the tables
        self.app.addEmptyLabel("empty_label2")

        # Label for the table of groups requesting help
        self.app.addLabel("groups_request_help_label",
                          "Groups requesting help:").config(font="Helvetica 15")
        self.app.setLabelSticky("groups_request_help_label", "w")
        # Add a table of groups requesting help
        self.app.addTable("groups_request_help", [
                          ["Group", "Description", "Time"]], action=self.assign_getting_help, actionButton="Mark as getting help")

        # Label for the table of groups getting help
        self.app.addLabel("groups_getting_help_label",
                          "Groups getting help: (ordered by time)").config(font="Helvetica 15")
        self.app.setLabelSticky("groups_getting_help_label", "w")

        # Add a table of groups getting help
        self.app.addTable("groups_getting_help", [
                          ["Group", "Description", "Time", "TA"]], action=self.assign_got_help, actionButton="Mark as got help")

        # Add label for group status
        self.app.addLabel("group_status_label", "Groups present and status:").config(
            font="Helvetica 15")
        self.app.setLabelSticky("group_status_label", "w")

        # Add a table of groups and their status
        self.app.addTable("group_status", [["Group", "Current task"]])

        # Setting up the component for the given ta
        self.show_enter_ta_name_popup()

        self.app.setStopFunction(self.stop)

        # Start the GUI
        self.app.go()

    def show_enter_ta_name_popup(self):
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

        if name == "":
            self.app.errorBox("Error", "Please enter a name")
            return
        
        if name.isalpha() == False:
            self.app.errorBox("Error", "Please enter a name with only letters")
            return

        # Set the name of the TA
        self.ta_name = name

        # Set the endpont for the TA
        self.ta_mqtt_endpoint = self.ta_name.lower().replace(" ", "_")

        self.app.hideSubWindow("Enter TA name")

        # Set the label in the upper right corner
        self.app.setLabel("upper_right_label", f"TA name: {name}")

        # Set the topics specific for the TA
        self.set_topics()

        # Subscribe to the topics
        self.subscribe_topics()

        # Request the tables to be updated for a late joiner
        self.request_update_of_tables()

        # Create the ta state machine
        self.create_ta_stm()

    def sub_window_closed(self):
        """ Close the application if the popup window is closed """
        # Close the application if the popup window is closed
        self.app.popUp("Info", "Application will stop", kind="info")
        self._logger.info('Application will stop')
        self.app.stop()

    def show_instructions(self):
        self.app.infoBox(title="Instructions",
                         message="Assign tasks to the students by filling in the description and duration of the task. \
                            The duration must be a number. \
                                When you are done, press the submit button to publish the tasks to the MQTT broker. \
                                    The tasks will be enumberated from 1 to n, where n is the number of tasks.")

    def request_update_of_tables(self):
        # Request the tables to be updated
        self._logger.info('Requesting update of tables')

        payload = self.create_payload(
            command="request_update_of_tables", header=self.ta_name, body="")

        self.publish_message(MQTT_TOPIC_TA_UPDATE, payload)

    def handle_request_help(self, header, body):
        # If group already in table, remove it
        for row in range(self.app.getTableRowCount("groups_request_help")):
            if self.app.getTableRow("groups_request_help", row)[0] == body[0]['group']:
                self.app.deleteTableRow("groups_request_help", row)
                break

        # Get the data from the payload
        group = body[0]['group']
        description = body[0]['description']
        time = body[0]['time']

        # Add the data to the table of groups requesting help
        self.app.addTableRow("groups_request_help", [
                             group, description, time])

        # Sort the table by time
        self.app.sortTable("groups_request_help", 2)

        # Log the action
        self._logger.info(
            f"Group {group} requested help with {description} at {time}")

        # Report the queue number to the group
        self.report_queue_number(header)

    def report_queue_number(self, group):
        # Get the number of groups in the queue
        queue_number = self.app.getTableRowCount("groups_request_help")

        # Wrap it in a list
        message = [{"queue_number": f"{queue_number + 1}"}]

        # Send the queue number to the group
        self.publish_message(MQTT_TOPIC_QUEUE_NUMBER + "/" + group, message)

    def assign_getting_help(self, row):
        # Get the row of the table
        data = self.app.getTableRow("groups_request_help", row)

        # Add the TA name to the data
        data.append(self.ta_name)

        # Add the row to the table of groups getting help
        self.app.addTableRow("groups_getting_help", data)
        # Remove the row from the table of groups requesting help
        self.app.deleteTableRow("groups_request_help", row)

        # Log the action
        self._logger.info(f"Group {data[0]} is getting help")

        # Report to group that it is getting help
        self.report_getting_help(data[0])

        self.notify_other_tas_getting_help(data, row)

        # Change state to "helping_group"
        self.stm_driver.send('help_group', self.ta_name)

    def notify_other_tas_getting_help(self, data, row):
        body = {
            "group": data[0],
            "description": data[1],
            "time": data[2],
            "ta": data[3],
            "row": row
        }

        payload = self.create_payload(
            command="ta_update_receiving_help", header=self.ta_name, body=body)

        self.publish_message(MQTT_TOPIC_TA_UPDATE, payload)

    def report_getting_help(self, group):
        # Wrap the group name in a list
        message = [{"group": group}]

        mqtt_topic_endpoint = group.lower().replace(" ", "_")

        # Send the group name to the group
        self.publish_message(MQTT_TOPIC_GETTING_HELP +
                             "/" + mqtt_topic_endpoint, message)

    def report_received_help(self, group):
        # Wrap the group name in a list
        message = [{"group": group}]

        mqtt_topic_endpoint = group.lower().replace(" ", "_")

        # Send the group name to the group
        self.publish_message(MQTT_TOPIC_RECEIVED_HELP +
                             "/" + mqtt_topic_endpoint, message)

    def assign_got_help(self, row):
        # Get the row of the table
        data = self.app.getTableRow("groups_getting_help", row)
        # Remove the row from the table of groups getting help
        self.app.deleteTableRow("groups_getting_help", row)

        # Log the action
        self._logger.info(f"Group {data[0]} got help")

        # Report to group that it got help
        self.report_received_help(data[0])

        # Notify other TAs that the group got help
        self.notify_other_tas_got_help(row)

        # Change state to "not_helping_group"
        self.stm_driver.send('help_recieved', self.ta_name)

    def notify_other_tas_got_help(self, row):

        body = {
            "row": row
        }

        payload = self.create_payload(
            command="ta_update_received_help", header=self.ta_name, body=body)

        self.publish_message(MQTT_TOPIC_TA_UPDATE, payload)

    def handle_group_present(self, header, body):
        # Get the data from the payload
        group = body['group']

        if self.app.getTableRowCount("assigned_tasks") == 0:
            self.app.addTableRow(
                "group_status", [group, "Waiting for TAs to assign tasks..."])
            return

        status = "Task 1 in progress"

        # Add the data to the table of groups and their status
        self.app.addTableRow("group_status", [group, status])

        # Send the list of tasks to the group
        if self.tasks_submitted:
            self.update_group_with_tasks(group)

    def update_group_with_tasks(self, group):
        data_list = []

        for row in range(self.app.getTableRowCount("assigned_tasks")):
            data_list.append(self.app.getTableRow("assigned_tasks", row))

        # Convert into a json list of dictionaries
        output_list = []

        for index, sublist in enumerate(data_list):
            task_dict = {
                "task": str(index+1),
                "description": sublist[0],
                "duration": sublist[1]
            }
            output_list.append(task_dict)

        mqtt_topic_endpoint = group.lower().replace(" ", "_")

        # Send the tasks to the group
        self.publish_message(MQTT_TOPIC_TASKS_LATE + "/" +
                             mqtt_topic_endpoint, output_list)

    def handle_group_done(self, header, body):
        # Get the data from the payload
        group = body[0]['group']
        delete_row = None

        # Find the row of the group in the table
        for row in range(self.app.getTableRowCount("group_status")):
            if self.app.getTableRow("group_status", row)[0] == group:
                delete_row = row
                break

        if delete_row is None:
            self._logger.error(f"Group {group} not found in table")
            return

        # Remove the row from the table of groups and their status
        self.app.replaceTableRow("group_status", delete_row, [group, "Done"])

    def handle_group_progress(self, header, body):
        # Get the data from the payload
        group = body[0]['group']
        task = body[0]['current_task']
        task = f"Task {task} in progress"
        update_row = None

        # Find the row of the group in the table
        for row in range(self.app.getTableRowCount("group_status")):
            if self.app.getTableRow("group_status", row)[0] == group:
                update_row = row
                break

        if update_row is None:
            self._logger.error(f"Group {group} not found in table")
            return

        # Update the row from the table of groups and their status
        self.app.replaceTableRow("group_status", update_row, [group, task])

    def add_task(self):
        data_list = self.app.getTableEntries("assigned_tasks")

        # Test if the description or duration is empty
        if data_list[0] == "" or data_list[1] == "":
            self.app.popUp(
                "Error", "Description and duration must be filled", kind="error")
            return

        # Test if the duration is a number
        try:
            int(data_list[1])
        except ValueError:
            self.app.popUp("Error", "Duration must be a number", kind="error")
            return

        self.app.addTableRow("assigned_tasks", data_list)

    def submit_tasks(self):
        # Test if the tasks have already been submitted
        if self.tasks_submitted:
            self.app.popUp(
                "Error", "The tasks have already been submitted. Can only submitt tasks once", kind="error")
            return

        # Test if there are any tasks
        if self.app.getTableRowCount("assigned_tasks") == 0:
            self.app.popUp(
                "Error", "There are no tasks to submit", kind="error")
            return

        data_list = []

        for row in range(self.app.getTableRowCount("assigned_tasks")):
            data_list.append(self.app.getTableRow("assigned_tasks", row))

        # Convert into a json list of dictionaries
        output_list = []

        for index, sublist in enumerate(data_list):
            task_dict = {
                "task": str(index+1),
                "description": sublist[0],
                "duration": sublist[1]
            }
            output_list.append(task_dict)

        # Change the status of the groups to "Task 1 in progress"
        for row in range(self.app.getTableRowCount("group_status")):
            data = self.app.getTableRow("group_status", row)
            data[1] = "Task 1 in progress"
            self.app.replaceTableRow("group_status", row, data)

        # Publish the tasks to the MQTT broker
        self.publish_message(MQTT_TOPIC_TASKS, output_list)

        payload = self.create_payload(
            command="ta_update_tasks", header=self.ta_name, body=output_list)

        # Send the tasks to the other TAs
        self.publish_message(MQTT_TOPIC_TA_UPDATE, payload)

        self.tasks_submitted = True

    def handle_ta_update_tasks(self, header, body):
        # Testing if the message is from the same TA then do nothing
        if header == self.ta_name:
            return

        # Test if there are any tasks
        if self.app.getTableRowCount("assigned_tasks") != 0:
            self._logger.info(
                "The tasks have already been submitted. Can only submitt tasks once")
            return

        # Add the tasks to the table
        for task in body:
            self.app.addTableRow("assigned_tasks", [
                                 task['description'], task['duration']])

        # Change the status of the groups to "Task 1 in progress"
        for row in range(self.app.getTableRowCount("group_status")):
            data = self.app.getTableRow("group_status", row)
            data[1] = "Task 1 in progress"
            self.app.replaceTableRow("group_status", row, data)

        self.tasks_submitted = True

    def handle_ta_update_receiving_help(self, header, body):
        # Testing if the message is from the same TA then do nothing
        if header == self.ta_name:
            return

        # Remove the row from the table of groups requesting help
        self.app.deleteTableRow("groups_request_help", body['row'])

        # Add the groups to the table
        self.app.addTableRow("groups_getting_help", [
                             body['group'], body['description'], body['time'], body['ta']])

    def handle_ta_update_received_help(self, header, body):
        # Testing if the message is from the same TA then do nothing
        if header == self.ta_name:
            return

        # Remove the row from the table of groups requesting help
        self.app.deleteTableRow("groups_getting_help", body['row'])

    def handle_request_update_of_tables(self, header, body):
        # Test if the message is from the same TA then do nothing
        if header == self.ta_name:
            return

        assigned_tasks, groups_request_help, groups_getting_help, group_status = [], [], [], []

        if self.app.getTableRowCount("assigned_tasks") != 0 and self.tasks_submitted:
            for row in range(self.app.getTableRowCount("assigned_tasks")):
                assigned_tasks.append(
                    self.app.getTableRow("assigned_tasks", row))

        if self.app.getTableRowCount("groups_request_help") != 0:
            for row in range(self.app.getTableRowCount("groups_request_help")):
                groups_request_help.append(
                    self.app.getTableRow("groups_request_help", row))

        if self.app.getTableRowCount("groups_getting_help") != 0:
            for row in range(self.app.getTableRowCount("groups_getting_help")):
                groups_getting_help.append(
                    self.app.getTableRow("groups_getting_help", row))

        if self.app.getTableRowCount("group_status") != 0:
            for row in range(self.app.getTableRowCount("group_status")):
                group_status.append(self.app.getTableRow("group_status", row))

        # Test if all the tables are empty, if so then do nothing
        if len(assigned_tasks) == 0 and len(groups_request_help) == 0 \
                and len(groups_getting_help) == 0 and len(group_status) == 0:
            return

        body = {
            "assigned_tasks": assigned_tasks,
            "groups_request_help": groups_request_help,
            "groups_getting_help": groups_getting_help,
            "group_status": group_status
        }

        payload = self.create_payload(
            command="ta_update_tables", header=self.ta_name, body=body)

        ta_endpoint = header.lower().replace(" ", "_")

        # Send the tasks to the TA that requested the update
        self.publish_message(MQTT_TOPIC_TA + "/" + ta_endpoint, payload)

    def handle_ta_update_tables(self, header, body):
        # Only update the tables once
        if self.update_tabels:
            return
        
        self.update_tabels = True

        # Test if there are any tasks
        if self.app.getTableRowCount("assigned_tasks") != 0:
            self._logger.info(
                "The tasks have already been submitted. Can only submitt tasks once")
            return

        # Add the tasks to the table
        if self.app.getTableRowCount("assigned_tasks") == 0:
            for item in body['assigned_tasks']:
                self.app.addTableRow("assigned_tasks", [
                                    item[0], item[1]])
                
        # Add the groups to the table
        if self.app.getTableRowCount("groups_request_help") == 0:
            for item in body['groups_request_help']:
                self.app.addTableRow("groups_request_help", [
                                    item[0], item[1], item[2]])

        # Add the groups to the table
        if self.app.getTableRowCount("groups_getting_help") == 0:
            for item in body['groups_getting_help']:
                self.app.addTableRow("groups_getting_help", [
                                    item[0], item[1], item[2], item[3]])

        # Add the groups to the table
        if self.app.getTableRowCount("group_status") == 0:
            for item in body['group_status']:
                self.app.addTableRow("group_status", [
                                    item[0], item[1]])

    def stop(self):
        """
        Stop the component.
        """
        # stop the MQTT client
        self.mqtt_client.loop_stop()

        # stop the stmpy drivers
        self.stm_driver.stop()

        # Log the shutdown
        self._logger.info('Shutting down TA client component')
        exit()
