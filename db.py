def get_database():
    from pymongo import MongoClient
    from pymongo.server_api import ServerApi

    # Provide the mongodb atlas url to connect python to mongodb using pymongo
    uri = uri = "mongodb+srv://cluster0.x1mi6.mongodb.net/myFirstDatabase?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority"
    client = MongoClient(uri,
                         tls=True,
                         tlsCertificateKeyFile='X509-cert-7522172699838072547.pem',
                         server_api=ServerApi('1'),
                         uuidRepresentation='standard')

    # Create the database for our example (we will use the same database throughout the tutorial
    return client['chopsticks']


def get_state_counts():
    filter = {
        '_id': {
            '$regex': '^.*0,0.*'
        },
        'total_out': {
            '$lt': 100
        }
    }
    sort = list({
                    'count': 1
                }.items())

    try:
        state_count = get_database()['state_transitions'].find_one(filter=filter,
                                                                   sort=sort
                                                                   )['_id'].split(',')
    except:
        state_count = [0, 0, 0, 0, 0, 0]

    hands = []
    player_hands = []
    print(state_count)
    for i in range(0, len(state_count)):
        print(i)
        if i % 2 == 0:
            player_hands = []
        player_hands.append(int(state_count[i]))

        if i % 2 == 1:
            if player_hands == [0, 0]:
                hands.append([1, 1])
            else:
                hands.append(player_hands)
        print(player_hands)

    return hands
