# -*- coding: utf-8 -*-
from flask import Flask
from pymongo import MongoClient

app = Flask(__name__)
app.config.from_object('config')
app.config.from_pyfile('config.py')

if app.config['MONGO_USER'] != "":
    mongoURI = 'mongodb://{}:{}@{}'.format(app.config['MONGO_USER'], app.config['MONGO_PWD'], app.config['MONGO_IP'])
    mongoclient = MongoClient(mongoURI, app.config['MONGO_PORT'])
else:
    mongoclient = MongoClient()
db = mongoclient.douku

from app import views