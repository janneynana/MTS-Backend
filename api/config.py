from datetime import timedelta

class Config(object):
    DEBUG = True
    TESTING = True
    PORT = "8000"
    
    # Set the secret key
    # This is implemented on top of cookies for you and signs the cookies cryptographically. 
    # What this means is that the user could look at the contents of your cookie but not modify it, 
    # unless they know the secret key used for signing.
    SECRET_KEY = "6f5b42c7e82861b4a75028638445669b533c6553fa7aad7c497509342f9633f4"
    
    JWT_SECRET_KEY = "zHF8vwEruF2GDZtzVBY9ose0zsSe9dSA"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']

    
    # for the Azure database 
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://{dbuser}:{dbpass}@{dbhost}/{dbname}?sslmode=require'.format(
    dbuser="cs407",
    dbpass="IBF-MTS-pwd",
    dbhost="ibf-mst-cs407.postgres.database.azure.com",
    dbname="postgres")
    
    SQLALCHEMY_BINDS = {
        'default':      SQLALCHEMY_DATABASE_URI,
    }
    UPLOAD_FOLDER = '../static'
    # local database
    #SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://myuser:mypassword@192.168.99.100/sport_stats'
    #SQLALCHEMY_TRACK_MODIFICATIONS = False
