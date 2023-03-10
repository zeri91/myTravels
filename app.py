# Python standard libraries
import json
import os
import sqlite3

# Third-party libraries
from flask import Flask, render_template, redirect, request, url_for
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
from models import User, db
import folium
from folium.plugins import MarkerCluster
import pandas as pd

# Internal imports
from db import init_db_command
from user import User

# Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

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

# Naive database setup
try:
    init_db_command()
except sqlite3.OperationalError:
    # Assume it's already been created
    pass

# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Creazione del database
#with app.app_context():
#    db.create_all()

# context passato a tutte le route
@app.context_processor
def usr_context():
    # using Flask-Login library, we can easily check if a user is logged in
    if current_user.is_authenticated:
        return {'usr_status': current_user.name, 'pagina':'profile'}
    else:
        return {'usr_status': 'click here to login', 'pagina':'login'}

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

        # Creare un nuovo utente e aggiungerlo al database
        nuovo_utente = User(username=username, password=password)
        db.session.add(nuovo_utente)
        db.session.commit()

        return "Registrazione effettuata con successo!"
    return render_template('registrazione.html')

@app.route('/map')
def map(): 
    airports = pd.read_csv("./data/airports-v2.csv").to_dict('records')
    eco_footprints = pd.read_csv("./data/footprint.csv")
    max_eco_footprint = eco_footprints["Ecological footprint"].max()
    political_countries = ("./static/admin_0_countries.geojson")

    m = folium.Map(
        location=(30, 10), zoom_start=3, tiles="cartodb positron", 
        width='80%', height='80%',
        )

    # folium.GeoJson(political_countries).add_to(m)

    folium.Choropleth(
        geo_data = political_countries,
        data = eco_footprints,
        columns=["Country/region", "Ecological footprint"],
        key_on="feature.properties.name",
        bins=[0, 1, 1.5, 2, 3, 4, 5, 6, 7, 8, max_eco_footprint],
        fill_color="RdYlGn_r",
        fill_opacity=0.8,
        line_opacity=0.3,
        nan_fill_color="white",
        legend_name="Ecological footprint per capita",
        name="Countries by ecological footprint per capita",
    ).add_to(m)

    # Creare un FeatureGroup per contenere tutti i marker
    marker_airports = folium.FeatureGroup(name='airports', show=False)
    marker_monuments = folium.FeatureGroup(name='monuments', show=True)
    
    # Aggiungere i markers al FeatureGroup
    for a in airports:
        nome = a['name']
        lat = a['latitude_deg']
        lon = a['longitude_deg']
        #marker = folium.Marker(location=[lat, lon], tooltip=nome, icon=folium.Icon(color='blue', icon='plane'))
        #marker.add_to(m)
        folium.Marker(location=[lat, lon], tooltip=nome, icon=folium.Icon(color='blue', icon='plane')).add_to(marker_airports)
    
    # Aggiungere il FeatureGroup alla mappa
    marker_airports.add_to(m)
    
    # aggiungi il layer con qualche monumento di test 
    folium.Marker(location=[38.897, -77.036], tooltip="white house", icon=folium.features.CustomIcon('./static/images/icons/white-house-c.png', icon_size=(30,30))).add_to(marker_monuments)
    folium.Marker(location=[41.890, 12.492], tooltip="colosseum", icon=folium.features.CustomIcon('./static/images/icons/colosseum-c.png', icon_size=(30,30))).add_to(marker_monuments)
    folium.Marker(location=[48.852, 2.350], tooltip="notre dame", icon=folium.features.CustomIcon('./static/images/icons/notre-dame-c.png', icon_size=(30,30))).add_to(marker_monuments)
    folium.Marker(location=[27.173, 78.042], tooltip="taj mahal", icon=folium.features.CustomIcon('./static/images/icons/taj-mahal.png', icon_size=(30, 30))).add_to(marker_monuments)
    folium.Marker(location=[43.7230159, 10.3966321974895], tooltip="leaning tower", icon=folium.features.CustomIcon('./static/images/icons/leaning-tower-c.png', icon_size=(30, 30))).add_to(marker_monuments)

    marker_monuments.add_to(m)

    # Add layer control to the map
    folium.LayerControl(position='topright').add_to(m)

    # Extract map components and put those on a page
    m.get_root().render()
    header = m.get_root().header.render()
    body_html = m.get_root().html.render()
    script = m.get_root().script.render()

    context = {'header': header, 'body_html': body_html, 'script': script}
    return render_template('map_v2.html', **context)

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
    return redirect(url_for("index"))

@app.route("/logout")
#The @login_required decorator is another tool from the Flask-Login toolbox and 
#will make sure that only logged in users can access this endpoint. 
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

if __name__ == '__main__':
    app.run(debug=True, ssl_context="adhoc")