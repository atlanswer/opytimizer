"""Satin Bowerbird Optimizer.
"""

import numpy as np
from tqdm import tqdm

import opytimizer.math.distribution as d
import opytimizer.math.random as r
import opytimizer.utils.exception as e
import opytimizer.utils.history as h
import opytimizer.utils.logging as l
from opytimizer.core.optimizer import Optimizer

logger = l.get_logger(__name__)


class SBO(Optimizer):
    """A SBO class, inherited from Optimizer.

    This is the designed class to define SBO-related
    variables and methods.

    References:
        S. H. S. Moosavi and V. K. Bardsiri.
        Satin bowerbird optimizer: a new optimization algorithm to optimize ANFIS
        for software development effort estimation.
        Engineering Applications of Artificial Intelligence (2017).

    """

    def __init__(self, params=None):
        """Initialization method.

        Args:
            params (dict): Contains key-value parameters to the mp_mutation-heuristics.

        """

        # Overrides its parent class with the receiving params
        super(SBO, self).__init__()

        # Step size
        self.alpha = 0.9

        # Probability of mutation
        self.p_mutation = 0.05

        # Percentage of width between lower and upper bounds
        self.z = 0.02

        # Builds the class
        self.build(params)

        logger.info('Class overrided.')

    @property
    def alpha(self):
        """float: Step size.

        """

        return self._alpha

    @alpha.setter
    def alpha(self, alpha):
        if not isinstance(alpha, (float, int)):
            raise e.TypeError('`alpha` should be a float or integer')
        if alpha < 0:
            raise e.ValueError('`alpha` should be >= 0')

        self._alpha = alpha

    @property
    def p_mutation(self):
        """float: Probability of mutation.

        """

        return self._p_mutation

    @p_mutation.setter
    def p_mutation(self, p_mutation):
        if not isinstance(p_mutation, (float, int)):
            raise e.TypeError('`p_mutation` should be a float or integer')
        if p_mutation < 0 or p_mutation > 1:
            raise e.ValueError('`p_mutation` should be between 0 and 1')

        self._p_mutation = p_mutation

    @property
    def z(self):
        """float: Percentage of width between lower and upper bounds.

        """

        return self._z

    @z.setter
    def z(self, z):
        if not isinstance(z, (float, int)):
            raise e.TypeError('`z` should be a float or integer')
        if z < 0 or z > 1:
            raise e.ValueError('`z` should be between 0 and 1')

        self._z = z

    def update(self, agents, best_agent, function, sigma):
        """Wraps updates over all agents and variables (eq. 1-7).

        Args:
            agents (list): List of agents.
            best_agent (Agent): Global best agent.
            function (Function): A Function object that will be used as the objective function.
            sigma (list): Width between lower and upper bounds.

        """

        # Calculates a list of fitness per agent
        fitness = [1 / (1 + agent.fit) if agent.fit >= 0 else 1 + np.abs(agent.fit) for agent in agents]

        # Calculates the total fitness
        total_fitness = np.sum(fitness)

        # Calculates the probability of each agent's fitness
        probs = [fit / total_fitness for fit in fitness]

        # Iterates through all agents
        for agent in agents:
            # For every decision variable
            for j in range(agent.n_variables):
                # Selects a random individual based on its probability
                s = d.generate_choice_distribution(len(agents), probs, 1)[0]

                # Calculates the lambda factor
                lambda_k = self.alpha / (1 + probs[s])

                # Updates the decision variable position
                agent.position[j] += lambda_k * ((agents[s].position[j] + best_agent.position[j]) / 2 - agent.position[j])

                # Generates an uniform random number
                r1 = r.generate_uniform_random_number()

                # If random number is smaller than probability of mutation
                if r1 < self.p_mutation:
                    # Mutates the decision variable position
                    agent.position[j] += sigma[j] * r.generate_gaussian_random_number()

            # Checks agent's limits
            agent.clip_by_bound()

            # Calculates its fitness
            agent.fit = function(agent.position)

    def run(self, space, function, store_best_only=False, pre_evaluate=None):
        """Runs the optimization pipeline.

        Args:
            space (Space): A Space object that will be evaluated.
            function (Function): A Function object that will be used as the objective function.
            store_best_only (bool): If True, only the best agent of each iteration is stored in History.
            pre_evaluate (callable): This function is executed before evaluating the function being optimized.

        Returns:
            A History object holding all agents' positions and fitness achieved during the task.

        """

        # Calculates the width between lower and upper bounds
        sigma = [self.z * (ub - lb) for lb, ub in zip(space.lb, space.ub)]

        # Initial search space evaluation
        self._evaluate(space, function, hook=pre_evaluate)

        # We will define a History object for further dumping
        history = h.History(store_best_only)

        # Initializing a progress bar
        with tqdm(total=space.n_iterations) as b:
            # These are the number of iterations to converge
            for t in range(space.n_iterations):
                logger.to_file(f'Iteration {t+1}/{space.n_iterations}')

                # Updates agents
                self._update(space.agents, space.best_agent, function, sigma)

                # Checks if agents meet the bounds limits
                space.clip_by_bound()

                # After the update, we need to re-evaluate the search space
                self._evaluate(space, function, hook=pre_evaluate)

                # Every iteration, we need to dump agents and best agent
                history.dump(agents=space.agents, best_agent=space.best_agent)

                # Updates the `tqdm` status
                b.set_postfix(fitness=space.best_agent.fit)
                b.update()

                logger.to_file(f'Fitness: {space.best_agent.fit}')
                logger.to_file(f'Position: {space.best_agent.position}')

        return history
