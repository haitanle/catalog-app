from flask import Flask, jsonify, request, render_template, redirect, url_for, flash, session as login_session

from models import Base,User,Team,Player

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

import random, string, requests, json, httplib2
import flask

from flask import make_response
from oauth2client.client import FlowExchangeError, flow_from_clientsecrets

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']

engine = create_engine('sqlite:///soccerCatalog.db')

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)

#endpoint to hanlde Google OAuth response 
@app.route('/gconnect', methods=['POST'])
def gconnect():
	#check for anti-forgery 
	if request.args.get('state') != login_session['state']:
		print('***Error anti-forgery does not match ***')
		response = make_response(json.dumps('Unable to verify forgery'),401)
		response.headers['Content-Type'] ='application/json'
		return response
	oneTimeCode = request.data

	try:
		oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
		oauth_flow.redirect_uri = 'postmessage'
		credentials = oauth_flow.step2_exchange(oneTimeCode)
	except FlowExchangeError:
		print("***Fail on authorization server***")
		response = make_response(json.dumps('Failed to upgrade the authorization code for token'),401)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Check that the access token is valid
	access_token = credentials.access_token
	url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
	h = httplib2.Http()
	result = json.loads(h.request(url,'GET')[1])

	# If there was an error in the access token info, abort.
	if result.get('error') is not None:
		print('***Error on token access ***')
		response = make_response(json.dumps(result.get('error')), 500)
		response.headers['Content-Type'] = 'application/json'
		return response

    # Verify that the access token is used for the intended user
  	gplus_id = credentials.id_token['sub']
  	if result['user_id'] != gplus_id:
  		print('***Error intended user ***')
  		response = make_response(json.dumps("Token's user ID doesn't match given user ID"),401)
  		response.headers['Content-Type'] = 'application/json'
  		return response
    
    #Verify that the access token is valid for this app. 
   	if result['issued_to'] != CLIENT_ID:
   		print('***Error invalid for app***')
   		response = make_response(json.dumps("Token's client ID does not match app"),401)
   		response.headers['Content-Type'] = 'application/json'
 		return response

    #Check to see if user is already logged in
   	stored_access_token = login_session.get('access_token')
   	stored_gplus_id = login_session.get('gplus_id')
   	if stored_access_token is not None and gplus_id == stored_gplus_id:
   		print("***User is already logged in***")
   		response = make_response(json.dumps('Current user is already connected'),200)
   		response.headers['Content-Type'] = 'application/json'
   		return response

    #store the access token in the session for later use.
   	login_session['access_token'] = credentials.access_token
   	login_session['gplus_id'] = gplus_id

    #Get user info
   	userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
   	params = {'access_token': credentials.access_token, 'alt':'json'}
   	answer = requests.get(userinfo_url, params=params)

   	data = answer.json()

   	login_session['username'] = data["name"]
   	login_session['picture'] = data["picture"]
   	login_session['email'] = data["email"]

    #Check if the user already in database, else create new user in db
   	if getUserID(login_session['email']) is None:
   		print("***Creating User***")
   		user_id = createUser(login_session)
   	else:
   		print("***User already created...logging in....***")
   		user_id = getUserID(login_session['email'])

   	login_session['user_id'] = user_id

   	output = '<h1>Welcome, %s!</h1><img src="%s" styles="width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"' %(login_session['username'],login_session['picture'])
   	flash("you are now logged in as %s" % login_session['username'])
   	print("done!")
	return output

@app.route('/gdisconnect')
def gdisconnect():
	# Only disconnect a connected user. 
 	access_token = login_session.get('access_token')
 	if access_token is None:
 		print('Access Token is None')
 		response = make_response(json.dumps('Current user not connected.'), 401)
 		response.headers['Content-Type'] = 'application/json'
 		return response

	#expire the oauth token
	result = requests.post('https://accounts.google.com/o/oauth2/revoke',
		params={'token': login_session['access_token']},
		headers = {'content-type':'application/x-www-form-urlencoded'})

	#remove all sessions
	try: 
		login_session.pop('username',None)
   		login_session.pop('picture',None)
   		login_session.pop('email',None)
   		login_session.pop('access_token',None)
   		login_session.pop('gplus_id',None)
   		login_session.pop('user_id',None)
   		login_session.pop('state', None)
   		login_session.pop('editable',None)
   		login_session.pop('logIn',None)

   	except KeyError:
   		response = make_response(json.dumps('Unable to remove user session'),401)
   		response.headers['Content-Type'] = 'application/json'
   		return response

	return redirect(url_for('main'))
	

@app.route('/')
@app.route('/main')
def main():
	if 'user_id' in login_session:
		login_session['logIn'] = True 
	else:
		login_session['logIn'] = False

	return render_template('main.html', state=generateState(), isLogin = login_session['logIn'], teams = getAllTeams())

