import json
import sys
from time import sleep

import config
from websocket import create_connection

ws = create_connection(f"ws{'s' if config.SERVER_SSL else ''}://{config.SERVER_IP}:{config.SERVER_PORT}{config.SERVER_PREFIX}", enable_multithread=True)
username = config.USERNAME
first_connect = True
lobby_id = None
go = False


if len(username) < 4:
    print("The minimum length for a name is 4 characters")
    sys.exit()


while True:
    sleep(1)
    
    if first_connect:
        first_connect = False
        ws.send(json.dumps({"data": {"username": username}}))
        data = json.loads(ws.recv())
        user_id = data["data"]["user_id"]
        
    if not lobby_id:
        choise = input("Create a lobby? (y/n): ")
        
        if "y" in choise.lower():
            ws.send(json.dumps({"data": {"lobby_create": True}}))
            data = json.loads(ws.recv())
            lobby_id = data["data"]["lobby_id"]
            print(f"ID lobby: {lobby_id}")
        else:
            lobby = input("Enter the lobby ID: ")
            lobby = lobby.rstrip().rstrip()
            ws.send(json.dumps({"data": {"lobby_id": lobby}}))
            data = json.loads(ws.recv())
            if data["status"] is True:
                lobby_id = data["data"]["lobby_id"]
            else:
                if data["error_message"] == "Lobby is full":
                    print("This lobby is already occupied")
                    continue
                
                if data["error_message"] == "Lobby is ended":
                    print("This lobby has already ended")
                    continue
                
                print("The lobby does not exist")
                continue
                
    if not go:
        choise = input("Your move(rock, paper, scissors): ").rstrip().rstrip().lower()
        check = True
        while check:
            if "rock" in choise:
                ws.send(json.dumps({"data": {"choise": "rock"}}))
                data = json.loads(ws.recv())
                if data["status"]:
                    check = False
                    go = True
            elif "paper" in choise:
                ws.send(json.dumps({"data": {"choise": "paper"}}))
                data = json.loads(ws.recv())
                if data["status"]:
                    check = False
                    go = True
            elif "scissors" in choise:
                ws.send(json.dumps({"data": {"choise": "scissors"}}))
                data = json.loads(ws.recv())
                if data["status"]:
                    check = False
                    go = True
            else:
                print("Wrong move")
                choise = input("Your move(rock, paper, scissors): ").rstrip().rstrip().lower()
                continue
                
            if data.get("error_message", "") == "Lobby is not full":
                print("Waiting for the second player")
                sleep(1)
                
            if data.get("error_message", "") == "Waiting for the opponent's move":
                print("Waiting for the opponent's move")
                sleep(1)

    ws.send("{}")
    data = json.loads(ws.recv())
    
    if data["status"]:
        win = data["data"]["who_win"]
        opponent_username = data["data"].get("opponent_username", None)
        
        if win == "draw":
            print(f"Draw! {username} и {opponent_username}.")
        elif win == user_id:
            print(f"Your win {opponent_username}!")
        else:
            print(f"You lose {opponent_username}!")
        
        break

ws.close()
