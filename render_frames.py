#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

Earthquakes / Erdbeben 2010-2019
source code behind https://www.youtube.com/watch?v=RLHM5MQ5kAs
https://github.com/pleiszenburg/earthquakes_youtube01

    render_frames.py: Rendering video frames as PNGs in parallel

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
import multiprocessing as mp
import os

import tqdm

import numpy as np
import numba as nb
import zarr

from lib.camera import Camera
from lib.image import Image
from lib.osm import read_osm

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# HELPER
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

_rad = lambda x: x * math.pi / 180.0

def _polar_to_cart(lon, lat, length):

    lon = _rad(lon)
    lat = _rad(lat)

    x = length * math.cos(lat) * math.cos(lon)
    y = length * math.cos(lat) * math.sin(lon)
    z = length * math.sin(lat)

    return x, y, z

def _polar_to_cart_geometries(polar, r):
    cart = []
    for collection_index, collection in enumerate(polar):
        for poly_index, poly in enumerate(collection):
            for subpoly_index, subpoly in enumerate(poly):
                cart.append([
                    _polar_to_cart(*point, r)
                    for point in subpoly
                ])
    return cart

def _distance(a, b):
    return math.sqrt(
        (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2
    )

def _filter_polygons(in_poly, max_distance = 700000):

    out_poly = []
    out_line = []

    for in_line in in_poly:

        out_line.clear()
        out_line.append( in_line[0] ) # A

        for A, B in zip(in_line[:-1], in_line[1:]):

            if _distance(A, B) > max_distance:
                if len(out_line) > 1:
                    out_poly.append(out_line.copy())
                out_line.clear()

            out_line.append(B)

        if len(out_line) > 1:
            out_poly.append(out_line.copy())
        out_line.clear()

    return out_poly

@nb.jit(nopython = True)
def _polar_to_cart_jit(lon, lat, length):

    lon = lon * math.pi / 180.0
    lat = lat * math.pi / 180.0

    return [
        length * np.cos(lat) * np.cos(lon),
        length * np.cos(lat) * np.sin(lon),
        length * np.sin(lat),
    ]

def _np_polar_to_cart(in_data, r):

    out_data = np.zeros((3, in_data.shape[1]), dtype = 'f4')
    for index in range(0, in_data.shape[1]):
        out_data[:, index] = _polar_to_cart_jit(
            lon = in_data[0, index],
            lat = in_data[1, index],
            length = r - (in_data[2, index] * 6000),
        )

    return out_data

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# PARALLEL WORKER
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def _worker_init(kwargs):
    global context
    context = _worker_context(**kwargs)

def _worker_work(frame_index):
    context.render_frame(frame_index)

class _worker_context:

    def __init__(self, fps, duration, W, H, R, osm_cart, usgs_cart):

        self._id = mp.current_process().name
        self._fps = fps
        self._duration = duration
        self._W = W
        self._H = H
        self._R = R
        self._osm_cart = osm_cart
        self._usgs_cart = usgs_cart

        self._dist = 3.0 * self._R
        self._frames = self._duration * self._fps

        self._camera = Camera()
        self._camera.set_focal(50.0)
        self._camera.set_factor(30)
        self._camera.set_center(self._W / 2, self._H / 2)

        self._usgs_cart_2d = np.zeros((2, self._usgs_cart.shape[1]), dtype = 'f4')

    def render_frame(self, frame_index):

        angle = 2 * math.pi * frame_index / self._frames

        self._camera.set_position(self._dist * math.cos(angle), self._dist * math.sin(angle), 0.0)
        self._camera.set_direction(_rad(180.0) + angle, 0.0)
        get_points = self._camera.compiled_get_points()

        image = Image(self._W, self._H, background_color = (0.1, 0.1, 0.1))

        for line in self._osm_cart:
            image.draw_polygon(
                *[self._camera.get_point(*point) for point in line],
                line_color = (0.7, 0.7, 0.7),
                line_width = 0.3,
            )

        get_points(self._usgs_cart, self._usgs_cart_2d)
        for index in range(self._usgs_cart_2d.shape[1]):
            image.draw_filledcircle(
                *self._usgs_cart_2d[:, index], r = 1.0,
                fill_color = (1.0, 0.0, 0.0),
            )

        image.save(os.path.join('frames', f'frame_{frame_index:05d}.png'))

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# MAIN ROUTINE
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def run():

    W, H = 1920, 1080
    R = 6371000.0

    fps = 60
    duration = 120

    DATA_OSM = os.path.join('data_osm', 'earth-seas-10km.geo.json')
    DATA_USGS = 'data_usgs.zarr'

    CPU_LEN = mp.cpu_count()

    print(f'Running in {CPU_LEN:d} processes!')

    print('Reading data ...')

    osm_polar = read_osm(DATA_OSM)
    osm_cart = _filter_polygons(_polar_to_cart_geometries(osm_polar, R))

    usgs = zarr.open(DATA_USGS, 'r')
    usgs_cart = _np_polar_to_cart(usgs['data'][:3, :], R)

    print('Starting workers ...')

    cpu_pool = mp.Pool(
        processes = CPU_LEN,
        initializer = _worker_init,
        initargs = (dict(
            fps = fps, duration = duration,
            W = W, H = H, R = R,
            osm_cart = osm_cart, usgs_cart = usgs_cart,
        ),),
    )

    print('Rendering ...')

    os.mkdir('frames')

    frame_indexes_before = range(0, duration * fps) # frame indexes
    pool_results = [
        cpu_pool.apply_async(
            _worker_work,
            args = (frame_index,)
        ) for frame_index in frame_indexes_before
        ]
    frame_indexes_after = [result.get() for result in tqdm.tqdm(pool_results)]

if __name__ == '__main__':
    run()
