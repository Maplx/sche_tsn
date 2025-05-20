## Map partition schedule to the TSN schedule
STATE=$1

FLOW_FILE="input/flows_state_${STATE}.csv"
SCHEDULE_FILE="input/partition_schedule_new.csv"

python3 main.py $FLOW_FILE $SCHEDULE_FILE > sche.txt

## Format the TSN schedule based on the `tsnkit` format
## Must run in order:
##python3 format_offset.py $FLOW_FILE
##python3 format_gcl.py $FLOW_FILE
##python3 format_route.py $FLOW_FILE
##python3 format_queue.py $FLOW_FILE
##python3 format_streams.py $FLOW_FILE
##python3 format_pcp.py

