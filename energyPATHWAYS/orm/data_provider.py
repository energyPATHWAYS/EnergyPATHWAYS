import os
import sqlalchemy
import sqlalchemy.orm
from sqlalchemy.engine.url import URL
import pandas as pd
import dbConf

from alchemy_util import engine, Session, Base, metadata
#import ipdb

frames = {}

def load(table, id_):
    if table not in frames:
        refresh(table)

    # FIXME: this makes the assumption that the id column is always the first index;
    # we should discuss whether we want to guarantee this in the database or if there's something we should do
    # in refresh() to guarantee it
    df = frames[table].loc[id_]

    # drop indexes that are entirely unused for this subset of the data
    empty_indexes = [idx for idx, label in enumerate(df.index.labels) if all(elem == -1 for elem in label)]
    df.reset_index(level=empty_indexes, drop=True, inplace=True)

    return df

# table here is assumed to be an instance of sqlalchemy.Table
def refresh(table):
    # column.key is the column name; any column that doesn't contain the value for the row is an index
    indexes = [column.key for column in table.columns if column.key != 'value']
    #query = session.query(table)
    frames[table] = pd.read_sql_table(table.name, engine, index_col=indexes).sort_index()


def save(table, id_, df, session=None, refresh_after=True):
    internalSession = False
    if session is None: 
        session = Session()
        internalSession = True
    # FIXME: need to add id column!
    del_rows = session.query(table).filter(table.c.id == id_)

    # TODO: I wanted the deleting and writing here to all be in one transaction, but it appears that
    # DataFrame.to_sql() goes straight to the engine and bypasses the session so I'm not sure we can get it
    # in the same transaction using this method. We obtain some measure of safety by not committing the
    # deletion until after the writing of the new rows completes.
    del_rows.delete(synchronize_session=False)

    write_df = df.copy()
    write_df['id'] = id_
    write_df.to_sql(table.name, engine, if_exists='append')

    session.commit()

    if refresh_after:
        refresh(table)

    if internalSession: 
        session.commit()
        session.close()


if __name__ == '__main__':
    print 'testing data provider'
    df = simpleLoad('DemandDriversData')
    print(df)