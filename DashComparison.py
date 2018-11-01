#!/home/thomas/anaconda3/bin/python

"""
    # Author : Thomas Neuer (tneuer)
    # File Name : DashComparison.py
    # Creation Date : Mon 29 Okt 2018 15:20:38 CET
    # Last Modified : Don 01 Nov 2018 02:18:23 CET
    # Description : Compares the results of the NBodySolvers for comparison.
"""
#==============================================================================

import os
import re
import time
import dash
import json
import random

import numpy as np
import plotly.graph_objs as go
import dash_core_components as dcc
import dash_html_components as html

from shutil import copyfile
from collections import deque
from dash.dependencies import Input, Output, Event, State

from LeapFrog import N_Body_Gravitation_LF
from RungeKutta2 import N_Body_Gravitation_RK2
from RungeKutta4 import N_Body_Gravitation_RK4
from NBody_solver import N_Body_Gravitationsolver as BaseSolver

####
# Global variables
####

SOLVER = {}
INITIALS = 0
DT = 60*60*24*4
RUNNING = False
CLICKS_START = 0
CLICKS_RESET = 0
M_SUN = 1.98892e30
INITIALFILE = "./user_initials.json"
CURRENTFILE = "./user_current.json"
DEFAULTPLANETS = ["earth", "venus", "mercury"]

####
# Construct a copy of the initial file, where user planets are appended
####
if not os.path.exists("./user_initials.json"):
    copyfile("./default_initial.json", INITIALFILE)

app = dash.Dash("vehicle_data")

