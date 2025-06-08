# Installation Guide

This guide provides detailed instructions for setting up the G|Flows Frontend application.

## Prerequisites

Before installing the application, ensure you have the following installed:

### Required Software

1. **Node.js** (version 18.0.0 or higher)
   - Download from [nodejs.org](https://nodejs.org/)
   - Verify installation: `node --version`

2. **npm** (version 9.0.0 or higher)
   - Comes with Node.js
   - Verify installation: `npm --version`

3. **Git** (for cloning the repository)
   - Download from [git-scm.com](https://git-scm.com/)
   - Verify installation: `git --version`

### System Requirements

- **Operating System**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **RAM**: Minimum 4GB, Recommended 8GB+
- **Disk Space**: 1GB free space
- **Internet Connection**: Required for package installation

## Installation Steps

### 1. Clone the Repository

\`\`\`bash
# Using HTTPS
git clone https://github.com/your-org/gflows-frontend.git

# Using SSH (if configured)
git clone git@github.com:your-org/gflows-frontend.git

# Navigate to project directory
cd gflows-frontend
\`\`\`

### 2. Install Dependencies

\`\`\`bash
# Install all required packages
npm install

# Alternative: Use yarn if preferred
# yarn install

# Alternative: Use pnpm if preferred  
# pnpm install
\`\`\`

### 3. Environment Configuration

\`\`\`bash
# Copy environment template
cp .env.example .env.local

# Edit the environment file
# On Windows: notepad .env.local
# On macOS/Linux: nano .env.local
\`\`\`

Configure the following variables in `.env.local`:

\`\`\`env
# Required
NEXT_PUBLIC_API_URL=http://localhost:3000
NODE_ENV=development

# Optional (for production)
# Add any additional configuration as needed
\`\`\`

### 4. Verify Installation

\`\`\`bash
# Check if all dependencies are installed correctly
npm list

# Run type checking
npm run type-check

# Run linting
npm run lint
\`\`\`

### 5. Start Development Server

\`\`\`bash
# Start the development server
npm run dev

# The application will be available at:
# http://localhost:3000
\`\`\`

## Alternative Installation Methods

### Using Docker

If you prefer to use Docker:

\`\`\`bash
# Build the Docker image
docker build -t gflows-frontend .

# Run the container
docker run -p 3000:3000 gflows-frontend
\`\`\`

### Using Package Managers

#### Yarn
\`\`\`bash
# Install dependencies
yarn install

# Start development
yarn dev
\`\`\`

#### pnpm
\`\`\`bash
# Install dependencies
pnpm install

# Start development
pnpm dev
\`\`\`

## Troubleshooting

### Common Issues

#### Node.js Version Issues
\`\`\`bash
# Check Node.js version
node --version

# If version is too old, update Node.js
# Visit nodejs.org for the latest version
\`\`\`

#### Permission Issues (macOS/Linux)
\`\`\`bash
# If you get permission errors, avoid using sudo
# Instead, configure npm to use a different directory
npm config set prefix ~/.npm-global

# Add to your shell profile (.bashrc, .zshrc, etc.)
export PATH=~/.npm-global/bin:$PATH
\`\`\`

#### Port Already in Use
\`\`\`bash
# If port 3000 is busy, use a different port
npm run dev -- -p 3001

# Or set the PORT environment variable
PORT=3001 npm run dev
\`\`\`

#### Dependency Installation Failures
\`\`\`bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
\`\`\`

### Getting Help

If you encounter issues:

1. **Check the logs** in your terminal for error messages
2. **Verify prerequisites** are correctly installed
3. **Check GitHub Issues** for similar problems
4. **Create a new issue** with detailed error information

## Next Steps

After successful installation:

1. **Explore the application** at `http://localhost:3000`
2. **Read the documentation** in the README.md
3. **Check the project structure** to understand the codebase
4. **Start developing** by modifying components in the `components/` directory

## Production Deployment

For production deployment, see the [Deployment Guide](DEPLOYMENT.md) or refer to the README.md file.
