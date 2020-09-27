from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Table
from sqlalchemy.orm import relationship
from bot_core import Base

user_team_association = Table('user_team_association', Base.metadata,
                                    Column('user_id', Integer, ForeignKey('users.id')),
                                    Column('team_id', Integer, ForeignKey('teams.id'))
                                    )

# Defines the unique user based on unique discord id
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    did = Column(Integer)
    players = relationship("UserGameRelation", back_populates='user')
    teams = relationship("User", secondary=user_team_association, back_populates="users")
    # Here be something else we want to store about the user


# Defines the game
class Game(Base):
    __tablename__ = 'games'
    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer)
    state_id = Column(Integer, ForeignKey('states.id'))
    state = relationship('State', back_populates='games')
    creator_id = Column(Integer, ForeignKey('users.id'))
    creator = relationship('User', back_populates='games_by_creator')
    platform_id = Column(Integer, ForeignKey('platforms.id'))
    platform = relationship('Platform', back_populates='games_by_platform')
    mode_id = Column(Integer, ForeignKey('modes.id'))
    mode = relationship('Mode', back_populates='games_by_mode')
    created_at = Column(DateTime)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    message_did = Column(Integer)
    game_message_did = Column(Integer)
    player_number = Column(Integer)
    teams_available = Column(Boolean)
    randomize_teams = Column(Boolean)


# Defines the game state (WAITING, IN PROGRESS, FINISHED, CANCELLED)
class State(Base):
    __tablename__ = 'states'
    id = Column(Integer, primary_key=True)
    name = Column(String)


# Defines the platforms (PC, PS, XBOX)
class Platform(Base):
    __tablename__ = 'platforms'
    id = Column(Integer, primary_key=True)
    name = Column(String)


# Defines the game modes (whatever we have here)
class Mode(Base):
    __tablename__ = 'modes'
    id = Column(Integer, primary_key=True)
    name = Column(String)


# Defines a team in terms of the game lobby. "Team 0" is for the players without teams
class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True)
    number = Column(Integer)
    size = Column(Integer)
    game_id = Column(Integer, ForeignKey('games.id'))
    game = relationship('Game', back_populates='teams')
    users = relationship("User", secondary=user_team_association, back_populates="teams")


# Not the best solution, but this is the table to report results
class GameResult(Base):
    __tablename__ = 'results'
    id = Column(Integer, primary_key=True)
    winners_id = Column(Integer, ForeignKey('teams.id'))
    winners = relationship('Team', back_populates='result')
    mode_id = Column(Integer, ForeignKey('modes.id'))
    mode = relationship('Mode', back_populates='games_by_mode')


# We need to persist various properties/settings as well. We just keep it as key/value pairs
class Property(Base):
    __tablename__ = 'properties'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    value = Column(String)

# TODO: Add the actual result reporting (don't know how are we going to do it yet
