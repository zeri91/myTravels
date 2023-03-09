# Python standard libraries
import json
import os
import sqlite3

# Third-party libraries
from flask import Flask, render_template, redirect, request, url_for, render_template_string
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db.init_app(app)

# Creazione del database
with app.app_context():
    db.create_all()

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
    airports = pd.read_csv("./data/airports.csv")
    eco_footprints = pd.read_csv("./data/footprint.csv")
    max_eco_footprint = eco_footprints["Ecological footprint"].max()
    political_countries = ("./static/admin_0_countries.geojson")

    m = folium.Map(location=(30, 10), zoom_start=3, tiles="cartodb positron", width='80%', height='80%')

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

    folium.LayerControl().add_to(m)

    # Extract map components and put those on a page
    m.get_root().render()
    header = m.get_root().header.render()
    body_html = m.get_root().html.render()
    script = m.get_root().script.render()

    context = {'header': header, 'body_html': body_html, 'script': script}
    return render_template('map_v2.html', **context)

@app.route("/components")
def components():
    """Extract map components and put those on a page."""
    m = folium.Map(
        width=800,
        height=600,
    )

    m.get_root().render()
    header = m.get_root().header.render()
    body_html = m.get_root().html.render()
    script = m.get_root().script.render()

    context = {'header': header, 'body_html': body_html, 'script': script}
    return render_template('map_v2.html', **context)
    


if __name__ == '__main__':
    app.run(debug=True)