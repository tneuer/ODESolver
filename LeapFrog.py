#!/home/thomas/anaconda3/bin/python

"""
    # Author : Thomas Neuer (tneuer)
    # File Name : LeapFrog.py
    # Creation Date : Son 28 Okt 2018 15:41:12 CET
    # Last Modified : Die 30 Okt 2018 14:36:45 CET
    # Description : Implement leapfrog algorithm
"""
#==============================================================================

import math
import json

import numpy as np
import matplotlib.pyplot as plt

from pprint import pprint
from numpy.linalg import norm
from collections import deque

np.set_printoptions(precision=16)

class N_Body_Gravitation_LF():
    """ Solver of PDE's via the LeapFrog method.
    Designed to solve gravitational N-Body systems.

    See https://en.wikipedia.org/wiki/Leapfrog_integration

    TODO:
        - Assertions
            - dimension of intitials
        - Plot option
        - Option to not save all but only current position (memory efficient)
        - write trajectories constantly to file
    """

    def __init__(self, dt, initials, verbose=True):
        """ Designed to solve gravitational N-Body systems.

        Arguments
        ---------
        dt : float
            Time step per integration
        initials : dict
            dict with the following keys:
                - "r": np.ndarray of dimension (n_bodies, dim)
                - "v": np.ndarray of dimension (n_bodies, dim)
                - "m": masses of the bodies
        """
        self.dt = dt
        self.pos = initials["r_init"]
        self.vel = initials["v_init"]
        self.mas = initials["masses"]
        self.mass_matrix = self.mas.reshape((1, -1, 1))*self.mas.reshape((-1, 1, 1))
        self.G = 6.67428e-11
        self.alreadyRun = False
        self.verbose = verbose
        self.dim = self.pos.shape[1]

    def evolve(self, steps, t_end=None, saveOnly=None, mass_sun=None):
        """ Evolves the system according to the potential.

        Either steps XOR t_end is needed.

        Arguments
        ---------
        steps : int [None]
            Evolve the system for "steps" steps.
        t_end : float [None]
            Evolve the system up to this time.

        Returns
        -------
        trajectories : np.ndarray
            Array of the same shape as initials["r"] across a third dimension representing
            time. So each element of the trajectories array is an array of shape (n_bodies, dim),
            indicating the current position.
        velocities : np.ndarray
            Array of the same shape as initials["v"] across a third dimension representing
            time. So each element of the trajectories array is an array of shape (n_bodies, dim),
            indicating the current velocity.
        times : np.ndarray
            One dimensional array indicating the timestamp of each step.
        energies : np.ndarray
            Array of shape (2, steps), giving kinetic and potential energy of the system at every timestep

        """
        if steps is None and t_end is not None:
            self.steps = int(np.ceil(t_end/self.dt))
            self.t_end = t_end
        elif t_end is None and steps is not None:
            self.steps = steps
            self.t_end = self.dt*steps
        else:
            raise ValueError("Need either steps OR t_end (excluse or).")

        if self.alreadyRun:
            self.pos = self.posCollect[-1]
            self.vel = self.velCollect[-1]

            if saveOnly != self.posCollect.maxlen:
                self.posCollect = deque(self.posCollect, maxlen=saveOnly)
                self.velCollect = deque(self.velCollect, maxlen=saveOnly)
                self.forces = deque(self.forces, maxlen=saveOnly)
                self.timesteps = deque(self.timesteps, maxlen=saveOnly)
                self.energies = deque(self.energies, maxlen=saveOnly)
        else:
            # Initializing of deques
            self.disps, self.dists = self.get_relative_distances()

            self.posCollect = deque([self.pos], maxlen=saveOnly)
            self.velCollect = deque([self.vel], maxlen=saveOnly)
            self.forces = deque(maxlen=saveOnly)
            self.timesteps = deque([0], maxlen=saveOnly)
            self.energies = deque([
                self.get_kinetic_energy_of_system(),
                self.get_potential_energy_of_system()
                ], maxlen=saveOnly)

            self.acc = self.get_next_acc()
            self.vel = self.vel + 0.5 * self.acc * self.dt

        if mass_sun is not None:
            sun_index = np.argmax(self.mas)
            self.mas[sun_index] = mass_sun
            self.mass_matrix = self.mas.reshape((1, -1, 1))*self.mas.reshape((-1, 1, 1))


        for step in range(steps):
            # Actual calulation: Leapfrog
            self.pos = self.pos + self.vel * self.dt
            self.disps, self.dists = self.get_relative_distances()
            self.acc = self.get_next_acc()
            self.vel = self.vel + self.acc * self.dt

            # Saving of statistics
            self.posCollect.append(self.pos)
            self.velCollect.append(self.vel)
            self.timesteps.append(self.timesteps[-1] + self.dt)
            self.energies.append([
                self.get_kinetic_energy_of_system(),
                self.get_potential_energy_of_system()
                ])

            if self.verbose and step % 500 == 0:
                print(step, "/", steps)

        self.alreadyRun = True
        return self.posCollect, self.velCollect, self.timesteps, self.energies, self.forces

    def get_relative_distances(self):
        disps = self.pos.reshape((1, -1, self.dim)) - self.pos.reshape((-1, 1, self.dim))
        dists = norm(disps, axis=2)
        dists[dists == 0] = np.inf # Avoid divide by zero warnings
        return disps, dists

    def get_next_acc(self):
        forces = self.G*self.disps*self.mass_matrix/np.expand_dims(self.dists, 2)**3
        forces_per_particle = forces.sum(axis=1)
        self.forces.append(forces_per_particle)
        return forces_per_particle/self.mas.reshape(-1, 1)

    def get_kinetic_energy_of_system(self):
        velocities_squared = (self.vel**2).sum(axis=1)
        individual_kin_energies = velocities_squared * self.mas
        return individual_kin_energies.sum()

    def get_potential_energy_of_system(self):
        individual_pot_energies = -self.mass_matrix/np.expand_dims(self.dists, 2)
        return individual_pot_energies.sum()

