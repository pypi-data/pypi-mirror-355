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
from dqrobotics.robot_modeling import DQ_SerialManipulator

from matplotlib import pyplot as plt

import numpy as np

from math import acos, sin, cos

def plot(obj, **kwargs):
    """
    An aggregator for all plot functions related to dqrobotics. Currently, supports `DQ` and `DQ_SerialManipulator`.

    Import it as follows:

        import dqrobotics_extensions.pyplot as dqp

    Before this can be used, please remember to initialise the plt Axes. Example:

        plt.figure()
        ax = plt.axes(projection='3d')
        dqp.plot(i_)
        plt.show()

    Plotting a unit DQ `x` (See internal function `pyplot._pyplot._plot_pose`):

        dqp.plot(x)

    Plotting a line DQ `l_dq` (See internal function `pyplot._pyplot._plot_line`):

        dqp.plot(l_dq, line=True)

    Plotting a plane DQ `pi_dq` (See internal function `pyplot._pyplot._plot_plane`):

        dqp.plot(pi_dq, plane=True)

    Plotting a `DQ_SerialManipulator` called `robot` at joint configurations `q` (See internal function `pyplot._pyplot._plot_serial_manipulator`):

        dqp.plot(robot, q=q)

    :param obj: The input to be plotted.
    :param kwargs: For arguments depending on the type of plot you need, see the description above.
    :raises RuntimeError: If the input instance `obj` has no meaning for function, or if the `obj` is not valid for the input options.
    """
    if isinstance(obj,DQ):
        if kwargs is None:
            _plot_dq(dq=obj)
        else:
            _plot_dq(obj, **kwargs)
    elif isinstance(obj,DQ_SerialManipulator):
        _plot_serial_manipulator(obj, **kwargs)
    else:
        raise RuntimeError(f"plot not implemented yet for {obj}")

def _plot_dq(dq : DQ,
             scale: float = 0.1,
             line = None,
             plane = None,
             sphere = None,
             radius = None,
             color = 'r',
             alpha = 0.8,
             ax = None
             ):
    """
    Implementing the pyplot valid options of
    https://github.com/dqrobotics/matlab/blob/master/%40DQ/plot.m
    the particular plotting functions did not inherit from these implementations and are an informed attempt of using
    DQ operators to plot the objects.

    :param dq: The input DQ.
    :param scale: If not None, defines the size of the frame.
    :param line: If not None, draw the input DQ as a line.
    :param plane: If not None, draw the input DQ as a plane.
    :param sphere: If not None, draw the input DQ as a sphere.
    :param color: Define the color of the frame, line, or plane.
    :param alpha: Define the alpha of the plane.
    :param ax: Figure Axes or plt.gca() if None.
    """
    if line is not None:
        _plot_line(l_dq=dq,
                   color=color,
                   length=scale,
                   ax=ax)
    elif plane is not None:
        _plot_plane(pi_dq=dq,
                    length_x=scale,
                    length_y=scale,
                    color=color,
                    alpha=alpha,
                    ax=ax)
    elif sphere is not None:
        _plot_sphere(p=dq,
                     radius=radius,
                     color=color,
                     alpha=alpha,
                     ax=ax)
    else:
        _plot_pose(x=dq,
                   length=scale,
                   ax=ax)

