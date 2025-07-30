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
from ._utils import _set_plot_labels, _set_plot_limits

from matplotlib import pyplot as plt
import matplotlib.animation as anm # Matplotlib animation
from functools import partial # Need to call functions correctly for matplotlib animations

from math import sin, cos
import numpy as np


def output_moving_primitives():
    """
    Calculate and visualize multiple moving primitives represented as DQs.
    """

    # Sampling time [s]
    tau = 0.01
    # Simulation time [s]
    time_final = 1
    # Store the plotted variables
    stored_x = []
    stored_l_dq = []
    stored_pi_dq = []
    stored_time = []

    x = DQ([1])
    ls_dq_init = [i_, j_, k_]
    pis_dq_init = [k_, normalize(i_ + j_), normalize(i_ + j_ + k_)]

    # Translation controller loop.
    for time in np.arange(0, time_final + tau, tau):

        # Modify line
        ls_dq = [Ad(x, l_dq_init) for l_dq_init in ls_dq_init]
        pis_dq = [Adsharp(x, pi_dq_init) for pi_dq_init in pis_dq_init]

        # Store data for posterior animation
        stored_x.append(x)
        stored_l_dq.append(ls_dq)
        stored_pi_dq.append(pis_dq)
        stored_time.append(time)

        # Move x
        r = cos((10 * time) / 2) + j_ * sin((10 * time) / 2)
        t = 0.1*(i_ + j_ + k_) * sin(time)
        x = r + 0.5 * E_ * t * r

    def animate_plot(n, stored_x, stored_l_dq, stored_pi_dq, stored_time):

        plt.cla()
        _set_plot_limits()
        _set_plot_labels()
        plt.title(f'Animation time={stored_time[n]:.2f} s out of {stored_time[-1]:.2f} s')

        dqp.plot(stored_x[n])

        line_colors = ['r+-', 'k.-', 'g+-', 'c-.']
        plane_colors = ['r', 'k', 'g', 'c']

        for line_counter in range(len(stored_l_dq[n])):
            l_dq = stored_l_dq[n][line_counter]
            dqp.plot(l_dq, line=True, scale=1, color=line_colors[line_counter % len(line_colors)])
        for plane_counter in range(len(stored_pi_dq[n])):
            pi_dq = stored_pi_dq[n][plane_counter]
            dqp.plot(pi_dq, plane=True, scale=1, color=plane_colors[plane_counter % len(plane_colors)], alpha=0.2)

    # Set up the plot
    fig = plt.figure(dpi=200, figsize=(12, 10))
    plt.axes(projection='3d')

    anim = anm.FuncAnimation(fig,
                      partial(animate_plot,
                              stored_x=stored_x,
                              stored_l_dq=stored_l_dq,
                              stored_pi_dq=stored_pi_dq,
                              stored_time=stored_time),
                      frames=len(stored_x))

    anim.save("output_moving_primitives.mp4")