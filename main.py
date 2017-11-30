from aiohttp import web

def get_all_checks():

    return "Nothing"

def get_check_status(id):
    result = ''
    if(id<1):
        result = get_all_checks()
    else:
        f = open("checks/{0}.log".format(id),"r")
        result = f.readline()
        f.close()

    return result

def print_check(id):
    # result = ''
    # if id == -1:
    #     result = "All checks"
    # else:
    result = get_check_status(id)

    return result


async def handle(request):
    name = request.match_info.get('name', "Anonymous")
    text = "Hello, " + name
    return web.Response(text=text)

async def handle_get(request):
    id = int(request.match_info.get('id', -1))
    text=print_check(id)
    return web.Response(text=text)

async def handle_post(request):
    name = request.match_info.get('id', "Anonymous")
    text = "Hello, " + name
    return web.Response(text=text)

async def handle_put(request):
    name = request.match_info.get('id', "Anonymous")
    text = "Hello, " + name
    return web.Response(text=text)

async def handle_delete(request):
    name = request.match_info.get('id', "Anonymous")
    text = "Hello, " + name
    return web.Response(text=text)

app = web.Application()
app.router.add_get('/', handle)
app.router.add_get('/endpoints', handle_get)
app.router.add_get('/endpoints/', handle_get)
app.router.add_post('/endpoints/', handle_post)
app.router.add_get('/endpoints/{id}', handle_get)
app.router.add_put('/endpoints/{id}', handle_put)
app.router.add_delete('/endpoints/{id}', handle_delete)


web.run_app(app, host='127.0.0.1', port=8080)