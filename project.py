from flask import Flask, render_template, request, redirect, jsonify, url_for, flash  # NOQA
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Items, User, Categories
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from flask import session as login_session
from flask import make_response
from functools import wraps
import httplib2
import json
import random
import string
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item catalog"

engine = create_engine('sqlite:///items.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Redirect to login page if not logged in
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'username' in login_session:
            return func(*args, **kwargs)
        else:
            return redirect(url_for('showLogin'))
    return wrapper


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('signin.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """
    Gathers data from Google Sign In API and places it
    inside a session variable.
    """
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

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

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['email'] = data['email']

    # See if a user exists, if it doesn't make a new one

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    return "Redirecting.."

    # DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
@login_required
def gdisconnect():
    """
    Deletes the login session and revokes the login token
    """
    access_token = login_session['access_token']
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps(
            'Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = ('https://accounts.google.com/o/oauth2/revoke?token=%s'
           % login_session['access_token'])
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('showItems'))
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# User Helper Functions


def createUser(login_session):
    newUser = User(user_name=login_session['username'],
                   user_email=login_session['email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(
        user_email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(user_email=email).one()
        return user.id
    except:
        return None


# Shows all categories
@app.route('/cat/')
@login_required
def showCats():
    cats = session.query(Categories).all()
    return render_template('showCat.html', cats=cats)


# Adds new category
@app.route('/cat/new/', methods=['GET', 'POST'])
@login_required
def newCat():
    if request.method == 'POST':
        cat = Categories(cat_name=request.form.get('name'),
                         user_id=login_session['user_id'])
        session.add(cat)
        session.commit()
        return redirect(url_for('showItems'))
    else:
        return render_template('newCat.html')


# Add delete a category
@app.route('/cat/<int:cat_id>/delete/', methods=['GET', 'POST'])
@login_required
def deleteCat(cat_id):
    cat = session.query(Categories).filter_by(id=cat_id).one()
    if cat.user_id == login_session['user_id']:
        if request.method == 'POST':
            session.delete(cat)
            session.commit()
            return redirect(url_for('showItems'))
        else:
            return render_template('deleteCat.html', cat_id=cat_id, cat=cat)
    return "Not authorized to modify this item!"


# Add edit a category
@app.route('/cat/<int:cat_id>/edit/', methods=['GET', 'POST'])
@login_required
def editCat(cat_id):
    cat = session.query(Categories).filter_by(id=cat_id).one()
    if cat.user_id == login_session['user_id']:
        if request.method == 'POST':
            cat.cat_name = request.form.get('name', None)
            session.add(cat)
            session.commit()
            return redirect(url_for('showItems'))
        else:
            return render_template('editCat.html', cat_id=cat_id, cat=cat)
    return "Not authorized to modify this item!"


# Show my items
@app.route('/')
@app.route('/items/')
def showItems():
    """
    This is for showing the main page of webapp with all items
    """
    items = session.query(Items).all()
    cats = session.query(Categories).all()
    return render_template(
        'project.html', items=items, login_session=login_session, cats=cats)


# Add new items
@app.route('/items/new/', methods=['GET', 'POST'])
@login_required
def newItem():
    if request.method == 'POST':
        newItem = Items(item_name=request.form.get('name'),
                        item_link=request.form.get('link'),
                        item_description=request.form.get('description'),
                        item_image=request.form.get('image'),
                        item_category_id=session.query(Categories).filter_by(
                            cat_name=request.form.get('category')).one().id,
                        user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        return redirect(url_for('showItems'))
    else:
        cat = session.query(Categories).all()
        return render_template('newItem.html', cat=cat)


# Edit items
@app.route('/items/<int:item_id>/edit/', methods=['GET', 'POST'])
@login_required
def editItem(item_id):
    item = session.query(Items).filter_by(id=item_id).one()
    cat = session.query(Categories).all()
    if item.user_id == login_session['user_id']:
        if request.method == 'POST':
            item.item_name = request.form.get('name', None)
            item.item_link = request.form.get('link', None)
            item.item_description = request.form.get('description', None)
            item.item_image = request.form.get('image', None)
            item.item_category_id = session.query(Categories).filter_by(
                cat_name=request.form.get('category', None)).one().id
            session.add(item)
            session.commit()
            return redirect(url_for('showItems'))
        else:
            return render_template('editItem.html', item_id=item_id,
                                   item=item, cat=cat)
    return "Not authorized to modify this item!"


# Delete items
@app.route('/items/<int:item_id>/delete/', methods=['GET', 'POST'])
@login_required
def deleteItem(item_id):
    item = session.query(Items).filter_by(id=item_id).one()
    if item.user_id == login_session['user_id']:
        if request.method == 'POST':
            session.delete(item)
            session.commit()
            return redirect(url_for('showItems'))
        else:
            return render_template('deleteItem.html', item=item)
    return "Not authorized to modify this item!"


# JSON endpoint for all items
@app.route('/items/JSON')
def itemsJSON():
    items = session.query(Items).all()
    return jsonify(Items=[i.serialize for i in items])


# JSON endpoint for specific item
@app.route('/items/<int:item_id>/JSON')
def specificItemJSON(item_id):
    item = session.query(Items).filter_by(id=item_id).one()
    return jsonify(item.serialize)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8005)
