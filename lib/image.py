# -*- coding: utf-8 -*-

"""

Earthquakes / Erdbeben 2010-2019
source code behind https://www.youtube.com/watch?v=RLHM5MQ5kAs
https://github.com/pleiszenburg/earthquakes_youtube01

    lib/image.py: Simple 2D cairo renderer

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

import cairo

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CLASS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class Image:

    def __init__(self, width, height, background_color = (1.0, 1.0, 1.0)):

        self._width, self._height = width, height
        self._surface = cairo.ImageSurface(cairo.FORMAT_RGB24, self._width, self._height)
        self._ctx = cairo.Context(self._surface)
        self._set_background_color(background_color)

    def save(self, fn):

        self._surface.write_to_png(fn)

    def draw_polygon(self,
        *points,
        **kwargs,
        ):

        assert len(points) >= 2
        self._ctx.move_to(*points[0])
        for point in points[1:]:
            self._ctx.line_to(*point)
        self._stroke(**kwargs)

    def draw_filledcircle(self,
        x = 0.0, y = 0.0, r = 1.0,
        fill_color = (1.0, 1.0, 1.0),
        ):

        self._ctx.arc(
            x, y, r,
            0, 2 * math.pi, # 0 to 360°
        )
        self._ctx.set_source_rgb(*fill_color)
        self._ctx.fill()

    def _stroke(self,
        line_color = (1.0, 1.0, 1.0),
        line_width = 1.0,
        **kwargs,
        ):

        self._ctx.set_source_rgb(*line_color)
        self._ctx.set_line_width(line_width)
        self._ctx.stroke()

    def _set_background_color(self,
        fill_color = (1.0, 1.0, 1.0),
        ):

        self._ctx.set_source_rgb(*fill_color)
        self._ctx.rectangle(0, 0, self._width, self._height)
        self._ctx.fill()
