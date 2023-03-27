# Group client component
import appJar as app
import os

class GroupClientComponent:
    def __init__(self):
        self.app = app.gui()
        self.tasks = ["Task 1", "Task 2", "Task 3"]
        self.image_path = '../../assets/green_light.png'
        self.setup_gui()

    def setup_gui(self):
        self.app.setSize(600, 400)  # Set the size of the GUI window
        self.app.addLabel("title", "Group Client Component")
        self.app.addLabel("tasks_label", "Current Tasks:")
        self.app.addListBox("tasks_list", self.tasks)
        self.app.addLabelEntry("Description")
        self.app.addButton("Request Help", self.on_request_help)
        self.app.go()

    def on_request_help(self):
        help_request = self.app.getEntry("Description")
        # Test if the help request is empty
        if help_request == "":
            self.app.popUp("Error", "Please enter a description of the help you need", kind="error")
            return
        self.app.clearEntry("Description")
        self.app.popUp("Success", "Help request sent successfully", kind="info")

if __name__ == '__main__':
    client = GroupClientComponent()
