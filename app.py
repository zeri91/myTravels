# Python standard libraries
import json
import os
import sqlite3

# Third-party libraries
from flask import Flask, render_template, redirect, request, url_for, flash, g
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user
)
from oauthlib.oauth2 import WebApplicationClient
import requests
from flask_sqlalchemy import SQLAlchemy
import folium
from folium import plugins
from folium.plugins import MarkerCluster
import pandas as pd

# Internal imports for the DB
from db import init_db_command
from user import User
# useful functions
import utils

# Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)
POSITIONSTACK_KEY = os.environ.get("POSITIONSTACK_KEY")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
#db.init_app(app)

# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.unauthorized_handler
def unauthorized():
    return "You must be logged in to access this content.", 403

################### 
# DB setup, si puó togliere una volta che il db é creato 
try:
    init_db_command()
except sqlite3.OperationalError:
    # Assume it's already been created
    pass

# OAuth2 client setup to communicate with Google server
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Executed before every request, if authenticated, retrieve all the 
# user saved locations
@app.before_request
def load_locations():
    if current_user.is_authenticated:
        if not hasattr(g, 'locations') or not g.locations:
            g.locations = User.get_user_locations(current_user.id)
    else:
        g.locations = []

# context passato a tutte le route con lo stato dell'utente
# @app.context_processor
# def usr_context():

@app.route('/')
def index():
    return render_template('index.html')

# Definizione della rotta per la pagina di registrazione
@app.route('/registrazione', methods=['GET', 'POST'])
def registrazione():
    if request.method == 'POST':
        # Ottenere i dati dal form di registrazione
        username = request.form['username']
        password = request.form['password']

    return render_template('registrazione.html')

@app.route('/map', methods=['GET', 'POST'])
def map(): 
    airports = pd.read_csv("./data/airports-v2.csv").to_dict('records')
    monuments = pd.read_csv("./data/monuments.csv").to_dict('records')
    eco_footprints = pd.read_csv("./data/footprint.csv")
    max_eco_footprint = eco_footprints["Ecological footprint"].max()
    political_countries = ("./static/admin_0_countries.geojson")
    # seven_seas = ("./static/geography_marine_polys.geojson")

    m = folium.Map(
        location=(30, 10), zoom_start=3, tiles="Stamen Watercolor", 
        width='80%', height='80%', max_bounds=True,
        )
    
    # Creare dei FeatureGroup per ogni categoria di marker
    marker_airports = folium.FeatureGroup(name='airports', show=False)
    marker_monuments = folium.FeatureGroup(name='monuments', show=True)
    marker_favourits = folium.FeatureGroup(name='favourits', show=True)

    # load the favourit locations of the user
    for l in g.locations:
        folium.Marker(location=[l['lat'], l['long']], tooltip=l['name'], icon=folium.Icon(color='blue', icon='star')).add_to(marker_favourits)
     
    # Aggiungere i markers ai FeatureGroup
    utils.add_to_featuregrp(airports, marker_airports, 'airports')
    utils.add_to_featuregrp(monuments, marker_monuments, 'monuments')

    # add the colored countries layer to the map
    folium.Choropleth(
        geo_data = political_countries,
        data = eco_footprints,
        columns=["Country/region", "Ecological footprint"],
        key_on="feature.properties.name",
        bins=[0, 1, 1.5, 2, 3, 4, 5, 6, 7, 8, max_eco_footprint],
        fill_color="RdYlGn_r",
        fill_opacity=0.8,
        line_opacity=0.3,
        nan_fill_color="transparent",
        legend_name="Ecological footprint per capita",
        name="Countries by ecological footprint per capita",
    ).add_to(m)

    # Aggiungere i FeatureGroup alla mappa
    marker_airports.add_to(m)
    marker_monuments.add_to(m)  
    marker_favourits.add_to(m)

    # coloro i mari
    #folium.GeoJson(
    #    data=seven_seas,
    #    style_function=lambda x: utils.get_water_style(),
    #    name = "seven seas"
    #).add_to(m)

    # prende le ricerche degli utenti e richiama l'API per trovare le coordinate 
    # del luogo richiesto e impostare un marker
    if request.method == 'POST':
        address = request.form['address']
        api_key = POSITIONSTACK_KEY
        lat, lon = get_lat_long(address, api_key)
        if lat and lon:
            folium.Marker(location=[lat, lon], popup=address).add_to(m)
            #return m._repr_html_()
        else:
            flash('Location not valid', 'error')

    # Add layer control to the map
    folium.LayerControl(position='topright').add_to(m)

    # Extract map components and put those on a page
    m.get_root().render()
    header = m.get_root().header.render()
    body_html = m.get_root().html.render()
    script = m.get_root().script.render()

    # clean the header generated by leaflet
    header = header.replace('<script src="https://code.jquery.com/jquery-1.12.4.min.js"></script>\n', '')
    header = header.replace('<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/js/bootstrap.bundle.min.js"></script>\n', '')
    header = header.replace('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/css/bootstrap.min.css"/>\n', '')
    header = header.replace('<link rel="stylesheet" href="https://netdna.bootstrapcdn.com/bootstrap/3.0.0/css/bootstrap.min.css">', '')
    header = header.replace('<link rel="stylesheet" href="https://netdna.bootstrapcdn.com/bootstrap/3.0.0/css/bootstrap.min.css"/>', '')
    header = header.replace('<meta http-equiv="content-type" content="text/html; charset=UTF-8" />', '')
    header = header.replace('<meta charset="UTF-8">', '')
    header = header.replace('<meta name="viewport" content="width=device-width, initial-scale=1.0">', '')
   
    context = {'header': header, 'body_html': body_html, 'script': script}
    return render_template('map_v2.html', **context)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name)

@app.route('/travelslist')
@login_required
def travels_list():
    if not hasattr(g, 'trips'):
        g.trips = User.get_user_trips(current_user.id)

    return render_template('travelslist.html', travels=g.trips)

@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that we have tokens (yay) let's find and hit URL
    # from Google that gives you user's profile information,
    # including their Google Profile Image and Email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # We want to make sure their email is verified.
    # The user authenticated with Google, authorized our
    # app, and now we've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # Create a user in our db with the information provided
    # by Google
    user = User(
        id_=unique_id, name=users_name, email=users_email, profile_pic=picture
    )

    # Doesn't exist? Add to database
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture)

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    return redirect(url_for("profile"))

@app.route("/logout")
#The @login_required decorator is another tool from the Flask-Login toolbox and 
#will make sure that only logged in users can access this endpoint. 
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

def get_lat_long(address, api_key):
    url = 'http://api.positionstack.com/v1/forward'
    params = {
        'access_key': api_key,
        'query': address,
        'limit': 1
    }
    response = requests.get(url, params=params).json()
    if response['data']:
        lat = response['data'][0]['latitude']
        lon = response['data'][0]['longitude']
        return lat, lon
    else:
        return (None, None)

if __name__ == '__main__':
    app.run(debug=True, ssl_context="adhoc")