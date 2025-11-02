#!/bin/bash

# Kill any processes running on ports 8000, 8080, and 8081
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:8080 | xargs kill -9 2>/dev/null || true
lsof -ti:8081 | xargs kill -9 2>/dev/null || true

# Activate the virtual environment
source agent/bin/activate

# Execute the Python scripts in order (all in background)
python server_query_agent.py &
SERVER_PID=$!

# Wait a moment for the server to start
sleep 2

# Execute client scripts in background
python feedback_client.py &
FEEDBACK_PID=$!

python internal_client.py &
INTERNAL_PID=$!

python summary_client.py &
SUMMARY_PID=$!

python calendar/server.py &
CALENDAR_PID=$!

python gemini_sched/lark_reader.py &

python gemini_sched/planning_2.py &
PLANNING_PID=$!

echo "All services started:"
echo "  - Server (port 8000): PID $SERVER_PID"
echo "  - Feedback Client (port 8080): PID $FEEDBACK_PID"
echo "  - Internal Client (port 8085): PID $INTERNAL_PID"
echo "  - Summary Client (port 8081): PID $SUMMARY_PID"
echo "  - Calendar Server: PID $CALENDAR_PID"
echo "  - Planning Server: PID $PLANNING_PID"
echo ""
# echo "Opening browser at: http://127.0.0.1:5500/calendar/index.html"
echo ""

# Open browser (macOS)
# open "http://127.0.0.1:5500/calendar/index.html"

echo "Press Ctrl+C to stop all services..."

# Wait for user interrupt
trap "kill $SERVER_PID $FEEDBACK_PID $INTERNAL_PID $SUMMARY_PID $CALENDAR_PID $PLANNING_PID 2>/dev/null; exit" INT TERM
wait