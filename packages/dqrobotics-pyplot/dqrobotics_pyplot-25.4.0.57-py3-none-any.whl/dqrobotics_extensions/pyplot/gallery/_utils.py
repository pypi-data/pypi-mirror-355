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
from matplotlib import pyplot as plt

def _set_plot_labels():
    ax = plt.gca()
    ax.set(
        xlabel='x [m]',
        ylabel='y [m]',
        zlabel='z [m]'
    )

def _set_plot_limits(lmin: float = -0.5, lmax: float = 0.5):
    ax = plt.gca()
    ax.set(
        xlim=[lmin, lmax],
        ylim=[lmin, lmax],
        zlim=[lmin, lmax]
    )