import os
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

class AIAMessageRepository:
  aiaDB: None

  def __init__(self, connectionString):
    connectiondmr = MongoClient(connectionString)
    self.aiaDB = connectiondmr["aia-db"]


  def insertAIAMessage(self, aiaMessage):
      _id = self.aiaDB["aIAMessage"].insert_one(aiaMessage)
      return _id.inserted_id
  
  def insertAIAReadMessage(self, aiaMessage):
      _id = self.aiaDB["aIAReadMessage"].insert_one(aiaMessage)
      return _id.inserted_id
  