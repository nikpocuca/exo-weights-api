import json
import requests
import numpy as np
import time
import pytest
from pprint import pprint

# Constants and Endpoints
session_id = "test"
number_of_nodes = 2
weights = [1.0 / number_of_nodes] * number_of_nodes
weights[-1] = 1.0 - sum(weights[:-1])
optimal_weights = [0.90, 0.10]
gen_endpoint = "http://0.0.0.0:8001/weights_gen/"
update_endpoint = "http://0.0.0.0:8001/weights_update/"
delete_endpoint = "http://0.0.0.0:8001/weights_update_delete/"

@pytest.fixture
def setup_initial_body():
    """Set up the initial body dictionary for requests."""
    return {
        "session_id": session_id,
        "number_of_nodes": number_of_nodes,
        "weights": weights,
        "max_weightings": [1.0] * number_of_nodes,
        "performance_metric": 0
    }

def handle_response(response):
    """Check and handle the HTTP response status."""
    assert response.status_code == 200, f"Request failed with status code {response.status_code}: {response.text}"
    return response.json()

def compute_objective_function(weights, optimal_weights):
    """Compute the objective function value given weights and optimal weights."""
    value = (np.array(weights) - np.array(optimal_weights)) ** 2
    return 1.0 / value.sum()

def test_weights_update_flow(setup_initial_body):
    # Delete any previous data
    delete_response = requests.post(delete_endpoint, json=setup_initial_body)
    handle_response(delete_response)

    # Begin experiment iterations
    body = setup_initial_body
    for i in range(100):

        if i == 0:
            # Initial update
            update_response = requests.post(update_endpoint, json=body)
            response_data = handle_response(update_response)
            assert "message" in response_data, "Expected 'message' in response"
            pprint(response_data)
        else:
            # Generate weights
            gen_response = requests.post(gen_endpoint, json=body)
            gen_data = handle_response(gen_response)
            assert "weights" in gen_data, "Expected 'weights' in generation response"
            weight_data = gen_data['weights']
            pprint(gen_data)

            # Calculate performance metric
            performance_value = compute_objective_function(weight_data, optimal_weights)

            # Update body for the next iteration
            body = {
                "session_id": session_id,
                "number_of_nodes": number_of_nodes,
                "weights": weight_data,
                "max_weightings": [1.0] * number_of_nodes,
                "performance_metric": performance_value
            }

            # Send update with the new performance metric
            update_response = requests.post(update_endpoint, json=body)
            update_data = handle_response(update_response)
            pprint(update_data)
