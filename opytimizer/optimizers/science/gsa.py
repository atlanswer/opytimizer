"""Gravitational Search Algorithm.
"""

import numpy as np
from tqdm import tqdm

import opytimizer.math.general as g
import opytimizer.math.random as r
import opytimizer.utils.constant as c
import opytimizer.utils.exception as e
import opytimizer.utils.history as h
import opytimizer.utils.logging as l
from opytimizer.core.optimizer import Optimizer

logger = l.get_logger(__name__)


class GSA(Optimizer):
    """A GSA class, inherited from Optimizer.

    This is the designed class to define GSA-related
    variables and methods.

    References:
        E. Rashedi, H. Nezamabadi-Pour and S. Saryazdi. GSA: a gravitational search algorithm.
        Information Sciences (2009).

    """

    def __init__(self, params=None):
        """Initialization method.

        Args:
            params (dict): Contains key-value parameters to the meta-heuristics.

        """

        logger.info('Overriding class: Optimizer -> GSA.')

        # Overrides its parent class with the receiving params
        super(GSA, self).__init__()

        # Initial gravity value
        self.G = 2.467

        # Builds the class
        self.build(params)

        logger.info('Class overrided.')

    @property
    def G(self):
        """float: Initial gravity.

        """

        return self._G

    @G.setter
    def G(self, G):
        if not isinstance(G, (float, int)):
            raise e.TypeError('`G` should be a float or integer')
        if G < 0:
            raise e.ValueError('`G` should be >= 0')

        self._G = G

    def _calculate_mass(self, agents):
        """Calculates agents' mass (eq. 16).

        Args:
            agents (list): List of agents.

        Returns:
            The agents' mass.

        """

        # Gathers the best and worst agents
        best, worst = agents[0].fit, agents[-1].fit

        # Calculating agents' masses using equation 15
        mass = [(agent.fit - worst) / (best - worst) for agent in agents]

        # Normalizing agents' masses
        norm_mass = mass / np.sum(mass)

        return norm_mass

    def _calculate_force(self, agents, mass, gravity):
        """Calculates agents' force (eq. 7-9).

        Args:
            agents (list): List of agents.
            mass (np.array): An array of agents' mass.
            gravity (float): Current gravity value.

        Returns:
            The attraction force between all agents.

        """

        # Calculates the force
        force = [[gravity * (mass[i] * mass[j]) / (g.euclidean_distance(agents[i].position, agents[j].position) + c.EPSILON)
                  * (agents[j].position - agents[i].position) for j in range(len(agents))] for i in range(len(agents))]

        # Transforms the force into an array
        force = np.asarray(force)

        # Applying a stochastic trait to the force
        force = np.sum(r.generate_uniform_random_number() * force, axis=1)

        return force

    def _update_velocity(self, force, mass, velocity):
        """Updates an agent velocity (eq. 11).

        Args:
            force (np.array): Matrix of attraction forces.
            mass (np.array): An array of agents' mass.
            velocity (np.array): Agent's current velocity.

        Returns:
            A new velocity.

        """

        # Calculates the acceleration using paper's equation 10
        acceleration = force / (mass + c.EPSILON)

        # Calculates the new velocity
        new_velocity = r.generate_uniform_random_number() * velocity + acceleration

        return new_velocity

    def _update_position(self, position, velocity):
        """Updates an agent position (eq. 12).

        Args:
            position (np.array): Agent's current position.
            velocity (np.array): Agent's current velocity.

        Returns:
            A new position.

        """

        # Calculates new position
        new_position = position + velocity

        return new_position

    def update(self, agents, velocity, iteration):
        """Method that wraps Gravitational Search Algorithm over all agents and variables.

        Args:
            agents (list): List of agents.
            velocity (np.array): Array of current velocities.
            iteration (int): Current iteration value.

        """

        # Sorting agents
        agents.sort(key=lambda x: x.fit)

        # Calculating the current gravity
        gravity = self.G / (iteration + 1)

        # Calculating agents' mass
        mass = self._calculate_mass(agents)

        # Calculating agents' attraction force
        force = self._calculate_force(agents, mass, gravity)

        # Iterates through all agents
        for i, agent in enumerate(agents):
            # Updates current agent velocities
            velocity[i] = self._update_velocity(force[i], mass[i], velocity[i])

            # Updates current agent positions
            agent.position = self._update_position(agent.position, velocity[i])

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

        # Creates an array of velocities
        velocity = np.zeros((space.n_agents, space.n_variables, space.n_dimensions))

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
                self._update(space.agents, velocity, t)

                # Checking if agents meet the bounds limits
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
