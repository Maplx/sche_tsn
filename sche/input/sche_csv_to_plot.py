import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# Read the CSV
df = pd.read_csv('partition_schedule.csv')

# Create custom colormap for applications (-1 to 3)
colors = ['#ffffff', '#d7191c', '#0000a7', '#eecc16', '#008146']
cmap = sns.color_palette(colors)

link_to_nodes = {
    0: ('A', 'B'),
    1: ('B', 'A'),
    2: ('B', 'C'),
    3: ('C', 'B'),
    4: ('C', 'D'),
    5: ('D', 'C'),
    6: ('A', 'C'),
    7: ('A', 'D')
}

# Create heatmap figure
plt.figure(figsize=(8, 2.5))
sns.heatmap(df.iloc[:, 1:].T,
            cmap=cmap,
            cbar=False,
            xticklabels=1,
            yticklabels=True,
            square=False,
            linewidths=0.75,
            linecolor='lightgray')

# Customize the heatmap
plt.xlabel('Time Slot', labelpad=10)
plt.xticks(np.arange(len(df)) + 0.5, range(len(df)), rotation=0)

# Replace link IDs with node pairs in yticks
current_labels = plt.gca().get_yticklabels()
new_labels = []
for label in current_labels:
    link_id = int(label.get_text().split(' ')[1])
    if link_id in link_to_nodes:
        node_pair = link_to_nodes[link_id]
        new_labels.append(f'({node_pair[0]}, {node_pair[1]})')
    else:
        new_labels.append(label.get_text())
plt.gca().set_yticklabels(new_labels)

plt.tight_layout()
plt.savefig('partition_schedule.svg', bbox_inches='tight')
plt.close()

# Create separate legend figure
plt.figure(figsize=(8, 1))
legend_elements = [
    plt.Rectangle((0,0),1,1, facecolor=colors[0], label='Idle', edgecolor='lightgray'),
    plt.Rectangle((0,0),1,1, facecolor=colors[1], label='App 0', edgecolor='lightgray'),
    plt.Rectangle((0,0),1,1, facecolor=colors[2], label='App 1', edgecolor='lightgray'),
    plt.Rectangle((0,0),1,1, facecolor=colors[3], label='App 2', edgecolor='lightgray'),
    plt.Rectangle((0,0),1,1, facecolor=colors[4], label='App 3', edgecolor='lightgray')
]
plt.legend(handles=legend_elements, 
          loc='center',
          ncol=5,
          frameon=False)

plt.axis('off')
plt.tight_layout()
plt.savefig('partition_schedule_legend.svg', bbox_inches='tight')
plt.close()