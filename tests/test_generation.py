import json 
import requests 
import numpy as np 
import time
from pprint import pprint

# experiment
session_id = "test"
number_of_nodes = 2
weights = [1.0/ number_of_nodes] * number_of_nodes
weights[-1] = 1.0 - sum(weights[:-1])
body = {   
    "session_id": session_id,
    "number_of_nodes": number_of_nodes,
    "weights": weights,
    "max_weightings": [1.0] * number_of_nodes,
    "performance_metric": 0
}

# Endpoints 
gen_endpoint = "http://0.0.0.0:8000/weights_gen/?"
update_endpoint = "http://0.0.0.0:8000/weights_update/?"
delete_endpoint = "http://0.0.0.0:8000/weights_update_delete/?"

def handle_response(response) -> None:
    # Check if the request was successful
    if response.status_code == 200:
        print("Response:")
        pprint(response.json())  # Print the JSON response from the server
    else:
        print("Request failed with status code:") 
        print(response.status_code)
        print("Response content:")
        print(response.text)


def compute_objective_function(weights, optimal_weights):
    value = (np.array(weights) - np.array(optimal_weights))**2

    return 1.0/ value.sum()

# delete any previous data 
delete_response = requests.post(delete_endpoint, json=body)
handle_response(delete_response)

optimal_weights = [0.90, 0.10]

# begin experiment iterations
for i in range(0, 100): 
    time.sleep(1)
    if i == 0: 
        update_response = requests.post(update_endpoint, json=body)
        handle_response(update_response)
    else: 

        gen_response = requests.post(gen_endpoint, json=body)
        handle_response(gen_response)

        weight_data = gen_response.json()['weights']
        value = compute_objective_function(weight_data, optimal_weights)

        body = {   
            "session_id": session_id,
            "number_of_nodes": number_of_nodes,
            "weights": weight_data,
            "max_weightings": [1.0] * number_of_nodes,
            "performance_metric": value
        }

        update_response = requests.post(update_endpoint, json=body)
        handle_response(update_response)

        # put in new data 