import sqlite3
import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from imblearn.over_sampling import SMOTE

# Set up database connection
dbPath = os.path.expanduser('~/Desktop/NBA Stats Analysis/NBA Data.sqlite')
conn = sqlite3.connect(dbPath)
cursor = conn.cursor()

# Function to fetch and prepare data
def fetch_and_prepare_data():
    cursor.execute("""
        SELECT * FROM game
        WHERE season_type = 'Regular Season'
        AND season_id >= 21987
    """)
    regular_season_games = cursor.fetchall()

    cursor.execute("""
        SELECT * FROM game
        WHERE season_type = 'Playoffs'
        AND season_id >= 41987
    """)
    playoff_games = cursor.fetchall()

    return regular_season_games, playoff_games

# Function to create dataset with labels for playoff participation and championship wins
def create_dataset(regular_season_games, playoff_games):
    data = []
    playoff_teams = set([game[3] for game in playoff_games] + [game[8] for game in playoff_games])
    championship_winners = set([game[3] for game in playoff_games if game[7] == 'W'])

    for game in regular_season_games:
        team_name = game[3]
        stats = {
            'teamName': team_name,
            'fgpAVG': game[11] or 0,
            'fg3pAVG': game[14] or 0,
            'ftpAVG': game[17] or 0,
            'ptsAVG': game[26] or 0,
            'orebAVG': game[18] or 0,
            'drebAVG': game[19] or 0,
            'astAVG': game[21] or 0,
            'stlAVG': game[22] or 0,
            'blkAVG': game[23] or 0,
            'tovAVG': game[24] or 0,
            'pfAVG': game[25] or 0,
            'wins': 1 if game[7] == 'W' else 0,
            'playoffs': 1 if team_name in playoff_teams else 0,
            'champion': 1 if team_name in championship_winners else 0
        }
        data.append(stats)

    return pd.DataFrame(data)

# Fetch and prepare data
regular_season_games, playoff_games = fetch_and_prepare_data()

# Create dataset
df = create_dataset(regular_season_games, playoff_games)

# Define features and labels
features = ['fgpAVG', 'fg3pAVG', 'ftpAVG', 'ptsAVG', 'orebAVG', 'drebAVG', 'astAVG', 'stlAVG', 'blkAVG', 'tovAVG', 'pfAVG', 'wins']
X = df[features]
y_playoffs = df['playoffs']
y_champion = df['champion']

# Split data into training and testing sets
X_train, X_test, y_train_playoffs, y_test_playoffs, y_train_champion, y_test_champion = train_test_split(X, y_playoffs, y_champion, test_size=0.2, random_state=42)

# Standardize features
scaler = StandardScaler().fit(X_train)
X_train_scaled = scaler.transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Oversample the minority class for playoff participation
smote = SMOTE(random_state=42)
X_train_playoffs_balanced, y_train_playoffs_balanced = smote.fit_resample(X_train_scaled, y_train_playoffs)

# Train playoff participation model on balanced data
playoff_model = LogisticRegression(random_state=42).fit(X_train_playoffs_balanced, y_train_playoffs_balanced)
playoff_predictions = playoff_model.predict(X_test_scaled)
print("Playoff Participation Model Accuracy:", accuracy_score(y_test_playoffs, playoff_predictions))
print(classification_report(y_test_playoffs, playoff_predictions, zero_division=1))

# Oversample the minority class for championship win
X_train_champion_balanced, y_train_champion_balanced = smote.fit_resample(X_train_scaled, y_train_champion)

# Train championship win model on balanced data
champion_model = RandomForestClassifier(random_state=42).fit(X_train_champion_balanced, y_train_champion_balanced)
champion_predictions = champion_model.predict(X_test_scaled)
print("Championship Win Model Accuracy:", accuracy_score(y_test_champion, champion_predictions))
print(classification_report(y_test_champion, champion_predictions, zero_division=1))

# Predict probabilities for new data (e.g., upcoming season's regular season stats)
def predict_playoff_and_championship_probs(new_data):
    new_data_scaled = scaler.transform(new_data)
    playoff_probs = playoff_model.predict_proba(new_data_scaled)[:, 1]
    champion_probs = champion_model.predict_proba(new_data_scaled)[:, 1]
    return playoff_probs, champion_probs

# Example new data (replace with actual new season data)
new_data = pd.DataFrame([{
    'fgpAVG': 0.45,
    'fg3pAVG': 0.36,
    'ftpAVG': 0.78,
    'ptsAVG': 110.0,
    'orebAVG': 10.5,
    'drebAVG': 32.1,
    'astAVG': 25.4,
    'stlAVG': 7.5,
    'blkAVG': 5.1,
    'tovAVG': 14.3,
    'pfAVG': 20.0,
    'wins': 50
}])

playoff_probs, champion_probs = predict_playoff_and_championship_probs(new_data)
print("Playoff Probability:", playoff_probs[0])
print("Championship Win Probability:", champion_probs[0])

conn.close()