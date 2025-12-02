import pandas as pd
import sqlite3

# Load CSVs
specimens = pd.read_csv('specimens.csv')
analyzers = pd.read_csv('analyzers.csv')
qc_events = pd.read_csv('qc_events.csv')
staffing = pd.read_csv('staffing_schedule.csv')

# Create in-memory SQLite database
conn = sqlite3.connect(':memory:')

# Write dataframes to SQL
specimens.to_sql('specimens', conn, index=False)
analyzers.to_sql('analyzers', conn, index=False)
qc_events.to_sql('qc_events', conn, index=False)
staffing.to_sql('staffing_schedule', conn, index=False)

# Read SQL script
with open('analysis.sql', 'r') as f:
    sql_script = f.read()

# Execute script (split by semicolon manually for SQLite script execution)
cursor = conn.cursor()
commands = sql_script.split(';')

results = {}

for command in commands:
    if command.strip():
        try:
            # Check if it's a SELECT query to fetch results
            if command.strip().upper().startswith('SELECT'):
                df_result = pd.read_sql_query(command, conn)
                # Store result based on query content (simple heuristic)
                if 'avg_tat_minutes' in command:
                    results['avg_tat_by_test'] = df_result
                elif 'failure_rate_pct' in command:
                    results['qc_failure_rate'] = df_result
                elif 'avg_stat_tat' in command:
                    results['bottleneck_hours'] = df_result
                elif 'downtime_minutes' in command:
                    results['downtime_impact'] = df_result
            else:
                cursor.execute(command)
        except Exception as e:
            print(f"Error executing command: {e}")

# Save results to CSV for dashboarding
for name, df in results.items():
    df.to_csv(f'{name}.csv', index=False)
    print(f"Saved {name}.csv")

print("SQL analysis complete.")
