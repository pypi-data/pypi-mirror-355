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


def output_planes():
    """
    Calculate and visualize multiple planes represented as DQs.
    """

    # pi1
    n1_pi = i_
    d1_pi = 0.1
    pi1_dq = n1_pi + E_ * d1_pi

    # pi2
    n2_pi = j_
    d2_pi = -0.1
    pi2_dq = n2_pi + E_ * d2_pi

    # pi3
    n3_pi = k_
    d3_pi = 0.2
    pi3_dq = n3_pi + E_ * d3_pi

    # pi4
    n4_pi = normalize(i_ + j_ + k_)
    d4_pi = 0
    pi4_dq = n4_pi + E_ * d4_pi

    # Plot using subplot
    fig = plt.figure(figsize=(12, 10))

    plane_list = [pi1_dq, pi2_dq, pi3_dq, pi4_dq]
    color_list = ['r', 'k', 'g', 'c']

    for i in range(0, len(plane_list)):
        pi_dq = plane_list[i]
        color = color_list[i]

        ax = plt.subplot(2, 2, i+1, projection='3d')
        dqp.plot(pi_dq, plane=True, scale=0.5, color=color)
        ax.title.set_text(rf'$\boldsymbol{{\pi}}_{i}$')
        _set_plot_labels()
        _set_plot_limits()

    fig.tight_layout()
    plt.savefig("output_planes.png")