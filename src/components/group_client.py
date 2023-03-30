# Group client component
import appJar as app
from datetime import datetime


class GroupClientComponent:
    def __init__(self):
        self.app = app.gui()
        self.tasks = ["Task 1: Implement a linked list. Duration: 30min", "Task 2: Implement a stack. Duration: 30min",
                      "Task 3: Implement a queue. Duration: 30min", "Task 4: Implement a binary search tree. Duration: 30min", "Task 5: Implement a hash table. Duration: 30min"]
        self.teams = ['Select a team'] + [team for team in range(1, 21)]
        self.image_path = '../../assets/green_light.png'
        self.setup_gui()

    def setup_gui(self):
        self.app.setSize(800, 400)  # Set the size of the GUI window
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

        # Add all tasks to the listbox
        for task in self.tasks:
            self.app.addCheckBox(task)

        self.app.addLabel("description_label",
                          "Need help? - Ask TAs for help!")
        self.app.addLabelEntry("Description:")
        self.app.addButton("Request Help", self.on_request_help)

        self.app.addHorizontalSeparator(colour="black")

        self.app.addLabel("light_label", "Light status:")
        self.app.addImage("light", self.image_path)
        self.init_popup()
        self.app.go()

    def show_message(self):
        self.app.infoBox(title="Instructions", 
                         message="Use the checkboxes to mark the tasks you have completed. \
                         When you are ready to request help, enter a description of the help you need in the text \
                          field below and click the 'Request Help' button. The TAs will then come to your group and \
                          help you with your tasks. Good luck!")

    def init_popup(self):
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
        self.app.popUp(
            "Success", "Help request sent successfully", kind="info")
        print(help_request)


if __name__ == '__main__':
    client = GroupClientComponent()
