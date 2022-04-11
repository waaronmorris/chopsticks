def get_database():
    from pymongo import MongoClient
    from pymongo.server_api import ServerApi

    # Provide the mongodb atlas url to connect python to mongodb using pymongo
    uri = "mongodb+srv://cluster0.x1mi6.mongodb.net/myFirstDatabase?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority"
    client = MongoClient(uri,
                         tls=True,
                         tlsCertificateKeyFile='X509-cert-7522172699838072547.pem',
                         server_api=ServerApi('1'),
                         uuidRepresentation='standard')

    # Create the database for our example (we will use the same database throughout the tutorial
    return client['chopsticks']