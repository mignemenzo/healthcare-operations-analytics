import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set seed for reproducibility
np.random.seed(42)
random.seed(42)

# Constants
START_DATE = datetime(2023, 1, 1)
DAYS = 90
NUM_SPECIMENS = 15000  # Approx 166 per day
ANALYZERS = [
    {'id': 'A001', 'name': 'Sysmex XN-3000', 'dept': 'Hematology'},
    {'id': 'A002', 'name': 'Sysmex XN-3000', 'dept': 'Hematology'},
    {'id': 'A003', 'name': 'ACL TOP 350', 'dept': 'Coagulation'},
    {'id': 'A004', 'name': 'Cobas 8000', 'dept': 'Chemistry'},
    {'id': 'A005', 'name': 'Cobas 8000', 'dept': 'Chemistry'},
    {'id': 'A006', 'name': 'Cepheid GeneXpert', 'dept': 'Microbiology'}
]
TEST_TYPES = {
    'Hematology': ['CBC', 'Diff'],
    'Coagulation': ['PT/INR', 'PTT'],
    'Chemistry': ['CMP', 'BMP', 'Troponin'],
    'Microbiology': ['COVID PCR', 'Flu A/B']
}
PRIORITIES = ['Routine', 'STAT']
STAFF_ROLES = ['Tech', 'Supervisor', 'Lab Assistant']
SHIFTS = [
    {'name': 'Day', 'start': 7, 'end': 15},
    {'name': 'Evening', 'start': 15, 'end': 23},
    {'name': 'Night', 'start': 23, 'end': 7}
]

# 1. Generate Analyzers Data
analyzers_data = []
current_date = START_DATE
for _ in range(DAYS):
    for analyzer in ANALYZERS:
        # Simulate downtime (randomly, some days have 0, others have spikes)
        is_down = np.random.choice([True, False], p=[0.1, 0.9])
        downtime = np.random.randint(30, 240) if is_down else 0
        uptime = 1440 - downtime
        
        analyzers_data.append({
            'analyzer_id': analyzer['id'],
            'analyzer_name': analyzer['name'],
            'department': analyzer['dept'],
            'uptime_minutes': uptime,
            'downtime_minutes': downtime,
            'date': current_date.strftime('%Y-%m-%d')
        })
    current_date += timedelta(days=1)

df_analyzers = pd.DataFrame(analyzers_data)

# 2. Generate Staffing Schedule
staff_data = []
staff_ids = [f'S{i:03d}' for i in range(1, 21)] # 20 staff members
current_date = START_DATE

for _ in range(DAYS):
    # Assign staff to shifts randomly but ensuring coverage
    daily_staff = random.sample(staff_ids, 12) # 12 staff per day
    
    for i, staff_id in enumerate(daily_staff):
        shift = SHIFTS[i % 3] # Distribute across 3 shifts
        
        # Shift times
        start_dt = current_date.replace(hour=shift['start'], minute=0, second=0)
        if shift['name'] == 'Night':
            end_dt = (current_date + timedelta(days=1)).replace(hour=shift['end'], minute=0, second=0)
        else:
            end_dt = current_date.replace(hour=shift['end'], minute=0, second=0)
            
        staff_data.append({
            'staff_id': staff_id,
            'shift_start': start_dt.strftime('%Y-%m-%d %H:%M:%S'),
            'shift_end': end_dt.strftime('%Y-%m-%d %H:%M:%S'),
            'role': np.random.choice(STAFF_ROLES, p=[0.7, 0.1, 0.2]),
            'dept': np.random.choice(['Hematology', 'Chemistry', 'Microbiology', 'Coagulation'])
        })
    current_date += timedelta(days=1)

df_staff = pd.DataFrame(staff_data)

# 3. Generate Specimens Data
specimens_data = []
current_time = START_DATE

