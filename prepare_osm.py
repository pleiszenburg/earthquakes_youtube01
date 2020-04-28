#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

Earthquakes / Erdbeben 2010-2019
source code behind https://www.youtube.com/watch?v=RLHM5MQ5kAs
https://github.com/pleiszenburg/earthquakes_youtube01

    prepare_osm.py: Fetching OSM data

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

import os

from lib.osm import fetch_osm

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# MAIN ROUTINE
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def run():

    os.mkdir('data_osm')
    fetch_osm(
        path = os.path.join('data_osm', 'earth-seas-10km.geo.json'),
        url = 'https://github.com/simonepri/geo-maps/releases/latest/download/earth-seas-10km.geo.json',
        )

if __name__ == '__main__':
    run()