app.layout = html.Div([
    html.H1(
            children='N-Body Solvers',
            style={
                'float': 'center',
                'textAlign': 'center',
                }
            ),

    html.Div([
        ####
        # Dropdown menu for planet selection
        ####
        html.Div([
            html.Div(children="Available planets:"),

            html.Div(id="div_dd_planets", children=dcc.Dropdown(
                id='dd_planets',
                options=[
                    {'label': "Sun", 'value': "sun"},
                    {'label': "Mercury", 'value': "mercury"},
                    {'label': "Venus", 'value': "venus"},
                    {'label': "Earth", 'value': "earth"},
                    {'label': "Mars", 'value': "mars"},
                    {'label': "Jupiter", 'value': "jupiter"},
                    {'label': "Saturn", 'value': "saturn"},
                    {'label': "Uranus", 'value': "uranus"},
                    {'label': "Neptune", 'value': "neptune"},
                    ],
                value=DEFAULTPLANETS,
                multi=True,
                style={"marginTop": "50px"}
                )),
            ],
            className="eight columns"),

        ####
        # Environment for entering custom planet
        ####
        html.Div([
            html.Div([
                html.Div([
                    html.Div("Bodyname", style={"textAlign": "center"}),
                    html.Div("x-init [AU]", style={"textAlign": "center", "marginTop": "3px"}),
                    html.Div("y-init [AU]", style={"textAlign": "center", "marginTop": "3px"}),
                    html.Div("z-init [AU]", style={"textAlign": "center", "marginTop": "3px"}),
                    html.Div("Colour [HTML]", style={"textAlign": "center", "marginTop": "3px"})
                    ],
                    className="three columns"),
                html.Div([
                    dcc.Input(id="bodyname", style={"width": "90%", "padding": "0px"}, value="Custom1"),
                    dcc.Input(id="xpos", style={"width": "90%", "padding": "0px"}),
                    dcc.Input(id="ypos", style={"width": "90%", "padding": "0px"}, value=0),
                    dcc.Input(id="zpos", style={"width": "90%", "padding": "0px"}, value=0),
                    dcc.Input(id="pcolor", style={"width": "90%", "padding": "0px"}),
                    ],
                    className="three columns"),
                html.Div([
                    html.Div("Bodymass [kg]", style={"textAlign": "center", "marginTop": "3px"}),
                    html.Div("vx-init [AU]", style={"textAlign": "center", "marginTop": "3px"}),
                    html.Div("vy-init [m/s]", style={"textAlign": "center", "marginTop": "3px"}),
                    html.Div("vz-init [m/s]", style={"textAlign": "center", "marginTop": "3px"}),
                    html.Button(id="AddPlanet", children="AddPlanet", style={"marginTop": "30px"})
                    ],
                    className="three columns"),
                html.Div([
                    dcc.Input(id="bodymass", style={"width": "90%", "padding": "0px"}),
                    dcc.Input(id="xvel", style={"width": "90%", "padding": "0px"}, value=0),
                    dcc.Input(id="yvel", style={"width": "90%", "padding": "0px"}),
                    dcc.Input(id="zvel", style={"width": "90%", "padding": "0px"}, value=0),
                    ],
                    className="three columns"),
                ],
                className="row")
            ],
            className="four columns"),
        ],
        className='row'),

    ####
    # Select integrator algorithm
    ####
    html.Div([
        html.Div(style={"marginTop": "10px"}),
        dcc.Checklist(
            id = "Solver",
            options=[
                {"label": "Leapfrog", "value": "LF"},
                {"label": "Runge-Kutta 2", "value": "RK2"},
                {"label": "Runge-Kutta 4", "value": "RK4"},
                ],
            values = ["LF"],
            labelStyle= {
                "display": "inline-block",
                "width": "200px",
                }
            ),
        ]),

    ####
    # Trajectories and energy is plotted here
    ####
    html.Div(
        children=html.Div(id='graphs'),
        ),
    dcc.Interval(id="graph-update", interval=1e8),

    ####
    # Plot function like Start_Stop, sun_mass, stepsise and drag
    ####
    html.Div([
        html.Div(id="StartStopButton", children=html.Button(
            id="start_stop",
            children="Start",
            style={"background-color": "#00F240"},
            className="two columns")),
        html.Button(id="reset", children="Reset", className="two columns"),

        html.Div(dcc.Slider(
            id="sun_mass",
            marks={i: "{}".format(np.round(10**i, 2)) for i in np.arange(-0.9, 0.9, 0.3)},
            min=-1,
            max=1,
            value=0,
            step=0.2,
            ), className="four columns"),

        html.Div(children="Timestep", className="one column"),
        html.Div(dcc.Input(
                    id="timestep",
                    value=DT,
                    style={"width": "95%", "padding": "0px"}
                    ),
                className="one column",
                style={"marginLeft": "-10px"}
                ),

        html.Div(children="Drag", className="one column"),
        html.Div(dcc.Input(
                    id="drag",
                    value=1,
                    style={"width": "95%", "padding": "0px"}
                    ),
                className="one column",
                style={"marginLeft": "-20px"}
                ),
        ],
        className="row"),

    html.Div(id="Trash1") # Pseudooutput from update_initials_from_json callback()
    ],
    style={
        'width':'98%',
        'margin-left':10,
        'margin-right':10,
        'max-width':50000},
    )



@app.callback(
        Output("StartStopButton", "children"),
        [Input("start_stop", "n_clicks"), Input("reset", "n_clicks")],
        [State("start_stop", "children")])
def change_start_to_stop_Button(clicks_start, clicks_reset, status):
    """ Changes green Start button to red Stop button when clicked and vice versa.

    A reset click changes from Stop to Start button, but leaves Start button unchanged.
    """
    global RUNNING
    if status == "Stop" or clicks_start is None:
        RUNNING = False
        button = html.Button(
            id="start_stop",
            children="Start",
            style={"background-color": "#00F240"},
            className="two columns")
        return button

    else:
        RUNNING = True
        button = html.Button(
            id="start_stop",
            children="Stop",
            style={"background-color": "#FF0000"},
            className="two columns")
        return button


