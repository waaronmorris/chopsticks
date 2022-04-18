from chopsticks import Game, create_player
from db import get_database
from player_actions import PlayerAction, EVENT_TYPE

game = Game()
player1 = create_player(2, 1)
player2 = create_player(2, 1)

game.register_player(player1)
game.register_player(player2)
actions = []

print(game.get_state())

actions.append(game.play_turn(PlayerAction(EVENT_TYPE.SEND,
                                           _from=list(player1.hands.values())[0],
                                           _to=list(player2.hands.values())[0])))

print(game.get_state())

actions.append(game.play_turn(PlayerAction(EVENT_TYPE.SEND,
                                           _from=list(player2.hands.values())[0],
                                           _to=list(player1.hands.values())[0])))

print(game.get_state())

actions.append(game.play_turn(PlayerAction(EVENT_TYPE.SPLIT,
                                           _from=list(player1.hands.values())[0],
                                           _to=list(player1.hands.values())[1],
                                           number_sent=1)))

print(game.get_state())

actions.append(game.play_turn(PlayerAction(EVENT_TYPE.SEND,
                                           _from=list(player2.hands.values())[0],
                                           _to=list(player1.hands.values())[0])))

print(game.get_state())

actions.append(game.play_turn(PlayerAction(EVENT_TYPE.SEND,
                                           _from=list(player1.hands.values())[0],
                                           _to=list(player2.hands.values())[1])))

print(game.get_state())

actions.append(game.play_turn(PlayerAction(EVENT_TYPE.SEND,
                                           _from=list(player2.hands.values())[0],
                                           _to=list(player1.hands.values())[0])))

print(game.get_state())

actions.append(game.play_turn(PlayerAction(EVENT_TYPE.SEND,
                                           _from=list(player1.hands.values())[0],
                                           _to=list(player2.hands.values())[0])))

print(game.get_state())

actions.append(game.play_turn(PlayerAction(EVENT_TYPE.SEND,
                                           _from=list(player2.hands.values())[0],
                                           _to=list(player1.hands.values())[0])))

print(game.get_state())

actions.append(game.play_turn(PlayerAction(EVENT_TYPE.SEND,
                                           _from=list(player1.hands.values())[1],
                                           _to=list(player2.hands.values())[0])))

print(game.get_state())

dbname = get_database()
collection_name = dbname["actions"]
collection_name.insert_many([action.__dict__() for action in actions])
