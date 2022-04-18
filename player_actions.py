from datetime import datetime
from enum import Enum
from uuid import uuid4

from player import Hand
from player_actions_exception import *

PLAYER_ACTION_COUNT = 0


def split_sticks(_from: "Hand", _to: "Hand", number_sent: int):
    if _from.player != _to.player:
        raise SplitError("cannot split with different active_players")
    if _from == _to:
        raise SplitError("cannot split with same hand")
    if _from.hand_dead:
        if ((_from.get_sticks() - number_sent) >= 5) or (_to.get_sticks() + number_sent) >= 5:
            raise SplitError("cannot split hand over 5")
        _from.set_sticks(_from.get_sticks() - number_sent)
        _to.set_sticks(_to.get_sticks() + number_sent)
    return [Hand(_from.hand_id, _from.get_sticks() - number_sent, _from.player),
            Hand(_to.hand_id, _to.get_sticks() + number_sent, _to.player)]


def send_sticks(_from: "Hand", _to: "Hand", **kwargs):
    if _from.get_sticks() <= 0:
        raise SendError("cannot send zero sticks")
    if _to.get_sticks() <= 0:
        raise SendError("cannot send to dead hand")
    # _to.set_sticks(_to.get_sticks() + _from.get_sticks())
    return [Hand(_to.hand_id, (_to.get_sticks() + _from.get_sticks()) % 5, _to.player)]


class EVENT_TYPE(Enum):
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
        self.event_number = PLAYER_ACTION_COUNT + 1

    def run(self, **kwargs):
        return self.event(_from=self.from_hand, _to=self.to_hand, number_sent=self.number_sent)

    def __dict__(self):
        return {
            'event_id': self.event_id,
            'event_time': self.event_time,
            'event_type': self.event_type,
            'player_num': self.from_hand.player.player_num,
            'player_id': self.from_hand.player.player_id,
            'from_hand': self.from_hand.__dict__(),
            'to_hand': self.to_hand.__dict__(),
            'number_sent': self.number_sent,
        }

    def __repr__(self):
        return f"{self.event_type}|" \
               f"{self.from_hand.player.player_num},{self.from_hand.hand_id}|" \
               f"{self.to_hand.player.player_num},{self.to_hand.hand_id}"
