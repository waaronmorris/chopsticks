from random import randint
from time import sleep
from uuid import uuid4

from chopsticks import Game, create_player
from cpu import RandomChopstickModel
from db import get_database, get_state_counts
from player_actions_exception import *

player_count = 3

for i_game in range(0, 10 ** 4):
    print("New Game")
    game = Game()

    hands = get_state_counts()
    players = [create_player(i, 2, hands[i], RandomChopstickModel) for i in range(0, player_count)]

    [game.register_player(player) for player in players]
    actions = []

    x = 0
    game_over = True
    while game_over:
        print(game.get_state())
        try:
            action = players[x % player_count].formulate_action(game_state=game.get_state())
            actions.append(game.play_turn(action))
            successful_play = False
            x = (x + 1) % player_count
            print(action)
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
                j = player.player_num % len(players)
                player_state = []
                for _ in players:
                    player_state = player_state + [hand.get_sticks() for hand in players[j].hands.values()]
                    j = (x + 1) % len(players)

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

            # dbname = get_database()
            # collection_name = dbname["actions"]
            # collection_name.insert_many([action.__dict__() for action in actions])

            dbname = get_database()
            collection_name = dbname["game"]
            collection_name.insert_one(game.__dict__())
    if (i_game > 0) and (i_game % 100 == 0):
        print("Game Over")
        print("Updating State Change")
        # get_database().collection('state_change').deleteMany({})
        get_database()['state'].aggregate([
        {
            '$addFields': {
                'next_move': {
                    '$add': [
                        '$player_move_number', 1
                    ]
                }
            }
        }, {
            '$lookup': {
                'from': 'state',
                'let': {
                    'game_uuid': '$game_uuid',
                    'player_id': '$player_id',
                    'player_move_number': '$next_move'
                },
                'pipeline': [
                    {
                        '$match': {
                            '$expr': {
                                '$and': [
                                    {
                                        '$eq': [
                                            '$game_uuid', '$$game_uuid'
                                        ]
                                    }, {
                                        '$eq': [
                                            '$player_id', '$$player_id'
                                        ]
                                    }, {
                                        '$eq': [
                                            '$player_move_number', '$$player_move_number'
                                        ]
                                    }
                                ]
                            }
                        }
                    }, {
                        '$project': {
                            '_id': 0
                        }
                    }
                ],
                'as': 'next_move'
            }
        }, {
            '$addFields': {
                'next_state': {
                    '$arrayElemAt': [
                        '$next_move.state_str', 0
                    ]
                },
                'next_reward': {
                    '$arrayElemAt': [
                        '$next_move.reward', 0
                    ]
                }
            }
        }, {
            '$merge': {
                'into': 'state_change',
                'on': '_id',
                'whenMatched': 'replace',
                'whenNotMatched': 'insert'
            }
        }
    ])

        print("Updating State Transitions")
        # get_database().collection('state_transitions').deleteMany({})
        get_database()['state_change'].aggregate([
        {
            '$group': {
                '_id': {
                    'state_str': '$state_str',
                    'next_state': '$next_state'
                },
                'observed': {
                    '$sum': 1
                }
            }
        }, {
            '$project': {
                'state_str': '$_id.state_str',
                'next_state': '$_id.next_state',
                'observed': '$observed',
                '_id': 0
            }
        }, {
            '$group': {
                '_id': '$state_str',
                'total_out': {
                    '$sum': '$observed'
                },
                'total_state_pairs': {
                    '$sum': 1
                }
            }
        }, {
            '$project': {
                '_id': 1,
                'state_str': '$_id',
                'total_out': 1,
                'total_state_pairs': 1
            }
        }, {
            '$merge': {
                'into': {
                    'db': 'chopsticks',
                    'coll': 'state_transitions'
                },
                'on': '_id',
                'whenMatched': 'replace',
                'whenNotMatched': 'insert'
            }
        }
    ])

        print("Updating State Summary")
        # get_database().collection('state_changes_summary').deleteMany({})
        get_database()['state_change'].aggregate([
        {
            '$lookup': {
                'from': 'state_transitions',
                'localField': 'state_str',
                'foreignField': '_id',
                'as': 'state_transitions'
            }
        }, {
            '$addFields': {
                'total_out': {
                    '$arrayElemAt': [
                        '$state_transitions.total_out', 0
                    ]
                },
                'total_state_pairs': {
                    '$arrayElemAt': [
                        '$state_transitions.total_state_pairs', 0
                    ]
                },
                'p': {
                    '$divide': [
                        1, {
                            '$arrayElemAt': [
                                '$state_transitions.total_state_pairs', 0
                            ]
                        }
                    ]
                }
            }
        }, {
            '$project': {
                'state_transitions': 0,
                'next_move': 0
            }
        }, {
            '$merge': {
                'into': 'state_changes_summary',
                'on': '_id',
                'whenMatched': 'replace',
                'whenNotMatched': 'insert'
            }
        }
    ])

    sleep(randint(0, 60))
