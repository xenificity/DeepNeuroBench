import pandas as pd
import matplotlib.pyplot as plt

# Clean professional style
plt.style.use('seaborn-v0_8-whitegrid')

# Load and select columns
df1 = pd.read_csv("vm1_plot_ready.csv")[['system_powertop_W', 'gpu_total_W', 'total_power_W']]
df2 = pd.read_csv("vm2_plot_ready.csv")[['system_powertop_W', 'gpu_total_W', 'total_power_W']]
df3 = pd.read_csv("vm3_plot_ready.csv")[['system_powertop_W', 'gpu_total_W', 'total_power_W']]

data = [
    (df1, 'VM1'),
    (df2, 'VM2'),
    (df3, 'VM3')
]
fig, axes = plt.subplots(3, 1, figsize=(12, 8.5), sharex=True, sharey=True)

colors = {
    'cpu':   '#1f77b4',
    'gpu':   '#ff7f0e',
    'total': '#2ca02c'
}

for ax, (df, vm_label) in zip(axes, data):
    ax.plot(df['system_powertop_W'], color=colors['cpu'],   lw=2.4, label='CPU')
    ax.plot(df['gpu_total_W'],       color=colors['gpu'],   lw=2.1, ls='--', label='GPU')
    ax.plot(df['total_power_W'],     color=colors['total'], lw=2.8, alpha=0.9, label='Total')
    
    ax.set_title(vm_label, fontsize=12, pad=8)
    ax.grid(True, linestyle=':', alpha=0.55)
    ax.tick_params(labelsize=10)

# Single legend OUTSIDE the plot area (above everything)
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels,
           loc='upper center',
           bbox_to_anchor=(0.5, 1.00),          # push higher
           ncol=3,
           fontsize=10.8,
           frameon=True,
           framealpha=0.95,
           title='Power Consumption on Resources',
           title_fontsize=11)

# Main title + labels
fig.suptitle("Power Consumption – C2 Cluster VMs", 
             fontsize=14, fontweight='bold', 
             y=1.06)  # give extra space above legend

fig.text(0.04, 0.5, 'Power (Watt)', va='center', rotation='vertical', fontsize=12)
axes[-1].set_xlabel('Time Interval (seconds)', fontsize=11.5)

# IMPORTANT: leave more top margin
plt.tight_layout(rect=[0.07, 0.04, 0.93, 0.88])  # reduced top rect to 0.88
plt.savefig("power_consumption_C2.png", dpi=400, bbox_inches='tight')
plt.show()

#Graph 2    
fig, ax = plt.subplots(figsize=(15, 7.8), dpi=130)

vm_styles = [
    {'name': 'VM1', 'color_cycle': ['#1f77b4', '#ff7f0e', '#2ca02c'], 'ls_cycle': ['-', '--', '-.'], 'lw': [2.8, 2.3, 3.2]},
    {'name': 'VM3', 'color_cycle': ['#4c78a8', '#ff9b9b', '#74d074'], 'ls_cycle': ['-', '--', '-.'], 'lw': [2.4, 2.0, 2.8]},
    {'name': 'VM2', 'color_cycle': ['#7f7f7f', '#d62728', '#17becf'], 'ls_cycle': ['-', '--', '-.'], 'lw': [2.5, 2.1, 3.0]}
]

for vm_style, df in zip(vm_styles, [df1, df2, df3]):
    vm = vm_style['name']
    c = vm_style['color_cycle']
    ls = vm_style['ls_cycle']
    lw = vm_style['lw']
    
    ax.plot(df['system_powertop_W'], color=c[0], ls=ls[0], lw=lw[0], label=f'{vm} – CPU')
    ax.plot(df['gpu_total_W'],       color=c[1], ls=ls[1], lw=lw[1], label=f'{vm} – GPU')
    ax.plot(df['total_power_W'],     color=c[2], ls=ls[2], lw=lw[2], label=f'{vm} – Total')

ax.set_title("Power Consumption – C2 Cluster VMs", fontsize=15, fontweight='bold')
ax.set_xlabel("Time Interval (seconds)", fontsize=12.5)
ax.set_ylabel("Power (Watt)", fontsize=12.5)

ax.legend(ncol=3, fontsize=10.2, loc='upper left', frameon=True, framealpha=0.94, 
          title="Virtual Machine and Resource", title_fontsize=11.5)

ax.grid(True, alpha=0.55, ls=':')
ax.tick_params(labelsize=10.8)

plt.tight_layout()
plt.savefig("power_consumption_C2_grouped.png", dpi=400, bbox_inches='tight')
plt.show()
