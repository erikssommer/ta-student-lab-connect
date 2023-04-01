# TA - Student lab connect
Semester project in the course Design of Communicating Systems at NTNU Trondheim

## Team 10 members
- Andreas Bjørnland
- Andreas Starheim Hernæs
- Edith Aguado
- Erik Storås Sommer
- Eva Vartdal Kvalø
- Petter Leine Alnes

## Project description
This project uses MQTT as communication protocol between two clients, a TA client and a student group client. The TA client is used to send out questions to the student group client. The student group client is used to answer the questions. The TA client can also send out a message to the student group client to indicate that the question is answered. The student group client can also send out a message to the TA client to indicate that the question is answered. 

### Install required packages
```bash
pip3 install -r requirements.txt
```

### How to run
Navigate to the src folder
```bash
cd src
```

Here there are two files, one for the TA client and one for the student client.
These files use the corresponding components and state machines

## Running the TA client
```bash
python3 ta_client.py
```

## Running the student group client
```bash
python3 group_client.py
```
