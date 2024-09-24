import argparse
import pandas as pd
from jaal import Jaal

def load_votes(league):
    return pd.read_csv(f'data/{league}/votes.csv')
def load_submissions(league):
    return pd.read_csv(f'data/{league}/submissions.csv')
def load_competitors(league):
    return pd.read_csv(f'data/{league}/competitors.csv')

def load_rounds(league):
    return pd.read_csv(f'data/{league}/rounds.csv')

parser = argparse.ArgumentParser("Music League Analyzer")
parser.add_argument("league_name", help="String name of directory in data folder that contains league files (votes.csv,competitors.csv,rounds.csv,submissions.csv)", type=str)
args = parser.parse_args()
league = args.league_name

votes = load_votes(league)
submissions = load_submissions(league)
competitors = load_competitors(league)
rounds = load_rounds(league)

number_of_rounds = len(rounds)

# Initialise dataframe with ids for all competitors
nodes = pd.DataFrame({"id" : competitors.Name})

round_id = rounds.ID[0]

# Pick out only submissions for the given round
#round1nodes = pd.merge(submissions.loc[submissions["Round ID"] == round_id], competitors, left_on="Submitter ID", right_on="ID")

# Create set of votes with submissions data added
#round1edges = pd.merge(submissions.loc[submissions["Round ID"] == round_id], votes.loc[votes["Round ID"] == round_id], suffixes=("_submitter", "_voter"), how="right", on= ["Spotify URI", "Round ID"])

all_votes = pd.merge(submissions, votes, suffixes=("_submitter", "_voter"), how="right", on= ["Spotify URI", "Round ID"])

# Swap IDs for Competitor names
all_votes = all_votes.merge(competitors, left_on="Voter ID", right_on="ID")
all_votes.rename(columns={"Name": "from"}, inplace=True)
all_votes = all_votes.merge(competitors, left_on="Submitter ID", right_on="ID")
all_votes.rename(columns={"Name": "to"}, inplace=True)

#all_votes = all_votes.loc[(all_votes["Round ID"]==round_id)]

# Initialize an empty list to store the preference data
preference = []

# Loop through the submitters and voters
for submitter in competitors.Name:
    for voter in competitors.Name:
        # Filter the rows where 'from' == voter and 'to' == submitter
        filtered_votes = all_votes.loc[(all_votes["from"] == voter) & (all_votes["to"] == submitter)]

        # Calculate the sum of 'Points Assigned'
        weight_value = filtered_votes["Points Assigned"].sum()

        # Append the result as a dictionary to the preference list
        preference.append({
            "from": voter,
            "to": submitter,
            "weight": weight_value
        })

# Convert the list of dictionaries to a pandas DataFrame
preference_df = pd.DataFrame(preference)

filtered_preferences = preference_df[preference_df['from'] != preference_df['to']]

# Initialize an empty list to store the results
results = []

# Iterate through unique pairs of people
for pair in filtered_preferences[['from', 'to']].apply(frozenset, axis=1).unique():
    if len(pair) == 2:  # Make sure it's a valid pair
        person1, person2 = pair

        # Calculate total points given from person1 to person2
        p1_to_p2 = filtered_preferences.loc[(filtered_preferences['from'] == person1) & (filtered_preferences['to'] == person2), 'weight'].sum()

        # Calculate total points given from person2 to person1
        p2_to_p1 = filtered_preferences.loc[(filtered_preferences['from'] == person2) & (filtered_preferences['to'] == person1), 'weight'].sum()

        total = p2_to_p1 + p1_to_p2
        # Determine who gave the most points
        if p1_to_p2 >= p2_to_p1:
            # Sum of weights (points exchanged between them)
            total_weight = p1_to_p2 - p2_to_p1

            results.append({'from': person1, 'to': person2, 'differential': total_weight, 'total': total})
        else:
            # Sum of weights (points exchanged between them)
            total_weight = p2_to_p1 - p1_to_p2

            results.append({'from': person2, 'to': person1, 'differential': total_weight, 'total': total})

# Convert the results to a DataFrame
final_preferences = pd.DataFrame(results)

# Print the result
print(final_preferences)

# Reformat dataframes into Jaal format
nodes.rename(columns={'Name': 'id'}, inplace=True)

#user = "Doug"
#final_preferences = final_preferences.loc[(final_preferences["from"] == user) | (final_preferences["to"] == user)]

final_preferences.to_csv("output.csv", index=False)
print(final_preferences.to_string())
# Fire data into Jaal plot
Jaal(final_preferences, nodes).plot(directed=True)#(directed=False, vis_opts={'physics':{'solver' : 'repulsion', 'edges': {'scaling': {'customScalingFunction': 'function (min, max, total, value) {return value / total;}', 'min': 5, 'max': 10}}}})

