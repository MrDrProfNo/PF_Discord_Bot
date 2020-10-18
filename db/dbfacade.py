from sqlalchemy.orm import sessionmaker, Query
from sqlalchemy import create_engine
import sqlalchemy
from db.model import Base, Platform, State, Mode, Player, Game, Team, Property
from game_modes import GameMode



class DatabaseFacade:

    def __init__(self, connection_string):
        engine = create_engine(connection_string, echo=True)
        maker = sessionmaker(bind=engine)
        self.session = maker()
        Base.metadata.create_all(engine)
        self.__init_on_startup()

    # All the database stuff will be encapsulated in this class

    # Sponsor of this code is Stackoverflow. Some magic with kwargs parsing
    def __create_if_absent(self, model, **kwargs):
        instance = self.session.query(model).filter_by(**kwargs).first()
        if instance is None:
            instance = model(**kwargs)
            self.session.add(instance)
            self.session.commit()

    # Here goes everything we need to pre-fill database on startup if neccessary
    def __init_on_startup(self):
        # Fill platforms
        self.__create_if_absent(Platform, name='PC')
        self.__create_if_absent(Platform, name='XBOX')
        self.__create_if_absent(Platform, name='PS')

        # Fill states
        self.__create_if_absent(State, name='WAITING')
        self.__create_if_absent(State, name='IN PROGRESS')
        self.__create_if_absent(State, name='FINISHED')
        self.__create_if_absent(State, name='CANCELLED')

        # Fill game modes
        for i in GameMode:
            self.__create_if_absent(Mode, name=i.full_name)

        self.session.commit()

    def get_player_by_did(self, player_did: str) -> Player:
        query_result: Query = self.session.query(Player).filter_by(did=player_did)

        if query_result.count() == 0:
            new_user = Player()
            new_user.did = player_did
            self.session.add(new_user)
            self.session.commit()
            return new_user
        elif query_result.count() >= 2:
            print("ERROR: Duplicate User Discord ID in Database: {}".format(
                player_did,
            ))
            return
        else:
            return query_result.first()

    def add_game(self, creator_did: str, platform: str, mode: str,
                 message_did: str):

        creator: Player = self.get_player_by_did(creator_did)

        new_game = Game()

        # state_id = Column(Integer, ForeignKey('states.id'))
        # state = relationship('State', back_populates='games')
        state = "WAITING"
        state_query: Query = self.session.query(State).filter_by(name=state)
        new_game.state_id = state_query.first().id

        # creator = relationship('User', back_populates='games')
        # creator_id = Column(Integer, ForeignKey('users.id'))
        new_game.creator_id = creator.id

        # platform_id = Column(Integer, ForeignKey('platforms.id'))
        # platform = relationship('Platform', back_populates='games')
        platform_query = self.session.query(Platform).filter_by(name=platform)
        new_game.platform_id = platform_query.first().id

        # mode_id = Column(Integer, ForeignKey('modes.id'))
        # mode = relationship('Mode', back_populates='games')
        mode_query = self.session.query(Mode).filter_by(name=mode[3])
        new_game.mode_id = mode_query.first().id

        # created_at = Column(DateTime)
        new_game.created_at = sqlalchemy.func.now()

        # started_at = Column(DateTime)
        # finished_at = Column(DateTime)
        # NOT ASSIGNED NOW

        # message_did = Column(String)
        # game_message_did = Column(String)
        new_game.message_did = message_did

        # player_number = Column(Integer)
        new_game.player_number = 0

        # teams_available = Column(Boolean)
        new_game.teams_available = True

        # randomize_teams = Column(Boolean)
        new_game.randomize_teams = mode[2]

        self.session.add(new_game)
        self.session.commit()

        team0 = Team()
        team0.number = 0
        team0.size = 12
        team0.game_id = new_game.id
        team0.players.append(creator)
        self.session.add(team0)

        # iterates over team sizes from the mode, and adjusts to 1-index
        for team_number in range(0, len(mode[1])):
            team = Team()
            team.number = team_number + 1
            team.size = mode[1][team_number]
            team.game_id = new_game.id

            self.session.add(team)

        self.session.commit()

        return new_game

    def get_game(self, game_id):
        return self.session.query(Game).filter_by(id=game_id).first()

    def get_property(self, property_name: str):
        property_query = self.session.query(Property).filter_by(
            name=property_name
        )
        property_row = property_query.first()
        if property_row is not None:
            return property_row.value
        else:
            print(f"get_property on non-existent property: {property_name}")
            return None
