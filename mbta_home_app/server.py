from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import requests
import socket
import os

from .red_line_descriptions import *


BASE_URL = "https://api-v3.mbta.com"
SOCKET_HOST = "127.0.0.1"
SOCKET_PORT = 65432


# STATION_NAME_TO_ID = {
#     "KENDALL/MIT" : ["70072", "70071"],
#     "CENTRAL SQUARE" : ["70070", "70069"]
# }


# REDLINE_ID_TO_STATION_NAME_MAPPING = {
#     1: "Alewife",
#     10: "Davis",
#     20: "Porter",
#     30: "Harvard",
#     40: "Central",
#     50: "Kendall/MIT",
#     60: "Charles/MGH",
#     70: "Park Street",
#     80: "Downtown Crossing",
#     90: "South Station",
#     100: "Broadway",
#     110: "Andrew",
#     120: "JFK/UMass",
#     130: "Savin Hill",       # Ashmont Branch
#     140: "Fields Corner",    # Ashmont Branch
#     150: "Shawmut",          # Ashmont Branch
#     160: "Ashmont",          # Ashmont Branch
#     170: "North Quincy",     # Braintree Branch
#     180: "Wollaston",        # Braintree Branch
#     190: "Quincy Center",    # Braintree Branch
#     200: "Quincy Adams",     # Braintree Branch
#     210: "Braintree",        # Braintree Branch
#     220: "UNKNOWN"
# }


# DIRECTION_ID_TO_DIRECTION_MAPPING = {
#     0: "SouthBound",
#     1: "NorthBound"
# }


class MBTAAPIClient:
    """
    Class to communicate with the MBTA Public API
    """
    def __init__(self):
        self.base_url = BASE_URL

        # Load API_KEY
        load_dotenv()
        self.api_key = os.getenv("API_KEY")

    def get_live_locations(self, route):
        endpoint = f"{self.base_url}/vehicles"
        params = {
            "api_key": self.api_key,
            "filter[route]": route,
            "page[limit]": 50
        }
        response = requests.get(endpoint, params=params)
        return response.json()


    def get_arrival_predictions(self, stop_id):
        endpoint = f"{self.base_url}/predictions"
        params = {
            "api_key": self.api_key,
            "filter[stop]": stop_id,
            "page[limit]": 50
        }
        response = requests.get(endpoint, params=params)
        return response.json()


    def get_station_stop_id(self, route, station_name):
        endpoint = f"{self.base_url}/stops"
        params = {
            'api_key': self.api_key,
            'filter[route]': route,  # Filter for Red Line stops
            'filter[name]': station_name  # Filter for Kendall/MIT station
        }
        # Make the request to the MBTA API
        response = requests.get(endpoint, params=params)
        return response.json()


class MBTAInformationRetriever:
    """
    Helper class to process the information received 
    from the MBTA Server
    """
    def __init__(self):
        self.mbta_api = MBTAAPIClient()
    

    def get_live_locations(self, route):
        """
        Get the live locations for a route
        """
        live_locations = self.mbta_api.get_live_locations(route)

        # process
        for attributes in live_locations["data"]:
            id = attributes["id"]
            direction_id = attributes["attributes"]["direction_id"]
            bearing = attributes["attributes"]["bearing"]
            current_status = attributes["attributes"]["current_status"]
            current_stop_sequence = attributes["attributes"]["current_stop_sequence"]
            
            if current_stop_sequence==50:
                print(f"Id: {id} | Direction id: {DIRECTION_ID_TO_DIRECTION_MAPPING[direction_id]} | Bearing: {bearing} | Current status: {current_status} {REDLINE_ID_TO_STATION_NAME_MAPPING[current_stop_sequence]} ({current_stop_sequence})")


    def get_station_stop_id(self, route, station_name):
        return self.mbta_api.get_station_stop_id(route, station_name)
    

    def get_arrival_predictions(self, station_id):
        print("Retrieving arrival predictions for station code: ", station_id)
        live_predictions = self.mbta_api.get_arrival_predictions(station_id)
        arrivals = []
        for attributes in live_predictions["data"]:
            id = attributes["id"]
            update_type = attributes["attributes"]["update_type"]
            status = attributes["attributes"]["status"]
            direction_id = attributes["attributes"]["direction_id"]
            arrival_time = attributes["attributes"]["arrival_time"]

            print("arrival time: ", arrival_time)
            given_time = datetime.fromisoformat(arrival_time).replace(tzinfo=None)
            curr_time = datetime.now()
            diff = given_time - curr_time
            diff = str(diff.total_seconds() // 60 + 1)
            arrivals.append(diff)
        return arrivals[:3]


class MBTAHomeAppServer:
    """
    Socket server to specifically handle requests for the 
    MBTA Home Application
    """

    def __init__(self):
        self._mbta_information_retriever = MBTAInformationRetriever()
        self._host = SOCKET_HOST
        self._port = SOCKET_PORT


    def _get_station_arrival_predictions(self, station_name):
        northbound_arrivals = self._mbta_information_retriever.get_arrival_predictions(STATION_NAME_TO_ID[station_name][0])
        southbound_arrivals = self._mbta_information_retriever.get_arrival_predictions(STATION_NAME_TO_ID[station_name][1])

        # pad to ensure there are 3 predictions for each direction
        while len(northbound_arrivals) < 3:
            northbound_arrivals.append("N/A")
        while len(southbound_arrivals) < 3:
            southbound_arrivals.append("N/A")
        return northbound_arrivals + southbound_arrivals

    def run_server(self):

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self._host, self._port))
            s.listen()

            # loop for handling a new connection when one closes
            while True:

                print("Server ready, waiting for client connection.")
                conn, _ = s.accept()
                print("Connection accepted")

                with conn:
                    # loop to keep receiving new info on one connection
                    while True:
                        data = conn.recv(1024).decode('utf-8')
                        if not data:
                            break

                        res = self._get_station_arrival_predictions(data)
                        res_str = ",".join(res)
                        print("res str: ", res_str)
                        print()

                        conn.sendall(res_str.encode('utf-8'))
                conn.close()

