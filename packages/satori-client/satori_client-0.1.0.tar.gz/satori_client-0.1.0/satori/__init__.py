import asyncio
import websockets
import json
import uuid

class Satori:
    def __init__(self, username: str, password: str, host: str):
        self.username = username
        self.password = password
        self.host = host
        self.ws = None
        self.pending = {}
        self.subscriptions = {}

    async def connect(self):
        self.ws = await websockets.connect(self.host)
        asyncio.create_task(self.listen())

    async def listen(self):
        async for message in self.ws:
            msg = json.loads(message)
            if msg.get("type") == "notification" and msg.get("key") in self.subscriptions:
                await self.subscriptions[msg["key"]](msg["data"])
            elif msg.get("id") in self.pending:
                fut = self.pending.pop(msg["id"])
                fut.set_result(msg)

    async def send(self, command: str, payload: dict):
        req_id = str(uuid.uuid4())
        msg = {
            "id": req_id,
            "username": self.username,
            "password": self.password,
            "command": command,
            **payload
        }
        future = asyncio.get_event_loop().create_future()
        self.pending[req_id] = future
        await self.ws.send(json.dumps(msg))
        return await future

    async def set(self, payload): return await self.send("SET", payload)
    async def get(self, payload): return await self.send("GET", payload)
    async def put(self, payload): return await self.send("PUT", payload)
    async def delete(self, payload): return await self.send("DELETE", payload)
    async def set_vertex(self, payload): return await self.send("SET_VERTEX", payload)
    async def get_vertex(self, payload): return await self.send("GET_VERTEX", payload)
    async def delete_vertex(self, payload): return await self.send("DELETE_VERTEX", payload)
    async def dfs(self, payload): return await self.send("DFS", payload)
    async def encrypt(self, payload): return await self.send("ENCRYPT", payload)
    async def decrypt(self, payload): return await self.send("DECRYPT", payload)
    async def set_ref(self, payload): return await self.send("SET_REF", payload)
    async def get_refs(self, payload): return await self.send("GET_REFS", payload)
    async def delete_ref(self, payload): return await self.send("DELETE_REF", payload)
    async def delete_refs(self, payload): return await self.send("DELETE_REFS", payload)
    async def query(self, payload): return await self.send("QUERY", payload)
    async def push(self, payload): return await self.send("PUSH", payload)
    async def pop(self, payload): return await self.send("POP", payload)
    async def splice(self, payload): return await self.send("SPLICE", payload)
    async def remove(self, payload): return await self.send("REMOVE", payload)

    async def notify(self, key, callback):
        self.subscriptions[key] = callback
        await self.send("NOTIFY", {"key": key})

    async def unnotify(self, key):
        self.subscriptions.pop(key, None)
        await self.send("UNNOTIFY", {"key": key})