if __name__ == "__main__":

    with open("./initial.json", "r") as f:
        initials = json.load(f)

    masses = []
    r_init = []
    v_init = []
    colors = []

    for key, value in initials.items():
        if key in ["Sun", "Earth", "Jupiter", "Mars"]:
            masses.append(value["mass"])
            r_init.append(value["r_init"][:2])
            v_init.append(value["v_init"][:2])
            colors.append(value["color"])

    masses = np.array(masses); r_init = np.array(r_init); v_init = np.array(v_init)
    r_max = np.max(r_init)

    initials = {
            "r": r_init,
            "v": v_init,
            "m": masses
            }
    pprint(initials)
    dt = 60*60*24

    leapfrog = N_Body_Gravitation_LF(dt, initials, verbose=False)

    positions, velocities, timesteps, energies, forces = leapfrog.evolve(steps=365, saveOnly=None)

    fig = plt.figure()
    fig.tight_layout()
    ax = plt.axes(xlim=(-r_max, r_max), ylim=(-r_max, r_max))
    ax.set_facecolor("k")
    ax.axis("off")
    fig.patch.set_facecolor("k")
    for i, (position, force) in enumerate(zip(positions, forces)):
        if i % 1 == 0:
            xs = position[:, 0]
            ys = position[:, 1]
            plt.scatter(xs, ys, color=colors)

            # fxs = force[1, 0]/1e12
            # fys = force[1, 1]/1e12
            # plt.arrow(xs[1], ys[1], fxs, fys)

        if i % 500 == 0:
            print(i, "/", len(timesteps))
    plt.show()

    # fig = plt.figure()
    # for i in range(1000):
    #     position, _, _, _, force = leapfrog.evolve(steps=1, saveOnly=365)
    #     if i % 1 == 0:
    #         xs = position[-1][:, 0]
    #         ys = position[-1][:, 1]
    #         plt.scatter(xs, ys, color=["b", "r", "y"])
    # 
    #         fxs, fys = force[-1][1, :]/1e12
    #         plt.arrow(xs[1], ys[1], fxs, fys)
    # 
    #     if i % 500 == 0:
    #         print(i, "/", 364)
    # 
    # plt.show()



