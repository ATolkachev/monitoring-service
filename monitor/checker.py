import asyncio
import json
from time import time
from pymongo import MongoClient
from multiprocessing import Process
import monitor.config
import pika


class CheckerService():
    _monitors = []

    def __init__(self):
        ini = monitor.config.ConfigReader()
        self._rest_config = ini.load_config(config="../config.ini")

        self.client = MongoClient(self._rest_config['server'])
        self.db = self.client[self._rest_config['database']]
        self.alert_collection = self.db['alerts']
        self.monitor_collection = self.db['monitor']

        monitor_count = self.load_monitors(self.monitor_collection)
        if (monitor_count == 0):
            print("There is no monitors in Database")
        else:
            print("{} monitors loaded.".format(monitor_count))

        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self._rest_config['amqp'],
                                      credentials=pika.PlainCredentials('guest', 'guest'),
                                      virtual_host="/"))

    def load_monitors(self, collection):
        monitors = []
        data = self.monitor_collection.find()

        for obj in data:
            monitor = {"id": int(obj['id']), "port": int(obj["port"]), "address": obj['address'], "alive": obj['alive']}
            monitors.append(monitor)

        self._monitors = monitors

        return len(self._monitors)

    def start_monitors(self):
        if (len(self._monitors) > 0):
            loop = asyncio.new_event_loop()
            # ioloop = asyncio.get_event_loop()
            # asyncio.wait(wait_tasks)
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.run_monitors())
            loop.close()
        else:
            print("There is no loaded monitors.")

    async def start_listen(self):

        async def listen_monitor():
            channel = self.connection.channel()
            channel.queue_declare(queue='monitor')
            print('Connected to RabbitMQ')

            def callback(ch, method, properties, body):

                decoded_body = body.decode()

                reload = json.loads(decoded_body)

                if (reload['reload']):
                    if (self.load_monitors(self.monitor_collection) > 0):
                        print("Monitors reloaded")
                        ch.basic_ack(delivery_tag=method.delivery_tag)

                return

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(callback,
                                  queue='monitor')

            channel.start_consuming()

        await asyncio.gather(listen_monitor())

    async def start_publish(self):

        async def publish_alerts():
            channel = self.connection.channel()
            channel.queue_declare(queue='alerts', durable=True)
            while True:
                for monitor in self._monitors:
                    channel.basic_publish(exchange='', routing_key='alerts', body=json.dumps(monitor))
                await asyncio.sleep(2)

        await asyncio.gather(publish_alerts())

    def listen_alerts(self):

        async def listen_alerts_queue():
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self._rest_config['amqp'],
                                          credentials=pika.PlainCredentials('guest', 'guest'),
                                          virtual_host="/"))

            channel = connection.channel()
            channel.queue_declare(queue='alerts', durable=True)

            def callback(ch, method, properties, body):

                decoded_body = body.decode()

                monitor = json.loads(decoded_body)

                try:
                    self.monitor_item(monitor)
                except:
                    print("Oops!")
                ch.basic_ack(delivery_tag=method.delivery_tag)

                return

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(callback,
                                  queue='alerts')

            channel.start_consuming()

        async def run_listeners():
            tasks = []
            for i in range(self._rest_config['workers']):
                tasks.append(listen_alerts_queue())

            await asyncio.gather(*tasks)

        alerts_loop = asyncio.get_event_loop()
        # asyncio.set_event_loop(alerts_loop)
        alerts_loop.run_until_complete(run_listeners())

    async def run_monitors(self):
        while True:
            tasks = []
            for item in self._monitors:
                # await asyncio.gather(self.monitor_item(item))
                tasks.append(self.monitor_item(item))
            # await asyncio.wait(tasks)

            await asyncio.gather(*tasks)
            await asyncio.sleep(5)

    def monitor_item(self, item):
        response = ''
        status = True
        self._start_time = time()
        connector = asyncio.open_connection(host=item['address'], port=item['port'])
        try:
            asyncio.wait_for(connector, timeout=0.3)
            response = 'Success'
        except:
            status = False
            response = 'Failed'
        finally:
            print("Monitor {}: Test {}:{} - {}".format(item['id'], item['address'], item['port'], response))
            self.update_monitor(monitor=item, status=status)
            connector.close()

    def update_monitor(self, monitor, status):
        update_time = int(time())
        if monitor['alive'] != status:
            self.monitor_collection.find_one_and_update({'id': monitor['id']},
                                                        {'$set': {"alive": status, 'since': update_time}})
            monitor['alive'] = status


def RunChecker():
    check = CheckerService()
    # check.start_monitors()

    for i in range(check._rest_config['forks']):
        p = Process(target=check.listen_alerts, args=())
        p.start()

    publish_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(publish_loop)
    publish_loop.run_until_complete(check.start_publish())
    listen_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(listen_loop)
    listen_loop.run_until_complete(check.start_listen())

    publish_loop.close()
    listen_loop.close()


if __name__ == '__main__':
    RunChecker()
