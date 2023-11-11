from nba_api.stats.endpoints import leaguegamefinder, boxscoretraditionalv2, playbyplay
from nba_api.stats.static import teams
import pandas as pd

def get_game_id(team_name, game_date):
    # Fetch team data
    team_dict = teams.get_teams()
    team = [team for team in team_dict if team['full_name'] == team_name][0]
    team_id = team['id']

    # Find games for the team
    gamefinder = leaguegamefinder.LeagueGameFinder(team_id_nullable=team_id)
    games = gamefinder.get_data_frames()[0]

    # Filter games by date
    games_filtered = games[games['GAME_DATE'] == game_date]
    if not games_filtered.empty:
        return games_filtered['GAME_ID'].values[0]
    else:
        return None

def get_starting_lineup(game_id):
    # Fetch the box score data for the specified game
    boxscore = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
    player_stats = boxscore.player_stats.get_data_frame()

    # Filter the data to get the starting lineup
    starting_lineup = player_stats[player_stats['START_POSITION'] != '']

    # Extract and print the names of the starting players
    for index, player in starting_lineup.iterrows():
        print(f"{player['PLAYER_NAME']} - {player['TEAM_ABBREVIATION']} - {player['START_POSITION']}")

def get_substitution_data(game_id):
     # Retrieve play-by-play data for a specific game
    pbp = playbyplay.PlayByPlay(game_id=game_id).get_data_frames()[0]

    # Filter out the events that indicate players entering or leaving the game
    substitutions = pbp[pbp['EVENTMSGTYPE'] == 8]

    # Display the substitutions to see when players enter and leave
    print(substitutions[['PERIOD', 'PCTIMESTRING', 'HOMEDESCRIPTION', 'VISITORDESCRIPTION']])

team_name = 'Charlotte Hornets'  
game_date = '2023-11-10'         

game_id = get_game_id(team_name, game_date)
if game_id:
    print("Starting Lineups")
    get_starting_lineup(game_id)
    print("Substitutions")
    get_substitution_data(game_id)
else:
    print("No game found for the specified team and date")
