# Earthquakes / Erdbeben 2010-2019

[![Watch the video](https://img.youtube.com/vi/RLHM5MQ5kAs/maxresdefault.jpg)](https://youtu.be/RLHM5MQ5kAs)

10 years of earthquakes / 2010-01-01 to 2019-12-31 / 1356502 events / depth exaggerated by a factor of 6

## Open Data

- earthquakes: United States Geological Survey (USGS)
- contours: Copyright © OpenStreetMap contributors / Open Database License 1.0

# Open Source Software

- pycairo: 2D rendering
- custom ray-tracer: 3D to 2D
- numpy & numba: acceleration
- zarr: data handling & storage
- ffmpeg: video encoding

## Rendering the video yourself

Ensure that you have the following software installed:

- `python` (3.6 or newer)
- `cairo` (plus header / development files)
- `zlib` (plus header / development files)
- `ffmpeg`
- `gcc`
- `git`

Clone this repository from Github and change into its directory:

```bash
git clone https://github.com/pleiszenburg/earthquakes_youtube01.git
cd earthquakes_youtube01/
```

Create a new virtual environment if desired and activate it:

```bash
python3 -m venv env
source env/bin/activate
pip install -U pip setuptools
```

Now you can install the dependencies, fetch the data and render the video:

```bash
pip install -r requirements.txt
./prepare_osm.py
./prepare_usgs.py
./render_frames.py
./render_video.py
```