for i in range(NUM_SPECIMENS):
    # Randomize collection time within the 90 days
    # Add some peak hours logic (morning rounds 6-9 AM)
    day_offset = np.random.randint(0, DAYS)
    hour_probs = [0.02]*6 + [0.15, 0.15, 0.10, 0.08] + [0.05]*14 # Higher prob 6-9 AM
    hour_probs = np.array(hour_probs) / np.sum(hour_probs)
    hour = np.random.choice(range(24), p=hour_probs)
    minute = np.random.randint(0, 60)
    
    collection_time = START_DATE + timedelta(days=day_offset, hours=int(hour), minutes=minute)
    
    # Determine test type and analyzer
    dept = np.random.choice(list(TEST_TYPES.keys()))
    test_type = np.random.choice(TEST_TYPES[dept])
    possible_analyzers = [a['id'] for a in ANALYZERS if a['dept'] == dept]
    analyzer_id = np.random.choice(possible_analyzers)
    
    priority = np.random.choice(PRIORITIES, p=[0.8, 0.2])
    
    # Timestamps logic
    # Received: 15-60 mins after collection
    received_delay = np.random.randint(15, 60)
    received_time = collection_time + timedelta(minutes=received_delay)
    
    # Resulted: Depends on priority and random delay (simulating issues)
    base_tat = np.random.randint(20, 45) if priority == 'STAT' else np.random.randint(45, 120)
    # Add outliers (long TAT)
    if np.random.random() < 0.05:
        base_tat += np.random.randint(60, 300)
        
    resulted_time = received_time + timedelta(minutes=base_tat)
    
    specimens_data.append({
        'specimen_id': f'SP{i:06d}',
        'patient_id': f'P{np.random.randint(1000, 5000)}',
        'test_type': test_type,
        'priority': priority,
        'collection_time': collection_time.strftime('%Y-%m-%d %H:%M:%S'),
        'received_time': received_time.strftime('%Y-%m-%d %H:%M:%S'),
        'resulted_time': resulted_time.strftime('%Y-%m-%d %H:%M:%S'),
        'analyzer_id': analyzer_id
    })

df_specimens = pd.DataFrame(specimens_data)

# 4. Generate QC Events
qc_data = []
qc_id_counter = 1

for index, row in df_analyzers.iterrows():
    # 3 levels of QC per day per analyzer usually
    # But let's simulate random QC runs
    num_qc_runs = np.random.randint(1, 4)
    
    for _ in range(num_qc_runs):
        # QC result
        # 95% pass rate
        result = np.random.choice(['Pass', 'Fail'], p=[0.95, 0.05])
        level = np.random.choice(['Normal', 'Abnormal'])
        
        # Timestamp within that day
        hour = np.random.randint(0, 24)
        minute = np.random.randint(0, 60)
        qc_time = datetime.strptime(row['date'], '%Y-%m-%d') + timedelta(hours=hour, minutes=minute)
        
        qc_data.append({
            'qc_id': f'QC{qc_id_counter:05d}',
            'analyzer_id': row['analyzer_id'],
            'level': level,
            'result': result,
            'timestamp': qc_time.strftime('%Y-%m-%d %H:%M:%S')
        })
        qc_id_counter += 1

df_qc = pd.DataFrame(qc_data)

# 5. Generate Test Volume by Hour (Aggregated)
# We can derive this from specimens, but let's create a separate summary file as requested
df_specimens['collection_dt'] = pd.to_datetime(df_specimens['collection_time'])
df_specimens['hour_key'] = df_specimens['collection_dt'].dt.floor('h')

volume_summary = df_specimens.groupby(['hour_key', 'test_type']).size().reset_index(name='volume')
volume_summary.rename(columns={'hour_key': 'timestamp'}, inplace=True)

# Save all to CSV
df_specimens.drop(columns=['collection_dt', 'hour_key'], inplace=True, errors='ignore')
df_specimens.to_csv('specimens.csv', index=False)
df_analyzers.to_csv('analyzers.csv', index=False)
df_staff.to_csv('staffing_schedule.csv', index=False)
df_qc.to_csv('qc_events.csv', index=False)
volume_summary.to_csv('test_volume_by_hour.csv', index=False)

print("Data generation complete. Files created: specimens.csv, analyzers.csv, staffing_schedule.csv, qc_events.csv, test_volume_by_hour.csv")
