from enum import Enum


# The Enum with all game modes. Using array of teams instead of number, since there may be asymmetrical game modes.
class GameMode(Enum):
    FFA = (0, [], False, "FFA")
    DUEL = (2, [], False, "1v1")
    FIXED2V2 = (4, [2, 2], False, "2v2 Fixed Teams")
    FIXED3V3 = (6, [3, 3], False, "3v3 Fixed Teams")
    FIXED4V4 = (8, [4, 4], False, "3v3 Fixed Teams")
    FIXED2V2V2 = (6, [2, 2, 2], False, "2v2v2 Fixed Teams")
    FIXED2V2V2V2 = (8, [2, 2, 2, 2], False, "2v2v2v2 Fixed Teams")
    RANDOM2V2 = (4, [2, 2], True, "2v2 Random Teams")
    RANDOM3V3 = (6, [3, 3], True, "3v3 Random Teams")
    RANDOM4V4 = (8, [4, 4], True, "3v3 Random Teams")
    RANDOM2V2V2 = (6, [2, 2, 2], True, "2v2v2 Random Teams")
    RANDOM2V2V2V2 = (8, [2, 2, 2, 2], True, "2v2v2v2 Random Teams")
    AI = (0, [], False, "vs AI")

    def __init__(self, player_num, teams, random, full_name):
        self.player_num = player_num
        self.teams = teams
        self.random = random
        self.full_name = full_name
