from threading import Thread
import stmpy
from appJar import gui
from datetime import datetime
import logging
from state_machines.ta_stm import TaLogic
from mqtt_clients.mqtt_ta_client import MqttTaClient

# TA client component

class TaClientComponent:

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
        print(f'logging under name {__name__}.')
        self._logger.info('Starting Component')

        # Create the MQTT handler
        self.mqtt_ta_client = MqttTaClient(self, logger)

        # Start the MQTT client in a separate thread to avoid blocking
        try:
            thread = Thread(target=self.mqtt_ta_client.mqtt_client.loop_start())
            thread.start()
        except KeyboardInterrupt:
            print("Interrupted")
            self.mqtt_ta_client.mqtt_client.disconnect()

        # Start the stmpy driver, without any state machines for now
        self.stm_driver = stmpy.Driver()
        self.stm_driver.start(keep_active=True)

        self._logger.debug('Component initialization finished')

        # Tracking if the tasks have been submitted (to avoid multiple submissions)
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
                          ["Description", "Duration (Minutes)"]], addRow=self.add_task, addButton='Add task')

        # Add a button to submit the tasks
        self.app.addButton("Submit tasks", self.submit_tasks)

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

        # Basic error handling for ensuring that the TA enters a name that can be used identifing the TA
        if name == "":
            self.app.errorBox("Error", "Please enter a name")
            return

        if name.isalpha() == False:
            self.app.errorBox("Error", "Please enter a name with only letters")
            return

        # Set the name of the TA
        self.ta_name = name

        # Set the endpont for the TA
        self.mqtt_ta_client.ta_mqtt_endpoint = self.ta_name.lower().replace(" ", "_")

        self.mqtt_ta_client.ta_name = self.ta_name

        self.app.hideSubWindow("Enter TA name")

        # Set the label in the upper right corner
        self.app.setLabel("upper_right_label", f"TA name: {name}")

        # Set the topics specific for the TA
        self.mqtt_ta_client.set_topics()

        # Subscribe to the topics
        self.mqtt_ta_client.subscribe_topics()

        # Request the tables to be updated for a late joiner
        self.mqtt_ta_client.request_update_of_tables()

        # Notify the student groups of the TA joining
        self.mqtt_ta_client.notify_student_groups_of_ta()

        # Create the ta state machine
        self.create_ta_stm()

    def sub_window_closed(self):
        """ Close the application if the popup window is closed """
        # Close the application if the popup window is closed
        self.app.popUp("Info", "Application will stop", kind="info")
        self._logger.info('Application will stop')
        self.app.stop()

    def show_instructions(self):
        """ Show instructions for the TA """
        self.app.infoBox(title="Instructions",
                         message="Assign tasks to the students by filling in the description and duration of the task. \
                            The duration must be a number. \
                                When you are done, press the submit button to publish the tasks to the MQTT broker. \
                                    The tasks will be enumberated from 1 to n, where n is the number of tasks.")

    def handle_request_help(self, header, body):
        # If group already in table, remove it
        for row in range(self.app.getTableRowCount("groups_request_help")):
            if self.app.getTableRow("groups_request_help", row)[0] == body['group']:
                self.app.deleteTableRow("groups_request_help", row)
                break

        # Get the data from the payload
        group = body['group']
        description = body['description']
        time = body['time']

        # Add the data to the table of groups requesting help
        self.app.addTableRow("groups_request_help", [
                             group, description, time])

        # Sort the table by time
        self.app.sortTable("groups_request_help", 2)

        # Log the action
        self._logger.info(
            f"Group {group} requested help with {description} at {time}")

        queue_number = self.app.getTableRowCount("groups_request_help")

        # Report the queue number to the group
        self.mqtt_ta_client.report_queue_number(header, queue_number + 1)

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
        self.mqtt_ta_client.report_getting_help(data[0])

        # Send the new queue number to all the groups
        self.send_new_queue_number_to_groups()

        self.notify_other_tas_getting_help(data, row)

        # Change state to "helping_group"
        self.stm_driver.send('help_group', self.ta_name)

    def send_new_queue_number_to_groups(self):
        for row in range(self.app.getTableRowCount("groups_request_help")):
            # Get the group name
            group = self.app.getTableRow("groups_request_help", row)[0]

            # Send the new queue number to the group
            self.mqtt_ta_client.report_queue_number(group, row + 1)

    def notify_other_tas_getting_help(self, data, row):
        # Create the body of the payload
        body = {
            "group": data[0],
            "description": data[1],
            "time": data[2],
            "ta": data[3],
            "row": row
        }

        self.mqtt_ta_client.notify_other_tas_getting_help(body)

    def assign_got_help(self, row):
        # Get the row of the table
        data = self.app.getTableRow("groups_getting_help", row)
        # Remove the row from the table of groups getting help
        self.app.deleteTableRow("groups_getting_help", row)

        # Log the action
        self._logger.info(f"Group {data[0]} got help")

        # Report to group that it got help
        self.mqtt_ta_client.report_received_help(data[0])

        # Notify other TAs that the group got help
        self.mqtt_ta_client.notify_other_tas_got_help(row)

        # Change state to "not_helping_group"
        self.stm_driver.send('help_recieved', self.ta_name)

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

        # Send the list of tasks to the group
        self.mqtt_ta_client.send_tasks_to_group(group, output_list)

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
        # Test if there are any groups present
        if self.app.getTableRowCount("group_status") == 0:
            self.app.popUp(
                "Error", "There are no groups to assign tasks to", kind="error")
            return

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

        # Send the list of tasks to the groups
        self.mqtt_ta_client.submit_tasks_to_groups(output_list)
        # Send the list of tasks to the TAs
        self.mqtt_ta_client.submit_tasks_to_tas(output_list)

        # Change the status of the tasks to submitted
        self.tasks_submitted = True

    def handle_group_present(self, header, body):
        # Notify the group that the TA is present
        self.mqtt_ta_client.report_ta_present(header)

        # Get the data from the payload
        group = body['group']

        if self.app.getTableRowCount("assigned_tasks") == 0 and not self.tasks_submitted:
            self.app.addTableRow(
                "group_status", [group, "Waiting for TAs to assign tasks..."])
            return

        status = "Task 1 in progress"

        # Add the data to the table of groups and their status
        self.app.addTableRow("group_status", [group, status])

        # Send the list of tasks to the group
        if self.tasks_submitted:
            self.update_group_with_tasks(group)

    def handle_group_done(self, header, body):
        # Get the data from the payload
        group = body['group']
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

    # Handle request methods

    def handle_group_progress(self, header, body):
        # Get the data from the payload
        group = body['group']
        task = body['current_task']
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

        # Get the data from the tables
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

        # Create the body of the payload
        body = {
            "assigned_tasks": assigned_tasks,
            "groups_request_help": groups_request_help,
            "groups_getting_help": groups_getting_help,
            "group_status": group_status
        }

        # Send the tables to the TA requesting the update
        self.mqtt_ta_client.send_tables_to_ta(header, body)

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

        # Update the table of assigned tasks
        if self.app.getTableRowCount("assigned_tasks") == 0:
            if len(body['assigned_tasks']) != 0:
                for item in body['assigned_tasks']:
                    self.app.addTableRow("assigned_tasks", [
                        item[0], item[1]])

                self.tasks_submitted = True
        

        # Update the groups requesting help
        if self.app.getTableRowCount("groups_request_help") == 0:
            for item in body['groups_request_help']:
                self.app.addTableRow("groups_request_help", [
                    item[0], item[1], item[2]])

        # Update the table of groups getting help
        if self.app.getTableRowCount("groups_getting_help") == 0:
            for item in body['groups_getting_help']:
                self.app.addTableRow("groups_getting_help", [
                    item[0], item[1], item[2], item[3]])

        # Update the status of the groups
        if self.app.getTableRowCount("group_status") == 0:
            for item in body['group_status']:
                self.app.addTableRow("group_status", [
                    item[0], item[1]])

    def stop(self):
        """
        Stop the component.
        """
        # stop the MQTT client
        self.mqtt_ta_client.mqtt_client.loop_stop()

        # stop the stmpy drivers
        self.stm_driver.stop()

        # Log the shutdown
        self._logger.info('Shutting down TA client component')
        exit()