def _plot_plane(pi_dq,
                length_x: float,
                length_y: float,
                color,
                alpha: float,
                ax=None):
    """
    Draw a plane representing the DQ pi_dq. In this plot, the normal will be represented by the local z-axis of the plane
    and the plane will span in its local x-y axis.
    :param pi_dq: The DQ representation of the plane.
    :param length_x: The desired x-axis length.
    :param length_y: The desired y-axis length.
    :param color: Define the color of the plane.
    :param alpha: Define the alpha of the plane.
    :param ax: Figure Axes or plt.gca() if None.
    :raises RuntimeError: If argument `x` is not a plane.
    """

    if not is_plane(pi_dq):
        raise RuntimeError(f"The input pi_dq = {pi_dq} is not a plane.")
    # https://stackoverflow.com/questions/26989131/add-cylinder-to-plot
    # I modified the code above to use dual quaternion algebra.
    if ax is None:
        ax = plt.gca()

    # For plotting, we need to align the z-axis of the plot to the normal of the plane.
    n = P(pi_dq)
    d = D(pi_dq)

    # Find a rotation that aligns the origin's z-axis with the normal to the plane.
    if not np.allclose(n.q, k_.q, atol=DQ_threshold):
        phi: float = acos(dot(k_, n).q[0])
        v: DQ = cross(k_, n) * (1.0 / sin(phi))
        r: DQ = cos(phi / 2.0) + v * sin(phi / 2.0)
    else:
        r: DQ = DQ([1])

    # The translation about z is after the normal is applied.
    x_dq: DQ = r * (1 + 0.5*E_ * d * k_)

    # Sanity check: is the point in the plane?
    p = translation(x_dq)
    if not np.isclose(dot(p, n).q[0], d.q[0], atol=DQ_threshold):
        raise RuntimeError(f"The point {p} is not in the plane. <p, n> = {dot(p, n).q[0]} != {d.q[0]}.")

    # Cylindrical points start at zero
    x = np.linspace(-length_x / 2.0, length_x / 2.0, 2)
    y = np.linspace(-length_y / 2.0, length_y / 2.0, 2)

    x_grid, y_grid = np.meshgrid(x, y)
    z_grid = np.zeros(x_grid.shape)

    x_grid_ad, y_grid_ad, z_grid_ad = __dq_adjoint_grid(x_dq, x_grid, y_grid, z_grid)

    ax.plot_surface(x_grid_ad,
                    y_grid_ad,
                    z_grid_ad,
                    alpha=alpha,
                    color=color)

def _plot_serial_manipulator(robot: DQ_SerialManipulator,
                             q: np.ndarray,
                             line_color: str = "k",
                             line_width = 3,
                             cylinder_color: str = "b",
                             cylinder_alpha: float = 0.8,
                             cylinder_radius: float = 0.02,
                             cylinder_height: float = 0.07,
                             ax=None):
    """
    Draw a serial manipulator at a given joint configuration q. Each joint transformation will be connected by a line
    with spec line_color and width linewidth.
    :param robot: A concrete subclass of DQ_SerialManipulator.
    :param q: The joint configurations.
    :param line_color: A suitable color for the line.
    :param line_width: The width is compatible with matplotlib.
    :param cylinder_color: A suitable color for the cylinder.
    :param cylinder_alpha: The alpha of the cylinder.
    :param ax: Figure Axes or plt.gca() if None.
    """
    if ax is None:
        ax = plt.gca()

    x_plot = []
    y_plot = []
    z_plot = []

    # Store pose information and draw reference frames of each joint
    for i in range(0, robot.get_dim_configuration_space()):
        xi = robot.fkm(q, i)
        t = translation(xi)
        x_plot.append(t.q[1])
        y_plot.append(t.q[2])
        z_plot.append(t.q[3])

        __plot_revolute_joint(xi,
                              color=cylinder_color,
                              alpha=cylinder_alpha,
                              height_z=cylinder_height,
                              radius=cylinder_radius,
                              ax=ax)
        _plot_pose(xi, ax=ax)

    # Draw the reference frame
    x_ref = robot.get_reference_frame()
    t_ref = translation(x_ref)
    _plot_pose(x_ref, ax=ax)
    # Draw line connecting reference frame to joint 0
    ax.plot3D((t_ref.q[1], x_plot[0]),
              (t_ref.q[2], y_plot[0]),
              (t_ref.q[3], z_plot[0]),
              line_color,
              linewidth=line_width)

    # Draw lines connecting the sequential reference frames
    for i in range(0, len(x_plot) - 1):
        ax.plot3D((x_plot[i], x_plot[i + 1]),
                  (y_plot[i], y_plot[i + 1]),
                  (z_plot[i], z_plot[i + 1]),
                  color=line_color,
                  linewidth=line_width)

    # Draw end effector frame
    x_eff = robot.fkm(q)
    t_eff = translation(x_eff)
    _plot_pose(x_eff, ax=ax)
    # Draw line connecting last joint to end effector frame
    ax.plot3D((t_eff.q[1], x_plot[-1]),
              (t_eff.q[2], y_plot[-1]),
              (t_eff.q[3], z_plot[-1]),
              line_color,
              linewidth=line_width)


