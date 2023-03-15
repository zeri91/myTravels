# utils.py
import folium

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