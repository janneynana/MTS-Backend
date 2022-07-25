import os
from datetime import date
from sqlalchemy_utils import database_exists, create_database, drop_database
# from .config import Config
from config import Config

class Database():
    DEFAULT = 'postgresql+psycopg2://{dbuser}:{dbpass}@{dbhost}/{dbname}?sslmode=require'.format(
    dbuser="cs407",
    dbpass="IBF-MTS-pwd",
    dbhost="ibf-mst-cs407.postgres.database.azure.com",
    dbname="postgres")
    
    @staticmethod
    def create_tournament_db(tournament):
        current_year = str(date.today().year)
        db_name = "Tournament" + str(tournament.creator_id) + str(tournament.id) + str(current_year)
        db_url = f'postgresql+psycopg2://cs407:IBF-MTS-pwd@ibf-mst-cs407.postgres.database.azure.com/{db_name}?sslmode=require'
        if not database_exists(db_url):
            create_database(db_url)
        tournament.db_name = db_name
        tournament.year = current_year
        tournament.db_url = db_url
        return tournament
    
    @staticmethod
    def delete_tournament_db(tournament):
        db_url = tournament.db_url
        if database_exists(db_url):
            drop_database(db_url)
    
    @staticmethod
    def getTournamentFolder(tournament):
        path = os.path.join(Config.UPLOAD_FOLDER, tournament.name)
        if not os.path.exists(path):
            os.makedirs(path)
        return path
    
    @staticmethod
    def getTeamFolder(tournament):
        path = os.path.join(Database.getTournamentFolder(tournament), "Team")
        if not os.path.exists(path):
            os.makedirs(path)
        return path
    
    @staticmethod
    def getWildFolder(tournament):
        path = os.path.join(Database.getTournamentFolder(tournament), "WildTeam")
        if not os.path.exists(path):
            os.makedirs(path)
        return path
    
    @staticmethod
    def getTeamFolder(tournament):
        path = os.path.join(Database.getTournamentFolder(tournament), "Team")
        if not os.path.exists(path):
            os.makedirs(path)
        return path
    
    @staticmethod
    def getJudgeFolder(tournament):
        path = os.path.join(Database.getTournamentFolder(tournament), "Judge")
        if not os.path.exists(path):
            os.makedirs(path)
        return path
        
    @staticmethod
    def getRoundFolder(tournament, round_num):
        path = os.path.join(Database.getTournamentFolder(tournament), "Round" + str(round_num))
        if not os.path.exists(path):
            os.makedirs(path)
        return path

"""
import psycopg2
z

class Database:

    def get_connection(self):
        connection = psycopg2.connect(
            host = "ibf-mst-cs407.postgres.database.azure.com",
            database = "postgres",
            user = "cs407",
            password="IBF-MTS-pwd",
            port=5432,
            sslmode="require"
        )
        print("Connection established")
        return connection

        """
