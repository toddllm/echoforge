# EchoForge Authentication System Migration Plan

This document outlines the step-by-step plan for replacing EchoForge's existing authentication system with a TypeScript/NextJS authentication system from the source project.

## Overview

We'll implement this migration in stages to ensure stability and proper functionality at each step:

1. **Stage 1**: Remove the existing authentication system from EchoForge
2. **Stage 2**: Copy and implement the source authentication system with minimal changes
3. **Stage 3**: Connect the new authentication frontend to the EchoForge backend

## Stage 1: Remove Existing Authentication

### Goals
- Disable the current authentication system in EchoForge
- Ensure the application functions correctly without authentication
- Prepare the codebase for the new authentication system

### Steps

1. **Create a temporary bypass for auth**:
   - Modify `app/core/auth.py` to bypass all authentication checks
   - Update any middleware that enforces authentication

2. **Disable auth routes**:
   - Comment out or disable the existing auth API routes
   - Keep routes accessible but non-functional

3. **Remove auth UI components**:
   - Disable login/signup pages or redirect to placeholder pages

4. **Testing**:
   - Verify all API endpoints function without authentication
   - Test core functionality to ensure nothing breaks when auth is removed

## Stage 2: Implement New Authentication Frontend

### Goals
- Copy the source authentication system to a new NextJS frontend
- Make minimal modifications required for EchoForge
- Set up database for authentication

### Steps

1. **Create new NextJS frontend application**:
   ```bash
   npx create-next-app@latest echoforge-frontend --typescript
   cd echoforge-frontend
   npm install
   ```

2. **Copy core authentication files**:
   - From source project:
     - `src/lib/auth.ts`
     - `src/lib/authContext.tsx`
     - `src/lib/encryption.ts`
     - `src/middleware.ts`
     - Auth-related API routes (login, signup, etc.)
     - Authentication UI components

3. **Set up Prisma with SQLite**:
   ```bash
   npm install prisma @prisma/client
   npx prisma init
   ```

4. **Configure Prisma schema**:
   - Modify `prisma/schema.prisma` to use SQLite:
   ```
   datasource db {
     provider = "sqlite"
     url      = "file:./echoforge.db"
   }
   ```
   - Copy and adapt user/profile models from source project
   - Add EchoForge-specific fields if needed

5. **Install required dependencies**:
   ```bash
   npm install bcryptjs jose mailgun.js form-data uuid
   npm install -D @types/bcryptjs @types/uuid
   ```

6. **Customize the authentication system**:
   - Update branding and styling for EchoForge
   - Modify email templates
   - Update environment variables

7. **Set up frontend routes**:
   - Login page
   - Signup page
   - Forgot password page
   - Reset password page
   - User profile page

8. **Testing**:
   - Test the authentication flow without backend connectivity
   - Verify that users can register, login, and reset passwords
   - Check token generation and validation

## Stage 3: Connect Authentication to Backend

### Goals
- Integrate the new authentication frontend with the EchoForge backend
- Ensure proper token validation and authorization
- Clean up any unnecessary code

### Steps

1. **Create API proxy endpoints**:
   - Create NextJS API routes that proxy requests to the EchoForge backend
   - Add proper token validation to protected routes

2. **Update middleware**:
   - Implement middleware to handle authenticated sessions
   - Set up proper token forwarding to backend services

3. **Backend API updates**:
   - Modify EchoForge backend to accept and validate JWT tokens
   - Create endpoints for token validation

4. **UI integration**:
   - Connect frontend components to backend services
   - Update navigation to handle authenticated state

5. **Comprehensive testing**:
   - End-to-end testing of authentication flows
   - Test authorization for all protected routes
   - Verify session persistence

6. **Cleanup**:
   - Remove any remaining code from the old authentication system
   - Consolidate configuration and environment variables

## Technical Requirements

### Frontend
- Node.js 18+
- Next.js 14+
- TypeScript 5+
- Prisma 6+
- Tailwind CSS (for UI components)

### Backend
- Python 3.9+
- FastAPI
- SQLite/PostgreSQL
- JWT validation libraries

### Environment Variables

**Frontend (.env.local)**:
```
DATABASE_URL="file:./echoforge.db"
NEXTAUTH_SECRET="your-secret-key"
NEXTAUTH_URL="http://localhost:3000"
JWT_SECRET="your-jwt-secret"
BACKEND_API_URL="http://localhost:8000"
MAILGUN_API_KEY="your-mailgun-key"
MAILGUN_DOMAIN="your-domain.com"
```

**Backend (.env)**:
```
JWT_SECRET="same-jwt-secret-as-frontend"
```

## Notes

- No users will be migrated from the old system - new users will be created manually for testing
- Database schema may need adjustments based on specific EchoForge requirements
- Additional customization may be needed for any EchoForge-specific user attributes
- All auth requests from the frontend will eventually be proxied to the backend API 