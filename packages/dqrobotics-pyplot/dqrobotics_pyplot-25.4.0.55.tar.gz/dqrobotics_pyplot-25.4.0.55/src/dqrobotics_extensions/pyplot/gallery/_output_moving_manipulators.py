"""
Copyright (C) 2025 Murilo Marques Marinho (www.murilomarinho.info)

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

Author: Murilo M. Marinho
"""
from dqrobotics import *

# Adding the prefix `dqp` to help users differentiate from `plt`
import dqrobotics_extensions.pyplot as dqp
from dqrobotics.robots import KukaLw4Robot
from dqrobotics.utils.DQ_Math import deg2rad

from ._utils import _set_plot_labels, _set_plot_limits

from matplotlib import pyplot as plt
import matplotlib.animation as anm # Matplotlib animation
from functools import partial # Need to call functions correctly for matplotlib animations

import numpy as np

from math import pi, cos, sin


def output_moving_manipulators():
    """
    Calculate and visualize multiple moving primitives represented as DQs.
    """

    # Animation function
    def animate_robots(n, robots, stored_qs, stored_time):
        """
        Create an animation function compatible with `plt`.
        Adapted from https://marinholab.github.io/OpenExecutableBooksRobotics//lesson-dq8-optimization-based-robot-control.
        :param n: The frame number, necessary for `pyplot`.
        :param robots: The `DQ_SerialManipulator` tuple instance to plot.
        :param stored_qs: The sequence of joint configurations.
        :param stored_time: The sequence of timepoints to plot in the title.
        """
        plt.cla()
        _set_plot_limits(-0, 1.0)
        _set_plot_labels()
        plt.title(f'Joint control time={stored_time[n]:.2f} s out of {stored_time[-1]:.2f} s')

        R1, R2 = robots
        dqp.plot(R1, q=stored_qs[n][0],
                 line_color='r',
                 line_width=5,
                 cylinder_color="k",
                 cylinder_alpha=0.9,
                 cylinder_radius=0.035,
                 cylinder_height=0.1)
        dqp.plot(R2, q=stored_qs[n][1],
                 line_color='b',
                 cylinder_color="c",
                 cylinder_alpha=0.3)

    # Define the robots
    R1 = KukaLw4Robot.kinematics()
    R1.set_reference_frame(cos(pi/2) + k_*sin(pi/2))
    R2 = KukaLw4Robot.kinematics()
    R2.set_reference_frame(1 + 0.5*E_*(0.75*i_ + 0.75*j_))

    # Sampling time [s]
    tau = 0.01
    # Simulation time [s]
    time_final = 1
    # Initial joint values [rad]
    q1 = deg2rad([0, 45, 0, -45, 0, 45, 0])
    q2 = q1
    # Store the control signals
    stored_qs = []
    stored_time = []

    # Translation controller loop.
    for time in np.arange(0, time_final + tau, tau):

        # Store data for posterior animation
        stored_qs.append((q1, q2))
        stored_time.append(time)

        # Joint-space velocities
        u1 = np.ones(7)
        u2 = -0.1 * np.ones(7)

        # Move the robots
        q1 = q1 + u1 * tau
        q2 = q2 + u2 * tau

    # Set up the plot
    fig = plt.figure(dpi=200, figsize=(12, 10))
    plt.axes(projection='3d')

    anim = anm.FuncAnimation(fig,
                             partial(animate_robots,
                                     robots=(R1, R2),
                                     stored_qs=stored_qs,
                                     stored_time=stored_time),
                             frames=len(stored_qs))

    anim.save("output_moving_manipulators.mp4")