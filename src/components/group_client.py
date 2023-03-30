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
        self.init_popup()
        self.app.go()
    
    def init_popup(self):
        # Define the popup window
        self.app.startSubWindow("Enter Message", modal=True)
        self.app.setSize(300, 200)
        self.app.addLabel("message_label", "Enter your message:")
        self.app.addEntry("message_entry")
        self.app.addButton("Submit", self.submit_message)
        self.app.stopSubWindow()
        
        # Show the popup window
        self.app.showSubWindow("Enter Message")

    def submit_message(self):
        # Retrieve the message from the input field
        message = self.app.getEntry("message_entry")
        
        # Test if the message is empty
        if message == "":
            self.app.popUp("Error", "Please enter a message", kind="error")
            return
        self.group_nr = message
        # Close the popup window
        self.app.hideSubWindow("Enter Message")
        # Set the label in the upper right corner
        self.app.setSticky("ne")
        self.app.setLabel("upper_right_label", self.group_nr)
    

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
