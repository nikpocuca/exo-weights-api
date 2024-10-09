import json
from typing import Union, List
from fastapi import FastAPI
from pydantic import BaseModel, conlist, validator
import dirichlet
import numpy as np 

import redis
from redis import Redis


app = FastAPI()
redis_connection = redis.Redis(host='red', port=6379)

@app.get("/")
def read_root():
    return {
        "message": """ 
    An analytics tool to help users get better performance for 
    multi-node setups.   
    """
    }



class WeightsLog(BaseModel):
    number_of_nodes: int 
    weights: List[float]  # Ensure at least one weight is provided


    @validator('number_of_nodes')
    def check_number_of_nodes(cls, number_of_nodes):
        if number_of_nodes < 2:
            raise ValueError('number_of_nodes must be greater than or equal to 2.')
        return number_of_nodes


    @validator('weights')
    def check_weights_sum(cls, weights, values):
        if not weights:
            raise ValueError('Weights list cannot be empty.')
        weight_sum = sum(weights)
        if weight_sum != 1.0:
            raise ValueError(f'Sum of weights must be 1.0, but got {weight_sum}.')
        
        # Ensure the number of weights equals the number of nodes
        number_of_nodes = values.get('number_of_nodes')
        if number_of_nodes is not None and len(weights) != number_of_nodes:
            raise ValueError(f'Number of weights must equal number_of_nodes ({number_of_nodes}), but got {len(weights)}.')
        
        return weights



@app.post("/weights_log/")
def weights_log(message: WeightsLog):
    return {
        "message": "weights_log: SUCCESS", 
        "number_of_nodes": message.number_of_nodes, 
        "weights": message.weights
    }



class WeightsUpdate(BaseModel):
    session_id: str
    number_of_nodes: int 
    weights: List[float]
    max_weightings: List[float]
    performance_metric: float 

    @validator('number_of_nodes')
    def check_number_of_nodes(cls, number_of_nodes):
        if number_of_nodes < 2:
            raise ValueError('number_of_nodes must be greater than or equal to 2.')
        return number_of_nodes


    @validator('weights')
    def check_weights_sum(cls, weights, values):
        if not weights:
            raise ValueError('Weights list cannot be empty.')
        weight_sum = sum(weights)
        if weight_sum != 1.0:
            raise ValueError(f'Sum of weights must be 1.0, but got {weight_sum}.')
        
        # Ensure the number of weights equals the number of nodes
        number_of_nodes = values.get('number_of_nodes')
        if number_of_nodes is not None and len(weights) != number_of_nodes:
            raise ValueError(f'Number of weights must equal number_of_nodes ({number_of_nodes}), but got {len(weights)}.')
        
        return weights


def generate_random_weights(message)-> List[float]: 

    max_weights = message.max_weightings

    dirichlet_params_to_be_stored = {
    'params': [1.0] * message.number_of_nodes
    }
    new_weight_samples = np.random.dirichlet( dirichlet_params_to_be_stored['params'],
    1000)

    cleaned_results = new_weight_samples[(new_weight_samples < max_weights).all(1)]

    new_weights = cleaned_results[0]

    new_weights[-1] = 1.0 - sum(new_weights[:-1])

    return new_weights

def generate_weights_from_params(params, message): 

    max_weights = message.max_weightings

    dirichlet_params_to_be_stored = {
    'params': params
    }

    new_weight_samples = np.random.dirichlet( dirichlet_params_to_be_stored['params'],
        1000)

    cleaned_results = new_weight_samples[(new_weight_samples < max_weights).all(1)]
    new_weights = cleaned_results[0]
    new_weights[-1] = 1.0 - sum(new_weights[:-1])
    return new_weights



