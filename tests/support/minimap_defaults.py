# -*- coding: utf-8 -*-
import json
import os
from support import ROOT as REPOSITORY

ROOT = os.path.join(REPOSITORY, 'res', 'configs', 'driftkings', 'default', 'minimap_enhancements')


def defaults():
    data = {}
    for name in ('minimap.json', 'minimap_labels.json', 'minimap_circles.json', 'minimap_lines.json'):
        with open(os.path.join(ROOT, name), 'rb') as stream:
            data.update(json.loads(stream.read().decode('utf-8-sig')))
    return data
