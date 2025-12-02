import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set style
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

# Load data
specimens = pd.read_csv('specimens.csv')
analyzers = pd.read_csv('analyzers.csv')
qc_events = pd.read_csv('qc_events.csv')

# Preprocessing for plots
specimens['received_time'] = pd.to_datetime(specimens['received_time'])
specimens['resulted_time'] = pd.to_datetime(specimens['resulted_time'])
specimens['tat_min'] = (specimens['resulted_time'] - specimens['received_time']).dt.total_seconds() / 60
specimens['hour'] = specimens['received_time'].dt.hour
specimens['date'] = specimens['received_time'].dt.date

# 1. Turnaround Time Trend (Daily Avg)
daily_tat = specimens.groupby('date')['tat_min'].mean().reset_index()
plt.figure(figsize=(14, 6))
sns.lineplot(data=daily_tat, x='date', y='tat_min', marker='o', color='#2c3e50', linewidth=2.5)
plt.title('Daily Average Turnaround Time (90 Days)', fontsize=16, fontweight='bold')
plt.xlabel('Date', fontsize=12)
plt.ylabel('Avg TAT (Minutes)', fontsize=12)
plt.axhline(y=60, color='r', linestyle='--', label='Target (60 min)')
plt.legend()
plt.tight_layout()
plt.savefig('dashboard_tat_trend.png', dpi=300)
plt.close()

# 2. TAT Heatmap by Hour of Day vs Test Type
heatmap_data = specimens.pivot_table(index='test_type', columns='hour', values='tat_min', aggfunc='mean')
plt.figure(figsize=(16, 8))
sns.heatmap(heatmap_data, cmap='RdYlGn_r', annot=True, fmt='.0f', cbar_kws={'label': 'Avg TAT (min)'})
plt.title('Turnaround Time Heatmap: Test Type vs. Hour of Day', fontsize=16, fontweight='bold')
plt.xlabel('Hour of Day (24h)', fontsize=12)
plt.ylabel('Test Type', fontsize=12)
plt.tight_layout()
plt.savefig('dashboard_tat_heatmap.png', dpi=300)
plt.close()

# 3. Analyzer Downtime vs Output
# Aggregate downtime per analyzer
downtime_agg = analyzers.groupby('analyzer_name')['downtime_minutes'].sum().reset_index()
# Aggregate volume per analyzer
volume_agg = specimens.merge(analyzers[['analyzer_id', 'analyzer_name']], on='analyzer_id').groupby('analyzer_name').size().reset_index(name='volume')

merged_metrics = pd.merge(downtime_agg, volume_agg, on='analyzer_name')

fig, ax1 = plt.subplots(figsize=(12, 6))

color = 'tab:red'
ax1.set_xlabel('Analyzer', fontsize=12)
ax1.set_ylabel('Total Downtime (Minutes)', color=color, fontsize=12)
sns.barplot(data=merged_metrics, x='analyzer_name', y='downtime_minutes', ax=ax1, color=color, alpha=0.6)
ax1.tick_params(axis='y', labelcolor=color)

ax2 = ax1.twinx()  
color = 'tab:blue'
ax2.set_ylabel('Total Test Volume', color=color, fontsize=12)
sns.lineplot(data=merged_metrics, x='analyzer_name', y='volume', ax=ax2, color=color, marker='o', linewidth=3)
ax2.tick_params(axis='y', labelcolor=color)

plt.title('Analyzer Performance: Downtime vs. Test Volume', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig('dashboard_downtime_volume.png', dpi=300)
plt.close()

# 4. QC Failure Trends
qc_events['timestamp'] = pd.to_datetime(qc_events['timestamp'])
qc_events['date'] = qc_events['timestamp'].dt.date
qc_fail_daily = qc_events[qc_events['result'] == 'Fail'].groupby('date').size().reset_index(name='failures')

plt.figure(figsize=(14, 6))
sns.barplot(data=qc_fail_daily, x='date', y='failures', color='#e74c3c')
plt.title('Daily QC Failure Count', fontsize=16, fontweight='bold')
plt.xlabel('Date', fontsize=12)
plt.ylabel('Number of Failed QC Runs', fontsize=12)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('dashboard_qc_failures.png', dpi=300)
plt.close()

print("Dashboard visualizations generated.")
