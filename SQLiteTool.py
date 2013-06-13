# -*- coding: utf-8 -*-
#
#------ dofreq.py ---- 
# v 0.1 2011 Feb 24: initital release
# 
# 
#
# (c) 2011 CMHK Radio Network
#
#from PyQt4.QtCore import *
from PyQt4.QtGui import *
#from qgis.core import *
#from qgis.gui import *

import os

import pyodbc
import xlrd
import math  #use to calculate the bearing of arrows

from pyspatialite import dbapi2 as sqlite3

#Initialize SQLite Db
def InitializeSqliteDB(sqlite_path):
    if os.path.exists(sqlite_path) :
        os.remove(sqlite_path)
    
    try:
        sqlite_conn = sqlite3.connect(sqlite_path)
    except:
        return False
    
    sqlite_cursor = sqlite_conn.cursor()
    
    # initializing Spatial MetaData
    SQL_cmd = 'SELECT InitSpatialMetadata()'
    sqlite_cursor.execute(SQL_cmd)

    #delete unnecessary spatial_ref_sys as the file size is large
    SQL_cmd = 'DELETE FROM "spatial_ref_sys" where srid!= 2326 and srid!= 4326'
    sqlite_cursor.execute(SQL_cmd)
    
    SQL_cmd = 'VACUUM'
    sqlite_cursor.execute(SQL_cmd)
    
    sqlite_conn.commit()
    sqlite_conn.close()
    
    return True
        

def CreateTbl_SiteCoor(DB_SiteDB_path, sqlite_conn, Tbl_SiteCoor_name):
    SiteDB_conn = pyodbc.connect('DRIVER={Microsoft Access Driver (*.mdb)}; DBQ=' + DB_SiteDB_path)
    SiteDB_cursor = SiteDB_conn.cursor()
    
    sqlite_cursor = sqlite_conn.cursor()
    
    #Create Table of Site Coordinate

    Tbl_MST_name = "Master Site Table"
    
    SQLITE_cmd = 'CREATE TABLE [' + Tbl_SiteCoor_name + '] ([SiteID] TEXT, [HK1980] BLOB);'
    sqlite_cursor.execute(SQLITE_cmd)

    
    SQL_cmd = 'SELECT [Live_Site_ID], [Easting], [Northing] ' + \
                'FROM [' + Tbl_MST_name + '] ' + \
                'WHERE [Live_Site_ID] IS NOT NULL AND ([Site_Status_Idx] = 1 OR [Site_Status_Idx] = 18) ' + \
                'GROUP BY [Live_Site_ID], [Easting], [Northing] ' + \
                'ORDER BY [Live_Site_ID] ' + \
                ';'

                
    for row in SiteDB_cursor.execute(SQL_cmd):
        SQLITE_cmd = 'INSERT INTO [' + Tbl_SiteCoor_name + '] ([SiteID], [HK1980]) ' + \
                    "VALUES(" + '"' + row.Live_Site_ID + '", ' + "GeomFromText('POINT(" + str(row.Easting) + " " + str(row.Northing) + ")',2326) " + ") " \
                    ";"
                    
        sqlite_cursor.execute(SQLITE_cmd)
    
    sqlite_conn.commit
    
    AddSpatialiteGeometryCol(sqlite_conn, Tbl_SiteCoor_name, "POINT")
    
def CreateTbl_SiteAndCellCoorFromCellInfo(sqlite_conn, system):
    sqlite_cursor = sqlite_conn.cursor()
    
    SQLITE_cmd = "CREATE TABLE [CellCoor_" + system + "] AS " +\
                    "SELECT DISTINCT CellID, Azimuth, HK1980, WGS84 " +\
                    "FROM SiteDB." + system + "_cellinfo " +\
                    "GROUP BY [CellID] " +\
                    ";"
    sqlite_cursor.execute(SQLITE_cmd)
    
    SQLITE_cmd = "CREATE TABLE [SiteCoor_" + system + "] AS " +\
                    "SELECT DISTINCT SUBSTR([CellID], 1, LENGTH([CellID])-1) AS SiteID, StartPoint([hk1980]) AS HK1980, StartPoint([WGS84]) AS WGS84 " +\
                    "FROM SiteDB." + system + "_cellinfo  " +\
                    "GROUP BY [SiteID] " +\
                    ";"
    sqlite_cursor.execute(SQLITE_cmd)
    
    sqlite_conn.commit()
    
def DelTbl_SiteAndCellCoorFromCellInfo(sqlite_conn, system):
    sqlite_cursor = sqlite_conn.cursor()
    
    SQLITE_cmd = "DROP TABLE [CellCoor_" + system + "]"
    sqlite_cursor.execute(SQLITE_cmd)

    SQLITE_cmd = "DROP TABLE [SiteCoor_" + system + "]"
    sqlite_cursor.execute(SQLITE_cmd)
    sqlite_conn.commit()
    
