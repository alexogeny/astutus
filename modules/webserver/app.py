import asyncio
from signal import signal, SIGINT
from sanic import Sanic
from sanic import response

app = Sanic(__name__)


@app.route("/")
async def elixum_web_app(request):
    return response.json({"hello": "world"})

