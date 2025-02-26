#!/bin/bash
# Kill a process and all its children.

# Check if the parent PID is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <parent_pid>"
  exit 1
fi

PARENT_PID=$1

# Function to kill a process and its children
kill_process_tree() {
  local pid=$1
  # Get all child PIDs of the given PID
  local child_pids=$(ps --ppid $pid -o pid=)
  
  # Recursively kill child processes
  for child_pid in $child_pids; do
    kill_process_tree $child_pid
  done
  
  # Kill the given PID
  if kill -0 $pid 2>/dev/null; then
    echo "Killing process $pid"
    kill -9 $pid
  else
    echo "Process $pid does not exist"
  fi
}

# Kill the parent process and its children
kill_process_tree $PARENT_PID

echo "Parent process $PARENT_PID and all its child processes have been killed."