@app.post("/weights_gen/")
def weights_gen(message: WeightsUpdate):
    """
    pulls data from a session id, and current weight, 
    fits a dirichlet model, and samples a new set of weights. 
    """

    key_ = "session_" + message.session_id
    dirichlet_model_key_ = "dirichlet_" + key_

    max_weights = np.array(message.max_weightings)

    try: 

        resultant_data = json.loads(redis_connection.get(
                key_
            ))

        number_of_data_points = resultant_data['num_weights_collected'] 
        weight_data_list = []
        performance = []  

        for i in range(number_of_data_points):
            weight_data_list.append(resultant_data[str(i)]['weights'][0])
            performance.append(resultant_data[str(i)]['performance_metric'])

        weight_data_np = np.array(weight_data_list)
        ordered_index = np.argsort(performance)[::-1]

        weight_data_np = weight_data_np[ordered_index]

        # insert optimization 
        if len(weight_data_np) > 50:
            try:
                model_params = dirichlet.mle(weight_data_np[:20],)

                new_weights = generate_weights_from_params(model_params, message)

                return {"message": "/weights_update/: SUCCESS, model fit, generated weights",
                    "weights": list(new_weights)}

            except Exception as e: 
                
                new_weights = generate_random_weights(message)
                return {"message": "/weights_update/: SUCCESS, model failed to be fit, generated random weights",
                        "weights": list(new_weights),
                        "error":{  
                            "type": type(e).__name__,  # captures the exception type
                            "message": str(e),         # captures the exception message
                        }}

        else: 
            new_weights = generate_random_weights(message)
            return {"message": "/weights_update/: SUCCESS, not enough data, generated random weights",
                    "weights": list(new_weights)}

        # TODO fast api can run as a background task for writing data after computation. 

    except Exception as e: 
            new_weights = generate_random_weights(message)

            return {"message": "/weights_update/: FAILURE, dirichlet model key exists, but fails to be logged",
            "session_key": key_,
             "weights": list(new_weights),
              "error":{  
                            "type": type(e).__name__,  # captures the exception type
                            "message": str(e),         # captures the exception message
                        }}




@app.post("/weights_update/") 
def weights_update(message: WeightsUpdate):
    """
    connects to redis database and updates performance metrics
    """

    key_ = "session_" + message.session_id

    if redis_connection.exists(key_):
        
        # if the key exists try to load data

        try:
            resultant_data = json.loads(redis_connection.get(
                key_
            ))

            # check if nodes are the same 
            if message.number_of_nodes != resultant_data['number_of_nodes']: 
                return {"message": "/weights_update/: FAILURE, number of nodes are not the same for the session"}


            # parse data
            best_perf_metric = resultant_data['best_performance_metric']
            best_weights = resultant_data['best_weights']

            if best_perf_metric < message.performance_metric: 
                best_perf_metric = message.performance_metric 
                best_weights = message.weights

                resultant_data['best_performance_metric'] = best_perf_metric
                resultant_data['best_weights'] = best_weights

                resultant_data['num_weights_collected'] += 1

                new_key_for_data = resultant_data['num_weights_collected'] - 1
                resultant_data[new_key_for_data] = {
                    "weights": [message.weights],
                    "performance_metric": message.performance_metric
                    }

                redis_connection.set(key_, 
                    json.dumps(resultant_data)
                )
                
                return {"message": "/weights_update/: SUCCESS, best weights updated",
                "best_perf_metric": best_perf_metric,
                "best_weights": best_weights,
                "best_out_of": resultant_data['num_weights_collected'],
                }

            else:
                resultant_data['num_weights_collected'] +=1
                new_key_for_data = resultant_data['num_weights_collected'] - 1
                
                resultant_data[new_key_for_data] = {
                    "weights": [message.weights],
                    "performance_metric": message.performance_metric
                    }

                redis_connection.set(key_, 
                    json.dumps(resultant_data)
                )
                
                return {"message": "/weights_update/: SUCCESS, no change in best weights",
                "best_perf_metric": best_perf_metric,
                "best_weights": best_weights,
                "best_out_of": resultant_data['num_weights_collected']}
                
    
        except: 
            return {
                "message": "/weights_update/: FAILURE",
                "reason": f"key {key_} but no data, consider deleting it using /session_delete/"
            }

    else: 

        weight_data_to_be_stored = {
            "num_weights_collected": 1,
            "number_of_nodes": message.number_of_nodes,
            "best_performance_metric": message.performance_metric,
            "best_weights": message.weights,
            0: {"weights": [message.weights],
                "performance_metric": message.performance_metric},   
        }

        redis_connection.set(key_, 
            json.dumps(weight_data_to_be_stored)
        )

        return {"message": "/weights_update/: SUCCESS, first weights in",
                "best_perf_metric": message.performance_metric,
                "best_weights": message.weights}


@app.post("/weights_update_delete/")
def weights_update_delete(message: WeightsUpdate):
    """
    connects to redis database. 
    """

    key_ = "session_" + message.session_id


    if redis_connection.exists(key_):
        
        redis_connection.delete(key_)
        return {
            "message": f"/weights_update_delete/: SUCCESS, key {key_} deleted"
        }

    else: 

        return {
            "message": f"/weights_update_delete/: FAILURE, key {key_} not found"
            }