def _plot_pose(x: DQ, length: float = 0.1, ax=None):
    """
    Draw a reference frame at a given pose x.
    :param x: the pose as a unit DQ.
    :param length: the length of each axis' line. Has a default value.
    :param ax: Figure Axes or plt.gca() if None.
    :raises RuntimeError: If argument `x` is not a unit dual quaternion.
    """
    if not is_unit(x):
        raise RuntimeError(f"The input x = {x} is not a unit dual quaternion.")
    if ax is None:
        ax = plt.gca()

    t = translation(x)

    i_prime = Ad(x, i_)
    j_prime = Ad(x, j_)
    k_prime = Ad(x, k_)

    # Centre of the reference frame
    ax.plot3D(t.q[1],
              t.q[2],
              t.q[3],
              "kx")

    # x-axis arrow
    ax.quiver(t.q[1], t.q[2], t.q[3],
              i_prime.q[1], i_prime.q[2], i_prime.q[3],
              length=length,
              color="r",
              normalize=True)

    # y-axis arrow
    ax.quiver(t.q[1], t.q[2], t.q[3],
              j_prime.q[1], j_prime.q[2], j_prime.q[3],
              length=length,
              color="g",
              normalize=True)

    # z-axis arrow
    ax.quiver(t.q[1], t.q[2], t.q[3],
              k_prime.q[1], k_prime.q[2], k_prime.q[3],
              length=length,
              color="b",
              normalize=True)

def _plot_line(l_dq: DQ, color: str = "r", length: float = 10.0, ax=None):
    """
    Draw a line representing the DQ l_dq.
    :param l_dq: the DQ representation of the line.
    :param color: the color.
    :param length: the length.
    :param ax: Figure Axes or plt.gca() if None.
    :raises RuntimeError: If argument `x` is not a line.
    """
    if not is_line(l_dq):
        raise RuntimeError(f"The input l_dq = {l_dq} is not a line.")
    if ax is None:
        ax = plt.gca()

    # Decompose line
    l = P(l_dq)
    m = D(l_dq)

    # This is always a point in the line. More specifically, the projection of 0i_ + 0j_ + 0k_ onto the line.
    pl = cross(l, m)

    pl_positive = pl + (length / 2.0) * l
    pl_negative = pl - (length / 2.0) * l

    ax.plot3D((pl_negative.q[1], pl_positive.q[1]),
              (pl_negative.q[2], pl_positive.q[2]),
              (pl_negative.q[3], pl_positive.q[3]),
              color) # It's important not to use the named `color` so that we accept strings such as `r-`.

def _plot_sphere(p: DQ, radius: float, color = 'b', alpha: float = 0.8, ax=None):
    """
    Draw a sphere of a given `radius` centered at `p`, where `p` is a pure quaternion.

    See: https://stackoverflow.com/questions/64656951/plotting-spheres-of-radius-r.

    :param p: the DQ representing the centre of the sphere.
    :param radius: the radius of the sphere.
    :param color: the color of the sphere.
    :param alpha: the transparency of the sphere.
    :param ax: Figure Axes or plt.gca() if None.
    :raises: RuntimeError: If `p` is not a pure quaternion.
    """
    if (not is_quaternion(p)) or (not is_pure(p)):
        raise RuntimeError(f"The input p = {p} is not a pure quaternion.")
    if ax is None:
        ax = plt.gca()

    u, v = np.mgrid[0:2 * np.pi:50j, 0:np.pi:50j]
    x = radius * np.cos(u) * np.sin(v)
    y = radius * np.sin(u) * np.sin(v)
    z = radius * np.cos(v)

    ax.plot_surface(x - p.q[1], y - p.q[2], z - p.q[3], color=color, alpha=alpha)


def __plot_revolute_joint(x,
                          height_z,
                          radius,
                          color,
                          alpha,
                          ax=None):
    """
    This internal function is used to draw cylinders, for now, for DQ_SerialManipulators. The cylinder's height is through
    its z-axis, and it spans from -height_z/2 to +height_z/2.
    :param x: the pose as a DQ.
    :param height_z: the height of the cylinder.
    :param radius: the radius of the cylinder.
    :param color: the color of the cylinder.
    :param alpha: the transparency of the cylinder.
    :param ax: Figure Axes or plt.gca() if None.
    """
    __plot_cylinder(x,
                    height_z=height_z,
                    radius=radius,
                    color=color,
                    alpha=alpha,
                    ax=ax)


