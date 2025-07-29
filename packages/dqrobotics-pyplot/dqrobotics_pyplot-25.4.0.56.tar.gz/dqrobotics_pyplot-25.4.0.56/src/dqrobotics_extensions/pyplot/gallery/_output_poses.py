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

from math import sin, cos, pi

def output_poses():
    """
    Calculate and visualize multiple poses represented as DQs.
    """

    # x1
    t1 = 0
    r1 = 1
    x1 = r1 + 0.5 * E_ * t1 * r1

    # x2
    t2 = 0.1 * j_
    r2 = cos(pi / 4) + i_ * sin(pi / 4)
    x2 = r2 + 0.5 * E_ * t2 * r2

    # x3
    t3 = - 0.1 * k_ + 0.2 * i_
    r3 = cos(pi / 32) + k_ * sin(pi / 32)
    x3 = r3 + 0.5 * E_ * t3 * r3

    # x4
    x4 = x1 * x2 * x3

    # Plot using subplot
    fig = plt.figure(figsize=(12, 10))

    pose_list = [x1, x2, x3, x4]

    for i in range(0, len(pose_list)):
        x = pose_list[i]

        ax = plt.subplot(2, 2, i+1, projection='3d')
        dqp.plot(x)
        ax.title.set_text(rf'$\boldsymbol{{x}}_{i}$')
        _set_plot_labels()
        _set_plot_limits()

    fig.tight_layout()
    plt.savefig("output_poses.png")