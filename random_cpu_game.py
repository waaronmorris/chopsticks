from uuid import uuid4
from time import sleep

from chopsticks import Game, create_player
from cpu import RandomChopstickModel
from db import get_database
from player_actions_exception import *

for j in range(0, 10**4):
    print("new_game")
    game = Game()
    players = [create_player(2, 1, RandomChopstickModel) for i in range(0, 3)]

    [game.register_player(player) for player in players]
    actions = []

    print(game.get_state())
    x = 0
    game_over = True
    while game_over:
        print(game.get_state())
        try:
            action = players[x % 3].formulate_action(game_state=game.get_state())
            actions.append(game.play_turn(action))
            successful_play = False
            x = (x + 1) % 3
        except SplitError as e:
            print(e)
            successful_play = True
        except SendError as e:
            print(e)
            successful_play = True
        except TurnError as e:
            print(e)
            x = (x + 1) % 3
            successful_play = False
        except GameOver as e:
            print("Game Over")
            print(e)
            game_over = True
            break
        except Exception as e:
            raise e

        if game.is_game_over():
            game_over = False

            player_list = {}

            x = 0

            for player in players:
                x = player.player_num % len(players)
                player_state = []
                for _ in players:
                    player_state = player_state + [hand.get_sticks() for hand in players[x].hands.values()]
                    x = (x + 1) % len(players)

                states = {'event_id': uuid4(),
                          'game_id': game.game_id,
                          'game_uuid': game.game_uuid,
                          'player_id': player.player_id,
                          'player_num': player.player_num,
                          'player_move_number': player.move_count,
                          'action': None,
                          'state_str': ','.join([str(stick) for stick in player_state]),
                          'reward': 1 if player.live_hands > 0 else -1
                          }

                dbname = get_database()
                collection_name = dbname["state"]
                collection_name.insert_one(states)

            dbname = get_database()
            collection_name = dbname["actions"]
            collection_name.insert_many([action.__dict__() for action in actions])

            dbname = get_database()
            collection_name = dbname["game"]
            collection_name.insert_one(game.__dict__())
    print("Game Over")
    sleep(5)
