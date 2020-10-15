from sqlalchemy.orm import sessionmaker, Query
from sqlalchemy import create_engine
from db.model import Base, Platform, State, Mode, Player, Game
from game_modes import GameMode


class DatabaseFacade:

    def __init__(self, connection_string):
        engine = create_engine(connection_string, echo=True)
        maker = sessionmaker(bind=engine)
        self.session = maker()
        Base.metadata.create_all(engine)
        self.__init_on_startup()

    # All the database stuff will be incapsulated in this class

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

    def get_player_by_did(self, player_did: int) -> Player:
        query_result: Query = self.session.query(Player).filter_by(did=player_did)

        if query_result.count() == 0:
            new_user = Player()
            new_user.did = player_did
            self.session.add(new_user)
            self.session.commit()
            return new_user
        elif query_result.count() >= 0:
            print("ERROR: Duplicate User Discord ID in Database: {}".format(
                player_did,
            ))
        else:
            return query_result.first()

    def add_game(self, creator_did: int, platform: str):

        # channel_id = Column(Integer)
        # channel_id = ????

        # state_id = Column(Integer, ForeignKey('states.id'))
        # state = relationship('State', back_populates='games')
        state = "WAITING"
        state_id_query: Query = self.session.query(State).filter_by(name=state)
        state_id = state_id_query.first().id

        # creator = relationship('User', back_populates='games')
        # creator_id = Column(Integer, ForeignKey('users.id'))
        creator_id = self.get_player_by_did(creator_did).id

        # platform_id = Column(Integer, ForeignKey('platforms.id'))
        # platform = relationship('Platform', back_populates='games')
        # mode_id = Column(Integer, ForeignKey('modes.id'))
        # mode = relationship('Mode', back_populates='games')
        # created_at = Column(DateTime)
        # started_at = Column(DateTime)
        # finished_at = Column(DateTime)
        # message_did = Column(String)
        # game_message_did = Column(String)
        # player_number = Column(Integer)
        # teams_available = Column(Boolean)
        # randomize_teams = Column(Boolean)
        # teams = relationship('Team')
        self.session.add(game)
        self.session.commit()


