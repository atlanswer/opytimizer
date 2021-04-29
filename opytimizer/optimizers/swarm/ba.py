"""Bat Algorithm.
"""

import copy

import numpy as np
from tqdm import tqdm

import opytimizer.math.random as rnd
import opytimizer.utils.exception as ex
import opytimizer.utils.history as h
import opytimizer.utils.logging as l
from opytimizer.core.optimizer import Optimizer

logger = l.get_logger(__name__)


class BA(Optimizer):
    """A BA class, inherited from Optimizer.

    This is the designed class to define BA-related
    variables and methods.

    References:
        X.-S. Yang. A new metaheuristic bat-inspired algorithm.
        Nature inspired cooperative strategies for optimization (2010).

    """

    def __init__(self, params=None):
        """Initialization method.

        Args:
            params (dict): Contains key-value parameters to the meta-heuristics.

        """

        logger.info('Overriding class: Optimizer -> BA.')

        # Overrides its parent class with the receiving params
        super(BA, self).__init__()

        # Minimum frequency range
        self.f_min = 0

        # Maximum frequency range
        self.f_max = 2

        # Loudness parameter
        self.A = 0.5

        # Pulse rate
        self.r = 0.5

        # Builds the class
        self.build(params)

        logger.info('Class overrided.')

    @property
    def f_min(self):
        """float: Minimum frequency range.

        """

        return self._f_min

    @f_min.setter
    def f_min(self, f_min):
        if not isinstance(f_min, (float, int)):
            raise ex.TypeError('`f_min` should be a float or integer')
        if f_min < 0:
            raise ex.ValueError('`f_min` should be >= 0')

        self._f_min = f_min

    @property
    def f_max(self):
        """float: Maximum frequency range.

        """

        return self._f_max

    @f_max.setter
    def f_max(self, f_max):
        if not isinstance(f_max, (float, int)):
            raise ex.TypeError('`f_max` should be a float or integer')
        if f_max < 0:
            raise ex.ValueError('`f_max` should be >= 0')
        if f_max < self.f_min:
            raise ex.ValueError('`f_max` should be >= `f_min`')

        self._f_max = f_max

    @property
    def A(self):
        """float: Loudness parameter.

        """

        return self._A

    @A.setter
    def A(self, A):
        if not isinstance(A, (float, int)):
            raise ex.TypeError('`A` should be a float or integer')
        if A < 0:
            raise ex.ValueError('`A` should be >= 0')

        self._A = A

    @property
    def r(self):
        """float: Pulse rate.

        """

        return self._r

    @r.setter
    def r(self, r):
        if not isinstance(r, (float, int)):
            raise ex.TypeError('`r` should be a float or integer')
        if r < 0:
            raise ex.ValueError('`r` should be >= 0')

        self._r = r

    def _update_frequency(self, min_frequency, max_frequency):
        """Updates an agent frequency (eq. 2).

        Args:
            min_frequency (float): Minimum frequency range.
            max_frequency (float): Maximum frequency range.

        Returns:
            A new frequency.

        """

        # Generating beta random number
        beta = rnd.generate_uniform_random_number()

        # Calculating new frequency
        # Note that we have to apply (min - max) instead of (max - min) or it will not converge
        new_frequency = min_frequency + (min_frequency - max_frequency) * beta

        return new_frequency

    def _update_velocity(self, position, best_position, frequency, velocity):
        """Updates an agent velocity (eq. 3).

        Args:
            position (np.array): Agent's current position.
            best_position (np.array): Global best position.
            frequency (float): Agent's frequency.
            velocity (np.array): Agent's current velocity.

        Returns:
            A new velocity.

        """

        # Calculates new velocity
        new_velocity = velocity + (position - best_position) * frequency

        return new_velocity

    def _update_position(self, position, velocity):
        """Updates an agent position (eq. 4).

        Args:
            position (np.array): Agent's current position.
            velocity (np.array): Agent's current velocity.

        Returns:
            A new position.

        """

        # Calculates new position
        new_position = position + velocity

        return new_position

    def update(self, agents, best_agent, function, iteration, frequency, velocity, loudness, pulse_rate):
        """Wraps Bat Algorithm over all agents and variables.

        Args:
            agents (list): List of agents.
            best_agent (Agent): Global best agent.
            function (Function): A function object.
            iteration (int): Current iteration value.
            frequency (np.array): Array of frequencies.
            velocity (np.array): Array of current velocities.
            loudness (np.array): Array of loudnesses.
            pulse_rate (np.array): Array of pulse rates.

        """

        # Declaring alpha constant
        alpha = 0.9

        # Iterates through all agents
        for i, agent in enumerate(agents):
            # Updates frequency
            frequency[i] = self._update_frequency(self.f_min, self.f_max)

            # Updates velocity
            velocity[i] = self._update_velocity(agent.position, best_agent.position, frequency[i], velocity[i])

            # Updates agent's position
            agent.position = self._update_position(agent.position, velocity[i])

            # Generating a random probability
            p = rnd.generate_uniform_random_number()

            # Generating a random number
            e = rnd.generate_gaussian_random_number()

            # Check if probability is bigger than current pulse rate
            if p > pulse_rate[i]:
                # Performing a local random walk (eq. 5)
                # We apply 0.001 to limit the step size
                agent.position = best_agent.position + 0.001 * e * np.mean(loudness)

            # Checks agent limits
            agent.clip_by_bound()

            # Evaluates agent
            agent.fit = function(agent.position)

            # Checks if probability is smaller than loudness and if fit is better
            if p < loudness[i] and agent.fit < best_agent.fit:
                # Copying the new solution to space's best agent
                best_agent = copy.deepcopy(agent)

                # Increasing pulse rate (eq. 6)
                pulse_rate[i] = self.r * (1 - np.exp(-alpha * iteration))

                # Decreasing loudness (eq. 6)
                loudness[i] = self.A * alpha

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

        # Instanciating array of frequencies, velocities, loudness and pulse rates
        frequency = rnd.generate_uniform_random_number(self.f_min, self.f_max, space.n_agents)
        velocity = np.zeros((space.n_agents, space.n_variables, space.n_dimensions))
        loudness = rnd.generate_uniform_random_number(0, self.A, space.n_agents)
        pulse_rate = rnd.generate_uniform_random_number(0, self.r, space.n_agents)

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
                self._update(space.agents, space.best_agent, function, t, frequency, velocity, loudness, pulse_rate)

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
