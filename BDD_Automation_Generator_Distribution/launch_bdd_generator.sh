#!/bin/bash
# BDD Automation Generator Launcher for Linux/macOS
# This script launches the BDD Automation Generator application on Unix-like systems

# Color codes for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BLUE}${BOLD}========================================${NC}"
echo -e "${BLUE}${BOLD}   BDD Automation Generator Launcher    ${NC}"
echo -e "${BLUE}${BOLD}========================================${NC}"

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to script directory
cd "$SCRIPT_DIR" || { 
    echo -e "${RED}Error: Could not change to script directory.${NC}" 
    exit 1
}

# Check for Python
echo -e "\n${YELLOW}Checking for Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON="python3"
    echo -e "${GREEN}Python 3 found.${NC}"
elif command -v python &> /dev/null; then
    PYTHON="python"
    echo -e "${GREEN}Python found.${NC}"
else
    echo -e "${RED}Error: Python not found. Please install Python 3.${NC}"
    read -p "Press Enter to exit..."
    exit 1
fi

# Check Python version
PY_VERSION=$($PYTHON --version | cut -d' ' -f2)
echo -e "${GREEN}Python version: $PY_VERSION${NC}"

# Check if launch.py exists
if [ ! -f "launch.py" ]; then
    echo -e "${RED}Error: launch.py not found. Make sure you're in the correct directory.${NC}"
    read -p "Press Enter to exit..."
    exit 1
fi

# Launch the application
echo -e "\n${BLUE}${BOLD}Starting BDD Automation Generator...${NC}"
$PYTHON launch.py

# Check exit code
if [ $? -ne 0 ]; then
    echo -e "\n${RED}Application exited with an error.${NC}"
    read -p "Press Enter to exit..."
fi

exit 0
