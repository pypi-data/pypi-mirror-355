import os
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
from aia_utils.model.aia_model import AIASemanticGraph

load_dotenv()

class AIASemanticGraphRepository:
  aiaDB: None

  def __init__(self, connectionString):
    connectiondmr = MongoClient(connectionString)
    self.aiaDB = connectiondmr["aia-db"]

  def save(self, aiaSemanticGraph: AIASemanticGraph):
      _id = self.aiaDB["aIASemanticGraph"].insert_one(aiaSemanticGraph.dict())
      return str(_id.inserted_id)