from data_source import Base
from sqlalchemy import Column, Integer, Text, text

class CleaningMethod(Base):
    __tablename__ = 'CleaningMethods'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"CleaningMethods_id_seq\"'::regclass)"))
    name = Column(Text, unique=True)

class InputType(Base):
    __tablename__ = 'InputTypes'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"InputTypes_id_seq\"'::regclass)"))
    name = Column(Text, unique=True)

class OtherIndex(Base):
    __tablename__ = 'OtherIndexes'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"OtherIndexes_id_seq\"'::regclass)"))
    name = Column(Text)