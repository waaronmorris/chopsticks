from random import randint
import pandas as pd

from chopsticks.player_actions import PlayerAction, EVENT_TYPE
from chopsticks.player_actions_exception import TurnError


def make_state_string(_state):
    return f"[({_state[0][0]},{_state[0][1]}),({_state[1][0]},{_state[1][1]})]"


class BaseChopstickModel:
    def __init__(self, player):
        self.player = player

    def execute(self, game_state):
        state = [sticks for sticks, _ in game_state]
        hands = [hands for _, hands in game_state]
        if state[0] >= 3 and state[1] <= 1:
            action = PlayerAction(EVENT_TYPE.SPLIT,
                                  _from=hands[0],
                                  _to=hands[1],
                                  number_sent=1)
            return action

        if state[1] >= 3 and state[0] <= 1:
            action = PlayerAction(EVENT_TYPE.SPLIT,
                                  _from=hands[1],
                                  _to=hands[0],
                                  number_sent=1)
            return action

        for x in range(2, len(state)):
            sticks = state[x]
            hand = hands[x]
            if sticks > 0:
                if state[0] > state[1]:
                    action = PlayerAction(EVENT_TYPE.SEND,
                                          _from=hands[0],
                                          _to=hand)
                    return action
                else:
                    action = PlayerAction(EVENT_TYPE.SEND,
                                          _from=hands[1],
                                          _to=hand)
                    return action


class RandomChopstickModel(BaseChopstickModel):

    def __init__(self, player):
        super(RandomChopstickModel, self).__init__(player)

    def execute(self, game):
        from_hand = None

        if self.player.live_hands <= 0:
            raise TurnError(f"Player:{self.player.player_num}|Dead")

        while from_hand is None:
            i_hand = randint(0, len(self.player.hands) - 1)
            if self.player.hands[i_hand].get_sticks() > 0:
                from_hand = self.player.hands[i_hand]

        if randint(0, 1) == 1:
            # Attack

            for i in range(len(self.player.hands), len(game)):
                stick, to_hand = game[i]
                if stick > 0:
                    _action = PlayerAction(EVENT_TYPE.SEND,
                                           _from=from_hand,
                                           _to=to_hand,
                                           number_sent=from_hand.get_sticks())
                    return _action
        else:
            # Split
            for i in range(0, len(self.player.hands)):
                stick, to_hand = game[i]
                if from_hand == to_hand:
                    pass
                else:
                    if stick >= 0 & stick < 5:
                        _action = PlayerAction(EVENT_TYPE.SPLIT,
                                               _from=from_hand,
                                               _to=to_hand,
                                               number_sent=randint(1, from_hand.get_sticks()))
                    return _action


class TwoPlayerPolicy(BaseChopstickModel):
    def __init__(self, player):
        self.policy = pd.read_json("policy/2p.json")
        super(TwoPlayerPolicy, self).__init__(player)

    def execute(self, game):
        print(f"execute|{game.get_state()}")
        mdp_game_state = []
        a = ()
        for count in range(len(game.get_state())):
            j = game.get_state()[count][0]
            a = a + tuple([j])
            if count % 2 == 1:
                mdp_game_state.append(a)
                a = ()

        action = self.policy[self.policy['state'] ==
                             make_state_string(mdp_game_state)]['policy_str'].iloc[0].split(",")

        if action[0] == 'send':
            _from = self.player.hands[int(action[1])]
            _to = game.players[1].hands[int(action[2])]
            return PlayerAction(EVENT_TYPE.SEND, _from=_from, _to=_to)
        elif action[0] == 'split':
            _from = self.player.hands[int(action[1])]
            _to = self.player.hands[int(action[2])]
            _number_sent = int(action[3])
            return PlayerAction(EVENT_TYPE.SPLIT, _from=_from, _to=_to, number_sent=_number_sent)
