import csv
from collections import defaultdict

def csv_to_latex_table():
    # Read the CSV data
    csv_data = []
    with open('all_flows.csv', 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            csv_data.append(row)

    # Group flows by state
    flows_by_state = defaultdict(list)
    for row in csv_data:
        flows_by_state[int(row['State ID'])].append(row)

    # Generate LaTeX table
    latex_table = []
    latex_table.append(r'\begin{table}[htbp]')
    latex_table.append(r'    \centering')
    latex_table.append(r'    \caption{Flow Configurations for Each Stage with Paths and Periods}')
    latex_table.append(r'    \label{tab:flow_configs}')
    latex_table.append(r'    \begin{tabular}{cccl}')
    latex_table.append(r'        \hline')
    latex_table.append(r'        \textbf{App} & \textbf{Flow} & \textbf{Period} & \textbf{Node Path} \\')
    latex_table.append(r'        \hline')

    # Add flows for each state
    for state in sorted(flows_by_state.keys()):
        latex_table.append(r'        \multicolumn{4}{c}{\textbf{Stage ' + str(state) + r'}} \\')
        latex_table.append(r'        \hline')
        
        # Sort flows by App ID and Flow ID
        state_flows = sorted(flows_by_state[state], 
                           key=lambda x: (int(x['App ID']), int(x['Flow ID'])))
        
        for flow in state_flows:
            row = f"        {flow['App ID']} & {flow['Flow ID']} & {flow['Period']} & {flow['Node Path']} \\\\"
            latex_table.append(row)
        
        latex_table.append(r'        \hline')

    latex_table.append(r'    \end{tabular}')
    latex_table.append(r'\end{table}')

    # Write to file
    with open('flow_table.tex', 'w') as file:
        file.write('\n'.join(latex_table))

# Example usage
if __name__ == "__main__":
    csv_to_latex_table()