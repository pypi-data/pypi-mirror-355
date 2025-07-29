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
from dqrobotics_extensions.pyplot.gallery._output_poses import output_poses
from dqrobotics_extensions.pyplot.gallery._output_lines import output_lines
from dqrobotics_extensions.pyplot.gallery._output_planes import output_planes
from dqrobotics_extensions.pyplot.gallery._output_spheres import output_spheres
from dqrobotics_extensions.pyplot.gallery._output_moving_primitives import output_moving_primitives
from dqrobotics_extensions.pyplot.gallery._output_moving_manipulators import output_moving_manipulators

def main():

    output_poses()
    output_lines()
    output_planes()
    output_spheres()
    output_moving_primitives()
    output_moving_manipulators()

if __name__ == "__main__":
    main()