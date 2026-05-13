#!/bin/bash
# pscript.sh - Monitor GPU power/energy + attempt powertop (FABRIC VM friendly)

# Output files
CSV_FILE="gpu_power_log.csv"
FINAL_LOG="power_energy.out"
PLOT_DATA="plot_ready.csv"
PLOT_PNG="gpu_power_energy.png"

# Clear / initialize files
> "$FINAL_LOG"
echo "timestamp,elapsed_s,sample,system_powertop_W,gpu_total_W,gpu_energy_J_cum,gpu_energy_Wh_cum" > "$CSV_FILE"

count=1
start_time=$SECONDS
last_time=$start_time
gpu_energy_J=0

echo "Starting GPU power & energy monitoring while screen 'MYDSTAT' exists..."
echo "Ctrl+C or kill the MYDSTAT screen to stop."

while screen -ls | grep -q "MYDSTAT"; do
    now=$(date '+%Y-%m-%d %H:%M:%S')
    current_time=$SECONDS
    elapsed=$((current_time - start_time))
    delta_s=$((current_time - last_time))

    # 1. Try powertop (often NA in VMs) — deterministic run + safe parsing
    tmpfile="pdata.$$"
    sudo powertop --csv="$tmpfile" --time=2 >/dev/null 2>&1
    powertop_w="NA"
    if [ -f "$tmpfile" ]; then
        # Prefer the "system baseline" line; take the numeric field before the units
        powertop_w=$(grep -i "system baseline" "$tmpfile" | head -1 | awk '{print $(NF-1)}' | sed 's/[^0-9.]//g')
        [ -z "$powertop_w" ] && powertop_w="NA"
        rm -f "$tmpfile"
    fi

    # 2. Get total GPU power (Watts) - sum over all GPUs
    gpu_w="0.00"
    if command -v nvidia-smi >/dev/null 2>&1; then
        powers=$(nvidia-smi --query-gpu=power.draw --format=csv,noheader,nounits 2>/dev/null)
        if [ -n "$powers" ]; then
            gpu_w=$(echo "$powers" | awk '{sum += $1} END {printf "%.2f", sum}')
        fi
    fi

    # 3. Accumulate GPU energy (Joules = average power × time interval)
    if [ "$gpu_w" != "0.00" ] && [ "$delta_s" -gt 0 ]; then
        energy_this_step=$(awk "BEGIN {print $gpu_w * $delta_s}")
        gpu_energy_J=$(awk "BEGIN {print $gpu_energy_J + $energy_this_step}")
    fi
    gpu_energy_Wh=$(awk "BEGIN {print $gpu_energy_J / 3600}")

    # Log
    printf "%s,%d,%d,%s,%.2f,%.1f,%.3f\n" \
        "$now" "$elapsed" "$count" "$powertop_w" "$gpu_w" "$gpu_energy_J" "$gpu_energy_Wh" >> "$CSV_FILE"

    echo "[$count] $now | Powertop: ${powertop_w} W | GPU: ${gpu_w} W | GPU energy: ${gpu_energy_J} J (${gpu_energy_Wh} Wh)" >> "$FINAL_LOG"

    count=$((count + 1))
    last_time=$current_time

    sleep 10   # ← actual 10-second interval
done

echo "Monitoring stopped."

# Prepare clean data for plotting (skip header)
tail -n +2 "$CSV_FILE" | cut -d',' -f 4,5,6 > "$PLOT_DATA"  # elapsed,gpu_W,gpu_J

python3 - << 'PYEOF'
import pandas as pd
import matplotlib.pyplot as plt

plt.style.use("seaborn-whitegrid")

# read trimmed data: powertop,gpu_power,cumulative_energy
df = pd.read_csv("./plot_ready.csv", header=None,
                 names=["system_powertop_W", "gpu_power_W", "gpu_energy_J"])

# ensure numeric
df["system_powertop_W"] = pd.to_numeric(df["system_powertop_W"], errors="coerce").fillna(0.0)
df["gpu_power_W"] = pd.to_numeric(df["gpu_power_W"], errors="coerce").fillna(0.0)
df["gpu_energy_J"] = pd.to_numeric(df["gpu_energy_J"], errors="coerce").fillna(0.0)

# compute total power
df["total_power_W"] = df["system_powertop_W"] + df["gpu_power_W"]

x = df.index  # use sample index on x-axis

fig, ax1 = plt.subplots(figsize=(11, 6))

ax1.plot(x, df["total_power_W"], color="black", lw=2, label="Total power (W)")
ax1.plot(x, df["gpu_power_W"], color="crimson", lw=1.5, marker="x", ms=6, label="GPU power (W)")
ax1.plot(x, df["system_powertop_W"], color="green", lw=1.5, marker="o", ms=6, label="System Powertop (W)")
ax1.set_xlabel("Time interval (seconds)", fontsize=12)
ax1.set_ylabel("Power (W)", fontsize=12)
ax1.tick_params(axis="y")
ax1.grid(alpha=0.35)

ax2 = ax1.twinx()
ax2.plot(x, df["gpu_energy_J"], color="tab:blue", lw=1.5, marker="o", ms=5, label="Cumulative energy (J)")
ax2.set_ylabel("Energy (J)", fontsize=12)
ax2.tick_params(axis="y")

# combined legend
lines, labels = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines + lines2, labels + labels2, loc="upper center", ncol=3, fontsize=10)

plt.title("CPU, GPU energy consumption & Cumulative Energy", fontsize=14)
plt.tight_layout()
plt.savefig("gpu_power_energy.png", dpi=200, bbox_inches="tight")
print("Plot saved → gpu_power_energy.png")
PYEOF



# Cleanup temporary files
# rm -f pdata.tmp "$CSV_FILE" "$PLOT_DATA" 2>/dev/null

rm -f pdata.tmp "$CSV_FILE" 2>/dev/null

echo "Done. Check:"
echo "  - Log:          $FINAL_LOG  (human readable)"
echo "  - CSV:          $CSV_FILE   (detailed numbers)"
echo "  - Plot:         $PLOT_PNG"
