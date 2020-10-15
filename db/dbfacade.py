from sqlalchemy.orm import sessionmaker, Query
from sqlalchemy import create_engine
from db.model import Base, Platform, State, Mode, User, Game
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

    def get_user_by_did(self, user_did: int, user_name: str) -> User:
        query_result: Query = self.session.query(User).filter_by(did=user_did)

        if query_result.count() == 0:
            new_user = User()
            new_user.did = user_did
            new_user.name = user_name
            self.session.add(new_user)
            self.session.commit()
            return new_user
        elif query_result.count() >= 0:
            print("ERROR: Duplicate User Discord ID in Database: {}, {}".format(
                user_did,
                user_name
            ))
        else:
            return query_result.first()

    def add_game(self, game: Game):
        self.session.add(game)
        self.session.commit()


