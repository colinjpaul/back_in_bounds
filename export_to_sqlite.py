import os
import sqlite3
import pandas as pd
import numpy as np

def ensure_launch_monitor_csv():
    """Generates mock launch monitor data if CSV is not present on disk."""
    os.makedirs('data', exist_ok=True)
    csv_path = 'data/launch_mon_may21_26.csv'
    if not os.path.exists(csv_path):
        clubs = ['Driver', '5 Wood', '4 Iron', '5 Iron', '6 Iron', '7 Iron', '8 Iron', '9 Iron', 'PW', 'LW (58)']
        dates = ['06-07-24', '12-08-24', '15-10-24', '04-03-25', '14-05-25', '21-05-26', '23-05-26', '12-06-26', '18-07-26']
        base_stats = {
            'Driver': {'speed': (95, 101), 'smash': (1.42, 1.48), 'distance_mult': 2.45},
            '5 Wood': {'speed': (88, 93), 'smash': (1.38, 1.44), 'distance_mult': 2.30},
            '4 Iron': {'speed': (82, 86), 'smash': (1.33, 1.39), 'distance_mult': 2.20},
            '5 Iron': {'speed': (80, 84), 'smash': (1.31, 1.37), 'distance_mult': 2.15},
            '6 Iron': {'speed': (77, 81), 'smash': (1.29, 1.35), 'distance_mult': 2.10},
            '7 Iron': {'speed': (74, 78), 'smash': (1.27, 1.33), 'distance_mult': 2.05},
            '8 Iron': {'speed': (71, 75), 'smash': (1.25, 1.31), 'distance_mult': 2.00},
            '9 Iron': {'speed': (68, 72), 'smash': (1.23, 1.29), 'distance_mult': 1.95},
            'PW': {'speed': (65, 69), 'smash': (1.20, 1.26), 'distance_mult': 1.90},
            'LW (58)': {'speed': (60, 64), 'smash': (1.10, 1.18), 'distance_mult': 1.65}
        }
        data = []
        np.random.seed(42)
        for _ in range(120):
            club = np.random.choice(clubs)
            date = np.random.choice(dates)
            stats = base_stats[club]
            speed = np.round(np.random.uniform(*stats['speed']), 1)
            smash = np.round(np.random.uniform(*stats['smash']), 2)
            total = np.round(speed * smash * stats['distance_mult'] * np.random.uniform(0.97, 1.03), 1)
            data.append({'Date': date, 'Club': club, 'Club Speed': speed, 'Smash': smash, 'Total': total})
        pd.DataFrame(data).to_csv(csv_path, index=False)
    return csv_path

def sync_csv_to_sqlite():
    """
    Exports CSV datasets (Fermoy round telemetry and launch monitor practice)
    into a structured SQLite relational database ('data/analytics.db').
    """
    os.makedirs('data', exist_ok=True)
    db_path = 'data/analytics.db'
    conn = sqlite3.connect(db_path)
    
    # 1. Export Fermoy Rounds CSV if available
    fermoy_csv = 'data/fermoy_rounds.csv'
    if os.path.exists(fermoy_csv):
        rounds_df = pd.read_csv(fermoy_csv)
        rounds_df.to_sql('fermoy_rounds', conn, if_exists='replace', index=False)
        print(f"[SQL SYNC] Successfully written {len(rounds_df)} rows to 'fermoy_rounds' table in {db_path}")
        
    # 2. Export Launch Monitor Range Sessions CSV
    launch_csv = ensure_launch_monitor_csv()
    launch_df = pd.read_csv(launch_csv)
    launch_df.to_sql('range_sessions', conn, if_exists='replace', index=False)
    print(f"[SQL SYNC] Successfully written {len(launch_df)} rows to 'range_sessions' table in {db_path}")
        
    conn.close()
    return db_path

if __name__ == '__main__':
    sync_csv_to_sqlite()
