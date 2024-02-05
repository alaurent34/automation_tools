import sqlalchemy.sql.sqltypes.JSON

VIANOVA_EXTRACT = []
VIANOVA_LOAD = {
    'type': 'sql',
    'driver': 'postgresql',
    'server': '',
    'database': 'Staging',
    'user': '',
    'pwd': '',
    'fast_executemany': True
}

VIANOVA_DATA_TYPES = {
    'DateRanges': sqlalchemy.sql.sqltypes.JSON,
    'MetricsByVocation': sqlalchemy.sql.sqltypes.JSON,
    'MetricsByIndustry': sqlalchemy.sql.sqltypes.JSON,
    'MetricsByVehicleClass': sqlalchemy.sql.sqltypes.JSON,
    'MetricsByFuelType': sqlalchemy.sql.sqltypes.JSON,
    'OsmLandUse': sqlalchemy.sql.sqltypes.JSON,
    'StopLocation': sqlalchemy.sql.sqltypes.JSON
}
