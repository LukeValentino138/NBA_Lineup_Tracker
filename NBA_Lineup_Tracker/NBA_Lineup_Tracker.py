from nba_api.stats.endpoints import leaguegamefinder, boxscoretraditionalv2, playbyplay
from nba_api.stats.static import teams
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import timedelta

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)  
pd.set_option('display.max_colwidth', None)

games_data = {}

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

def get_last_name(full_name):
    name_parts = full_name.split()

    known_suffixes = ["Jr.", "Sr.", "II", "III", "IV"]
    if name_parts[-1] in known_suffixes:
        return " ".join(name_parts[-2:])  # Include the last name with the suffix
    else:
        return name_parts[-1]

def get_starting_lineups(game_id):
    boxscore = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
    player_stats = boxscore.player_stats.get_data_frame()

    players_with_position = player_stats.loc[player_stats['START_POSITION']!= '', 'PLAYER_NAME'].apply(get_last_name)
    return players_with_position

def get_substitution_data(game_id):
    # Retrieve play-by-play data for a specific game
    pbp = playbyplay.PlayByPlay(game_id=game_id).get_data_frames()[0]

    # Filter out the events that indicate players entering or leaving the game
    substitutions = pbp[pbp['EVENTMSGTYPE'] == 8]

    return substitutions[['PERIOD', 'PCTIMESTRING', 'HOMEDESCRIPTION', 'VISITORDESCRIPTION']]

def convert_time(period, time_str):
    minutes, seconds = map(int, time_str.split(":"))
    return (period - 1) * 12 + (12 - minutes) + seconds / 60



def add_game(games_data, game_id):
    if game_id not in games_data:
        games_data[game_id] = {}

def add_team_to_game(games_data, game_id, team_name):
    if game_id in games_data and team_name not in games_data[game_id]:
        games_data[game_id][team_name] = {}

def add_player_to_team_in_game(games_data, game_id, team_name, player_name):
    if game_id in games_data and team_name in games_data[game_id] and player_name not in games_data[game_id][team_name]:
        games_data[game_id][team_name][player_name] = {"Minutes": []}

def add_minutes_to_player_in_game(games_data, game_id, team_name, player_name, subin_time):
    if game_id in games_data and team_name in games_data[game_id] and player_name in games_data[game_id][team_name]:
        games_data[game_id][team_name][player_name]["Minutes"].append([subin_time, None])

def update_subout_time_in_game(games_data, game_id, team_name, player_name, subout_time):
    if game_id in games_data and team_name in games_data[game_id] and player_name in games_data[game_id][team_name]:
        for time_entry in reversed(games_data[game_id][team_name][player_name]["Minutes"]):
            if time_entry[1] is None:
                time_entry[1] = subout_time
                break

def init_starters(games_data, game_id, starting_lineups, visitor_team, home_team):
    add_game(games_data, game_id)
    add_team_to_game(games_data, game_id, visitor_team)
    add_team_to_game(games_data, game_id, home_team)

    # Process the visitor team's players (first five entries)
    for player in starting_lineups[:5]:
        add_player_to_team_in_game(games_data, game_id, visitor_team, player)
        add_minutes_to_player_in_game(games_data, game_id, visitor_team, player, 0)
        update_subout_time_in_game(games_data, game_id, visitor_team, player, None)  # Initialize with None

    # Process the home team's players (next five entries)
    for player in starting_lineups[5:]:
        add_player_to_team_in_game(games_data, game_id, home_team, player)
        add_minutes_to_player_in_game(games_data, game_id, home_team, player, 0)
        update_subout_time_in_game(games_data, game_id, home_team, player, None)  # Initialize with None


def process_substitutions(games_data, game_id, df_substitutions, visitor_team, home_team):
    for _, row in df_substitutions.iterrows():
        # Process for home team
        if pd.notna(row['HOMEDESCRIPTION']):
            process_substitution_entry(games_data, game_id, row['PERIOD'], row['PCTIMESTRING'], row['HOMEDESCRIPTION'], home_team)

        # Process for visitor team
        if pd.notna(row['VISITORDESCRIPTION']):
            process_substitution_entry(games_data, game_id, row['PERIOD'], row['PCTIMESTRING'], row['VISITORDESCRIPTION'], visitor_team)


