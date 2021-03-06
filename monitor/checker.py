import asyncio
import json
from time import time
from typing import Dict

from pymongo import MongoClient
from multiprocessing import Process
from os import getenv
import pika
import argparse

from monitor.config import Env


class CheckerService():
    _monitors = []
    _rest_config = {}
    _start_time: int

    _forks = []

    # all arg defaults are now sourced from environment and must be set
    _env_args = {
        "CHECKER_ADDRESS": Env('address', str, '127.0.0.1'),
        "CHECKER_PORT": Env('port', int, '8081'),
        "CHECKER_DB_CONN_STRING": Env('server', str, None),
        "CHECKER_DATABASE_NAME": Env('database', str, None),
        "CHECKER_AMQP_NAME": Env('amqp', str, None),
        "CHECKER_FORKS_NUM": Env('forks', int, 4),
        "CHECKER_WORKERS_NUM": Env('workers', int, 4),
    }

    def __init__(self):
        self._rest_config = self.load_args()

    def load_args(self):

        def _read_env_args() -> Dict:
            defaults = dict()
            for env_var, arg in self._env_args.items():
                try:
                    env = arg.env_type(getenv(env_var, arg.env_default))
                    if env is not None:
                        defaults[arg.env_name] = env
                except:
                    raise Exception(
                        "checker.py: Environment variable '{}'(of type '{}') is not set to a type-valid default value.".format(
                            env_var, arg[1]))
            return defaults

        def create_parser():
            parser = argparse.ArgumentParser(
                prog='cheker.py',
                description='''Monitoring service Checker''',
                epilog='''(c) Alexander Tolkachev 2017.''',
                add_help=True
            )

            # cmd arguments are optional and override or complement environment defaults
            parser.add_argument('--address', type=str, help='Listening Address', required=False)
            parser.add_argument('--port', type=int, help='Listening Port', required=False)
            parser.add_argument('--db', type=str, help='Database connection string', required=False)
            parser.add_argument('--database', type=str, help='Monitoring database name', required=False)
            parser.add_argument('--amqp', type=str, help='AMQP server', required=False)
            parser.add_argument('--forks', type=int, help='Amount of Forks', required=False)
            parser.add_argument('--workers', type=int, help='Amount of Workers', required=False)

            return parser

        # getting defaults from the env - all values guaranteed
        config = _read_env_args()

        parser = create_parser()
        args, unknown = parser.parse_known_args()

        arg_dict = {'server': args.db,
                    'database': args.database,
                    'forks': args.forks,
                    'workers': args.workers,
                    'amqp': args.amqp}

        config.update({k: v for k, v in arg_dict.items() if v is not None})

        return config

    def load_monitors(self):
        monitors = []
        data = self.monitor_collection.find()

        for obj in data:
            monitor = {"id": int(obj['id']), "port": int(obj["port"]), "address": obj['address'], "alive": obj['alive']}
            monitors.append(monitor)

        self._monitors = monitors

        return len(self._monitors)

    def init_db(self):
        self.client = MongoClient(self._rest_config['server'], connect=False)
        self.db = self.client[self._rest_config['database']]
        self.alert_collection = self.db['alerts']
        self.monitor_collection = self.db['monitor']

    def start_monitor(self):
        self.init_db()
        monitor_count = self.load_monitors()
        if (monitor_count == 0):
            print("There is no monitors in Database")
        else:
            print("{} monitors loaded.".format(monitor_count))

        self.init_amqp()

    def start_listen_monitor(self):

        def listen_monitor(channel):
            channel.queue_declare(queue='monitor')
            print('Connected to RabbitMQ')

            def callback(ch, method, properties, body):

                decoded_body = body.decode()

                reload = json.loads(decoded_body)

                if (reload['reload']):
                    self.restart_monitors()
                    self.load_monitors()
                    print("Monitors reloaded")
                    ch.basic_ack(delivery_tag=method.delivery_tag)

                return

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(on_message_callback=callback, queue='monitor')

            channel.start_consuming()

        self.init_amqp()

        listen_monitor(self.connection.channel())

    async def start_publish(self):

        async def publish_alerts():
            channel = self.connection.channel()
            channel.queue_declare(queue='alerts', durable=True)
            while True:
                self.load_monitors()
                for monitor in self._monitors:
                    channel.basic_publish(exchange='', routing_key='alerts', body=json.dumps(monitor))
                await asyncio.sleep(2)

        self.start_monitor()
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
            channel.basic_consume(on_message_callback=callback, queue='alerts')

            channel.start_consuming()

        async def run_listeners():
            tasks = []
            for i in range(self._rest_config['workers']):
                tasks.append(listen_alerts_queue())

            await asyncio.gather(*tasks)

        self.start_monitor()
        alerts_loop = asyncio.new_event_loop()
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

    def init_amqp(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self._rest_config['amqp'],
                                      credentials=pika.PlainCredentials('guest', 'guest'),
                                      virtual_host="/")
        )

    def restart_monitors(self):
        if self._forks:
            for i in self._forks:
                i.terminate()
        self._forks = []
        for i in range(self._rest_config['forks']):
            p = Process(target=self.listen_alerts, args=())
            self._forks.append(p)
            p.start()


async def run_amqp_processes(check):
    p = Process(target=check.start_listen_monitor, args=())
    p.start()
    await check.start_publish()


def run_checker():
    check = CheckerService()
    check.restart_monitors()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_amqp_processes(check))

    loop.close()


if __name__ == '__main__':
    run_checker()
