# utils.py
import folium
import requests

def add_to_featuregrp(list, featuregrp, type):
    if type == 'airports':
        for a in list:
            nome = a['name']
            lat = a['latitude_deg']
            lon = a['longitude_deg']
            folium.Marker(location=[lat, lon], tooltip=nome, icon=folium.Icon(color='blue', icon='plane')).add_to(featuregrp)
    if type == 'monuments':
        for m in list:
            print(m)
            nome = m['name']
            lat = m['latitude_deg']
            lon = m['longitude_deg']
            folium.Marker(location=[lat, lon], tooltip=nome, icon=folium.features.CustomIcon('./static/images/icons/' + nome.replace(" ", "-") + '.png', icon_size=(30,30))).add_to(featuregrp)
    return
    
def get_water_style():
    return {
        'fillColor': '#3186cc',
        'color': '#3186cc',
        'fillOpacity': 0.3,
        'opacity': 0.3
    }

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