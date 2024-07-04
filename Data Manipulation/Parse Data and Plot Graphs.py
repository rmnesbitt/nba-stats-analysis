import sqlite3
import os
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull
import numpy as np
from adjustText import adjust_text

# Set up database connection
dbPath = os.path.expanduser('~/Desktop/NBA Stats Analysis/NBA Data.sqlite')
conn = sqlite3.connect(dbPath)
cursor = conn.cursor()


# Function to fetch unique years
def fetch_years():
    cursor.execute("""
        SELECT DISTINCT season_id % 10000 as year
        FROM game
        WHERE (season_type = 'Regular Season' OR season_type = 'Playoffs')
        AND season_id >= 41987
        AND season_id >= 21987
        AND season_id NOT IN (42012, 21993, 21995, 21999, 22001, 22005)
    """)
    return [row[0] for row in cursor.fetchall()]


# Function to fetch playoff teams for a given year
def fetch_po_teams(year):
    cursor.execute(f"""
        SELECT DISTINCT teamName 
        FROM "(Playoffs) {year} Averages"
    """)
    return [team[0] for team in cursor.fetchall()]


# Function to fetch the winner of the playoffs for a given year
def fetch_winner(year):
    cursor.execute(f"""
        SELECT team_name_home AS teamName
        FROM game
        WHERE season_id = "4{year}" AND wl_home = 'W' AND game_date = (SELECT MAX(game_date) FROM game WHERE season_id = "4{year}")
        UNION
        SELECT team_name_away AS teamName
        FROM game
        WHERE season_id = "4{year}" AND wl_away = 'W' AND game_date = (SELECT MAX(game_date) FROM game WHERE season_id = "4{year}")
        LIMIT 1
    """)
    winner = cursor.fetchone()
    return winner[0] if winner else None


# Function to plot clusters
def plot_clusters(year, df, po_teams, winner):
    features = ['fgpAVG', 'fg3pAVG', 'ftpAVG', 'ptsAVG', 'orebAVG', 'drebAVG', 'astAVG', 'stlAVG', 'blkAVG', 'tovAVG',
                'pfAVG', 'wins', 'losses']
    X = df[features]

    # Standardize features
    XScaled = StandardScaler().fit_transform(X)

    # Perform PCA
    principalComponents = PCA(n_components=2).fit_transform(XScaled)
    dfPCA = pd.DataFrame(data=principalComponents, columns=['PC1', 'PC2'])

    # Perform KMeans clustering
    kmeans = KMeans(n_clusters=4, random_state=42).fit(dfPCA)
    df['Cluster'] = kmeans.predict(dfPCA)

    # Plot clusters
    plt.figure(figsize=(20, 12))
    plt.scatter(dfPCA['PC1'], dfPCA['PC2'], c=df['Cluster'], cmap='viridis')
    plt.title(f'Clusters of Teams for {year}')
    plt.xlabel('Principal Component 1')
    plt.ylabel('Principal Component 2')
    plt.colorbar(label='Cluster')

    # Annotate points with team names
    texts = []
    for i in range(dfPCA.shape[0]):
        color = 'red' if df['teamName'][i] == winner else 'blue' if df['teamName'][i] in po_teams else 'black'
        texts.append(plt.text(dfPCA['PC1'][i], dfPCA['PC2'][i], df['teamName'][i], fontsize=12, color=color,
                              fontweight='bold' if color != 'black' else 'normal'))

    # Adjust text to avoid overlap
    adjust_text(texts, arrowprops=dict(arrowstyle='->', color='grey', lw=0.5))

    # Plot cluster centroids
    centroids = kmeans.cluster_centers_
    for centroid in centroids:
        plt.scatter(centroid[0], centroid[1], marker='.', s=200, c='green')

    # Plot convex hulls for clusters
    colors = plt.cm.viridis(np.linspace(0, 1, 4))
    for cluster in range(4):
        cluster_points = dfPCA[df['Cluster'] == cluster]
        if len(cluster_points) >= 3:
            hull = ConvexHull(cluster_points)
            for simplex in hull.simplices:
                plt.plot(cluster_points.iloc[simplex, 0], cluster_points.iloc[simplex, 1], c=colors[cluster],
                         linewidth=1)
        elif len(cluster_points) == 2:
            plt.plot(cluster_points.iloc[:, 0], cluster_points.iloc[:, 1], c=colors[cluster], linewidth=1)

    plt.show()


# Fetch unique years
years = fetch_years()

# Process each year
for year in years:
    po_teams = fetch_po_teams(year)
    winner = fetch_winner(year)
    df = pd.read_sql_query(f'SELECT * FROM "(Regular Season) {year} Averages"', conn)
    plot_clusters(year, df, po_teams, winner)

# Close the database connection
conn.close()
