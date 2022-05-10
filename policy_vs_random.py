from random import randint
from time import sleep
from uuid import uuid4

from chopsticks.chopsticks import Game, create_player
from chopsticks.cpu import RandomChopstickModel, TwoPlayerPolicy
from chopsticks.db import get_database, get_state_counts, update_game_state
from chopsticks.player_actions_exception import *

player_count = 2

for i_game in range(0, 10 ** 4):
    print("New Game")
    game = Game()

    players = [
               create_player(0, 2, [1, 1], TwoPlayerPolicy, player_type='MDP1'),
               create_player(1, 2, [1, 1], TwoPlayerPolicy, player_type="MDP2")]

    [game.register_player(player) for player in players]
    actions = []

    x = 0
    game_over = True
    while game_over:
        print(game.get_state())
        try:
            if isinstance(players[x % player_count].model, TwoPlayerPolicy):
                action = players[x % player_count].formulate_action(game=game)
            else:
                action = players[x % player_count].formulate_action(game=game.get_state())
            actions.append(game.play_turn(action))
            successful_play = False
            x = (x + 1) % player_count
        except SplitError as e:
            print(e)
            successful_play = True
        except SendError as e:
            print(e)
            successful_play = True
        except TurnError as e:
            print(e)
            x = (x + 1) % player_count
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

            j = 0

            print(players, [player.player_num for player in players])

            for player in players:
                j = player.player_num
                player_state = []
                for _ in players:
                    player_state = player_state + [hand.get_sticks() for hand in players[j].hands.values()]
                    j = (j + 1) % len(players)

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

                try:
                    dbname = get_database()
                    collection_name = dbname["state"]
                    collection_name.insert_one(states)
                except:
                    dbname = get_database()
                    collection_name = dbname["state"]
                    collection_name.insert_one(states)

            # dbname = get_database()
            # collection_name = dbname["actions"]
            # collection_name.insert_many([action.__dict__() for action in actions])

            try:
                dbname = get_database()
                collection_name = dbname["game"]
                collection_name.insert_one(game.__dict__())
            except:
                dbname = get_database()
                collection_name = dbname["game"]
                collection_name.insert_one(game.__dict__())

    if (i_game > 0) and (i_game % 100 == 0):
        print("Game Over")
        update_game_state()
