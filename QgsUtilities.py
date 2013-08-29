# -*- coding: utf-8 -*-
#
#------ QgsUtilities.py ---- 
# v 0.1 2011 Feb 24: initital release
# 
# 
#
# (c) 2011 CMHK Radio Network
#

from qgis.core import *

#Transform Coordinate
def CoorTransform(point, crs_src, crs_des):
    transformer = QgsCoordinateTransform(crs_src, crs_des)
    pt = transformer.transform(point)
    
    return pt