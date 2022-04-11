from datetime import datetime
from enum import Enum
from uuid import uuid4

from exceptions import *

from db import get_database
dbname = get_database()

class Hand:

    def __init__(self, hand_id, sticks, player):
        self.uuid = uuid4()
        self.hand_id = hand_id
        self.__sticks = 0
        self.__set_player(player)
        self.set_sticks(sticks)

    def __set_player(self, player):
        self.player = player
        return self

    def get_sticks(self):
        return self.__sticks

    def set_sticks(self, sticks):
        self.__sticks = sticks

    @property
    def hand_dead(self):
        if self.get_sticks() == 0:
            return 1
        return 0

    def __repr__(self):
        return f"{self.hand_id}"

    def __dict__(self):
        return {
            'uuid': self.uuid,
            'hand_id': self.hand_id,
            'sticks': self.get_sticks(),
            'player': {
                'player_num': self.player.player_num,
                'player_id': self.player.player_id
            },
        }


class Player:
    player_count = 0

    def __init__(self):
        self.player_num = self.player_count
        self.add_player_count()
        self.hands = {}
        self.player_id = uuid4()

    @classmethod
    def add_player_count(cls):
        cls.player_count = cls.player_count + 1

    def change_hand(self, hand):
        self.hands[hand.hand_id] = hand

    @property
    def dead_hands(self):
        return sum([hand.hand_dead == 1 for hand in self.hands.values()])

    @property
    def live_hands(self):
        return sum([hand.hand_dead == 0 for hand in self.hands.values()])

    def __repr__(self):
        return f"{self.player_id}"

    def __dict__(self):
        return {'player_id': self.player_id,
                'player_num': self.player_num,
                'hand': {hand.__dict__() for _, hand in self.hands}
                }


def split_sticks(_from: Hand, _to: Hand, number_sent: int):
    if _from.player != _to.player:
        raise SplitError("cannot split with different active_players")
    if ((_from.get_sticks() - number_sent) >= 5) or (_to.get_sticks() + number_sent) >= 5:
        raise SplitError("cannot split over hand over 5")
    # _from.set_sticks(_from.get_sticks() - number_sent)
    # _to.set_sticks(_to.get_sticks() + number_sent)
    return [Hand(_from.hand_id, _from.get_sticks() - number_sent, _from.player),
            Hand(_to.hand_id, _to.get_sticks() + number_sent, _to.player)]


def send_sticks(_from: Hand, _to: Hand, **kwargs):
    if _from.get_sticks() <= 0:
        raise SendError("cannot send zero sticks")
    if _to.get_sticks() <= 0:
        raise SendError("cannot send to dead hand")
    # _to.set_sticks(_to.get_sticks() + _from.get_sticks())
    return [Hand(_to.hand_id, (_to.get_sticks() + _from.get_sticks()) % 5, _to.player)]


def create_player(hand_count, starting_sticks):
    player = Player()
    for i in range(0, hand_count):
        player.change_hand(Hand(i, starting_sticks, player))
    return player


class EVENTTYPE(Enum):
    SPLIT = ('split', split_sticks)
    SEND = ('send', send_sticks)


class PlayerAction:
    def __init__(self, event_type, **kwargs):
        self.event_time = datetime.utcnow()
        self.event_id = uuid4()
        self.event_type = event_type.value[0]
        self.event = event_type.value[1]
        self.to_hand = kwargs.get('_to')
        self.from_hand = kwargs.get('_from')
        self.number_sent = kwargs.get('number_sent')

    def run(self, **kwargs):g
        return self.event(_from=self.from_hand, _to=self.to_hand, number_sent=self.number_sent)

    def __dict__(self):
        return {
            'event_id': self.event_id,
            'event_time': self.event_time,
            'event_type': self.event_type,
            'from_hand': self.from_hand.__dict__(),
            'to_hand': self.to_hand.__dict__(),
            'number_sent': self.number_sent,
        }

    def __repr__(self):
        return f"{self.event_type}|" \
               f"{self.from_hand.player.player_num},{self.from_hand.hand_id}|" \
               f"{self.to_hand.player.player_num},{self.to_hand.hand_id}"


class Game:
    def __init__(self):
        self.players = []

    @property
    def active_players(self):
        return [player for player in self.players if player.live_hands > 0]

    def register_player(self, player):
        self.players.append(player)

    def is_game_over(self):
        if len(self.active_players) == 1:
            return True
        return False

    def play_turn(self, action, **kwargs):
        states = {'event_id': action.event_id}
        if not self.is_game_over():
            if action.from_hand.player.player_id != self.active_players[0].player_id:
                raise TurnError(
                    f"It is {self.active_players[0].player_id} turn. Please Wait Your Turn {action.from_hand.player1.player_id}.")

            try:
                states['prior_state'] = self.get_state()
                hands = action.run(**kwargs)
                for hand in hands:
                    hand.player.change_hand(hand)
                states['new_state'] = self.get_state()
            except SplitError as e:
                raise e

            if action.to_hand.player.live_hands == 0:
                # self.active_players.pop(action.to_hand.player1)
                print(f"ELIMINATED|{action.to_hand.player.player_id}")

            self.players.append(self.players.pop(self.players.index(self.active_players[0])))

            if self.is_game_over():
                print(f"WINNER|{self.active_players[0]}")

            collection_name = dbname["state"]
            collection_name.insert_one(states)
            return action
        raise GameOver(f"WINNER|{self.active_players[0]}")

    def get_turn_player(self):
        if not self.is_game_over():
            return self.active_players[0]
        raise GameOver(f"WINNER|{self.active_players[0]}")

    def get_state(self):
        return [[hand.get_sticks() for hand in player.hands.values()] for player in self.players]