@app.callback(
        Output("div_dd_planets", "children"),
        [Input("AddPlanet", "n_clicks")],
        [State("dd_planets", "value"), State("dd_planets", "options"),
        State("bodyname", "value"), State("bodymass", "value"),
        State("xpos", "value"), State("ypos", "value"), State("zpos", "value"),
        State("xvel", "value"), State("yvel", "value"), State("zvel", "value"),
        State("pcolor", "value")]
        )
def update_dropdown_planets(clicks, values, options, *args):
    """ If the "Add Planet" button is pressed, the dropdown menu for the planets gets updated.

    First the input is checked for consistency:
        - bodyname : str
        - bodymass : float
        - xpos/ypos/zpos : float
        - xvel/yvel/zvel : float
        - pcolor : color

    The resulting change of the dropdown menu leads to the call of
    the callback update_initials_from_json(), which stores the new planet in both the files
    ./user_initials.json and ./user_current
    """
    global INITIALS

    correct_planet_format = transform_user_planet_input(args)
    if correct_planet_format: #Planet is accepted and added to ./user_current.json
        name = correct_planet_format["name"]
        options += [{"label": name, "value": name.lower()}]
        values += [name.lower()]
        INITIALS[name] = {
                "mass": correct_planet_format["mass"],
                "r_init": correct_planet_format["r_init"],
                "v_init": correct_planet_format["v_init"],
                "color": correct_planet_format["color"]
                }

    # if False: return old dropdown menu
    dropdown_menu = dcc.Dropdown(
        id='dd_planets',
        options=options,
        value=values,
        multi=True,
        style={"marginTop": "50px"}
        )

    return dropdown_menu


def transform_user_planet_input(user_input):
    """ Check if the user input for the new body has the correct datatype

    Needed:
        - bodyname : str
        - bodymass : float
        - xpos/ypos/zpos : float
        - xvel/yvel/zvel : float
        - pcolor : color
    """
    planet_info = {}
    try:
        planet_info["name"] = user_input[0]
        planet_info["mass"] = np.float(user_input[1])
        planet_info["r_init"] = [
                np.float(user_input[2]),
                np.float(user_input[3]),
                np.float(user_input[4])]
        planet_info["v_init"] = [
                np.float(user_input[5]),
                np.float(user_input[6]),
                np.float(user_input[7])]
        planet_info["color"] = re.search("#[0-F]{6}", user_input[8]).group(0)

        return planet_info

    except (TypeError, ValueError, AttributeError):
        print("Following types need to be provided:\n"+
                "\t- bodyname : str"+
                "\t- bodymass : float"+
                "\t- xpos/ypos/zpos : float"+
                "\t- xvel/yvel/zvel : float"+
                "\t- pcolor : HTML-color (#[0-F]{6})"
            )
        return False


@app.callback(output=Output("Trash1", "children"), inputs=[Input("dd_planets", "value")])
def update_initials_from_json(bodies):
    """ Gets triggered if a user changes the dropdown for the planets.

    Initializes the ./user_current.json file if not already existing and reads initials
    Also updates when new planet is added, as this also drops the dropdown menu.
    """
    global INITIALS

    ####
    # Save into ./user_current.json
    ####
    if not os.path.exists("./user_current.json"): #Initializes ./user_current.json
        copyfile("./user_initials.json", "./user_current.json")
        INITIALS = BaseSolver.read_initials_from_json("./user_current.json")
    else:
        updated_current = {}
        print("SHOULD HER, \n\n\n", INITIALS)
        for i, body in enumerate(INITIALS["names"]):
            updated_current[body] = {
                    "mass": INITIALS["masses"][i],
                    "r_init": list(INITIALS["r_init"][i].astype(float)),
                    "v_init": list(INITIALS["v_init"][i].astype(float)),
                    "color": INITIALS["colors"][i]
                    }
        updated_current = json.dumps(updated_current)
        with open("./user_current.json", "w") as f:
            f.write(updated_current)

        ####
        # Save into ./user_initials.json
        ####
        with open("./user_current.json", "r") as f:
            user_initial = json.load(f)
        for body in bodies:
            if body not in user_initial:
                user_initial[body] = {
                    "mass": updated_current[body]["mass"],
                    "r_init": updated_current[body]["r_init"],
                    "v_init": updated_current[body]["v_init"],
                    "color": updated_current[body]["color"]
                    }
        updated_initials = json.dumps(user_initial)
        with open("./user_initials.json", "w") as f:
            f.write(updated_initials)

        INITIALS = BaseSolver.read_initials_from_json("./user_current.json")

    ####
    # Update initials for dropped planets
    ####
    to_delete = []
    for i, selected_body in enumerate(INITIALS["names"]):
        if selected_body not in bodies:
            to_delete.append(i)

    INITIALS["names"] = np.delete(INITIALS["names"], i)
    INITIALS["masses"] = np.delete(INITIALS["masses"], i)
    INITIALS["r_init"] = np.delete(INITIALS["r_init"], i)
    INITIALS["v_init"] = np.delete(INITIALS["v_init"], i)
    INITIALS["colors"] = np.delete(INITIALS["colors"], i)


