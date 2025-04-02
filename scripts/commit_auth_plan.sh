#!/bin/bash
# Commit Authentication Migration Plan to Repository

set -e  # Exit on any error

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the echoforge directory
if [ ! -d "app" ] || [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}Error: This script must be run from the echoforge directory${NC}"
    exit 1
fi

# Make scripts executable
chmod +x scripts/disable_auth.py
chmod +x scripts/connect_auth_backend.py
chmod +x scripts/setup_frontend_auth.sh
chmod +x scripts/commit_auth_plan.sh

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}Error: git is not installed${NC}"
    exit 1
fi

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}Initializing git repository...${NC}"
    git init
fi

# Stage the files
echo -e "${YELLOW}Staging files...${NC}"
git add AUTH_MIGRATION_PLAN.md
git add scripts/disable_auth.py
git add scripts/connect_auth_backend.py
git add scripts/setup_frontend_auth.sh
git add scripts/commit_auth_plan.sh

# Commit the changes
echo -e "${YELLOW}Committing changes...${NC}"
git commit -m "Add authentication migration plan and scripts

This commit includes:
- Detailed migration plan for replacing the auth system
- Stage 1 script to disable existing auth system
- Stage 2 script to set up NextJS frontend with auth
- Stage 3 script to connect frontend auth to backend"

# Push to the repository
if git remote | grep -q "origin"; then
    # Get the current branch name
    BRANCH=$(git branch --show-current)
    if [ -z "$BRANCH" ]; then
        BRANCH="main" # Default to main if we're in detached HEAD state
    fi
    
    echo -e "${YELLOW}Pushing to origin/$BRANCH...${NC}"
    git push origin HEAD:$BRANCH
else
    echo -e "${YELLOW}No remote repository configured. To push, first add a remote:${NC}"
    echo "  git remote add origin <repository-url>"
    echo "  git push -u origin main"
fi

echo -e "${GREEN}"
echo "====================================================="
echo "   Authentication Migration Plan Committed!"
echo "====================================================="
echo -e "${NC}"
echo "The migration plan and scripts have been committed to the repository."
echo ""
echo "Next steps:"
echo "1. Review the AUTH_MIGRATION_PLAN.md file"
echo "2. Start with Stage 1 by running: python scripts/disable_auth.py"
echo "3. Test the application without authentication"
echo "4. Set up the frontend with: bash scripts/setup_frontend_auth.sh"
echo "5. Test the frontend authentication in isolation"
echo "6. Connect to backend with: python scripts/connect_auth_backend.py"
echo ""
echo -e "${YELLOW}Remember to set secure JWT secrets in both frontend and backend${NC}" 