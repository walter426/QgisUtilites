'/***************************************************************************
'                               QGS Utilities
'                             -------------------
'    begin                : 2013-07-23
'    copyright            : (C) 2013 by Walter Tsui
'    email                : waltertech426@gmail.com
' ***************************************************************************/

'/***************************************************************************
' *                                                                         *
' *   This program is free software; you can redistribute it and/or modify  *
' *   it under the terms of the GNU General Public License as published by  *
' *   the Free Software Foundation; either version 2 of the License, or     *
' *   (at your option) any later version.                                   *
' *                                                                         *
' ***************************************************************************/

from qgis.core import *

from math import *

from PlanTool.tools.generic.textmarker import *    #used for labelling

#Coordinate Transform by crs id
def CoorTransformByCrsId(point, crs_id_src, crs_id_des):
    crs_src = QgsCoordinateReferenceSystem()
    crs_src.createFromSrid(crs_id_src)

    crs_des = QgsCoordinateReferenceSystem()
    crs_des.createFromSrid(crs_id_des)

    transformer = QgsCoordinateTransform(crs_src, crs_des)
    pt = transformer.transform(point)
    
    return pt
    
    
#Coordinate Transform
def CoorTransform(point, crs_src, crs_des):
    transformer = QgsCoordinateTransform(crs_src, crs_des)
    pt = transformer.transform(point)
    
    return pt
    
#Draw Vectors according to an candidate list 
def DrawVectorsInCandList(mapCanvas, CandFldName, CandList, VL, TextMakerList_l, color, RubberBand_l):
    #QMessageBox.information(None, "OK", str(CandList))
    
    for item in TextMakerList_l:
        mapCanvas.scene().removeItem(item)
        
    if len(CandList) <= 0:
        RubberBand_l.reset(False)
        return
    
    str_find = ""
    
    for item in CandList:
        str_find = str_find + 'or ' + CandFldName + '=\'' + item + '\''       
    
    str_find = str_find.lstrip('or ')
    
    VL.removeSelection(False)    
    VL.setSubsetString(str_find)
    VL.invertSelection()
    VL.setSubsetString("")

    featlist = VL.selectedFeatures()
    
    if VL.selectedFeatureCount == 0:
       return
    
    fNIdx_Cand = VL.fieldNameIndex(CandFldName)
    Qgs_MPL = QgsGeometry().asMultiPolyline()
    
    
    VL_crs = QgsCoordinateReferenceSystem()
    VL_crs.createFromEpsg(VL.crs().epsg())
    mapCanvas_crs = mapCanvas.mapRenderer().destinationCrs()
    
    for feature in featlist:
        QgsPoint_O = feature.geometry().vertexAt(0)
        QgsPoint_O = CoorTransform(QgsPoint_O, VL_crs, mapCanvas_crs)

        QgsPoint_D = feature.geometry().vertexAt(1)
        QgsPoint_D = CoorTransform(QgsPoint_D, VL_crs, mapCanvas_crs)
        
        #Create Cell ID label for the indicated vector
        Dist = sqrt(QgsPoint_O.sqrDist(QgsPoint_D))
        
        v_OD = [QgsPoint_D.x() - QgsPoint_O.x(), QgsPoint_D.y() - QgsPoint_O.y()]
        v_OL = [-v_OD[0]/2, -v_OD[1]/2]

        QgsPoint_L = QgsPoint(v_OL[0] + QgsPoint_O.x(), v_OL[1] + QgsPoint_O.y())
        
        TextMaker_l = TextMarker(mapCanvas)
        TextMaker_l.setColor(color)
        TextMaker_l.text(feature.attributeMap()[fNIdx_Cand].toString())
        
        TextMaker_l.setMapPosition(QgsPoint_L)
        TextMakerList_l.append(TextMaker_l)        

        Qgs_MPL.append([QgsPoint_O, QgsPoint_D])
    
    #QMessageBox.information(None, "OK", str(len(featlist)))
    RubberBand_l.reset(False)
    RubberBand_l.setColor(color)
    RubberBand_l.setWidth(2)
    RubberBand_l.setToGeometry(QgsGeometry.fromMultiPolyline(Qgs_MPL), None)
    RubberBand_l.show()
   
   