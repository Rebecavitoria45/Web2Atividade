from PIL import Image, ImageDraw
import os
from confluent_kafka import Consumer, KafkaError
import json
import logging
from time import sleep
from uuid import uuid4
from confluent_kafka import Producer
import time
#from notificator_app.app import notificate


OUT_FOLDER = '/processed/text/'
NEW = '_text'
IN_FOLDER = "/appdata/static/uploads/"

TOPIC='operation'

def delivery_report(errmsg, data):
    """
    Reports the Failure or Success of a message delivery.
    Args:
        errmsg  (KafkaError): The Error that occured while message producing.
        data    (Actual message): The message that was produced.
    Note:
        In the delivery report callback the Message.key() and Message.value()
        will be the binary format as encoded by any configured Serializers and
        not the same object that was passed to produce().
        If you wish to pass the original object(s) for key and value to delivery
        report callback we recommend a bound callback or lambda where you pass
        the objects along.
    """
    if errmsg is not None:
        print("Delivery failed for Message: {} : {}".format(data.key(), errmsg))
        return
    print('Message: {} successfully produced to Topic: {} Partition: [{}] at offset {}'.format(
        data.key(), data.topic(), data.partition(), data.offset()))

def create_text(path_file):
    pathname, filename = os.path.split(path_file)
    output_folder = pathname + OUT_FOLDER

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    operation = "text"
 
    original_image = Image.open(path_file)
    draw = ImageDraw.Draw(original_image)    
    name, ext = os.path.splitext(filename)
    draw.text((0, 0),f"{name}", fill='black', font_size=35)
    original_image.save(output_folder + name + NEW + ext)
    
    publish(TOPIC, filename)
    
def get_json_str(timestamp, filename):
    d = {
        'timestamp': timestamp,
        'new_file': filename,
        'operation': 'text'
    }
    return json.dumps(d)
    
def publish(topic, filename):
    p = Producer({'bootstrap.servers': 'kafka1:19091,kafka2:19092,kafka3:19093'})
    p.produce(topic, key=str(uuid4()), value=get_json_str(time.time(), filename), on_delivery=delivery_report)
    p.flush()
    
    

#sleep(30)
### Consumer
c = Consumer({
    'bootstrap.servers': 'kafka1:19091,kafka2:19092,kafka3:19093',
    'group.id': 'text-group',
    'client.id': 'client-1',
    'enable.auto.commit': True,
    'session.timeout.ms': 6000,
    'default.topic.config': {'auto.offset.reset': 'smallest'}
})

c.subscribe(['image'])
#{"timestamp": 1649288146.3453217, "new_file": "9PKAyoN.jpeg"}

try:
    while True:
        msg = c.poll(0.1)
        if msg is None:
            continue
        elif not msg.error():
            data = json.loads(msg.value())
            filename = data['new_file']
            logging.warning(f"READING {filename}")
            create_text(IN_FOLDER + filename)
            logging.warning(f"ENDING {filename}")
        elif msg.error().code() == KafkaError._PARTITION_EOF:
            logging.warning('End of partition reached {0}/{1}'
                  .format(msg.topic(), msg.partition()))
        else:
            logging.error('Error occured: {0}'.format(msg.error().str()))

except KeyboardInterrupt:
    pass
finally:
    c.close()
