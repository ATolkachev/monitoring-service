import json
from time import time
from aiohttp import web
from pymongo import MongoClient
import pika
import argparse
import sys

class RestService():
    _max_monitor_id = 0
    _rest_config = {}

    def __init__(self):
        self._rest_config = self.load_args()
        self._rest_config["server"] = self._rest_config['server']
        self._rest_config["amqp"] = self._rest_config['amqp']

        self.client = MongoClient(self._rest_config['server'])
        self.db = self.client[self._rest_config['database']]
        self.alert_collection = self.db['alerts']
        self.monitor_collection = self.db['monitor']

        self.get_max_monitor_id()

    def load_args(self):

        def createParser():
            parser = argparse.ArgumentParser(
                prog='rest.py',
                description='''Monitoring service REST-API''',
                epilog='''(c) Alexander Tolkachev 2017.''',
                add_help=True
            )

            parser.add_argument('--address', type=str, help='Listening Address', default="127.0.0.1")
            parser.add_argument('--port', type=int, help='Listening Port', default=8080)
            parser.add_argument('--db', type=str, help='Database connection string', required=False, default="mongodb://127.0.0.1/")
            parser.add_argument('--database', type=str, help='Monitoring database name', required=False,
                                default="monitoring")
            parser.add_argument('--amqp', type=str, help='AMQP server', required=False,
                                default="127.0.0.1")

            return parser

        parser = createParser()
        args, unknown = parser.parse_known_args()

        return {'server': args.db,
                'database': args.database,
                'address': args.address,
                'port': args.port,
                'amqp': args.amqp}

    def get_max_monitor_id(self):
        max_dict = self.monitor_collection.find().sort([("id", -1)]).limit(1)

        self._max_monitor_id = 0

        for doc in max_dict:
            self._max_monitor_id = int(doc['id'])

        return self._max_monitor_id
        # sort({_id:-1}).limit(1).pretty()

    def get_monitor(self, id):
        return self.monitor_collection.find_one({"id": id})

    def get_status(self, monitor_id):
        return self.alert_collection.find_one({"monitor_id": monitor_id})

    def get_alert(self, id):
        return self.alert_collection.find_one({"_id": id})

    def insert_monitor(self, monitor):
        result = self.monitor_collection.insert_one(monitor)

        return monitor["id"]

    def __exit__(self, exc_type, exc_value, traceback):
        self.client.close()

    def get_all_checks(self):
        result = []
        data = self.monitor_collection.find({})
        for check in data:
            result.append(self.prepare_monitor(check))

        return result

    def get_check_status(self, id):
        result = ''
        if (id < 1):
            result = {"items": self.get_all_checks()}
        else:
            result = self.prepare_monitor(self.get_monitor(id))

        return json.dumps(result, ensure_ascii=False)

    def print_check(self, id):
        result = self.get_check_status(id)

        return result

    def check_insert_monitor(self, insert_data):
        result = dict()

        if "address" in insert_data:
            result["address"] = insert_data["address"]
        else:
            raise Exception("Please provide address")

        if "name" in insert_data:
            result["name"] = insert_data["name"]
        else:
            raise Exception("Please provide name")

        if "port" in insert_data:
            if isinstance(insert_data.get("port"), int) and insert_data["port"] > 0 and insert_data["port"] < 65536:
                result["port"] = insert_data["port"]
            else:
                raise Exception("Error: Wrong port")
        else:
            raise Exception("Please provide port number")

        result["id"] = self.get_max_monitor_id() + 1
        result["alive"] = False
        result["since"] = int(time())
        result["enabled"] = True

        return result

    def update_monitor(self, monitor, update):
        self.monitor_collection.find_one_and_update({'id': monitor},
                                                    {'$set': update})

        return monitor

    def check_update_monitor(self, update):
        result = dict()

        if "address" in update:
            result["address"] = update["address"]

        if "name" in update:
            result["name"] = update["name"]

        if "port" in update:
            if isinstance(update.get("port"), int) and update["port"] > 0 and update["port"] < 65536:
                result["port"] = update["port"]
            else:
                raise Exception("Error: Wrong port")

        if len(result) == 0:
            raise Exception("Nothing to update")

        return result

    def delete_monitor(self, id):
        result = self.monitor_collection.delete_many({"id": id})

        return result.deleted_count

    async def handle(self, request):
        text = "Hello, this is Monitoring service."
        return web.Response(text=text)

    async def handle_get(self, request):
        id = int(request.match_info.get('id', -1))
        text = str(self.print_check(id))
        return web.json_response(text=text)

    async def handle_post(self, request):
        data = await request.json()
        # id = int(request.match_info.get('id', -1))

        try:
            id = self.insert_monitor(self.check_insert_monitor(data))
        except:
            return web.Response(status=500, text="Something going wrong.")
        print("New monitor Added with ID={}".format(id))

        text = json.dumps({"id": id})

        self.send_update_monitor()

        return web.json_response(text=text)

    async def handle_put(self, request):
        id = int(request.match_info.get('id', -1))

        if (id <= 0):
            return web.Response(status=500, text="Wrong ID provided.")

        data = await request.json()
        try:
            id = self.update_monitor(id, self.check_update_monitor(data))
        except:
            return web.Response(status=500, text="Something going wrong.")

        print("Monitor with ID {} Updated".format(id))

        text = json.dumps({"id": id})

        self.send_update_monitor()

        return web.json_response(text=text)

    async def handle_delete(self, request):
        text = '{"Deleted": true}'
        id = int(request.match_info.get('id', -1))

        if (id > 0):
            if self.delete_monitor(id) == 0:
                text = '{"Deleted": false}'
        else:
            return web.Response(status=500, text="Wrong ID.")

        self.send_update_monitor()

        return web.json_response(text=text)

    def prepare_monitor(self, base_monitor):
        return {"address": base_monitor["address"],
                "name": base_monitor["name"],
                "port": int(base_monitor["port"]),
                "id": int(base_monitor["id"]),
                "alive": base_monitor["alive"],
                "since": int(base_monitor["since"])}

    def send_update_monitor(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=self._rest_config['amqp'],
                                                                       credentials=pika.PlainCredentials('guest',
                                                                                                         'guest'),
                                                                       virtual_host="/"))
        channel = connection.channel()
        channel.queue_declare(queue='monitor')
        channel.basic_publish(exchange='', routing_key='monitor', body='{"reload": true}')
        connection.close()

    def main(self):

        # s = self.get_monitor(1)

        # print(s)

        app = web.Application()
        app.router.add_get('/', self.handle)
        app.router.add_get('/endpoints', self.handle_get)
        app.router.add_get('/endpoints/', self.handle_get)
        app.router.add_post('/endpoints/', self.handle_post)
        app.router.add_get('/endpoints/{id}', self.handle_get)
        app.router.add_put('/endpoints/{id}', self.handle_put)
        app.router.add_delete('/endpoints/{id}', self.handle_delete)

        web.run_app(app, host=self._rest_config['address'], port=self._rest_config['port'])


def RunRest():
    rest = RestService()
    rest.main()


if __name__ == '__main__':
    RunRest()
