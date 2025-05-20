#!/bin/bash

# if [ "$#" -ne 1 ]; then
#     echo "Usage: $0 <SUFFIX>"
#     exit 1
# fi

# SUFFIX=$1


# Define the username to login to the servers
USER="ubuntu"

# Define the directory where the log files are stored on the servers
REMOTE_DIR="/home/ubuntu"

# Define the local directory where you want to save the log files
LOCAL_DIR="../sche/logs"

for i in $(seq 13 16)
do
  # Construct the server IP
  SERVER="192.168.50.$i"
  
  # Use scp to copy the .log files from the server to the local machine
  scp -o StrictHostKeyChecking=no "${USER}@${SERVER}:${REMOTE_DIR}/*.log" $LOCAL_DIR
done