def __dq_adjoint(x: DQ, t: DQ):
    """
    This internal function currently does not seem to exist in the implementation of dqrobotics. It will be replaced
    when it's available.
    I'm basing this on (25) of https://faculty.sites.iastate.edu/jia/files/inline-files/dual-quaternion.pdf.

    :param x: A unit dual quaternion.
    :param t: A pure quaternion representing the point to be transformed.
    :return: A pure quaternion of representing the transformed point.
    :raises RuntimeError: If argument `x` is not a unit dual quaternion, or if `t` is not a pure quaternion.
    """
    if not is_unit(x):
        raise RuntimeError("The argument x must be a unit dual quaternion.")
    if not (is_pure(t) and is_quaternion(t)):
        raise RuntimeError("The argument t must be a pure quaternion.")

    t_dq = 1 + E_ * t
    return D(conj(Adsharp(x, t_dq)))


def __dq_adjoint_grid(x: DQ, x_grid, y_grid, z_grid):
    """
    This internal function runs `__dq_adjoint` through all elements of a grid so that calculations are simplified.
    For instance, to move a cylinder or other surface around a plot.
    :param x: A unit dual quaternion.
    :param x_grid: A suitable x-axis grid element.
    :param y_grid: A suitable y-axis grid element.
    :param z_grid: A suitable z-axis grid element.
    :return: The transformed grids by `x`.
    :raises RuntimeError: If argument grids have different shapes.
    """
    if x_grid.shape != y_grid.shape or x_grid.shape != z_grid.shape:
        raise RuntimeError("Shapes of arguments must be the same.")

    shape = x_grid.shape
    rows, cols = shape

    x_grid_ad = np.zeros(shape)
    y_grid_ad = np.zeros(shape)
    z_grid_ad = np.zeros(shape)

    for i in range(0, rows):
        for j in range(0, cols):
            x_element = x_grid[i, j]
            y_element = y_grid[i, j]
            z_element = z_grid[i, j]

            p = x_element*i_ + y_element*j_ + z_element*k_
            p_prime = __dq_adjoint(x, p)

            x_grid_ad[i, j] = p_prime.q[1]
            y_grid_ad[i, j] = p_prime.q[2]
            z_grid_ad[i, j] = p_prime.q[3]

    return x_grid_ad, y_grid_ad, z_grid_ad


def __plot_cylinder(x,
                    height_z: float,
                    radius: float,
                    color: str,
                    alpha: float,
                    ax=None):
    """
    Internal method to draw a cylinder. x is a unit dual quaternion that defines the centre of the cylinder. The cylinder
    will span from -height_z/2 to +height_z/2. Use param_dict to define anything to be passed on to plot_surface.
    :param x: a unit dual quaternion representing the pose of the centre of the cylinder.
    :param height_z: the height of the cylinder.
    :param radius: the radius of the cylinder.
    :param color: the color of the cylinder.
    :param alpha: the transparency of the cylinder.
    :param ax: Figure Axes or plt.gca() if None.
    :raises RuntimeError: If argument `x` is not a unit dual quaternion.
    """
    if not is_unit(x):
        raise RuntimeError("The argument x must be a unit dual quaternion.")
    # https://stackoverflow.com/questions/26989131/add-cylinder-to-plot
    # I modified the code above to use dual quaternion algebra.
    if ax is None:
        ax = plt.gca()

    # Cylindrical points start at zero
    z = np.linspace(-height_z / 2.0, height_z / 2.0, 20)  # Draw half the cylinder
    theta = np.linspace(0, 2 * np.pi, 20)
    theta_grid, z_grid = np.meshgrid(theta, z)
    x_grid = radius * np.cos(theta_grid)
    y_grid = radius * np.sin(theta_grid)

    x_grid_ad, y_grid_ad, z_grid_ad = __dq_adjoint_grid(x, x_grid, y_grid, z_grid)

    ax.plot_surface(x_grid_ad,
                    y_grid_ad,
                    z_grid_ad,
                    color=color,
                    alpha=alpha)