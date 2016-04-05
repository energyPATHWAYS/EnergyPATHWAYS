from data_source import Base
from sqlalchemy import Column, Integer, Text, Float, ForeignKey, PrimaryKeyConstraint, text


class OtherIndex(Base):
    __tablename__ = 'OtherIndexes'

    id = Column(Integer, primary_key=True) #, server_default=text("nextval('\"OtherIndexes_id_seq\"'::regclass)"))
    name = Column(Text, unique=True)