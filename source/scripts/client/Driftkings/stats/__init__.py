# -*- coding: utf-8 -*-
"""Vehicle data and rating calculations for the unified Driftkings package."""
__CORE_NAME__ = 'Driftkings.stats'

__all__ = ('getVehicleInfoData', 'calculateXvmScale', 'calculateXTDB', 'calculateXTE',
           'xvm_stat', 'scaleValuesInstance')

from .vehinfo import getVehicleInfoData, calculateXvmScale, calculateXTDB, calculateXTE, scaleValuesInstance
from .xvm_stats import xvm_stat
