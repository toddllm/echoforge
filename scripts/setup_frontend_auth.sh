#!/bin/bash
# Setup EchoForge Frontend with Authentication

set -e  # Exit on any error

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Banner
echo -e "${GREEN}"
echo "====================================================="
echo "   EchoForge Frontend Authentication Setup Script"
echo "====================================================="
echo -e "${NC}"

# Check if source app exists
SOURCE_PATH="/home/tdeshane/development/fertilia-journey-app"
if [ ! -d "$SOURCE_PATH" ]; then
    echo -e "${RED}Error: Source project not found at $SOURCE_PATH${NC}"
    exit 1
fi

# Create frontend directory
FRONTEND_DIR="$HOME/echoforge-frontend"
echo -e "${YELLOW}Step 1: Creating NextJS frontend application${NC}"

if [ -d "$FRONTEND_DIR" ]; then
    echo -e "${YELLOW}Frontend directory already exists. Do you want to remove it and start fresh? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "Removing existing directory..."
        rm -rf "$FRONTEND_DIR"
    else
        echo "Will use existing directory. Proceed with caution."
    fi
fi

if [ ! -d "$FRONTEND_DIR" ]; then
    echo "Creating new NextJS application..."
    npx create-next-app@latest "$FRONTEND_DIR" --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"
    cd "$FRONTEND_DIR" || exit 1
    echo "NextJS application created successfully."
else
    cd "$FRONTEND_DIR" || exit 1
fi

# Install dependencies
echo -e "${YELLOW}Step 2: Installing required dependencies${NC}"
npm install prisma @prisma/client bcryptjs jose mailgun.js form-data uuid
npm install -D @types/bcryptjs @types/uuid

# Setup Prisma
echo -e "${YELLOW}Step 3: Setting up Prisma with SQLite${NC}"
npx prisma init

# Modify Prisma schema
echo -e "${YELLOW}Step 4: Configuring Prisma schema${NC}"
cat > "./prisma/schema.prisma" << EOF
// This is your Prisma schema file,
// learn more about it in the docs: https://pris.ly/d/prisma-schema

generator client {
  provider      = "prisma-client-js"
  binaryTargets = ["native"]
}

datasource db {
  provider = "sqlite"
  url      = "file:./echoforge.db"
}

// User model for authentication
model User {
  id              String       @id @default(uuid())
  email           String       @unique
  passwordHash    String
  username        String?      @unique  // Optional for EchoForge
  resetToken      String?
  resetTokenExpiry DateTime?
  isActive        Boolean      @default(true)
  isAdmin         Boolean      @default(false)
  createdAt       DateTime     @default(now())
  updatedAt       DateTime     @updatedAt
  profile         Profile?
}

// User profile information
model Profile {
  id              String    @id @default(uuid())
  userId          String    @unique
  user            User      @relation(fields: [userId], references: [id], onDelete: Cascade)
  firstName       String
  lastName        String
  bio             String?
  organization    String?
  themePreference String?   @default("dark")
  createdAt       DateTime  @default(now())
  updatedAt       DateTime  @updatedAt
}

// Session model
model Session {
  id        String    @id @default(uuid())
  userId    String    
  expiresAt DateTime
  data      String?    // JSON data stored as string
  createdAt DateTime  @default(now())
}
EOF

# Create .env.local file
echo -e "${YELLOW}Step 5: Setting up environment variables${NC}"
cat > "./.env.local" << EOF
# Database configuration
DATABASE_URL="file:./prisma/echoforge.db"

# Authentication
NEXTAUTH_SECRET="replace-with-your-secret-key-for-echoforge"
NEXTAUTH_URL="http://localhost:3000"
JWT_SECRET="replace-with-your-jwt-secret-key-for-echoforge"

# API Backend
BACKEND_API_URL="http://localhost:8000"

# Email service (for password reset)
MAILGUN_API_KEY="replace-with-your-mailgun-api-key"
MAILGUN_DOMAIN="replace-with-your-mailgun-domain"
EOF

