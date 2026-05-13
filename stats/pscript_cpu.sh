#!/bin/bash
# pscript.sh - Simple CPU/System Power Monitoring via Powertop (FABRIC VM friendly)

# Output files
CSV_FILE="plot_ready.csv"
FINAL_LOG="cpu_power.out"

# Clear / initialize files
> "$FINAL_LOG"
echo "timestamp,elapsed_s,sample,system_powertop_W" > "$CSV_FILE"

count=1
start_time=$SECONDS

echo "Starting CPU/System power monitoring via Powertop..."
echo "Monitoring runs while screen 'MYDSTAT' exists."
echo "Press Ctrl+C or kill the MYDSTAT screen to stop."

while screen -ls | grep -q "MYDSTAT"; do
    now=$(date '+%Y-%m-%d %H:%M:%S')
    elapsed=$((SECONDS - start_time))

    # Run Powertop and extract system baseline power
    tmpfile="pdata.$$"
    sudo powertop --csv="$tmpfile" --time=0 >/dev/null 2>&1
    powertop_w="NA"
    if [ -f "$tmpfile" ]; then
        powertop_w=$(grep -i "system baseline" "$tmpfile" | head -1 | awk '{print $(NF-1)}' | sed 's/[^0-9.]//g')
        [ -z "$powertop_w" ] && powertop_w="NA"
        rm -f "$tmpfile"
    fi

    # Log to CSV
    printf "%s,%d,%d,%s\n" "$now" "$elapsed" "$count" "$powertop_w" >> "$CSV_FILE"

    # Log to human-readable file
    echo "[$count] $now | Powertop (CPU/System): ${powertop_w} W" >> "$FINAL_LOG"

    count=$((count + 1))

    # Optional: add small delay to reduce load (recommended)
    # sleep 5
done

echo "Monitoring stopped."

# Cleanup temporary files
rm -f pdata.* 2>/dev/null

echo "Done. Check:"
echo " - Log:   $FINAL_LOG     (human readable summary)"
echo " - CSV:   $CSV_FILE      (detailed log)"
echo " - Plot:  $PLOT_PNG       (CPU power graph)"
