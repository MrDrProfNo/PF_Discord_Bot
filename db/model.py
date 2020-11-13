from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

player_team_association = Table('player_team_association', Base.metadata,
                              Column('player_id', Integer, ForeignKey('players.id')),
                              Column('team_id', Integer, ForeignKey('teams.id'))
                              )


# Defines the unique player based on unique discord id
class Player(Base):
    __tablename__ = 'players'
    id = Column(Integer, primary_key=True)
    did = Column(String)
    teams = relationship("Team", secondary=player_team_association, back_populates="players")
    games = relationship("Game")
    # Here be something else we want to store about the player


# Defines the game
class Game(Base):
    __tablename__ = 'games'
    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer)
    state_id = Column(Integer, ForeignKey('states.id'))
    state = relationship('State', back_populates='games')
    creator_id = Column(Integer, ForeignKey('players.id'))
    creator = relationship('Player', back_populates='games')
    platform_id = Column(Integer, ForeignKey('platforms.id'))
    platform = relationship('Platform', back_populates='games')
    mode_id = Column(Integer, ForeignKey('modes.id'))
    mode = relationship('Mode', back_populates='games')
    created_at = Column(DateTime)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    message_did = Column(String)
    game_message_did = Column(String)
    player_number = Column(Integer)
    teams_available = Column(Boolean)
    randomize_teams = Column(Boolean)
    teams = relationship('Team')

    def __str__(self):
        teams_list_str = [str(team) for team in self.teams]

        team_str = "\n".join(teams_list_str)

        return f"creator_did: {self.creator.did} \
                \nmode: {self.mode.name} \
                \nplatform: {self.platform.name} \
                \ncreated_at: {self.created_at} \
                \nteams:\n{team_str}\
                \nmessage_did: {self.message_did}"


# Defines the game state (WAITING, IN PROGRESS, FINISHED, CANCELLED)
class State(Base):
    __tablename__ = 'states'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    games = relationship('Game')


# Defines the platforms (PC, PS, XBOX)
class Platform(Base):
    __tablename__ = 'platforms'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    games = relationship('Game')


# Defines the game modes (whatever we have here)
class Mode(Base):
    __tablename__ = 'modes'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    games = relationship('Game')


# Defines a team in terms of the game lobby. "Team 0" is for the players without teams
class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True)
    number = Column(Integer)
    size = Column(Integer)
    game_id = Column(Integer, ForeignKey('games.id'))
    game = relationship('Game', back_populates='teams')
    players = relationship("Player", secondary=player_team_association, back_populates="teams")

    def __str__(self):
        return (f"Team{{id={self.id}, number={self.number}, size={self.size},"
                f"game_id={self.game_id}, playercount={len(self.players)}}}")


# Not the best solution, but this is the table to report results
class GameResult(Base):
    __tablename__ = 'results'
    id = Column(Integer, primary_key=True)
    winners_id = Column(Integer, ForeignKey('teams.id'))
    winners = relationship('Team')
    mode_id = Column(Integer, ForeignKey('modes.id'))
    mode = relationship('Mode')


# We need to persist various properties/settings as well. We just keep it as key/value pairs
class Property(Base):
    __tablename__ = 'properties'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    value = Column(String)

# TODO: Add the actual result reporting (don't know how are we going to do it yet
