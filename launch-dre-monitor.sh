#!/bin/bash
# DRE Guardian - Desktop Launcher for Linux/Mac
# Make executable: chmod +x launch-dre-monitor.sh
# Run: ./launch-dre-monitor.sh

echo ""
echo "========================================"
echo "  DRE GUARDIAN - Live Monitor"
echo "========================================"
echo ""

# Change to guardian directory
cd "$(dirname "$0")/guardian"

# Check if virtual environment exists
if [ -f "../venv/bin/activate" ]; then
    echo "[*] Activating virtual environment..."
    source ../venv/bin/activate
elif [ -f "../.venv/bin/activate" ]; then
    echo "[*] Activating virtual environment..."
    source ../.venv/bin/activate
else
    echo "[!] Warning: No virtual environment found"
    echo "[!] Using system Python"
fi

echo "[*] Starting governance monitor..."
echo "[*] Dashboard will open at http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop monitoring"
echo ""

# Run the monitor with dashboard
python cli.py monitor --dashboard
