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

    # Extract the names of the starting players
    return [player['PLAYER_NAME'] for index, player in starting_lineup.iterrows()]

def get_substitution_data(game_id):
    # Retrieve play-by-play data for a specific game
    pbp = playbyplay.PlayByPlay(game_id=game_id).get_data_frames()[0]

    # Filter out the events that indicate players entering or leaving the game
    substitutions = pbp[pbp['EVENTMSGTYPE'] == 8]
    return substitutions

def process_player_times(substitutions, starting_lineup):
    # Initialize player time tracking with starting lineup
    player_times = {player: [('in', '12:00', 'Unknown')] for player in starting_lineup}

    # Process each substitution
    for index, event in substitutions.iterrows():
        period = event['PERIOD']
        time = event['PCTIMESTRING']
        if event['HOMEDESCRIPTION']:
            player_in = event['HOMEDESCRIPTION'].split(' FOR ')[0].strip('SUB: ')
            player_out = event['HOMEDESCRIPTION'].split(' FOR ')[-1]
            team = 'Home'
        elif event['VISITORDESCRIPTION']:
            player_in = event['VISITORDESCRIPTION'].split(' FOR ')[0].strip('SUB: ')
            player_out = event['VISITORDESCRIPTION'].split(' FOR ')[-1]
            team = 'Visitor'

        # Add the times for player_in and player_out
        if player_in and player_in not in player_times:
            player_times[player_in] = []
        if player_out and player_out in player_times:
            player_times[player_out].append(('out', time, team))

        if player_in:
            player_times[player_in].append(('in', time, team))

    return player_times

team_name = 'Charlotte Hornets'  
game_date = '2023-11-10'         

game_id = get_game_id(team_name, game_date)
if game_id:
    print(f"Game ID found: {game_id}")
    starting_lineup = get_starting_lineup(game_id)
    if starting_lineup:
        print("Starting Lineup:")
        for player in starting_lineup:
            print(player)

        substitutions = get_substitution_data(game_id)
        print("\nSubstitution Events:")
        print(substitutions)

        player_times = process_player_times(substitutions, starting_lineup)
        print("\nPlayer Times:")
        for player, times in player_times.items():
            print(f"{player}: {times}")
    else:
        print("No starting lineup data found for the game.")
else:
    print("No game found for the specified team and date")
