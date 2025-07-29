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


def output_lines():
    """
    Calculate and visualize multiple lines represented as DQs.
    """

    # l1
    l1 = i_
    m1 = cross(-0.1 * j_, l1)
    l1_dq = l1 + E_ * m1

    # l2
    l2 = j_
    m2 = cross(0.3 * k_, l2)
    l2_dq = l2 + E_ * m2

    # l3
    l3 = k_
    m3 = cross(0.2 * i_, l3)
    l3_dq = l3 + E_ * m3

    # l4
    l4 = j_
    m4 = 0
    l4_dq = l4 + E_ * m4

    # Plot using subplot
    fig = plt.figure(figsize=(12, 10))

    line_list = [l1_dq, l2_dq, l3_dq, l4_dq]
    color_list = ['r-', 'k-', 'g-', 'c-.']

    for i in range(0, len(line_list)):
        l_dq = line_list[i]
        color = color_list[i]

        ax = plt.subplot(2, 2, i+1, projection='3d')
        dqp.plot(l_dq, line=True, scale=0.5, color=color)
        ax.title.set_text(rf'$\boldsymbol{{l}}_{i}$')
        _set_plot_labels()
        _set_plot_limits()

    fig.tight_layout()
    plt.savefig("output_lines.png")