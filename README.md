# ODESolver

### Description

This is a full set of solvers for the gravitational N-Body problems, solved for small systems with the typical Integrators Leapfrog, Runge-Kutta 2 and Runge-Kutta 4.

* The NBody_Solver.py file implements a parent class for all the others, which handles initialization (read-in) of the initial values, the time step and the reuse of older initial values . The children need to implement a get_next_steps(self, steps) method, where positions and velocities are calculated. In the for-loop the save_system_information(self, positions, velocities) needs to be called after every iteration.
* The LeapFrog.py module implements the leapfrog method solver.
* The RungeKutta2.py module implements the Runge-Kutta 2 solver.
* The RungeKutta4.py module implements the Runge-Kutta 4 solver.



* The Comparator.py module implements a class which compares the performance of the solvers in terms of energy and runtime. As input it takes a dictonary of solvers, the timestep and the number of steps.
  * The compare method evaluates the solvers for the given steps
  * Planet Earth is shown as comparison planet for the trajectories
  * The results can be directly saved



![Energies](/home/tneuer/Algorithmen/NBodySolver/Energies_500k.png)



![Trajectories](/home/tneuer/Algorithmen/NBodySolver/Trajectories_500k.png)



#### Dependencies

- .json
- color
- Dash



``` bash
# Color package
>> pip install color

# json package
>> pip install json

# Dash (from https://dash.plot.ly/installation)
>> pip install dash==0.28.5  # The core dash backend
>> pip install dash-html-components==0.13.2  # HTML components
>> pip install dash-core-components==0.35.1  # Supercharged components
```





##### TODO

- ~~Implements logartihmic mass scaling for point size~~
- ~~Dark background colour~~
- Destruction of colliding planets
- add Planet live
- ~~Change mass of sun~~
- ~~planets get smaller with bigger scale~~
- show planet position before adding
- draw every quarter year where earth should be
- ~~refactor with Superclass ODESOLVER~~
- Comparison to true values in sun-earth system --> error calculation

