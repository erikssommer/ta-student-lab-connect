# TA - Student lab connect
Semester project in the course Design of Communicating Systems at NTNU Trondheim

## Team 10 members
- ...
- ...
- Edith Aguado Roca
- Erik Storås Sommer
- ...
- ...

## Project description
This project uses MQTT as communication protocol between two clients, a TA client and a student group client. The TA client is used to send out tasks to the student group clients. The student group clients is used by the groups to register progress and request help if needed. The TA client can then see the progress of the groups and help them if needed.

## How to run the project
### Install required packages
```bash
pip3 install -r requirements.txt
```


### Navigate to the src folder
```bash
cd src
```

Here there are two files, one for the TA client and one for the student client.
These files use the corresponding components and state machines

### Running the TA client
```bash
python3 ta_client.py
```

### Running the student group client
```bash
python3 group_client.py
```
