from sqlalchemy.orm import sessionmaker, Query
from sqlalchemy import create_engine
import sqlalchemy
from db.model import Base, Platform, State, Mode, Player, Game, Team, Property
from game_modes import GameMode



class DatabaseFacade:
    
    session = None

    def __init__(self, connection_string):
        engine = create_engine(connection_string, echo=True)
        maker = sessionmaker(bind=engine)
        global session
        session = maker()
        Base.metadata.create_all(engine)
        self.__init_on_startup()

    # All the database stuff will be encapsulated in this class

    # Sponsor of this code is Stackoverflow. Some magic with kwargs parsing
    def __create_if_absent(self, model, **kwargs):
        instance = session.query(model).filter_by(**kwargs).first()
        if instance is None:
            instance = model(**kwargs)
            session.add(instance)
            session.commit()

    # Here goes everything we need to pre-fill database on startup if neccessary
    def __init_on_startup(self):
        # Fill platforms
        self.__create_if_absent(Platform, name='PC')
        self.__create_if_absent(Platform, name='XBOX')
        self.__create_if_absent(Platform, name='PS4')

        # Fill states
        self.__create_if_absent(State, name='WAITING')
        self.__create_if_absent(State, name='IN PROGRESS')
        self.__create_if_absent(State, name='FINISHED')
        self.__create_if_absent(State, name='CANCELLED')

        # Fill game modes
        for i in GameMode:
            self.__create_if_absent(Mode, name=i.full_name)

        session.commit()

    @staticmethod
    def get_player_by_did(player_did: str) -> Player:
        query_result: Query = session.query(Player).filter_by(did=player_did)

        if query_result.count() == 0:
            new_user = Player()
            new_user.did = player_did
            session.add(new_user)
            session.commit()
            return new_user
        elif query_result.count() >= 2:
            print("ERROR: Duplicate User Discord ID in Database: {}".format(
                player_did,
            ))
            return
        else:
            return query_result.first()

    @staticmethod
    def add_game(creator_did: str, platform: str, mode: list,
                 message_did: str):

        print(f"Got mode: {mode}")

        creator: Player = DatabaseFacade.get_player_by_did(creator_did)

        new_game = Game()

        # state_id = Column(Integer, ForeignKey('states.id'))
        # state = relationship('State', back_populates='games')
        state = "WAITING"
        state_query: Query = session.query(State).filter_by(name=state)
        new_game.state_id = state_query.first().id

        # creator = relationship('User', back_populates='games')
        # creator_id = Column(Integer, ForeignKey('users.id'))
        new_game.creator_id = creator.id

        # platform_id = Column(Integer, ForeignKey('platforms.id'))
        # platform = relationship('Platform', back_populates='games')
        platform_query = session.query(Platform).filter_by(name=platform)
        new_game.platform_id = platform_query.first().id

        # mode_id = Column(Integer, ForeignKey('modes.id'))
        # mode = relationship('Mode', back_populates='games')
        mode_query = session.query(Mode).filter_by(name=mode[3])
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

        session.add(new_game)
        session.commit()

        team0 = Team()
        team0.number = 0
        team0.size = 12
        team0.game_id = new_game.id
        team0.players.append(creator)
        session.add(team0)

        # iterates over team sizes from the mode, and adjusts to 1-index
        for team_number in range(0, len(mode[1])):
            team = Team()
            team.number = team_number + 1
            team.size = mode[1][team_number]
            team.game_id = new_game.id

            session.add(team)

        session.commit()

        return new_game

    @staticmethod
    def get_game_by_id(game_id: int) -> Game:
        return session.query(Game).filter_by(id=game_id).first()

    @staticmethod
    def get_game_by_message_did(message_did: str) -> Game:
        return session.query(Game).filter_by(message_did=message_did).first()

    @staticmethod
    def get_game_by_game_message_did(game_message_did: str) -> Game:
        return session.query(Game).filter_by(
            game_message_did=game_message_did
        ).first()

    @staticmethod
    def get_game_by_channel_did(channel_did: str) -> Game:
        print(f"Get on channel with did {channel_did}")
        return session.query(Game).filter_by(
            channel_id=channel_did
        ).first()

    @staticmethod
    def update_game(game_id: int,
                    message_did: str = None,
                    game_message_did: str = None,
                    channel_did: str = None) -> None:
        game: Game = DatabaseFacade.get_game_by_id(game_id)

        if message_did is not None:
            game.message_did = message_did

        if game_message_did is not None:
            game.game_message_did = game_message_did

        if channel_did is not None:
            game.channel_id = channel_did

        session.commit()

    @staticmethod
    def get_property(property_name: str) -> Property:
        property_query = session.query(Property).filter_by(
            name=property_name
        )
        property_row = property_query.first()
        if property_row is not None:
            return property_row
        else:
            print(f"get_property on non-existent property: {property_name}")
            return None

    @staticmethod
    def set_property(prop_name: str, prop_value: str):
        print(f"prop({prop_name}, {prop_value})")
        prop: str = DatabaseFacade.get_property(prop_name)
        print(f"looked up {prop_name} and got: {str(prop)}")
        if prop is not None:
            prop.value = prop_value
            session.commit()
        else:
            prop = Property()
            session.add(prop)
            prop.name = prop_name
            prop.value = prop_value

            session.commit()
            return

    @staticmethod
    def add_player_to_team(game_id: int, team_number: int, player: Player):
        game: Game = DatabaseFacade.get_game_by_id(game_id)
        DatabaseFacade._add_player_to_team(game, team_number, player)

        session.commit()

    @staticmethod
    def _add_player_to_team(game: Game, team_number: int, player: Player):
        print(f"Adding player {player.id} to game: {game.id}, "
              f"team: {team_number}")
        team: Team = game.teams[team_number]
        if not player in team.players:
            team.players.append(player)

        session.commit()

    @staticmethod
    def add_player_to_game(game_id: int, player: Player):
        print(f"Adding player: {player.id} to game: {game_id}")
        game: Game = DatabaseFacade.get_game_by_id(game_id)
        # put them on team 0
        DatabaseFacade._add_player_to_team(game, 0, player)

        session.commit()

    @staticmethod
    def remove_player_from_game(game_id: int, player: Player):
        game: Game = DatabaseFacade.get_game_by_id(game_id)
        for team in game.teams:
            if player in team.players:
                print(f"Found {player} in team {team.id}")
                team.players.remove(player)
                session.commit()
            else:
                print(f"Didn't find {player} in team {team.id}")
