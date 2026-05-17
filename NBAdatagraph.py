import pandas as pd
from neo4j import GraphDatabase
import getpass

df_players = pd.read_csv("players.csv")
df_games = pd.read_csv("games.csv")
df_ranking = pd.read_csv("ranking.csv")
df_details = pd.read_csv("games_details.csv", low_memory=False)

players = df_players.to_dict(orient="records")
teams = df_ranking[['TEAM_ID', 'TEAM', 'CONFERENCE']].drop_duplicates(subset='TEAM_ID').to_dict(orient="records")
games = df_games.to_dict(orient="records")
details = df_details.to_dict(orient="records")

def batch(data, size=500):
    for i in range(0, len(data), size):
        yield data[i:i+size]

print("=============================")
print("       NEO4J LOGIN           ")
print("=============================")
USER = input("User(par defaut: neo4j): ")
PASSWORD = getpass.getpass("Password               : ")

URI = "bolt://localhost:7687"
AUTH = USER, PASSWORD

with GraphDatabase.driver(URI, auth=AUTH) as driver:

    # Creation de noeuds teams
    driver.execute_query("""
        UNWIND $teams AS team
        MERGE (t:team {Id: team.TEAM_ID})
        SET t.Name = team.TEAM,
            t.Conference = team.CONFERENCE
    """, teams=teams)

    # Creation de noeuds players
    driver.execute_query("""
        UNWIND $players AS player
        MERGE (p:player {Id: player.PLAYER_ID})
        SET p.Name = player.PLAYER_NAME,
            p.Team_id = player.TEAM_ID,
            p.Season = player.SEASON
    """, players=players)

    # Creation de noeuds games
    for chunk in batch(games):
        driver.execute_query("""
            UNWIND $games AS game
            MERGE (g:game {Id: game.GAME_ID})
            SET g.Date = game.GAME_DATE_EST,
                g.Status = game.GAME_STATUS_TEXT,
                g.Home_team_id = game.HOME_TEAM_ID,
                g.Visitor_team_id = game.VISITOR_TEAM_ID,
                g.Season = game.SEASON,
                g.Home_team_wins = game.HOME_TEAM_WINS,
                g.Pts_home = game.PTS_home,
                g.Fg_pct_home = game.FG_PCT_home,
                g.Ft_pct_home = game.FT_PCT_home,
                g.Fg3_pct_home = game.FG3_PCT_home,
                g.Ast_home = game.AST_home,
                g.Reb_home = game.REB_home,
                g.Pts_away = game.PTS_away,
                g.Fg_pct_away = game.FG_PCT_away,
                g.Ft_pct_away = game.FT_PCT_away,
                g.Fg3_pct_away = game.FG3_PCT_away,
                g.Ast_away = game.AST_away,
                g.Reb_away = game.REB_away
        """, games=chunk)

    # Relation joueurs-equipe
    driver.execute_query("""
        UNWIND $players AS player
        MATCH (p:player {Id: player.PLAYER_ID})
        MATCH (t:team {Id: player.TEAM_ID})
        MERGE (p)-[:APPARTIENT_A]->(t)
    """, players=players)

    # Relation equipe-match
    for chunk in batch(games):
        driver.execute_query("""
            UNWIND $games AS game
            MATCH (t:team {Id: game.HOME_TEAM_ID})
            MATCH (g:game {Id: game.GAME_ID})
            MERGE (t)-[:A_JOUE]->(g)
        """, games=chunk)

        driver.execute_query("""
            UNWIND $games AS game
            MATCH (t:team {Id: game.VISITOR_TEAM_ID})
            MATCH (g:game {Id: game.GAME_ID})
            MERGE (t)-[:A_JOUE]->(g)
        """, games=chunk)

    # Relation joueur-match avec stats
    for chunk in batch(details):
        driver.execute_query("""
            UNWIND $details AS detail
            MATCH (p:player {Id: detail.PLAYER_ID})
            MATCH (g:game {Id: detail.GAME_ID})
            MERGE (p)-[r:A_JOUE]->(g)
            SET r.min = detail.MIN,
                r.pts = detail.PTS,
                r.reb = detail.REB,
                r.ast = detail.AST,
                r.stl = detail.STL,
                r.blk = detail.BLK,
                r.to = detail.TO,
                r.fgm = detail.FGM,
                r.fga = detail.FGA,
                r.fg_pct = detail.FG_PCT,
                r.fg3m = detail.FG3M,
                r.fg3a = detail.FG3A,
                r.fg3_pct = detail.FG3_PCT,
                r.ftm = detail.FTM,
                r.fta = detail.FTA,
                r.ft_pct = detail.FT_PCT,
                r.oreb = detail.OREB,
                r.dreb = detail.DREB,
                r.plus_minus = detail.PLUS_MINUS
        """, details=chunk)