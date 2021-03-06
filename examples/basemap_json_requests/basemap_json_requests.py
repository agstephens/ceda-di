#! /usr/bin/env python

import json
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import requests

font = {
    'family' : 'sans-serif',
    'size'   : 4
}

matplotlib.rc('font', **font)

with open("./sample_es_query.json") as f:
    payload = f.read()


r = requests.get("http://fatcat-test.jc.rl.ac.uk:9200/badc/eufar/_search", data=payload)
if r.status_code == 200:
    resp = json.loads(r.content)

    m = Basemap(projection='gall',
                resolution='f',
                llcrnrlon=(-180.0),
                llcrnrlat=(-90.0),
                urcrnrlon=(180.0),
                urcrnrlat=(90.0))

    m.drawcoastlines()
    m.fillcontinents(color='coral',lake_color='aqua')
    m.drawmapboundary(fill_color='aqua')

    for hit in resp["hits"]["hits"]:
        data = hit["_source"]

        if data["spatial"] is not None:
            xs = [c[0] for c in data["spatial"]["geometries"]["coordinates"]]
            ys = [c[1] for c in data["spatial"]["geometries"]["coordinates"]]
            maxx = max(xs)
            minx = min(xs)

            maxy = max(ys)
            miny = min(ys)

            m.plot(xs, ys, lw=0.5, latlon=True)

    plt.savefig("out.png", dpi=320, bbox_inches='tight')
