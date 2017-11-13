"""This is the search space's structure and its basic functions module.
"""

import json

import numpy as np

import opytimizer.core.agent as Agent
import opytimizer.optimizers.pso as PSO


class SearchSpace(object):
    """ A SearchSpace class for running meta-heuristic optimization
        techniques.

        # Argument
            model_path: JSON model file containing all the needed information
            to create a Search Space.

        # Properties
            agent: List of agents.
            optimizer: Choosen optimizer algorithm.
            hyperparams: Search space-related hyperparams.

        # Methods

        # Class Methods

        # Internal Methods
    """

    def __init__(self, **kwargs):
        # These properties will be set upon call of self.build()
        self._built = False

        allowed_kwargs = {'model_path'
                         }
        for kwarg in kwargs:
            if kwarg not in allowed_kwargs:
                raise TypeError('Keyword argument not understood:', kwarg)

        if 'model_path' in kwargs:
            model_path = kwargs['model_path']
            with open(model_path) as json_file:
                model = json.load(json_file)
        else:
            raise Exception(
                'Json file is missing. Please include the argument model_path.')

        # Gathering JSON keywords
        n_agents = model['n_agents']
        n_variables = model['agent']['n_variables']
        n_dimensions = model['agent']['n_dimensions']
        optimizer = model['optimizer']['algorithm']
        optimizer_hyperparams = model['optimizer']['hyperparams']
        hyperparams = model['hyperparams']

        # Applying variables to their corresponding creations
        self.agent = [Agent.Agent(n_variables=n_variables,
                                  n_dimensions=n_dimensions) for _ in range(n_agents)]
        if optimizer == 'PSO':
            self.optimizer = PSO.PSO(hyperparams=optimizer_hyperparams)
        self.hyperparams = hyperparams
