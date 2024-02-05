import json
import urllib.parse

import pandas as pd
from sqlalchemy import create_engine

import connections


def getEngine(server, database, driver, Trusted_Connection='yes',
              autocommit=True, fast_executemany=True, user='', pwd=''):
    """ Create a connection to a sql server via sqlalchemy
    Arguments:
    server -- The server name (str). e.g.: 'SQL2012PROD03'
    database -- The specific database within the server (str). e.g.: 'LowFlows'
    driver -- The driver to use for the connection (str). e.g.: SQL Server
    trusted_conn -- Is the connection to be trusted. 'Yes' or 'No' (str).
    """

    if driver == 'SQL Server':
        engine = create_engine(
            f"mssql+pyodbc://{server}/{database}"
            f"?driver={driver}"
            f"&Trusted_Connection={Trusted_Connection}"
            f"&autocommit={autocommit}",
            fast_executemany=fast_executemany
        )
    elif driver == 'postgresql':
        user = urllib.parse.quote_plus(user)
        pwd = urllib.parse.quote_plus(pwd)
        engine = create_engine(
            f"postgresql+psycopg2://{user}:{pwd}@{server}/{database}"
        )
    else:
        raise NotImplementedError('No other connections supported')
    return engine


def main():
    """
    doc
    """

    data = []
    for file in connections.VIANOVA_EXTRACT:
        df = pd.read_csv(file)

        df['DateRanges'] = df['DateRanges'].apply(lambda x: eval(x))
        df['DateRanges'] = df['DateRanges'].apply(
                lambda x: json.dumps(x, default=str)
        )
        data.append(df)

    data = pd.concat(data)

    con = getEngine(**connections.VIANOVA_LOAD)

    data.to_sql(
        name='livraisons',
        schema='vnv',
        con=con,
        if_exists='replace',
        dtype=connections.VIANOVA_DATA_TYPES
    )


if __name__ == '__main__':
    main()
