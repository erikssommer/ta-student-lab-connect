class MqttTa:
    def __init__(self, mqtt_client, topic):
        self.mqtt_client = mqtt_client
        self.topic = topic
        
    