def process_substitution_entry(games_data, game_id, period, time_str, description, team):
    try:
        # Find indices of 'SUB:' and 'FOR' in the description
        sub_index = description.index('SUB:') + len('SUB:')
        for_index = description.index('FOR')

        # Extract player names (subin_player is being subbed in, subout_player is being subbed out)
        subin_player_full = description[sub_index:for_index].strip()
        subout_player_full = description[for_index + len('FOR'):].strip()

        # Get last names (accounting for suffixes)
        subin_player = get_last_name(subin_player_full)
        subout_player = get_last_name(subout_player_full)

        time = convert_time(period, time_str)

        # Update subout time for the player being subbed out
        if subout_player in games_data[game_id][team]:
            update_subout_time_in_game(games_data, game_id, team, subout_player, time)
        else:
            # This case handles non-starters or players not previously added
            add_player_to_team_in_game(games_data, game_id, team, subout_player)
            add_minutes_to_player_in_game(games_data, game_id, team, subout_player, 0)  # Add with subin time of 0
            update_subout_time_in_game(games_data, game_id, team, subout_player, time)

        # Add subin entry for the player being subbed in
        if subin_player not in games_data[game_id][team]:
            add_player_to_team_in_game(games_data, game_id, team, subin_player)
        add_minutes_to_player_in_game(games_data, game_id, team, subin_player, time)

    except ValueError:
        print(f"Invalid substitution format: {description}")





import matplotlib.pyplot as plt

def create_gantt_chart(games_data):
    for game_id in games_data:
        fig, ax = plt.subplots(figsize=(15, 8))

        # Each team will have a different color for distinction
        colors = {"Charlotte Hornets": "blue", "Dallas Mavericks": "orange"}
        
        # Starting y position for the bars
        y_pos = 0
        player_labels = []

        # Iterate through each team and player in the game data
        for team, players in games_data[game_id].items():
            for player, player_data in players.items():
                player_labels.append(player)
                for session in player_data["Minutes"]:
                    start, end = session
                    if end is None:
                        end = 48  # Assuming a full game time 

                    # Create a bar for each playing session
                    ax.barh(y_pos, end - start, left=start, height=0.4, color=colors.get(team, "grey"), edgecolor='black')

                y_pos += 1

        # Setting the limits, labels, and ticks for the chart
        ax.set_yticks(range(len(player_labels)))
        ax.set_yticklabels(player_labels)
        ax.set_xlim(0, 48)  # Setting the x-axis to represent the game duration in minutes
        ax.set_xticks([0, 12, 24, 36, 48])
        ax.set_xlabel('Time (minutes)')
        ax.set_title(f"Player Substitution Timings for Game ID: {game_id}")

        plt.tight_layout()
        plt.show()

def print_games_data(games_data):
    for game_id, teams in games_data.items():
        print(f"Game ID: {game_id}")
        for team_name, players in teams.items():
            print(f"  Team: {team_name}")
            for player_name, player_data in players.items():
                print(f"    Player: {player_name}")
                for session in player_data["Minutes"]:
                    print(f"      Session: {session}")


team_name = 'Charlotte Hornets'  
game_date = '2023-11-05'         

visitor_team = "Charlotte Hornets"
home_team = "Dallas Mavericks"

game_id = get_game_id(team_name, game_date)
if game_id:
    starting_lineups = get_starting_lineups(game_id)  # Fetch starting lineups for both teams
    
    substitutions = get_substitution_data(game_id)

    print (substitutions)
    init_starters(games_data, game_id, starting_lineups, visitor_team, home_team)

    process_substitutions(games_data, game_id, substitutions, visitor_team, home_team)

    print_games_data(games_data)

    create_gantt_chart(games_data)