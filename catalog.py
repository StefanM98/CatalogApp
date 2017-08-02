from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
app = Flask(__name__)

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Catagory, Item, Base

# New Imports for auth
from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBsession = sessionmaker(bind = engine)
session = DBsession()


@app.route('/')
def catalog():
    # Checks if user is logged in and then returns the correct home page
    catagories = session.query(Catagory).all()
    #catagories = ["Holidays", "Seasons", "My Little Poney", "Disney"]
    recentItems = session.query(Item).order_by(Item.time_created).limit(6).all()
    return render_template('home.html', catagories=catagories, recentItems=recentItems)



# Login Routes

@app.route('/login')
def login():
    # Shows login page
    return "Login Page"


@app.route('/logout')
def logout():
    # Logsout the user
    return "Logout Page"




# Catagory Routes

@app.route('/<string:catagory>')
def catagory(catagory):
    #  Returns page for selected catagory
    return "Page for %s" % catagory


@app.route('/<string:catagory>/edit')
def editCatagory(catagory):
    # If user is authorized shows a page to edit a catagory
    return "Page for changing the %s catagory" % catagory


@app.route('/<string:catagory>/delete')
def deleteCatagory(catagory):
    # If user is authorized shows a page to delete a catagory
    return "Page for deleting the %s catagory" % catagory


@app.route('/new')
def newCatagory():
    # If user is authorized shows a page to add a catagory
    return "Page for adding a new catagory"




# Item Routes

@app.route('/<string:catagory>/<int:item>')
def item(catagory, item):
    # Returns page for selected item
    return ("Page for %s, in the %s catagory" % (item, catagory))


@app.route('/<string:catagory>/<int:item>/edit')
def editItem(catagory, item):
    # If user is authorized shows a page to edit an item
    return ("Edit page for %s, in the %s catagory" % (item, catagory))


@app.route('/<string:catagory>/<int:item>/delete')
def deleteItem(catagory, item):
    # If user is authorized shows a page to delete an item
    return ("Delete page for %s, in the %s catagory" % (item, catagory))


@app.route('/<string:catagory>/new')
def newItem(catagory):
    # If user is authorized shows a page to add a new item
    return "Page for adding a new item to the %s catagory" % catagory






# Start server
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.static_folder='static'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
