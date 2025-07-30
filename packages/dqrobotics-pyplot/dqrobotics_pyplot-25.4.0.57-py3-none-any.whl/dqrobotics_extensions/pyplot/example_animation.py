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
import numpy as np

from dqrobotics import *
from dqrobotics.robots import KukaLw4Robot
from dqrobotics.utils.DQ_Math import deg2rad

# Adding the prefix `dqp` to help users differentiate from `plt`
import dqrobotics_extensions.pyplot as dqp

import matplotlib.pyplot as plt
import matplotlib.animation as anm # Matplotlib animation
from functools import partial # Need to call functions correctly for matplotlib animations

# Animation function
def animate_robot(n, robot, stored_q, stored_time):
    """
    Create an animation function compatible with `plt`.
    Adapted from https://marinholab.github.io/OpenExecutableBooksRobotics//lesson-dq8-optimization-based-robot-control.
    :param n: The frame number, necessary for pyplot.
    :param robot: The DQ_SerialManipulator instance to plot.
    :param stored_q: The sequence of joint configurations.
    :param stored_time: The sequence of timepoints to plot in the title.
    """
    plt.cla()
    plt.xlabel('x [m]')
    plt.xlim([-1.0, 0.0])
    plt.ylabel('y [m]')
    plt.ylim([-0.5, 0.5])
    plt.gca().set_zlabel('z [m]')
    plt.gca().set_zlim([0, 0.5])
    plt.title(f'Joint control time={stored_time[n]:.2f} s out of {stored_time[-1]:.2f} s')

    dqp.plot(robot, q=stored_q[n])

def main():

    # Define the robot
    robot = KukaLw4Robot.kinematics()

    # Sampling time [s]
    tau = 0.01
    # Simulation time [s]
    time_final = 1
    # Initial joint values [rad]
    q = deg2rad([0, 45, 0, -45, 0, 45, 0])
    # Store the control signals
    stored_q = []
    stored_time = []

    # Translation controller loop.
    for time in np.arange(0, time_final + tau, tau):
        # Output to console
        print(f"Simulation at time = {time}")

        # Store data for posterior animation
        stored_q.append(q)
        stored_time.append(time)

        # A joint-space velocity
        u = np.ones(7)

        # Move the robot
        q = q + u * tau

    # Set up the plot
    fig = plt.figure()
    plt.axes(projection='3d')

    anim = anm.FuncAnimation(fig,
                      partial(animate_robot,
                              robot=robot,
                              stored_q=stored_q,
                              stored_time=stored_time),
                      frames=len(stored_q))

    plt.show()

if __name__ == "__main__":
    main()