def get_database():
    from pymongo import MongoClient
    from pymongo.server_api import ServerApi

    # Provide the mongodb atlas url to connect python to mongodb using pymongo
    uri = uri = "mongodb+srv://cluster0.x1mi6.mongodb.net/myFirstDatabase?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority"
    client = MongoClient(uri,
                         tls=True,
                         tlsCertificateKeyFile='X509-cert-7522172699838072547.pem',
                         server_api=ServerApi('1'),
                         uuidRepresentation='standard',
                         serverSelectionTimeoutMS=10 ** 4,
                         maxPoolSize=None
                         )

    # Create the database for our example (we will use the same database throughout the tutorial
    return client['chopsticks']


def get_state_counts():
    filter = {
        '_id': {
            '$regex': '[1-9],[1-9],[1-9],[1-9],[0-9],[0-9]'
        },
        'total_out': {
            '$lt': 10
        },
        'total_state_pairs': {
            '$lt': 3
        },
    }
    sort = list({
                    'total_state_pairs': 1
                }.items())

    try:
        state_count = get_database()['state_transitions'].find_one(filter=filter,
                                                                   sort=sort
                                                                   )['_id'].split(',')
    except:
        state_count = [0, 0, 0, 0, 0, 0]

    hands = []
    player_hands = []
    for i in range(0, len(state_count)):
        if i % 2 == 0:
            player_hands = []
        player_hands.append(int(state_count[i]))

        if i % 2 == 1:
            if player_hands == [0, 0]:
                hands.append([1, 1])
            else:
                hands.append(player_hands)

    return hands


def update_game_state():
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
            '$addFields': {
                'action_str': {
                    '$concat': [
                        '$action', '|(', {
                            '$toString': '$to_player'
                        }, ',', {
                            '$toString': '$to_hand'
                        }, ')|(', {
                            '$toString': '$player_num'
                        }, ',', {
                            '$toString': '$hand_num'
                        }, ')|', {
                            '$toString': '$number_sent'
                        }
                    ]
                }
            }},
        {
            '$merge': {
                'into': 'state_change',
                'on': '_id',
                'whenMatched': 'replace',
                'whenNotMatched': 'insert'
            }
        }
    ], maxTimeMS= 8 * (10**6))

    print("Updating State Transitions")
    get_database()['state_change'].aggregate([
        {
            '$group': {
                '_id': {
                    'state_str': '$state_str',
                    'action': {
                        '$concat': [
                            '$action', '|(', {
                                '$toString': '$to_player'
                            }, ',', {
                                '$toString': '$to_hand'
                            }, ')|(', {
                                '$toString': '$player_num'
                            }, ',', {
                                '$toString': '$hand_num'
                            }, ')|', {
                                '$toString': '$number_sent'
                            }
                        ]
                    },
                    'next_state': '$next_state'
                },
                'observed': {
                    '$sum': 1
                }
            }
        }, {
            '$project': {
                'state_str': '$_id.state_str',
                'action': '$_id.action',
                'next_state': '$_id.next_state',
                'observed': '$observed',
                '_id': 0
            }
        }, {
            '$group': {
                '_id': {
                    'state': '$state_str',
                    'action': '$action'
                },
                'total_state_action_pairs': {
                    '$sum': 1
                }
            }
        }, {
            '$project': {
                '_id': 1,
                'state_str': '$_id.state',
                'action': '$_id.action',
                'total_out': 1,
                'total_state_action_pairs': 1
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
    ], maxTimeMS=1.8 * (10**6))

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
    ], maxTimeMS=1.8 * (10**6))
