from uuid import uuid4

class Hand:
    def __init__(self, hand_id, hand_num, sticks, player):
        self.uuid = uuid4()
        self.hand_id = hand_id
        self.hand_num = hand_num
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
        self.hands: {int, Hand} = {}
        self.player_id = uuid4()
        self.move_count = 1

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

    def make_move(self):
        self.move_count = self.move_count + 1

    def __repr__(self):
        return f"{self.player_id}"

    def __dict__(self):
        return {'player_id': self.player_id,
                'player_num': self.player_num,
                'hands': [hand.__dict__() for hand in self.hands.values()]
                }


class ComputerPlayer(Player):
    def __init__(self, model):
        self.model = model(self)
        super(ComputerPlayer, self).__init__()

    def formulate_action(self, game_state):
        action: "PlayerAction" = self.model.execute(game_state)
        return action
