from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class P2PTransaction(Base):
    __tablename__ = 'p2p_transactions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String, nullable=False)  # 'buy' or 'sell'
    date = Column(DateTime, default=datetime.now)
    comment = Column(String, nullable=True)

    def __repr__(self):
        return f"<P2PTransaction(user_id={self.user_id}, amount={self.amount}, date={self.date}, type={self.transaction_type})>"

def init_db(database_url):
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session() 