@app.callback(
        Output("graph-update", "interval"),
        [Input("start_stop", "n_clicks"), Input("reset", "n_clicks")],
        [State("graph-update", "interval"), State("Solver", "values")]
        )
def control_Animation(start_clicks, reset_clicks, interval, chosen_solver):
    """ Starts the interval-event (internal clock) if Start Button is pressed,
    else stops the timer if the Stop or Reset Buttons are pressed.

    Also if the Reset button is pressed new initial values get read from ./user_current.json
    and all solvers are newly initialized.

    The stopping is implemented as setting the interval time to 1e8 millisecond. Else
    an interval of 200 ms is chosen.
    """

    global CLICKS_START, CLICKS_RESET, SOLVER, DT, R_MAX_INIT, R_MAX, INITIALS

    # Start or Stop Buttons are pressed
    if start_clicks is not None:
        CLICKS_START = start_clicks # Increase counter for Start/Stop button
        interval = 200 if interval==1e8 else 1e8 # Kill timer by setting it to 1e8

    # Reset button was clicked
    elif reset_clicks is not None and CLICKS_RESET-reset_clicks:
        CLICKS_RESET = reset_clicks # Increase counter for Reset button
        INITIALS = BaseSolver.read_initials_from_json("./user_current.json")
        R_MAX = np.max(INITIALS["r_init"])
        R_MAX = 1.05 * R_MAX # Increase plot margin a little bit on all sides

        # Serves as initial scale. If R_MAX gets bigger the planets get smaller
        # (ZOOM OUT effect)
        R_MAX_INIT = R_MAX

        # Initialize solver
        solverdict = {
                "LF": N_Body_Gravitation_LF,
                "RK2": N_Body_Gravitation_RK2,
                "RK4": N_Body_Gravitation_RK4
                }
        SOLVER = {s: solverdict[s](DT, INITIALS, verbose=False) for s in chosen_solver}
        interval= 1e8

    return interval


@app.callback(
        Output("graphs", "children"),
        [Input("dd_planets", "value"), Input("sun_mass", "value"),
        Input("timestep", "value"), Input("drag", "value"), Input("reset", "n_clicks")],
        [State("start_stop", "n_clicks"), State("Solver", "values")],
        events=[Event("graph-update", "interval")]
        )
