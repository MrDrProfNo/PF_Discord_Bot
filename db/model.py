from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from bot_core import Base


# Defines the unique user based on unique discord id
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    discord_id = Column(Integer)
    # Here be something else we want to store about the user


# Defines the game
class Game(Base):
    __tablename__ = 'games'
    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer)
    state_id = Column(Integer, ForeignKey('states.id'))
    state = relationship('State', back_populates='games')
    created_at = Column(DateTime)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    message_id = Column(Integer)


# Defines the game state (WAITING, IN PROGRESS, FINISHED, CANCELLED)
class State(Base):
    __tablename__ = 'states'
    id = Column(Integer, primary_key=True)
    name = Column(String)
