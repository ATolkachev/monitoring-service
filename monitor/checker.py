import asyncio
from time import time
from pymongo import MongoClient

class CheckerService():

    _monitors = []

    def __init__(self):
        self.client = MongoClient('127.0.0.1', 27017)
        self.db = self.client['monitoring']
        self.alert_collection = self.db['alerts']
        self.monitor_collection = self.db['monitor']

        monitor_count=self.load_monitors(self.monitor_collection)
        if(monitor_count==0):
            print("There is no monitors in Database")
        else:
            print("{} monitors loaded.".format(monitor_count))

    def load_monitors(self,collection):
        data = self.monitor_collection.find()

        for obj in data:
            monitor = {"id": int(obj['id']), "port": int(obj["port"]), "address": obj['address'], "alive": obj['alive']}
            self._monitors.append(monitor)

        return len(self._monitors)

    def start_monitors(self):
        if(len(self._monitors)>0):
            loop = asyncio.new_event_loop()
            #ioloop = asyncio.get_event_loop()
            #asyncio.wait(wait_tasks)
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.run_monitors())
            loop.close()
        else:
            print("There is no loaded monitors.")

    async def run_monitors(self):
        tasks = []
        for item in self._monitors:
            #await asyncio.gather(self.monitor_item(item))
            tasks.append(self.monitor_item(item))
        #await asyncio.wait(tasks)

        await asyncio.gather(*tasks)

    async def monitor_item(self, item):
        response = ''
        status = True
        while True:
            self._start_time = time()
            connector = asyncio.open_connection(host=item['address'], port=item['port'])
            try:
                await asyncio.wait_for(connector,timeout=0.3)
                response = 'Success'
            except:
                status = False
                response = 'Failed'
            finally:
                print("Monitor {}: Test {}:{} - {}".format(item['id'],item['address'],item['port'],response))
                self.update_monitor(monitor=item, status=status)
                connector.close()
            await asyncio.sleep(5)

    def update_monitor(self, monitor, status):
        update_time = int(time())
        if monitor['alive'] != status:
            self.monitor_collection.find_one_and_update({'id': monitor['id']}, {'$set': {"alive": status, 'since': update_time}})
            monitor['alive'] = status

if __name__ == '__main__':
    check = CheckerService()
    check.start_monitors()

def RunChecker():
    check = CheckerService()
    check.start_monitors()