import os
from datetime import datetime, timedelta
import streamlit as st
import requests


API_KEY = st.secrets.get("REJSEPLANEN_API_KEY") or os.environ.get("REJSEPLANEN_API_KEY")
WALK_MINUTES = 12


def parse_time(t: str) -> datetime:
    """Parse time string, handling both HH:MM and HH:MM:SS formats."""
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(t, fmt)
        except ValueError:
            pass
    raise ValueError(f"Unexpected time format: {t}")


# Station IDs
NORREPORT_ID = "8600646"
HELLERUP_ID = "8600655"


def get_catchable_train(origin_id, dest_id, walk_minutes):
    """Find the next catchable train from origin to dest (departing in walk_minutes+)."""
    url = "https://www.rejseplanen.dk/api/trip"
    params = {
        "originId": origin_id,
        "destId": dest_id,
        "format": "json",
        "numF": 5
    }
    headers = {"Authorization": f"Bearer {API_KEY}"}

    response = requests.get(url, params=params, headers=headers)
    data = response.json()

    if "Trip" not in data or not data["Trip"]:
        return None

    now = datetime.now()

    for trip in data["Trip"]:
        legs = trip["LegList"]["Leg"]
        # Find first journey leg (skip WALK legs)
        leg = next((l for l in legs if l.get("type") == "JNY"), None)
        if not leg:
            continue

        dep_time = parse_time(leg["Origin"]["time"]).replace(
            year=now.year, month=now.month, day=now.day
        )
        # Handle midnight rollover
        if dep_time < now - timedelta(hours=1):
            dep_time += timedelta(days=1)

        minutes_until = (dep_time - now).total_seconds() / 60
        if minutes_until >= walk_minutes:
            return {
                "departure": leg["Origin"]["time"],
                "arrival": leg["Destination"]["time"],
                "train": leg.get("name", "Unknown"),
                "destination": leg["Destination"]["name"],
                "dep_time": dep_time
            }

    return None


if not API_KEY:
    st.error("REJSEPLANEN_API_KEY environment variable not set")
    st.stop()

# Route configurations
ROUTES = {
    "kjeld": {
        "name": "Kjeld Langes Gade 1",
        "origin_station": NORREPORT_ID,
        "dest_station": HELLERUP_ID,
        "walk_to": "Nørreport St."
    },
    "gersonsvej": {
        "name": "Gersonsvej 59",
        "origin_station": HELLERUP_ID,
        "dest_station": NORREPORT_ID,
        "walk_to": "Hellerup St."
    }
}

# Initialize session state for route selection
if "selected_route" not in st.session_state:
    st.session_state.selected_route = "kjeld"

# Toggle buttons for route selection
col1, col2 = st.columns(2)
with col1:
    if st.button(
        "Kjeld Langes Gade",
        type="primary" if st.session_state.selected_route == "kjeld" else "secondary",
        use_container_width=True
    ):
        st.session_state.selected_route = "kjeld"
        st.rerun()

with col2:
    if st.button(
        "Gersonsvej",
        type="primary" if st.session_state.selected_route == "gersonsvej" else "secondary",
        use_container_width=True
    ):
        st.session_state.selected_route = "gersonsvej"
        st.rerun()

# Get current route config
route = ROUTES[st.session_state.selected_route]

# Get next catchable train
train = get_catchable_train(route["origin_station"], route["dest_station"], WALK_MINUTES)

if train:
    # Calculate leave_by time
    leave_by = train["dep_time"] - timedelta(minutes=WALK_MINUTES)

    st.subheader(f"{route['name']} → {train['destination']}")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Leave by", leave_by.strftime("%H:%M"))
        st.caption(f"Walk {WALK_MINUTES} min to {route['walk_to']}")
    with col2:
        st.metric("Arrival", train["arrival"])
        st.caption(f"Train departs {train['departure']}")

    st.info(f"🚶 Walk to {route['walk_to']} → 🚆 {train['train']}")
else:
    st.warning("Could not find train")
