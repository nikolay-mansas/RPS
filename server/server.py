import json
from time import sleep
from uuid import uuid4

import config
import uvicorn
from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from redis import asyncio as aioredis

app = FastAPI()
redis_pool = aioredis.ConnectionPool.from_url(f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}/{config.REDIS_DB}", decode_responses=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

choices = ["rock", "paper", "scissors"]


async def get_redis() -> aioredis.Connection:
    return await aioredis.Redis(connection_pool=redis_pool)


def generate_response(
    status: bool = True,
    data: dict | None = None,
    error_message: str | None = None
) -> dict:
    return {"status": status, "data": data, "error_message": error_message}


@app.websocket("/rps")
async def rps_game(
    websocket: WebSocket,
    redis: aioredis.Connection = Depends(get_redis)
):
    await websocket.accept()
    
    user_id: str | None = None
    lobby_id: str | None = None
    lobby: dict | None = None
    
    try:
        while True:
            try:
                data = await websocket.receive_json()
            except json.JSONDecodeError as e:
                await websocket.send_json(generate_response(False, error_message="Invalid JSON data: " + str(e)))
                continue
            
            if not user_id:
                username = data.get("data", {}).get("username", None)
                
                if not username:
                    await websocket.send_json(generate_response(False, error_message="Username is required"))
                    continue
                
                user_id = str(uuid4())
                await redis.set(f"username:{user_id}", username)
                
                await websocket.send_json(generate_response(data={"username": username, "user_id": user_id}))
                continue
            
            if not lobby:
                d = data.get("data", {})
                
                lobby_create = d.get("lobby_create")
                
                if lobby_create:
                    lobby_id = str(uuid4())
                    lobby = {user_id: None}
                    await redis.hset(f"lobby:{lobby_id}", user_id, "")
                    await redis.hset(f"lobby:{lobby_id}", "end", "n")
                    
                    await websocket.send_json(generate_response(data={"lobby_id": lobby_id}))
                    continue
                
                lobby_id = d.get("lobby_id")
                
                if not lobby_id:
                    await websocket.send_json(generate_response(False, error_message="Lobby ID is required"))
                    continue
                
                lobby = await redis.hgetall(f"lobby:{lobby_id}")
                if lobby: # games.get(lobby_id)
                    if len(lobby) > 2:
                        await websocket.send_json(generate_response(False, error_message="Lobby is full"))
                        continue
                    if lobby["end"] == "y":
                        await websocket.send_json(generate_response(False, error_message="Lobby is ended"))
                        continue
                    
                    await redis.hset(f"lobby:{lobby_id}", user_id, "")
                    await websocket.send_json(generate_response(data={"lobby_id": lobby_id}))
                    continue
                
                await websocket.send_json(generate_response(False, error_message="Lobby not found"))
                continue

            if len(await redis.hgetall(f"lobby:{lobby_id}")) != 3:
                await websocket.send_json(generate_response(False, error_message="Lobby is not full"))
                continue
            
            r = await redis.hgetall(f"lobby:{lobby_id}")
            if r[user_id] == "":
                d = data.get("data", {})
            
                if choise := d.get("choise", "").lower():
                    if choise not in choices:
                        await websocket.send_json(generate_response(False, error_message="Invalid choise"))
                        continue
                    
                    await redis.hset(f"lobby:{lobby_id}", user_id, choise)
                    await websocket.send_json(generate_response(True))
                    continue
                
                await websocket.send_json(generate_response(False, error_message="Choise is required"))
                continue
            
            t = await redis.hgetall(f"lobby:{lobby_id}")
            del t[user_id]
            del t["end"]
            
            opponent_move = list(t.values())[0]
            opponent_id = list(t.keys())[0]
            user_move = await redis.hgetall(f"lobby:{lobby_id}")
            user_move = user_move[user_id]
            opponent_username = await redis.get(f"username:{opponent_id}")
            
            if username == opponent_username:
                opponent_username += " (2)"
            
            if not user_move:
                await websocket.send_json(generate_response(False, error_message="Waiting for the your move"))
                continue
                
            if not opponent_move:
                await websocket.send_json(generate_response(False, error_message="Waiting for the opponent's move"))
                continue
            
            if opponent_move == user_move:
                await websocket.send_json(generate_response(True, {"who_win": "draw", "opponent_username": opponent_username}))
                await redis.hset(f"lobby:{lobby_id}", "end", "y")
            elif (opponent_move == "rock" and user_move == "scissors") or \
                 (opponent_move == "scissors" and user_move == "paper") or \
                 (opponent_move == "paper" and user_move == "rock"):
                    await websocket.send_json(generate_response(data={"who_win": user_id, "opponent_username": opponent_username}))
                    await redis.hset(f"lobby:{lobby_id}", "end", "y")
            else:
                await websocket.send_json(generate_response(data={"who_win": opponent_id, "opponent_username": opponent_username}))
                await redis.hset(f"lobby:{lobby_id}", "end", "y")
            
            sleep(3)
            break
    except WebSocketDisconnect:
        print(f"User: {user_id} disconnected")
    else:
        await websocket.close()


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host=config.HOST,
        port=config.PORT,
        ssl_keyfile=config.SSL_KEY_FILE,
        ssl_certfile=config.SSL_CERT_FILE,
        workers=config.WORKERS,
        ws_ping_timeout=600
        )
