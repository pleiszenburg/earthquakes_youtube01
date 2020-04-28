# -*- coding: utf-8 -*-

"""

Earthquakes / Erdbeben 2010-2019
source code behind https://www.youtube.com/watch?v=RLHM5MQ5kAs
https://github.com/pleiszenburg/earthquakes_youtube01

    lib/usgs.py: Handling USGS data

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

import datetime
import os
import re

import requests
import tqdm

import zarr
from numcodecs import Blosc

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# API
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def fetch_usgs(fld, a, b):

    for d1, d2 in _date_interval_range(a, b):

        r = requests.get(
            'https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&'
            f'starttime={d1[0]:04d}-{d1[1]:02d}-{d1[2]:02d}&endtime={d2[0]:04d}-{d2[1]:02d}-{d2[2]:02d}'
        )
        with open(os.path.join(fld, f'{d1[0]:04d}-{d1[1]:02d}-{d1[2]:02d}.csv'), 'w', encoding = 'utf-8') as f:
            f.write(r.text)

def reencode_usgs(src_fld, target):

    usgs_data_raw = []

    for fn in tqdm.tqdm(os.listdir(src_fld)):
        if not fn.endswith('.csv'):
            continue
        usgs_data_raw.extend( _read_usgs_csv( os.path.join(src_fld, fn) ) )

    usgs_data = [quake for quake in usgs_data_raw if _quake_ok(quake)]
    print(f'Quakes ok={len(usgs_data):d} broken={len(usgs_data_raw)-len(usgs_data):d}')

    usgs_data.sort(key = lambda x: x['time'])

    usgs_zarr = zarr.open(
        target,
        'w',
    )

    usgs_zarr.zeros(
        'time',
        shape = (len(usgs_data),),
        chunks = (10000,),
        dtype = 'u8',
        compressor = Blosc(cname = 'lz4'),
    )
    usgs_zarr['time'][:] = [int(quake['time'].timestamp() * 1000) for quake in usgs_data]

    fields = ['lon', 'lat', 'depth', 'mag', 'horizontalError', 'depthError', 'magError']
    usgs_zarr.zeros(
        'data',
        shape = (len(fields), len(usgs_data)),
        chunks = (len(fields), 10000,),
        dtype = 'f4',
        compressor = Blosc(cname = 'lz4'),
    )
    usgs_zarr.attrs['fields'] = fields
    for field_index, field in enumerate(fields):
        usgs_zarr['data'][field_index, :] = [quake[field] for quake in usgs_data]

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# HELPER
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def _date_interval_range(a, b):

    A = datetime.datetime.strptime(f'{a[0]:04d}-{a[1]:02d}-{a[2]:02d}', '%Y-%m-%d')
    B = datetime.datetime.strptime(f'{b[0]:04d}-{b[1]:02d}-{b[2]:02d}', '%Y-%m-%d')

    for c1, c2 in zip( range(0, (B - A).days), range(1, (B - A).days + 1) ):
        C1 = A + datetime.timedelta(days = c1)
        C2 = A + datetime.timedelta(days = c2)
        yield (C1.year, C1.month, C1.day), (C2.year, C2.month, C2.day)

def _parse_date_str(date_str):
    if '1970-01-01T00:00:00.0Z' == date_str:
        date_str = '1970-01-01T00:00:00.000Z'
    return datetime.datetime.fromisoformat(
        date_str[:-1] + '+00:00'
    )

def _read_usgs_csv(fn):

    with open(fn, 'r', encoding = 'utf-8') as f:
        header = _split( next(f).strip('\n') )
        out = [
            {
                k: v for k, v in zip(header, _split(line.strip('\n')))
            }
            for line in f
            if len(line.strip()) != 0
        ]
    return [
        {
            'time': _parse_date_str(q['time']),
            'lat': float(q['latitude']) if len(q['latitude']) != 0 else None,
            'lon': float(q['longitude']) if len(q['longitude']) != 0 else None,
            'depth': float(q['depth']) if len(q['depth']) != 0 else None,
            'mag': float(q['mag']) if len(q['mag']) != 0 else None,
            'horizontalError': float(q['horizontalError']) if len(q['horizontalError']) != 0 else None,
            'depthError': float(q['depthError']) if len(q['depthError']) != 0 else None,
            'magError': float(q['magError']) if len(q['magError']) != 0 else None,
        }
        for q in out
    ]

def _quake_ok(quake):
    return all([
        quake['lat'] is not None,
        quake['lon'] is not None,
        quake['depth'] is not None,
    ])

_split = lambda x: re.split(''',(?=(?:[^'"]|'[^']*'|"[^"]*")*$)''', x)