def update_graphs(planets, sun_mass, timestep, drag, n_clicks_reset, n_clicks_start, ode_solvers):
    """ Tells the graph how to update depending on the input.

    Following global variables are read:
        # Information
        - CLICKS_START : counter of clicks used to determine if the start button was clicked
        - SOLVER : dictionary of selected solver objects
        - INITIALS : dictionary from the ./user_current.json files with the current bodies
        - RUNNING : Indicates wheter the simulation is running or stopped
        # Safety
        - GRAPHS : Used if the new graphs object files for some reason, last working graph
        - VALID_DRAG : Used if the input drag is not valid, last valid drag
        # Scale
        - R_MAX : sets the scale of the axis
        - R_MAX_INIT : Used as a scale for bodysize, if R_MAX gets bigger the bodies get smaller (ZOOM)
        - ENERGY_MAX : Used for scaling the energy plot
    """
    global CLICKS_START, SOLVER, INITIALS, RUNNING
    global GRAPHS, VALID_DRAG
    global R_MAX, R_MAX_INIT, ENERGY_MAX
    sun_mass = transform_sun_mass(sun_mass)
    graphs = []

    try:
        VALID_DRAG = int(drag)
    except (ValueError, TypeError):
        pass

    # Start Button was clicked at least once, already initialised solvers,...
    if CLICKS_START != 0:
        if RUNNING: #animate
            for solver in ode_solvers:
                results  = SOLVER[solver].evolve(steps=1, saveOnly=VALID_DRAG, mass_sun=sun_mass)
                positions = np.array(results[0])
                # velocities = results[1]
                # forces = results[2]
                energies = np.abs(np.array(results[3]).sum(axis=1))
                timesteps = results[4]

                # Rescale length scale if necessary
                # 1) General x and y-axis limits
                # 2) Size of objects hets smaller for bigger R_MAX (ZOOM OUT effect)
                max_pos = np.max(positions)
                if max_pos > R_MAX:
                    R_MAX = max_pos
                    R_MAX = 1.05 * R_MAX
                scale_for_escaping = R_MAX_INIT / R_MAX
                INITIALS["scaled_sizes"] = INITIALS["sizes"] * scale_for_escaping

                # Convert current timestep
                days = np.round(timesteps[-1]/(3600 * 24), 2)
                years = np.round(days/365,2)

    # Not initialised in the beginning, do this now for the first time
    else:
        INITIALS = BaseSolver.read_initials_from_json("./user_current.json")
        print("From here\n\n\n", INITIALS)
        R_MAX_INIT = np.max(INITIALS["r_init"])
        R_MAX = R_MAX_INIT
        R_MAX = 1.05 * R_MAX_INIT
        SOLVER = {"LF": N_Body_Gravitation_LF(DT, INITIALS, verbose=False)}
        positions = np.array([INITIALS["r_init"]])
        days = 0
        years = 0
        timesteps= [0]
        energies = [0]
        INITIALS["scaled_sizes"] = INITIALS["sizes"]
        ENERGY_MAX = 0

    if n_clicks_reset is not None:
        reset_clicked = bool(n_clicks_reset - CLICKS_RESET)
    else:
        reset_clicked = False

    if reset_clicked:
        print("RESET")
        R_MAX_INIT = np.max(INITIALS["r_init"])
        R_MAX = R_MAX_INIT
        R_MAX = 1.05 * R_MAX_INIT
        SOLVER = {"LF": N_Body_Gravitation_LF(DT, INITIALS, verbose=False)}
        positions = np.array([INITIALS["r_init"]])
        days = 0
        years = 0
        timesteps= [0]
        energies = [0]
        INITIALS["scaled_sizes"] = INITIALS["sizes"]
        ENERGY_MAX = 0

    # Update graphs with next points
    if RUNNING or CLICKS_START==0 or reset_clicked:
        traj_data = []
        energ_data = []
        print("from there\n\n", INITIALS)
        for i, name in enumerate(INITIALS["names"]):
            traj_data.append(go.Scatter(
                x = positions[:, i, 0],
                y = positions[:, i, 1],
                name = name,
                marker = {
                    "size": INITIALS["scaled_sizes"][i],
                    "color": INITIALS["colors"][i]
                    }
                ))

        if np.max(energies) > ENERGY_MAX:
            ENERGY_MAX = np.max(energies)

        energ_data.append(go.Bar(
            x = [0],
            y = [energies[-1]],
            name = "LF",
            ))


        planet_trajectories = html.Div(dcc.Graph(
                id="trajectories",
                figure={
                    'data': traj_data,
                    'layout' : go.Layout(
                        xaxis=dict(
                            range=(-R_MAX, R_MAX),
                            showgrid=False,
                            zeroline=False,
                            showline=False,
                            ticks="",
                            showticklabels=False
                            ),
                        yaxis=dict(
                            range=(-R_MAX, R_MAX),
                            showgrid=False,
                            zeroline=False,
                            showline=False,
                            ticks="",
                            showticklabels=False
                            ),
                        margin={'l':50,'r':1,'t':45,'b':1},
                        paper_bgcolor="#000000",
                        plot_bgcolor="#000000",
                        title='{} days / {} years'.format(days, years))
                }
                ), className="eight columns")

        planet_energies = html.Div(dcc.Graph(
                id="energies",
                figure={
                    'data': energ_data,
                    'layout' : go.Layout(
                        xaxis=dict(
                            range=(0, 3),
                            ),
                        yaxis=dict(
                            range=(0, ENERGY_MAX),
                            ),
                        margin={'l':50,'r':1,'t':45,'b':1},
                        title='Energies')
                }
                ), className="four columns")

        GRAPHS = html.Div([
                    planet_trajectories,
                    planet_energies,
                    ],
                    className="row"
                )

    return GRAPHS

