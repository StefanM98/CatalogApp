from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
app = Flask(__name__)

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Catagory, Item, Base, User

# New Imports for auth
from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from werkzeug import secure_filename
import os

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBsession = sessionmaker(bind = engine)
session = DBsession()

logged_in = True

@app.route('/')
def catalog():
    # Checks if user is logged in and then returns the correct home page
    catagories = session.query(Catagory).all()
    #catagories = ["Holidays", "Seasons", "My Little Poney", "Disney"]
    recentItems = session.query(Item).order_by(desc(Item.time_created)).limit(3).all()
    return render_template('home.html',
    catagories=catagories,
    recentItems=recentItems,
    logged_in=logged_in)



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

@app.route('/<string:catagory>/')
def catagory(catagory):
    #  Returns page for selected catagory
    # return "Page for %s" % catagory
    catagory = catagory.replace('_', ' ')
    catagories = session.query(Catagory).all()
    items = session.query(Item).filter_by(item_catagory=catagory).all()
    return render_template('catagory.html',
    catagories=catagories,
    catagory=catagory,
    items=items,
    logged_in=logged_in)


@app.route('/<string:catagory>/edit', methods=['GET', 'POST'])
def editCatagory(catagory):
    # If user is authorized shows a page to edit a catagory
    if logged_in:
        if request.method == 'GET':
            return render_template('edit_catagory.html', catagory=catagory)
        else:
            catagory = catagory.replace('_', ' ')
            thisCatagory = session.query(Catagory).filter_by(name=catagory).one()
            catagoryItems = session.query(Item).filter_by(item_catagory=catagory).all()
            thisCatagory.name = request.form['name']
            for i in catagoryItems:
                i.item_catagory = request.form['name']
                session.add(i)
            session.add(thisCatagory)
            session.commit()
            return redirect(url_for('catagory', catagory=thisCatagory.name.replace(' ', '_')))
    else:
        redirect(url_for('catagory', catagory=catagory))


@app.route('/<string:catagory>/delete', methods=['GET', 'POST'])
def deleteCatagory(catagory):
    # If user is authorized shows a page to delete a catagory
    if logged_in:
        if request.method == 'GET':
            return render_template('delete_catagory.html', catagory=catagory)
        else:
            catagory = catagory.replace('_', ' ')
            thisCatagory = session.query(Catagory).filter_by(name=catagory).one()
            session.delete(thisCatagory)
            session.commit()
            return redirect(url_for('catalog'))
    else:
        redirect(url_for('catagory', catagory=catagory))


@app.route('/new', methods=['GET', 'POST'])
def newCatagory():
    # If user is authorized shows a page to add a catagory
    if logged_in:
        if request.method == 'GET':
            return render_template('add_catagory.html')
        else:
            newCatagory = Catagory(name=request.form['name'], user_id=1)
            catagory = newCatagory.name.replace(' ', '_')
            session.add(newCatagory)
            session.commit()
            return redirect(url_for('catagory', catagory=catagory))
    else:
        return redirect(url_for('catalog'))




# Item Routes

@app.route('/<string:catagory>/<int:item>')
def item(catagory, item):
    # Returns page for selected item
    # return ("Page for %s, in the %s catagory" % (item, catagory))
    catagory = catagory.replace('_', ' ')
    item = session.query(Item).filter_by(id=item, item_catagory=catagory).one()
    items = session.query(Item).filter_by(item_catagory=catagory).all()
    user = session.query(User).filter_by(id=item.user_id).one()
    return render_template('item.html', catagory=catagory, item=item, items=items, user=user)


@app.route('/<string:catagory>/<int:item>/edit', methods=['GET', 'POST'])
def editItem(catagory, item):
    # If user is authorized shows a page to edit an item
    #return ("Edit page for %s, in the %s catagory" % (item, catagory))
    catagory = catagory.replace('_', ' ')
    thisItem = session.query(Item).filter_by(item_catagory=catagory, id=item).one()
    if request.method == 'GET':
        return render_template('edit_item.html', catagory=catagory, item=item, thisItem=thisItem)
    else:
        changes = 0

        # Checks for User Input
        if (request.form['name'] != ""):
            thisItem.name = request.form['name']
            changes += 1
        if (request.form['description'] != ""):
            thisItem.description = request.form['description']
            changes += 1
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                os.remove(os.path.join('./static', thisItem.image))
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename)))
                thisItem.image = "images/%s" % secure_filename(file.filename)
                changes += 1

        if (changes > 0):
            session.add(thisItem)
            session.commit()
            print "Updated Database."
            flash("Item Successfully Edited")
            return redirect(url_for('catagory', catagory=catagory))
        else:
            flash("ERROR: Please make a change or click the back arrow.")
            return render_template('edit_item.html', catagory=catagory, item=item)


@app.route('/<string:catagory>/<int:item>/delete', methods=['GET', 'POST'])
def deleteItem(catagory, item):
    # If user is authorized shows a page to delete an item
    catagory = catagory.replace('_', ' ')
    thisItem = session.query(Item).filter_by(item_catagory=catagory, id=item).one()
    if request.method == 'GET':
        print (os.path.join(url_for('static', filename=''), thisItem.image))
        return render_template('delete_item.html', catagory=catagory, item=item)
    else:
        os.remove(os.path.join('./static', thisItem.image))
        session.delete(thisItem)
        session.commit()
        return redirect(url_for('catagory', catagory=catagory.replace(' ', '_')))


@app.route('/<string:catagory>/new', methods=['GET', 'POST'])
def newItem(catagory):
    # If user is authorized shows a page to add a new item
    catagory = catagory.replace('_', ' ')
    if request.method == 'GET':
        return render_template('add_item.html', catagory=catagory)
    else:
        file = request.files['file']
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename)))
        newItem = Item(name=request.form['name'],
            description=request.form['description'],
            image = "images/%s" % secure_filename(file.filename),
            item_catagory=catagory,
            user_id=1)
        session.add(newItem)
        session.commit()
        return redirect(url_for('catagory', catagory=catagory.replace(' ', '_')))



# Start server
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.static_folder='static'
    app.config['UPLOAD_FOLDER'] = './static/images/'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
