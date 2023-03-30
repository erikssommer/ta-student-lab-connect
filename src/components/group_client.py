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
        self.app.setSticky("ne")
        self.app.addLabel("upper_right_label", "Group Number")
        self.app.setSticky("news")
        self.app.setStretch("both")
        self.app.addLabel("title", "Group Client Component")
        self.app.addLabel("tasks_label", "Current Tasks:")
        self.app.addListBox("tasks_list", self.tasks)
        self.app.addLabelEntry("Description")
        self.app.addButton("Request Help", self.on_request_help)
        self.app.addImage("light", self.image_path)
        self.init_popup()
        self.app.go()
    
    def init_popup(self):
        # Define the popup window
        self.app.startSubWindow("Enter Group Number", modal=True)
        self.app.setSize(300, 200)
        self.app.addLabel("message_label", "Enter your message:")
        self.app.addEntry("message_entry")
        self.app.addButton("Submit", self.submit_message)
        self.app.setStopFunction(self.sub_window_closed)
        self.app.stopSubWindow()
        
        # Show the popup window
        self.app.showSubWindow("Enter Group Number")

    def submit_message(self):
        # Retrieve the message from the input field
        message = self.app.getEntry("message_entry")

        # Test if the message is empty
        if message == "":
            self.app.popUp("Error", "Please enter a message", kind="error")
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
        help_request = self.app.getEntry("Description")
        # Test if the help request is empty
        if help_request == "":
            self.app.popUp("Error", "Please enter a description of the help you need", kind="error")
            return
        self.app.clearEntry("Description")
        self.app.popUp("Success", "Help request sent successfully", kind="info")

if __name__ == '__main__':
    client = GroupClientComponent()
