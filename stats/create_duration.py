file_path='timeline.html'
with open(file_path,'r') as file:
    data = file.read()
data=data.split("processes");data=data[2];data=data.split("\n")
new_data = []
for i in range(1,len(data)-12):
    tmp=data[i].split("[")[-1].split(",")
    if len(tmp) == 6: #normal
        tmp = tmp[3].split(":")[1]
    elif len(tmp) == 8:
        tmp = tmp[6].split(":")[1]
    data[i] = data[i].split(",")[0].split("\"")[3] + data[i].split("[")[1].split(":")[1].split(",")[0] + str(tmp)
    new_data.append(data[i])
# print(new_data)
duration = []
for i in new_data:
    if "(" in i:
        i = i.split(" ")[0] + "_" + i.split(" ")[1] + "," + i.split(" ")[2] + "," + i.split(" ")[3]
    else:
        i = i.split(" ")[0] + "," + i.split(" ")[1] + "," + i.split(" ")[2]
    # Remove } and ] from each element before appending
    i = i.replace('}', '').replace(']', '')
    duration.append(i)
# print(duration)
# convert this list of strings into tabular form
import pandas as pd
rows = [x.split(',') for x in duration]
df = pd.DataFrame(rows, columns=['process', 'start_epoch', 'end_epoch'])
df['duration']= df['end_epoch'].astype(int) - df['start_epoch'].astype(int)
initial=int(df['start_epoch'][0])
for i in range(0,len(df['start_epoch'])):
    df.loc[i,'start_epoch'] = int(df.loc[i,'start_epoch']) - initial
    df.loc[i,'end_epoch'] = int(df.loc[i,'start_epoch']) + int(df.loc[i,'duration'])
# df.to_csv('durations.csv',index=False)

import pandas as pd
import numpy as np
from zoneinfo import ZoneInfo  

# Ensure epoch columns are numeric (integers) so arithmetic works
df['start_epoch'] = pd.to_numeric(df['start_epoch'], errors='coerce').astype('int64')
df['end_epoch']   = pd.to_numeric(df['end_epoch'],   errors='coerce').astype('int64')

# Step 1: Convert millisecond epoch → datetime in CDT (handles DST correctly)
cdt = ZoneInfo("America/Chicago")

df['start_dt'] = pd.to_datetime(df['start_epoch'], unit='ms', utc=True).dt.tz_convert(cdt)
df['end_dt']   = pd.to_datetime(df['end_epoch'],   unit='ms', utc=True).dt.tz_convert(cdt)

# Step 2: Relative time in seconds since the very first start (deepprep_init)
global_start = int(df['start_epoch'].iloc[0])                  # first start in milliseconds (as int)
df['start_sec'] = (df['start_epoch'] - global_start) / 1000.0   # → seconds, float
df['end_sec']   = (df['end_epoch']   - global_start) / 1000.0   # → seconds, float

# Step 3: Duration in seconds
df['duration_sec'] = (df['end_epoch'] - df['start_epoch']) / 1000.0

# Optional: round to nice precision
df['start_sec']    = df['start_sec'].round(3)
df['end_sec']      = df['end_sec'].round(3)
df['duration_sec'] = df['duration_sec'].round(3)

# Drop helper columns if you don’t need the actual datetime objects
df = df.drop(['start_dt', 'end_dt'], axis=1)

# Reorder columns nicely
df = df[['process', 'start_sec', 'end_sec', 'duration_sec']]
df.to_csv('durations.csv',index=False)
print("duration.csv successfully completed")
