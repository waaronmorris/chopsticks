from uuid import uuid4

from db import get_database
from player import ComputerPlayer, Player, Hand
from player_actions_exception import *

dbname = get_database()

global HAND_ID
HAND_ID = 0


def create_player(hand_count, starting_sticks, model=None):
    global HAND_ID
    if model:
        player = ComputerPlayer(model=model)
    else:
        player = Player()
    for i in range(0, hand_count):
        player.change_hand(Hand(hand_id=HAND_ID, hand_num=i, sticks=starting_sticks, player=player))
        HAND_ID = HAND_ID + 1
    return player


class Game:
    games = 0

    def __init__(self):
        self.game_id = self.games
        self.game_uuid = uuid4()
        self.dead_players = []
        self.active_players = []
        self.increment_game_id()
        self.move_counter = 0

    @classmethod
    def increment_game_id(cls):
        cls.games = cls.games + 1
        return cls.games

    @property
    def players(self):
        return self.active_players + self.dead_players

    def register_player(self, player):
        self.active_players.append(player)

    def is_game_over(self):
        if len(self.active_players) == 1:
            return True
        return False

    def play_turn(self, action, **kwargs):
        states = {'event_id': action.event_id,
                  'game_id': self.game_id,
                  'game_uuid': self.game_uuid,
                  'player_id': action.from_hand.player.player_id,
                  'hand_num': action.from_hand.hand_num,
                  'player_num': action.from_hand.player.player_num,
                  'player_move_number': action.from_hand.player.move_count,
                  'action': action.event_type,
                  'to_player': action.to_hand.player.player_num,
                  'to_hand': action.to_hand.hand_num,
                  'number_sent': action.number_sent,
                  'state_str': ','.join([str(stick) for stick, _ in self.get_state()]),
                  'reward': 0
                  }

        if not self.is_game_over():
            if action.from_hand.player.player_id != self.active_players[0].player_id:
                raise TurnError(
                    f"It is {self.active_players[0].player_id} turn. Please Wait Your Turn {action.from_hand.player.player_id}.")

            try:
                states['state'] = tuple((sticks for sticks, _ in self.get_state()))
                hands = action.run(**kwargs)
                for hand in hands:
                    hand.player.change_hand(hand)
                # states['new_state'] = tuple((sticks for sticks, _ in self.get_state()))
            except SplitError as e:
                raise e

            # states['post_state_str'] = ','.join([str(stick) for stick, _ in self.get_state()])
            # states['post_state'] = self.get_state()

            if action.to_hand.player.live_hands == 0:
                self.dead_players.append(self.active_players.pop(self.active_players.index(action.to_hand.player)))
                print(f"ELIMINATED|{action.to_hand.player.player_id}")

            self.active_players.append(self.active_players.pop(self.active_players.index(self.active_players[0])))

            if self.is_game_over():
                # states['reward'] = +1
                print(f"WINNER|{self.active_players[0]}")

            collection_name = dbname["state"]
            collection_name.insert_one(states)
            action.from_hand.player.make_move()
            self.move_counter = self.move_counter + 1
            return action
        elif self.move_counter >= 10 ** 4:
            raise GameOver(f"Infinite Game")
        raise GameOver(f"WINNER|{self.active_players[0]}")

    def get_turn_player(self):
        if not self.is_game_over():
            return self.active_players[0]
        raise GameOver(f"WINNER|{self.active_players[0]}")

    def get_state(self):
        return [(hand.get_sticks(), hand) for player in self.players for hand in player.hands.values()]

    def __dict__(self):
        return {'game_over': self.is_game_over(),
                'game_uuid': self.game_uuid,
                'game_id': self.game_id,
                'players': [player.__dict__() for player in self.players]
                }