@app.route('/addPlayer', methods=['GET','POST'])
def addPlayer():
	if 'user_id' in login_session:
		if request.method == 'GET':
			return render_template('addPlayer.html', isLogin=login_session['logIn'], teams=getAllTeams())
		if request.method == 'POST':

			team = request.form['team'].split('|')
			team_id = team[0]
			team_name = team[1]

			newPlayer = Player(name = request.form['player_name'],
				user_id = login_session['user_id'],
				bio = request.form['player_description'],
				team_id = team_id,
				position = request.form['player_position'])
			session.add(newPlayer)
			session.commit()

			flash("New Player added: %s for team:%s" % (request.form['player_name'],team_name))
			return redirect(url_for('main'))
	else:
		return redirect(url_for('main'))


@app.route('/team/<int:team_id>')
def team(team_id):
	DBSession = sessionmaker(bind=engine)
	session = DBSession()

	teamName = session.query(Team).filter_by(id=team_id).one().name
	players = getTeam(team_id)

	if 'user_id' not in login_session:
		return render_template('team.html', state=generateState(), isLogin=False, team=teamName, teams=getAllTeams(), players = players)

	return render_template('team.html', state=generateState(), isLogin=login_session['logIn'], team=teamName, teams=getAllTeams(), players = players)


@app.route('/team/player/<int:player_id>')
def player(player_id):
	if 'user_id' not in login_session:
		return render_template('player.html', state=generateState(), isLogin=False, player = getPlayer(player_id))

	if editable(player_id):
		login_session['editable'] = True
	else: 
		login_session['editable'] = False

	return render_template('player.html', state=generateState(), session=login_session, player = getPlayer(player_id))

@app.route('/team/player/<int:player_id>/edit', methods=['GET','POST'])
def editPlayer(player_id):
	DBSession = sessionmaker(bind=engine)
	session = DBSession()

	if 'user_id' not in login_session:
		return redirect(url_for('main'))

	if not editable(player_id):
		return redirect(url_for('player',player_id = player_id))

	if request.method == 'GET':
		player = session.query(Player).filter_by(id=player_id).first()
		return render_template('editPlayer.html', player = player, teams=getAllTeams())
	elif request.method == 'POST':
		player = session.query(Player).filter_by(id=player_id).first()

		player.name = request.form['player_name']
		player.bio = request.form['player_description']
		player.position = request.form['player_position']
		
		team = request.form['team'].split('|')
		team_id = team[0]
		team_name = team[1]

		player.team_id = team_id

		session.add(player)
		session.commit()

		flash("Player Edited: %s for team:%s" % (request.form['player_name'],team_name))
		return redirect(url_for('main'))

@app.route('/team/player/<int:player_id>/delete', methods=['GET','POST'])
def deletePlayer(player_id):
	if 'user_id' not in login_session:
		return redirect(url_for('main'))
	if not editable(player_id):
		return redirect(url_for('player',player_id = player_id))

	DBSession = sessionmaker(bind=engine)
	session = DBSession()

	if request.method == 'GET':
		player = session.query(Player).filter_by(id=player_id).one()
		return render_template('deletePlayer.html', player=player)
	elif request.method == 'POST':
		player = session.query(Player).filter_by(id=player_id).one()
		team = session.query(Team).filter_by(id=player.team_id).one()
		session.delete(player)
		session.commit()

		flash("Player Deleted: %s from team: %s" % (player.name,team.name))
		return redirect(url_for('main'))

@app.route('/catalog.json')
def jsonData():
	return getSoccerJSON()

def generateState():
	state = ''.join(random.choice(string.ascii_uppercase + string.digits)
		for x in xrange(32))
	login_session['state'] = state
	return state

def getAllTeams():
	DBSession = sessionmaker(bind=engine)
	session = DBSession()

	teams = session.query(Team).all()
	return teams

def getTeam(team_id):
	DBSession = sessionmaker(bind=engine)
	session = DBSession()
	return session.query(Player).filter_by(team_id=team_id)

def getPlayer(player_id):
	DBSession = sessionmaker(bind=engine)
	session = DBSession()
	return session.query(Player).filter_by(id=player_id).first()

def editable(player_id):
	DBSession = sessionmaker(bind=engine)
	session = DBSession()

	creater_id =session.query(Player).filter_by(id=player_id).one().user_id
	if login_session['user_id'] == creater_id:
		return True
	return False

def getSoccerJSON():
	DBSession = sessionmaker(bind=engine)
	session = DBSession() 

	dataList = []
	teams = session.query(Team).all()
	for team in teams:
		players = session.query(Player).filter_by(team_id=team.id)
		playerList = []
		for player in players:
			playerList.append(player.serialize)
		dataList.append({team.serialize['teamName']:playerList})

	return jsonify(dataList)
			

def getUserID(email):
	DBSession = sessionmaker(bind=engine)
	session = DBSession()

	try:
		user = session.query(User).filter_by(email=email).one()
		return user.id
	except Exception:
		return None

def getUserInfo(user_id):
	DBSession = sessionmaker(bind=engine)
	session = DBSession()
	return session.query(User).filter_by(id=user_id).one()

def createUser(login_session):
	DBSession = sessionmaker(bind=engine)
	session = DBSession()

	newUser = User(username=login_session['username'], email = login_session['email'])
	session.add(newUser)
	session.commit()
	user = session.query(User).filter_by(email=login_session['email']).one()
	return user.id

if __name__ == '__main__':
	app.secret_key = 'supersecretkey'
	app.debug = True
	app.run(host='0.0.0.0', port =5000)