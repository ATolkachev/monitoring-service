import json
from time import time
from aiohttp import web
from pymongo import MongoClient

class RestService():

    _max_monitor_id = 0

    def __init__(self):
        self.client = MongoClient()
        self.client = MongoClient('127.0.0.1', 27017)
        self.db = self.client['monitoring']
        self.alert_collection = self.db['alerts']
        self.monitor_collection = self.db['monitor']

        self.get_max_monitor_id()

    def get_max_monitor_id(self):
        max_dict = self.monitor_collection.find().sort([("id", -1)]).limit(1)

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

    def get_check_status(self,id):
        result = ''
        if(id<1):
            result = {"items": self.get_all_checks()}
        else:
            result = self.prepare_monitor(self.get_monitor(id))

        return result

    def print_check(self,id):
        # result = ''
        # if id == -1:
        #     result = "All checks"
        # else:
        result = self.get_check_status(id)

        return result

    def check_insert_monitor(self, insert_data):
        result = dict()

        if "address" in insert_data:
            result["address"]=insert_data["address"]
        else:
            raise Exception("Please provide address")

        if "name" in insert_data:
            result["name"] = insert_data["name"]
        else:
            raise Exception("Please provide name")

        if "port" in insert_data:
            if isinstance(insert_data.get("port"), int) and insert_data["port"]>0 and insert_data["port"]<65536:
                result["port"]=insert_data["port"]
            else:
                raise Exception("Error: Wrong port")
        else:
            raise Exception("Please provide port number")

        result["id"]=self.get_max_monitor_id()+1
        result["alive"] = False
        result["since"] = time()
        result["enabled"] = True

        return result

    async def handle(self,request):
        name = request.match_info.get('name', "Anonymous")
        text = "Hello, " + name
        return web.Response(text=text)

    async def handle_get(self,request):
        id = int(request.match_info.get('id', -1))
        text=str(self.print_check(id))
        return web.Response(text=text)

    async def handle_post(self,request):
        data = await request.json()
        id = -1
        try:
            id = self.insert_monitor(self.check_insert_monitor(data))
        except:
            return web.Response(status=500, text="Something going wrong.")
        print("New monitor Added with ID={}".format(id))
        text = str({"id": id})
        return web.Response(text=text)

    async def handle_put(self,request):
        name = request.match_info.get('id', "Anonymous")
        text = "Hello, " + name
        return web.Response(text=text)

    async def handle_delete(self,request):
        name = request.match_info.get('id', "Anonymous")
        text = "Hello, " + name
        return web.Response(text=text)

    def prepare_monitor(self, base_monitor):
        result = dict()

        result["address"] = base_monitor["address"]
        result["name"] = base_monitor["name"]
        result["port"] = int(base_monitor["port"])
        result["id"] = int(base_monitor["id"])
        result["alive"] = base_monitor["alive"]
        result["since"] = int(base_monitor["since"])

        return result
    def main(self):

        #s = self.get_monitor(1)

        #print(s)

        app = web.Application()
        app.router.add_get('/', self.handle)
        app.router.add_get('/endpoints', self.handle_get)
        app.router.add_get('/endpoints/', self.handle_get)
        app.router.add_post('/endpoints/', self.handle_post)
        app.router.add_get('/endpoints/{id}', self.handle_get)
        app.router.add_put('/endpoints/{id}', self.handle_put)
        app.router.add_delete('/endpoints/{id}', self.handle_delete)


        web.run_app(app, host='127.0.0.1', port=8080)

if __name__ == '__main__':
    rest = RestService()
    rest.main()