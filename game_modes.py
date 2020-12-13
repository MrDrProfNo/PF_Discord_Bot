from enum import Enum


# The Enum with all game modes. Using array of teams instead of number, since there may be asymmetrical game modes.
class GameMode(Enum):
    FFA = (0, [], False, "FFA")
    DUEL = (2, [], False, "1v1")
    FIXED2v2 = (4, [2, 2], False, "2v2 Fixed Teams")
    FIXED3v3 = (6, [3, 3], False, "3v3 Fixed Teams")
    FIXED4v4 = (8, [4, 4], False, "4v4 Fixed Teams")
    FIXED5v5 = (10, [5, 5], False, "5v5 Fixed Teams")
    FIXED2v2v2 = (6, [2, 2, 2], False, "2v2v2 Fixed Teams")
    FIXED3v3v3 = (9, [3, 3, 3], False, "3v3v3 Fixed Teams")
    FIXED4v4v4 = (12, [4, 4, 4], False, "4v4v4 Fixed Teams")
    FIXED2v2v2v2 = (8, [2, 2, 2, 2], False, "2v2v2v2 Fixed Teams")
    FIXED3v3v3v3 = (12, [3, 3, 3, 3], False, "3v3v3v3 Fixed Teams")
    FIXED2v2v2v2v2 = (10, [2, 2, 2, 2, 2], False, "2v2v2v2v2 Fixed Teams")
    FIXED2v2v2v2v2v2 = (12, [2, 2, 2, 2, 2, 2], False, "2v2v2v2v2v2 Fixed Teams")
    RANDOM2v2 = (4, [2, 2], True, "2v2 Random Teams")
    RANDOM3v3 = (6, [3, 3], True, "3v3 Random Teams")
    RANDOM4v4 = (8, [4, 4], True, "4v4 Random Teams")
    RANDOM5v5 = (10, [5, 5], True, "5v5 Random Teams")
    RANDOM2v2v2 = (6, [2, 2, 2], True, "2v2v2 Random Teams")
    RANDOM3v3v3 = (9, [3, 3, 3], True, "3v3v3 Random Teams")
    RANDOM4v4v4 = (12, [4, 4, 4], True, "4v4v4 Random Teams")
    RANDOM2v2v2v2 = (8, [2, 2, 2, 2], True, "2v2v2v2 Random Teams")
    RANDOM3v3v3v3 = (12, [3, 3, 3, 3], True, "3v3v3v3 Random Teams")
    RANDOM2v2v2v2v2 = (10, [2, 2, 2, 2, 2], True, "2v2v2v2v2 Random Teams")
    RANDOM2v2v2v2v2v2 = (12, [2, 2, 2, 2, 2, 2], True, "2v2v2v2v2v2 Random Teams")
    AI = (0, [], False, "vs AI")

    def __init__(self, player_num, teams, random, full_name):
        self.player_num = player_num
        self.teams = teams
        self.random = random
        self.full_name = full_name
