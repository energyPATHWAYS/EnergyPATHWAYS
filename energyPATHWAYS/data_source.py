import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.url import URL
import pandas as pd

Base = declarative_base()


# For now we are expecting config to reach in and kick this since it has the config information
def init(db_conf):
    global engine
    engine = sa.create_engine(URL(**db_conf)) #,echo=True)
    global Session
    Session = sa.orm.sessionmaker(bind=engine)
    global session
    session = Session()


def fetch(cls):
    result = session.query(cls).all()
    # I was originally closing the session here, but that makes it impossible for the loaded objects to do
    # any additional lazy loading of their relationships
    return result


def fetch_as_dict(cls):
    return {obj.id: obj for obj in fetch(cls)}


def fetch_as_df(cls):
    # ignore the primary key column since it is not interesting for dataframe purposes
    cols = [column.key for column in cls.__mapper__.columns.values() if column.key != 'id']
    # any column that doesn't contain the value for the row is an index
    indexes = [col for col in cols if col != 'value']

    return pd.read_sql_table(cls.__tablename__, engine, columns=cols, index_col=indexes).sort_index()