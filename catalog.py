from flask import Flask, render_template, request, redirect, url_for, jsonify
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Catagory, Item, Base, User
from flask import session as login_session
from flask import make_response
from werkzeug import secure_filename
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from oauth2client import client, crypt
import os
import random
import string
import httplib2
import json
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBsession = sessionmaker(bind=engine)
session = DBsession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    auth_code = request.data

    # If this request does not have `X-Requested-With` header, may be a CSRF
    if not request.headers.get('X-Requested-With'):
        response = make_response(
            json.dumps('Missing X-Requested-With header'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    CLIENT_SECRET_FILE = 'client_secrets.json'

    # Exchange auth code
    credentials = client.credentials_from_clientsecrets_and_code(
        CLIENT_SECRET_FILE,
        ['profile', 'email', 'openid'],
        auth_code)

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['provider'] = 'google'
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # Checks if a user exists in the database. If not, creates one.
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img class="user-image" src="'
    output += login_session['picture']
    output += ' "> '
    print "done!"
    return output


def createUser(login_session):
    # Creates new user in the database and returns their id
    newUser = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        print "User not found."
        return None


# Facebook Login
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = (
        'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange'
        '_token&client_id=%s&client_secret=%s&fb_exchange_token=%s') % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = (
        'https://graph.facebook.com/v2.8/me?access_token=%s&'
        'fields=name,id,email') % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = (
        'https://graph.facebook.com/v2.8/me/picture?access_token=%s&'
        'redirect=0&height=200&width=200') % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' "> '

    return output


@app.route("/gdisconnect")
@app.route('/fbdisconnect')
# DISCONNECT - Finds which provider was used and then disconnects
# Revoke a current user's token and reset their login_session
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'facebook':
            facebook_id = login_session['facebook_id']
            url = 'https://graph.facebook.com/%s/permission' % facebook_id
            h = httplib2.Http()
            result = h.request(url, 'DELETE')[1]
            del login_session['username']
            del login_session['email']
            del login_session['picture']
            del login_session['user_id']
            del login_session['facebook_id']
            return redirect(url_for('catalog'))
        if login_session['provider'] == 'google':
            # Only disconnect a connected user.
            credentials = login_session.get('credentials')
            if credentials is None:
                response = make_response(
                    json.dumps('Current user not connected.'), 401)
                response.headers['Content-Type'] = 'application/json'
                return response
            # Execute HTTP GET request to revoke current token.
            access_token = credentials.access_token
            url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % (
                access_token)
            h = httplib2.Http()
            result = h.request(url, 'GET')[0]

            if result['status'] == '200':
                # Reset the user's session.
                del login_session['credentials']
                del login_session['gplus_id']
                del login_session['username']
                del login_session['email']
                del login_session['picture']
                del login_session['user_id']

                return redirect(url_for('catalog'))
            else:
                # For whatever reason, the given token was Invalid
                response = make_response(
                    json.dumps("Failed to revoke token for given user."), 400)
                response.headers['Content-Type'] = 'application/json'
                return response
    else:
        response = make_response(
            json.dumps("Failed to find login provider."), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


# API Routes
@app.route('/JSON')
def JSONCatagories():
    catagories = session.query(Catagory).all()
    return jsonify(Catagory=[catagory.serialize for catagory in catagories])


@app.route('/<string:catagory>/JSON')
def JSONCatagory(catagory):
    catagory = catagory.replace('_', ' ')
    items = session.query(Item).filter_by(item_catagory=catagory).all()
    return jsonify(Item=[item.serialize for item in items])


@app.route('/<string:catagory>/<string:item>/JSON')
def JSONItem(catagory, item):
    catagory = catagory.replace('_', ' ')
    item = session.query(Item).filter_by(item_catagory=catagory, id=item).one()
    return jsonify(Item=[item.serialize])


@app.route('/')
def catalog():
    # Checks if user is logged in and then returns the correct home page
    rule = request.url_rule
    catagories = session.query(Catagory).all()
    recentItems = session.query(Item).order_by(
        desc(Item.time_created)).limit(3).all()
    return render_template(
            'home.html',
            catagories=catagories,
            recentItems=recentItems,
            login_session=login_session,
            rule=rule)


@app.route('/search', methods=['POST'])
def searchCatalog():
    query = request.form['search']
    rule = request.url_rule
    searchItems = session.query(Item).filter(Item.name.contains(query)).all()
    catagories = session.query(Catagory).all()
    return render_template(
        'home.html',
        catagories=catagories,
        recentItems=searchItems,
        login_session=login_session,
        rule=rule,
        query=query)


# Login Routes

@app.route('/login')
def login():
    # Shows login page
    return "Login Page"


@app.route('/logout')
def logout():
    # Logs out the user
    return "Logout Page"


# Catagory Routes

@app.route('/<string:catagory>')
def catagory(catagory):
    #  Returns page for selected catagory
    catagory = catagory.replace('_', ' ')
    catagories = session.query(Catagory).all()
    items = session.query(Item).filter_by(item_catagory=catagory).all()
    return render_template(
        'catagory.html',
        catagories=catagories,
        catagory=catagory,
        items=items,
        login_session=login_session)


@app.route('/<string:catagory>/edit', methods=['GET', 'POST'])
def editCatagory(catagory):
    # If user is authorized shows a page to edit a catagory
    if 'username' in login_session:
        if request.method == 'GET':
            return render_template('edit_catagory.html', catagory=catagory)
        else:
            catagory = catagory.replace('_', ' ')
            thisCatagory = session.query(Catagory).filter_by(
                name=catagory).one()
            catagoryItems = session.query(Item).filter_by(
                item_catagory=catagory).all()
            thisCatagory.name = request.form['name']
            for i in catagoryItems:
                i.item_catagory = request.form['name']
                session.add(i)
            session.add(thisCatagory)
            session.commit()
            return redirect(url_for(
                'catagory',
                catagory=thisCatagory.name.replace(' ', '_'),
                login_session=login_session))
    else:
        return redirect(url_for('login'))


@app.route('/<string:catagory>/delete', methods=['GET', 'POST'])
def deleteCatagory(catagory):
    # If user is authorized shows a page to delete a catagory
    if 'username' in login_session:
        if request.method == 'GET':
            return render_template('delete_catagory.html', catagory=catagory)
        else:
            catagory = catagory.replace('_', ' ')
            thisCatagory = session.query(Catagory).filter_by(
                name=catagory).one()
            session.delete(thisCatagory)
            session.commit()
            return redirect(url_for('catalog'))
    else:
        return redirect(url_for('login'))


@app.route('/new', methods=['GET', 'POST'])
def newCatagory():
    # If user is authorized shows a page to add a catagory
    if 'username' in login_session:
        if request.method == 'GET':
            return render_template('add_catagory.html')
        else:
            newCatagory = Catagory(
                name=request.form['name'],
                user_id=login_session['user_id'])
            catagory = newCatagory.name.replace(' ', '_')
            session.add(newCatagory)
            session.commit()
            return redirect(url_for('catagory', catagory=catagory))
    else:
        return redirect(url_for('login'))


# Item Routes

@app.route('/<string:catagory>/<int:item>')
def item(catagory, item):
    # Returns page for selected item
    # return ("Page for %s, in the %s catagory" % (item, catagory))
    catagory = catagory.replace('_', ' ')
    try:
        thisItem = session.query(Item).filter_by(
            id=item,
            item_catagory=catagory).one()
    except:
        return "No item was found."
    items = session.query(Item).filter_by(item_catagory=catagory).all()
    user = session.query(User).filter_by(id=thisItem.user_id).one()

    try:
        prev_item = session.query(Item).order_by(Item.id.desc()).filter(
            Item.id < thisItem.id).filter_by(item_catagory=catagory).first()
    except:
        print "No more previous items"
        prev_item = ''

    try:
        next_item = session.query(Item).order_by(Item.id.asc()).filter(
            Item.id > thisItem.id).filter_by(item_catagory=catagory).first()
    except:
        print "No more items"
        next_item = ''

    return render_template(
            'item.html', catagory=catagory, item=thisItem,
            items=items, user=user, login_session=login_session,
            session=session, prev_item=prev_item, next_item=next_item)


@app.route('/<string:catagory>/<int:item>/edit', methods=['GET', 'POST'])
def editItem(catagory, item):
    # If user is authorized shows a page to edit an item
    if 'username' in login_session:
        catagory = catagory.replace('_', ' ')
        thisItem = session.query(Item).filter_by(
            item_catagory=catagory,
            id=item).one()
        if request.method == 'GET':
            return render_template(
                'edit_item.html',
                catagory=catagory,
                item=item,
                thisItem=thisItem)
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
                    try:
                        os.remove(os.path.join('./static', thisItem.image))
                    except:
                        print "Previous image not found."
                    file.save(os.path.join(
                        app.config['UPLOAD_FOLDER'],
                        secure_filename(file.filename)))
                    thisItem.image = "images/%s" % secure_filename(
                        file.filename)
                    changes += 1

            if (changes > 0):
                thisItem.user_id = login_session['user_id']
                session.add(thisItem)
                session.commit()
                print "Updated Database."
                return redirect(url_for(
                    'catagory',
                    catagory=catagory.replace(' ', '_')))
            else:
                return render_template(
                    'edit_item.html',
                    catagory=catagory,
                    item=item)
    else:
        return redirect(url_for('login'))


@app.route('/<string:catagory>/<int:item>/delete', methods=['GET', 'POST'])
def deleteItem(catagory, item):
    # If user is authorized shows a page to delete an item
    if 'username' in login_session:
        catagory = catagory.replace('_', ' ')
        thisItem = session.query(Item).filter_by(
            item_catagory=catagory,
            id=item).one()
        if request.method == 'GET':
            print (os.path.join(url_for(
                'static', filename=''), thisItem.image))
            return render_template(
                'delete_item.html',
                catagory=catagory,
                item=item)
        else:
            os.remove(os.path.join('./static', thisItem.image))
            session.delete(thisItem)
            session.commit()
            return redirect(url_for(
                'catagory',
                catagory=catagory.replace(' ', '_')))
    else:
        return redirect(url_for('login'))


@app.route('/<string:catagory>/new', methods=['GET', 'POST'])
def newItem(catagory):
    # If user is authorized shows a page to add a new item
    if 'username' in login_session:
        catagory = catagory.replace('_', ' ')
        if request.method == 'GET':
            return render_template('add_item.html', catagory=catagory)
        else:
            file = request.files['file']
            file.save(os.path.join(
                app.config['UPLOAD_FOLDER'],
                secure_filename(file.filename)))
            newItem = Item(
                name=request.form['name'],
                description=request.form['description'],
                image="images/%s" % secure_filename(file.filename),
                item_catagory=catagory,
                user_id=login_session['user_id'])
            session.add(newItem)
            session.commit()
            return redirect(url_for(
                'catagory',
                catagory=catagory.replace(' ', '_')))
    return redirect(url_for('login'))

# Start server
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.static_folder = 'static'
    app.config['UPLOAD_FOLDER'] = './static/images/'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