#Create a table Joining Two SQLite points into a Line string
def CreateTbl_TwoPtsToLineStr(sqlite_conn, Tbl_CoorSrc_name, Tbl_input_name, Tbl_output_name, JoinCond_s, JoinCond_e):
    sqlite_cursor = sqlite_conn.cursor()
    
    Tbl_output_1_name = Tbl_output_name + "_temp_1"
    
    SQL_cmd = 'CREATE TABLE [' + Tbl_output_1_name + '] AS ' + \
                'SELECT [' + Tbl_input_name + '].*, [' + Tbl_CoorSrc_name + '].[WGS84] AS [WGS84_s], [' + Tbl_CoorSrc_name + '].[HK1980] AS [HK1980_s] ' + \
                'FROM [' + Tbl_input_name + '] INNER JOIN [' + Tbl_CoorSrc_name + '] ON ' + JoinCond_s + \
                ';'
    sqlite_cursor.execute(SQL_cmd)
    
    
    Tbl_output_2_name = Tbl_output_name + "_temp_2"
    JoinCond_e = JoinCond_e.replace(Tbl_input_name, Tbl_output_1_name)
    
    SQL_cmd = 'CREATE TABLE [' + Tbl_output_2_name + '] AS ' + \
                'SELECT [' + Tbl_output_1_name+ '].*, [' + Tbl_CoorSrc_name + '].[WGS84] AS [WGS84_e], [' + Tbl_CoorSrc_name + '].[HK1980] AS [HK1980_e] ' + \
                'FROM [' + Tbl_output_1_name + '] INNER JOIN [' + Tbl_CoorSrc_name + '] ON ' + JoinCond_e + \
                ';'
    sqlite_cursor.execute(SQL_cmd)
    
    SQL_cmd = "DROP TABLE [" + Tbl_output_1_name + "]"
    sqlite_cursor.execute(SQL_cmd)   
    
    
    SQL_cmd = 'CREATE TABLE [' + Tbl_output_name + '] AS ' + \
                "SELECT *, MakeLine([WGS84_s], [WGS84_e]) AS [WGS84], MakeLine([HK1980_s], [HK1980_e]) AS [HK1980], Round(GeodesicLength(MakeLine([WGS84_s], [WGS84_e]))) AS [Distance]" + \
                'FROM [' + Tbl_output_2_name + '] ' + \
                'WHERE [WGS84] IS NOT NULL AND [HK1980] IS NOT NULL' + \
                ';' 
    sqlite_cursor.execute(SQL_cmd)
    
    SQL_cmd = "DROP TABLE [" + Tbl_output_2_name + "]"
    sqlite_cursor.execute(SQL_cmd)   
    sqlite_conn.commit()
    
    #Recover the geometry columns
    RecoverSpatialiteGeometryCol(sqlite_conn, Tbl_output_name, 'LINESTRING')

#Delete Spatialite Geometry Column   
def DeleteTblWithGeoCol_SiteCoor(sqlite_conn, tbl_name):
    sqlite_cursor = sqlite_conn.cursor()
    
    SQL_cmd = "SELECT DiscardGeometryColumn('" + tbl_name + "', 'HK1980')"
    sqlite_cursor.execute(SQL_cmd)
    
    SQL_cmd = "SELECT DiscardGeometryColumn('" + tbl_name + "', 'WGS84')"
    sqlite_cursor.execute(SQL_cmd)

    SQL_cmd = "DROP TABLE [" + tbl_name + "]"
    sqlite_cursor.execute(SQL_cmd)
    
    sqlite_conn.commit

#Recover Spatialite Geometry Column    
def RecoverSpatialiteGeometryCol(sqlite_conn, tbl_name, type):
    sqlite_cursor = sqlite_conn.cursor()
    
    SQL_cmd = "SELECT RecoverGeometryColumn('" + tbl_name + "', 'HK1980', 2326, '" + type + "', 2)"
    sqlite_cursor.execute(SQL_cmd)

    SQL_cmd = "SELECT RecoverGeometryColumn('" + tbl_name + "', 'WGS84', 4326, '" + type + "', 2)"
    sqlite_cursor.execute(SQL_cmd)
    
    sqlite_conn.commit()

#Add Spatialite Geometry Column
def AddSpatialiteGeometryCol(sqlite_conn, tbl_name, type):
    sqlite_cursor = sqlite_conn.cursor()
    
    #recover geom column, 2326 = HK1980Grid, 4326 = WSG84
    SQL_cmd = "SELECT RecoverGeometryColumn('" + tbl_name + "', 'HK1980', 2326, '" + type + "' ,2)"
    sqlite_cursor.execute(SQL_cmd)

    SQL_cmd="SELECT AddGeometryColumn('" + tbl_name + "', 'WGS84', 4326, '" + type + "' ,2)"
    sqlite_cursor.execute(SQL_cmd)

    SQL_cmd = "UPDATE [" + tbl_name + "] SET [WGS84] = Transform([HK1980], 4326)"
    sqlite_cursor.execute(SQL_cmd)
    sqlite_conn.commit()

#Data Type Mapping from xlrd to SQLite
def CTypeMapping_xlrdToSQLite(ctype):
    if ctype == 0:
        SQLiteType = "NULL"
        
    elif ctype == 1:
        SQLiteType = "TEXT"
        
    elif ctype == 2:
        SQLiteType = "REAL"
        
    elif ctype == 3:
        SQLiteType = "DATE"
        
    elif ctype == 4:
        SQLiteType = "TEXT"

    elif ctype == 5:
        SQLiteType = "TEXT"
        
    elif ctype == 6:
        SQLiteType = "TEXT"
        
    else:
        SQLiteType = "TEXT"
        
    return SQLiteType