# Create directories for auth files
echo -e "${YELLOW}Step 6: Creating directory structure${NC}"
mkdir -p ./src/lib
mkdir -p ./src/app/api/auth/login
mkdir -p ./src/app/api/auth/signup
mkdir -p ./src/app/api/auth/logout
mkdir -p ./src/app/api/auth/check
mkdir -p ./src/app/api/auth/forgot-password
mkdir -p ./src/app/api/auth/reset-password
mkdir -p ./src/app/api/auth/verify-reset-token
mkdir -p ./src/app/login
mkdir -p ./src/app/signup
mkdir -p ./src/app/forgot-password
mkdir -p ./src/app/reset-password
mkdir -p ./src/services

# Copy auth files from source project
echo -e "${YELLOW}Step 7: Copying authentication files${NC}"

# lib files
cp "$SOURCE_PATH/src/lib/auth.ts" ./src/lib/
cp "$SOURCE_PATH/src/lib/authContext.tsx" ./src/lib/
cp "$SOURCE_PATH/src/lib/encryption.ts" ./src/lib/
cp "$SOURCE_PATH/src/middleware.ts" ./src/

# API routes
cp "$SOURCE_PATH/src/app/api/auth/login/route.ts" ./src/app/api/auth/login/
cp "$SOURCE_PATH/src/app/api/auth/signup/route.ts" ./src/app/api/auth/signup/
cp "$SOURCE_PATH/src/app/api/auth/logout/route.ts" ./src/app/api/auth/logout/
cp "$SOURCE_PATH/src/app/api/auth/check/route.ts" ./src/app/api/auth/check/
cp "$SOURCE_PATH/src/app/api/auth/forgot-password/route.ts" ./src/app/api/auth/forgot-password/
cp "$SOURCE_PATH/src/app/api/auth/reset-password/route.ts" ./src/app/api/auth/reset-password/
cp "$SOURCE_PATH/src/app/api/auth/verify-reset-token/route.ts" ./src/app/api/auth/verify-reset-token/

# Pages
cp "$SOURCE_PATH/src/app/login/page.tsx" ./src/app/login/
cp "$SOURCE_PATH/src/app/signup/page.tsx" ./src/app/signup/
cp "$SOURCE_PATH/src/app/forgot-password/page.tsx" ./src/app/forgot-password/
cp "$SOURCE_PATH/src/app/reset-password/page.tsx" ./src/app/reset-password/

# Services
cp "$SOURCE_PATH/src/services/userService.ts" ./src/services/

echo -e "${YELLOW}Step 8: Running Prisma migration${NC}"
npx prisma migrate dev --name init

# Create a README with next steps
echo -e "${YELLOW}Step 9: Creating README with next steps${NC}"
cat > "./ECHOFORGE_FRONTEND_README.md" << EOF
# EchoForge Frontend

This is the new NextJS frontend for EchoForge with authentication integration.

## Setup

1. Install dependencies:
   \`\`\`
   npm install
   \`\`\`

2. Update environment variables in \`.env.local\` with your specific values.

3. Start the development server:
   \`\`\`
   npm run dev
   \`\`\`

## Next Steps

1. Update branding and styling to match EchoForge
2. Test the authentication flow
3. Create API proxy endpoints to connect to the EchoForge backend

## Authentication

The authentication system includes:
- Login
- Signup
- Password reset
- Session management

All auth files are copied from the source project and may need customization for EchoForge.

## Database

Using SQLite with Prisma ORM. The database file is located at \`./prisma/echoforge.db\`.
EOF

echo -e "${GREEN}"
echo "====================================================="
echo "   EchoForge Frontend Setup Complete!"
echo "====================================================="
echo -e "${NC}"
echo "To start the application:"
echo "  cd $FRONTEND_DIR"
echo "  npm run dev"
echo ""
echo "See ECHOFORGE_FRONTEND_README.md for next steps."
echo ""
echo -e "${YELLOW}NOTE: You will need to customize the files for EchoForge branding and functionality.${NC}" 