def transform_sun_mass(sun_mass_scale):
    """ Transforms sun mass given on logarithmic scale to kg
    """
    return M_SUN  * 10**sun_mass_scale


external_css = [
        'https://codepen.io/chriddyp/pen/bWLwgP.css',
        ]
for css in external_css:
    app.css.append_css({"external_url": css})

external_js = ['https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/js/materialize.min.js']
for js in external_css:
    app.scripts.append_script({'external_url': js})


        # INITIALS = BaseSolver.read_initials_from_json("./user_current.json")
        # print("From here\n\n\n", INITIALS)
        # R_MAX_INIT = np.max(INITIALS["r_init"])
        # R_MAX = R_MAX_INIT
        # R_MAX = 1.05 * R_MAX_INIT
        # SOLVER = {"LF": N_Body_Gravitation_LF(DT, INITIALS, verbose=False)}
        # positions = np.array([INITIALS["r_init"]])
        # days = 0
        # years = 0
        # timesteps= [0]
        # energies = [0]
        # INITIALS["scaled_sizes"] = INITIALS["sizes"]
        # ENERGY_MAX = 0

        # print("RESET")
        # R_MAX_INIT = np.max(INITIALS["r_init"])
        # R_MAX = R_MAX_INIT
        # R_MAX = 1.05 * R_MAX_INIT
        # SOLVER = {"LF": N_Body_Gravitation_LF(DT, INITIALS, verbose=False)}
        # positions = np.array([INITIALS["r_init"]])
        # days = 0
        # years = 0
        # timesteps= [0]
        # energies = [0]
        # INITIALS["scaled_sizes"] = INITIALS["sizes"]
        # ENERGY_MAX = 0



        # updated_current = {}
        # print("SHOULD HER, \n\n\n", INITIALS)
        # for i, body in enumerate(INITIALS["names"]):
        #     updated_current[body] = {
        #             "mass": INITIALS["masses"][i],
        #             "r_init": list(INITIALS["r_init"][i].astype(float)),
        #             "v_init": list(INITIALS["v_init"][i].astype(float)),
        #             "color": INITIALS["colors"][i]
        #             }
        # updated_current = json.dumps(updated_current)
        # with open("./user_current.json", "w") as f:
        #     f.write(updated_current)


        # INITIALS = BaseSolver.read_initials_from_json("./user_current.json")
if __name__ == "__main__":
    app.server.run(debug=True)

