from PIL import Image, ImageOps
import os
from confluent_kafka import Consumer, KafkaError
import json
import logging
from time import sleep
import smtplib, ssl
from email.message import EmailMessage

OUT_FOLDER = '/processed/notificator/'
NEW = '_notificator'
IN_FOLDER = "/appdata/static/uploads/"

def notificate(path_file, operation):
    pathname, filename = os.path.split(path_file)
    output_folder = pathname + OUT_FOLDER

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    name, ext = os.path.splitext(filename)
    
    port = 465
    smtp_server = "smtp.gmail.com"
    sender_email = os.getenv("GMAIL_EMAIL")
    receiver_email = os.getenv("GMAIL_EMAIL")
    password = os.getenv("GMAIL_PASS") 

    subject = "Notificação Atividade PubSub!"


    body = f"Olá {receiver_email}, no arquivo {filename} foi feita a operação de {operation}!"
    
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg.set_content(body)
    
    context = ssl.create_default_context()
    
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.send_message(msg)
    



#sleep(30)
### Consumer
c = Consumer({
    'bootstrap.servers': 'kafka1:19091,kafka2:19092,kafka3:19093',
    'group.id': 'notificator-group',
    'client.id': 'client-1',
    'enable.auto.commit': True,
    'session.timeout.ms': 6000,
    'default.topic.config': {'auto.offset.reset': 'smallest'}
})

c.subscribe(['operation'])
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
            operation = data['operation']
            notificate(IN_FOLDER + filename, operation)
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
