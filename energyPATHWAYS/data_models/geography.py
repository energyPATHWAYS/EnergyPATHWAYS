from data_source import Base
from sqlalchemy import Column, Integer, Text, text

class Geography(Base):
    __tablename__ = 'Geographies'

    id = Column(Integer, primary_key=True) #, server_default=text("nextval('\"Geographies_id_seq\"'::regclass)"))
    name = Column(Text, unique=True)

class GeographyMapKey(Base):
    __tablename__ = 'GeographyMapKeys'

    id = Column(Integer, primary_key=True) #, server_default=text("nextval('\"GeographyMapKeys_id_seq\"'::regclass)"))
    name = Column(Text, unique=True)