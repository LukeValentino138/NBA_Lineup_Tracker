from nba_api.stats.endpoints import leagueleaders
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players
import pandas as pd
import plotly.express as px
from nba_api.stats.endpoints import playbyplay
import pandas as pd
from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.static import teams

# Get the team ID for a specific team
team_dict = teams.get_teams()
# Example: Find the team ID for the Los Angeles Lakers
hornets = [team for team in team_dict if team['full_name'] == 'Charlotte Hornets'][0]
hornets_id = hornets['id']

# Use LeagueGameFinder to query past games for the Lakers
gamefinder = leaguegamefinder.LeagueGameFinder(team_id_nullable=hornets_id)
games = gamefinder.get_data_frames()[0]

# Now you can filter the games DataFrame for the game you want using criteria like date or opponent
# Example: Find a game against the Miami Heat on a specific date
games_filtered = games[(games['GAME_DATE'] == '2023-11-06')]

# Now you can filter the games DataFrame for the game you want using criteria like date or opponent
# Example: Find a game against the Miami Heat on a specific date
games_filtered = games[(games['GAME_DATE'] == '2023-11-05')]

# Check if any games were found
if not games_filtered.empty:
    # Retrieve the GAME_ID
    game_id = games_filtered['GAME_ID'].values[0]
    print(game_id)

    # Retrieve play-by-play data for a specific game
    pbp = playbyplay.PlayByPlay(game_id=game_id).get_data_frames()[0]

    # Filter out the events that indicate players entering or leaving the game
    substitutions = pbp[pbp['EVENTMSGTYPE'] == 8]

    # Display the substitutions to see when players enter and leave
    print(substitutions[['PERIOD', 'PCTIMESTRING', 'HOMEDESCRIPTION', 'VISITORDESCRIPTION']])
else:
    print("No games were found for the specified criteria.")
