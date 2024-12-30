from kafka import KafkaConsumer

import threading
import json
import time

class Consumer(threading.Thread):
    def __init__(self, topic, group_id, bootstrap_servers, **kwargs):
        super(Consumer, self).__init__()
        self.topic = topic
        self.group_id = group_id
        self.bootstrap_servers = bootstrap_servers
    
    def run(self):
        consumer = KafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        for message in consumer:
            print(message)