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
from dqrobotics.robots import KukaLw4Robot
from dqrobotics.utils.DQ_Math import deg2rad

# Adding the prefix `dqp` to help users differentiate from `plt`
import dqrobotics_extensions.pyplot as dqp

from matplotlib import pyplot as plt

from math import sin, cos, pi

def main():

    # Set up the plot
    plt.figure()
    plot_size = 1
    ax = plt.axes(projection='3d')
    ax.set_xlabel('$x$')
    ax.set_xlim((-plot_size, plot_size))
    ax.set_ylabel('$y$')
    ax.set_ylim((-plot_size, plot_size))
    ax.set_zlabel('$z$')
    ax.set_zlim((-plot_size, plot_size))

    # Draw a pose
    x_phi = pi / 3
    r = cos(x_phi) + i_ * sin(x_phi)
    x = r + 0.5 * E_ * (0.5 * j_ + 0.45 * k_) * r
    dqp.plot(x)

    # Draw a line
    l = k_
    m = cross(-0.3 * j_, l)
    l_dq = l + E_ * m
    dqp.plot(l_dq, line=True, scale=1)

    # Draw a plane
    n_pi = i_
    d_pi = 0.1
    pi_dq = n_pi + E_ * d_pi
    dqp.plot(pi_dq, plane=True, scale=1)

    # Draw a manipulator
    q = deg2rad([0, 45, 0, -90, 0, -45, 0])
    robot = KukaLw4Robot.kinematics()
    dqp.plot(robot, q=q)

    plt.show()

if __name__ == "__main__":
    main()