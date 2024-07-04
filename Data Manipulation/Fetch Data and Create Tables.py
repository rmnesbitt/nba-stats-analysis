import sqlite3
import os

# Set up database connection
dbPath = os.path.expanduser('~/Desktop/NBA Stats Analysis/NBA Data.sqlite')
conn = sqlite3.connect(dbPath)
cursor = conn.cursor()


# Function to create a new table for the given season
def create_table(name):
    cursor.execute(f'DROP TABLE IF EXISTS "{name}"')
    cursor.execute(f"""
        CREATE TABLE "{name}" (
            teamName TEXT,
            fgpAVG FLOAT,
            fg3pAVG FLOAT,
            ftpAVG FLOAT,
            ptsAVG FLOAT,
            orebAVG FLOAT,
            drebAVG FLOAT,
            astAVG FLOAT,
            stlAVG FLOAT,
            blkAVG FLOAT,
            tovAVG FLOAT,
            pfAVG FLOAT,
            wins FLOAT,
            losses FLOAT
        );
    """)


# Function to get unique teams for a given season
def unique_teams(seasonID):
    cursor.execute("""
        SELECT DISTINCT team_name_home AS teamName
        FROM game
        WHERE season_id = ?
        UNION
        SELECT DISTINCT team_name_away AS teamName
        FROM game
        WHERE season_id = ?
    """, (seasonID, seasonID))
    return cursor.fetchall()


# Function to get all games for a specific team and season
def team_games(teamName, seasonID):
    cursor.execute("""
        SELECT *
        FROM game
        WHERE season_id = ?
        AND (team_name_home = ? OR team_name_away = ?)
    """, (seasonID, teamName, teamName))
    return cursor.fetchall()


# Function to calculate the average stats for a team
def calc_stats(teamGames, teamName):
    stats = {key: 0 for key in
             ['fgpAVG', 'fg3pAVG', 'ftpAVG', 'ptsAVG', 'orebAVG', 'drebAVG', 'astAVG', 'stlAVG', 'blkAVG', 'tovAVG',
              'pfAVG', 'wins', 'losses']}
    count = len(teamGames)

    # Calculate total stats
    for game in teamGames:
        if game[3] == teamName:
            stats['fgpAVG'] += game[11] or 0
            stats['fg3pAVG'] += game[14] or 0
            stats['ftpAVG'] += game[17] or 0
            stats['ptsAVG'] += game[26] or 0
            stats['orebAVG'] += game[18] or 0
            stats['drebAVG'] += game[19] or 0
            stats['astAVG'] += game[21] or 0
            stats['stlAVG'] += game[22] or 0
            stats['blkAVG'] += game[23] or 0
            stats['tovAVG'] += game[24] or 0
            stats['pfAVG'] += game[25] or 0
            stats['wins'] += 1 if game[7] == "W" else 0
            stats['losses'] += 1 if game[7] != "W" else 0
        else:
            stats['fgpAVG'] += game[36] or 0
            stats['fg3pAVG'] += game[39] or 0
            stats['ftpAVG'] += game[42] or 0
            stats['ptsAVG'] += game[51] or 0
            stats['orebAVG'] += game[43] or 0
            stats['drebAVG'] += game[44] or 0
            stats['astAVG'] += game[46] or 0
            stats['stlAVG'] += game[47] or 0
            stats['blkAVG'] += game[48] or 0
            stats['tovAVG'] += game[49] or 0
            stats['pfAVG'] += game[50] or 0
            stats['wins'] += 1 if game[33] == "W" else 0
            stats['losses'] += 1 if game[33] != "W" else 0

    # Calculate average stats
    for key in stats:
        if key not in ('wins', 'losses'):
            stats[key] = round(stats[key] / count, 2) if count else 0

    return stats


# Function to insert stats into the appropriate table
def insert_stats(tableName, teamName, stats):
    cursor.execute(f"""
        INSERT INTO "{tableName}" (teamName, fgpAVG, fg3pAVG, ftpAVG, ptsAVG, orebAVG, drebAVG, astAVG, stlAVG, blkAVG, tovAVG, pfAVG, wins, losses)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
    teamName, stats['fgpAVG'], stats['fg3pAVG'], stats['ftpAVG'], stats['ptsAVG'], stats['orebAVG'], stats['drebAVG'],
    stats['astAVG'], stats['stlAVG'], stats['blkAVG'], stats['tovAVG'], stats['pfAVG'], stats['wins'], stats['losses']))


# Function to process each season
def process_season(season_type, min_id, exclude_ids):
    cursor.execute(f"""
        SELECT DISTINCT season_id as id
        FROM game
        WHERE season_type = "{season_type}"
        AND id >= '{min_id}'
        AND id NOT IN ({','.join('?' for _ in exclude_ids)})
    """, exclude_ids)
    unique_seasons = cursor.fetchall()
    unique_season_ids = [row[0] for row in unique_seasons]

    for season_id in unique_season_ids:
        season_year = int(season_id) % 10000
        table_name = f'({season_type}) {season_year} Averages'
        create_table(table_name)

        teams = unique_teams(season_id)
        for team in teams:
            team_name = team[0]
            team_games_data = team_games(team_name, season_id)
            averages = calc_stats(team_games_data, team_name)
            insert_stats(table_name, team_name, averages)


# Process regular season data
process_season("Regular Season", '21987', ['21993', '21995', '21999', '22001', '22005'])

# Process playoff data
process_season("Playoffs", '41987', ['42012'])

# Commit changes and close the connection
conn.commit()
conn.close()
