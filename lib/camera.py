# -*- coding: utf-8 -*-

"""

Earthquakes / Erdbeben 2010-2019
source code behind https://www.youtube.com/watch?v=RLHM5MQ5kAs
https://github.com/pleiszenburg/earthquakes_youtube01

    lib/camera.py: Simple pinhole camera

    Copyright (C) 2020 Sebastian M. Ernst <ernst@pleiszenburg.de>

<LICENSE_BLOCK>
The contents of this file are subject to the GNU General Public License
Version 2 ("GPL" or "License"). You may not use this file except in
compliance with the License. You may obtain a copy of the License at
https://www.gnu.org/licenses/old-licenses/gpl-2.0.txt
https://github.com/pleiszenburg/earthquakes_youtube01/blob/master/LICENSE

Software distributed under the License is distributed on an "AS IS" basis,
WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License for the
specific language governing rights and limitations under the License.
</LICENSE_BLOCK>

"""

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# IMPORT
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import math

import numpy as np
import numba as nb

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class Camera:

    def __init__(self):

        # relative size / "focal" distance
        self._KD = 75.0

        # plane center (offset)
        self._cx = 0.0
        self._cy = 0.0

        # plane scale factor
        self._factor = 1.0

        # flip plane on y
        self._flip = False

        # camera position
        self._KPosX = 0.0
        self._KPosY = 0.0
        self._KPosZ = 0.0

        # camera direction (angles)
        self._KA = 0.0
        self._KB = 0.0

        self._update_plane()

    def _update_plane(self):

        self._KBXX = math.sin(self._KA)
        self._KBXY = -math.cos(self._KA)
        self._KBXZ = 0.0

        SinB = math.sin(self._KB)
        CosB = math.cos(self._KB)

        self._KNX = self._KD * -self._KBXY * CosB
        self._KNY = self._KD * self._KBXX * CosB
        self._KNZ = self._KD * SinB

        kn_xy_abs = math.sqrt(self._KNX ** 2 + self._KNY ** 2)
        tmp = 1.0 / self._abs(
            self._KNX * SinB,
            self._KNY * SinB,
            -kn_xy_abs
            )

        self._KBYX = self._KNX * SinB * tmp
        self._KBYY = self._KNY * SinB * tmp
        self._KBYZ = -kn_xy_abs * tmp

    def set_center(self, x, y):

        self._cx = x
        self._cy = y

    def set_direction(self, angle_a, angle_b): # rad

        self._KA = angle_a
        self._KB = angle_b
        self._update_plane()

    def set_factor(self, factor):

        self._factor = factor

    def set_flip(self, flip):

        self._flip = flip

    def set_focal(self, kd):

        self._KD = kd
        self._update_plane()

    def set_position(self, x, y, z):

        self._KPosX = x
        self._KPosY = y
        self._KPosZ = z

    def get_point(self, x, y, z):

        ma = [
            [self._KBXX, self._KBYX, -(x - self._KPosX), -self._KNX],
            [self._KBXY, self._KBYY, -(y - self._KPosY), -self._KNY],
            [self._KBXZ, self._KBYZ, -(z - self._KPosZ), -self._KNZ],
            ]

        determ = (
              ma[0][0] * ma[1][1] * ma[2][2]
            + ma[0][1] * ma[1][2] * ma[2][0]
            + ma[0][2] * ma[1][0] * ma[2][1]
            - ma[0][2] * ma[1][1] * ma[2][0]
            - ma[0][0] * ma[1][2] * ma[2][1]
            - ma[0][1] * ma[1][0] * ma[2][2]
            )
        xx = (
              ma[0][3] * ma[1][1] * ma[2][2]
            + ma[0][1] * ma[1][2] * ma[2][3]
            + ma[0][2] * ma[1][3] * ma[2][1]
            - ma[0][2] * ma[1][1] * ma[2][3]
            - ma[0][3] * ma[1][2] * ma[2][1]
            - ma[0][1] * ma[1][3] * ma[2][2]
            )
        yy = (
              ma[0][0] * ma[1][3] * ma[2][2]
            + ma[0][3] * ma[1][2] * ma[2][0]
            + ma[0][2] * ma[1][0] * ma[2][3]
            - ma[0][2] * ma[1][3] * ma[2][0]
            - ma[0][0] * ma[1][2] * ma[2][3]
            - ma[0][3] * ma[1][0] * ma[2][2]
            )

        xx = xx / determ # TODO catch zero
        yy = yy / determ # TODO catch zero

        if self._flip:
            yy = -yy

        return xx * self._factor + self._cx, yy * self._factor + self._cy

    def compiled_get_points(self):

        def get_points(points_3d, points_2d):

            factor = np.float32(self._factor)
            flip = self._flip

            @nb.jit((
                nb.float32[:, :], nb.float32[:, :],
                nb.float32[:, :], nb.float32[:], nb.float32[:], nb.float32[:],
                ), nopython = True)
            def get_points_jit(
                points_3d, points_2d,
                ma, kpos, empty, offset,
                ):

                for index in range(0, points_3d.shape[1]):

                    ma[:, 2] = kpos - points_3d[:, index]

                    determ = (
                          ma[0][0] * ma[1][1] * ma[2][2]
                        + ma[0][1] * ma[1][2] * ma[2][0]
                        + ma[0][2] * ma[1][0] * ma[2][1]
                        - ma[0][2] * ma[1][1] * ma[2][0]
                        - ma[0][0] * ma[1][2] * ma[2][1]
                        - ma[0][1] * ma[1][0] * ma[2][2]
                        )

                    if determ == 0:
                        points_2d[:, index] = empty
                        continue

                    points_2d[0, index] = (
                          ma[0][3] * ma[1][1] * ma[2][2]
                        + ma[0][1] * ma[1][2] * ma[2][3]
                        + ma[0][2] * ma[1][3] * ma[2][1]
                        - ma[0][2] * ma[1][1] * ma[2][3]
                        - ma[0][3] * ma[1][2] * ma[2][1]
                        - ma[0][1] * ma[1][3] * ma[2][2]
                        )
                    points_2d[1, index] = (
                          ma[0][0] * ma[1][3] * ma[2][2]
                        + ma[0][3] * ma[1][2] * ma[2][0]
                        + ma[0][2] * ma[1][0] * ma[2][3]
                        - ma[0][2] * ma[1][3] * ma[2][0]
                        - ma[0][0] * ma[1][2] * ma[2][3]
                        - ma[0][3] * ma[1][0] * ma[2][2]
                        )

                    points_2d[:, index] *= factor / determ

                    if flip:
                        points_2d[1, index] = -points_2d[1, index]

                    points_2d[:, index] += offset

            ma = np.array([
                [self._KBXX, self._KBYX, 0.0, -self._KNX],
                [self._KBXY, self._KBYY, 0.0, -self._KNY],
                [self._KBXZ, self._KBYZ, 0.0, -self._KNZ],
                ], dtype = 'f4')
            kpos = np.array([
                self._KPosX,
                self._KPosY,
                self._KPosZ,
                ], dtype = 'f4')
            empty = np.array([
                np.nan,
                np.nan,
                ], dtype = 'f4')
            offset = np.array([
                self._cx,
                self._cy,
                ], dtype = 'f4')

            get_points_jit(
                points_3d, points_2d,
                ma, kpos, empty, offset,
                )

        return get_points

    @staticmethod
    def _abs(x, y, z):

        return math.sqrt(x ** 2 + y ** 2 + z ** 2)
