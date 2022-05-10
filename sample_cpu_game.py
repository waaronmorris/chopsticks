from chopsticks.chopsticks import Game, create_player
from chopsticks.cpu import BaseChopstickModel
import bson
from chopsticks.db import get_database

game = Game()
player1 = create_player(2, 1, BaseChopstickModel)
player2 = create_player(2, 1, BaseChopstickModel)

game.register_player(player1)
game.register_player(player2)
actions = []

for x in range(1, 20):
    if game.is_game_over():
        break
    print(game.get_state())
    if x % 2:
        actions.append(game.play_turn(player2.formulate_action(game_state=game.get_state())))
    else:
        actions.append(game.play_turn(player1.formulate_action(game_state=game.get_state())))

print(game.get_state())




