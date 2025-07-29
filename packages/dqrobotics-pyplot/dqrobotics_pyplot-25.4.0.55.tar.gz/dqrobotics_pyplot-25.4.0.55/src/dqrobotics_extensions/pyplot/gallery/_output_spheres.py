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

def output_spheres():
    """
    Calculate and visualize multiple spheres represented as DQs.
    """

    # p1
    p1 = DQ([0])
    r1 = 0.1

    # l2
    p2 = 0.1*i_
    r2 = 0.2

    # l3
    p3 = 0.2*j_
    r3 = 0.05

    # l4
    p4 = 0.1*i_ + 0.2*j_ + 0.1*k_
    r4 = 0.1

    # Plot using subplot
    fig = plt.figure(figsize=(12, 10))

    sphere_list = [(p1, r1), (p2, r2), (p3, r3), (p4, r4)]
    color_list = ['r', 'k', 'g', 'c']

    for i in range(0, len(sphere_list)):
        p, r = sphere_list[i]
        color = color_list[i]

        ax = plt.subplot(2, 2, i + 1, projection='3d')

        dqp.plot(p, sphere=True, radius=r, color=color)

        ax.title.set_text(rf'$\boldsymbol{{p}}_{i}$')
        _set_plot_labels()
        # https://matplotlib.org/stable/gallery/subplots_axes_and_figures/axis_equal_demo.html
        ax.axis('equal') # Adjusted to show that they are spheres not ellipsoids

    fig.tight_layout()
    plt.savefig("output_spheres.png")