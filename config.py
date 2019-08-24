from flask import Flask,render_template,request,url_for,redirect,session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import UserMixin,LoginManager,login_user,logout_user,current_user
from datetime import datetime
from flask_wtf.csrf import CSRFProtect
from rauth import OAuth1Service
from dotenv import load_dotenv
from os.path import join, dirname
import os

load_dotenv('.env')

app=Flask(__name__)
app.secret_key=os.environ['SECRET_KEY']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['SQLALCHEMY_DATABASE_URI']=os.environ['SQLALCHEMY_DATABASE_URI']
db=SQLAlchemy(app)
login_manager=LoginManager(app)
login_manager.login_view='index'
migrate=Migrate(app,db)
csrf=CSRFProtect(app)

service=OAuth1Service(
    name='twitter',
    consumer_key=os.environ['CONSUMER_KEY'],
    consumer_secret=os.environ['CONSUMER_SECRET'],
    request_token_url=os.environ['REQUEST_TOKEN_URI'],
    authorize_url=os.environ['AUTHORIZE_URI'],
    access_token_url=os.environ['ACCESS_TOKEN_URI'],
    base_url=os.environ['BASE_URI']
)