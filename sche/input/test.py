import pandas as pd

# # Load the uploaded Excel file
file_path = 'flows_information_with_nodes_1.xlsx'
data = pd.read_excel(file_path)

# # Print the filtered DataFrame in CSV format without the index
# print(data[data['State ID'] == 0].to_csv(index=False))
data.to_csv('flows_information_with_nodes.csv', index=False)


# # ================================
## Load the schedule
file_path = 'partition_schedule_1.xlsx'
schedule = pd.read_excel(file_path, header=0, index_col=0)

# # Create a new row with 'Time Slot' as 0 and all 'Link' values as -1
new_row = pd.DataFrame([[-1] * (schedule.shape[1])], columns=schedule.columns)
schedule = pd.concat([new_row, schedule], ignore_index=True)

# # Reset the index and rename it to 'Time Slot'
schedule = schedule.reset_index()
schedule = schedule.rename(columns={'index': 'Time Slot'})

print(schedule.to_csv(index=False))
schedule.to_csv('partition_schedule.csv', index=False)

## ---------------------------------------------------
## Seperate the stages into different files

all_flows = pd.read_csv("flows_information_with_nodes.csv")
all_flows = all_flows[["App ID", "State ID", "Flow ID", "Links", "Node Path", "Period"]]

for state in all_flows["State ID"].unique():
    print(state)
    all_flows[all_flows["State ID"] == state].to_csv(
        f"flows_state_{state}.csv", index=False
    )
