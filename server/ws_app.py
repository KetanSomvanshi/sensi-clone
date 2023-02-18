import json

from data_adapter.ws import WS
from models.sensi_models import BrokerWSMessage


async def listener():
    await WS.get_instance().connect()
    while True:
        data = await WS.get_instance().recv()
        message_from_broker = BrokerWSMessage.parse_obj(data)
        print(message_from_broker)
        if message_from_broker.data_type == 'quote':
            print("jfiljdsgvshkgbishguihsvnboir")


async def sender(data: json):
    await WS.get_instance().send(data)
