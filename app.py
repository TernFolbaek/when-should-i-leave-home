import os
import streamlit as st
import requests

st.title("When Should I Leave Home?")

API_KEY = os.environ.get("REJSEPLANEN_API_KEY")

if not API_KEY:
    st.error("REJSEPLANEN_API_KEY environment variable not set")
    st.stop()

url = "https://www.rejseplanen.dk/api/trip"
params = {
    "originCoordLat": "55.68290321618745",
    "originCoordLong": "12.564001112744467",
    "destId": "8600646",
    "format": "json",
    "numF": 1
}
headers = {"Authorization": f"Bearer {API_KEY}"}

response = requests.get(url, params=params, headers=headers)
data = response.json()

if "Trip" not in data:
    st.warning("No trips found")
    st.stop()

trip = data["Trip"][0]
leg = trip["LegList"]["Leg"][0]

origin = leg["Origin"]
destination = leg["Destination"]

st.subheader(f"Kjeld Langes Gade 1 → {destination['name']}")

col1, col2 = st.columns(2)
with col1:
    st.metric("Departure", f"{origin['time']}")
    st.caption(origin['date'])
with col2:
    st.metric("Arrival", f"{destination['time']}")

st.info(f"🚆 {leg.get('name', 'Unknown')}")