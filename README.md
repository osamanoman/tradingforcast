# G|Flows Frontend - Options Market Analysis Platform

A modern React-based dashboard for options market analysis, featuring real-time Greek exposure visualization and options flow tracking.

## 🚀 Features

- **GAMMA Analysis**: Interactive visualization of options Greek exposures (Gamma, Delta, Vanna, Charm)
- **Options Flow**: Real-time options transaction tracking with advanced filtering
- **Market Analysis**: Comprehensive market insights and trend analysis
- **Professional UI**: Built with shadcn/ui components and Tailwind CSS
- **Dark/Light Theme**: Seamless theme switching
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Real-time Updates**: Auto-refresh capabilities for live data

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Features Overview](#features-overview)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Deployment](#deployment)
- [Contributing](#contributing)

## 🚀 Quick Start

\`\`\`bash
# Clone the repository
git clone <repository-url>
cd gflows-frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local

# Start development server
npm run dev
\`\`\`

Open [http://localhost:3000](http://localhost:3000) to view the application.

## 📦 Installation

### Prerequisites

- Node.js 18.0 or higher
- npm 9.0 or higher
- Git

### Step-by-Step Installation

1. **Clone the repository**
   \`\`\`bash
   git clone <repository-url>
   cd gflows-frontend
   \`\`\`

2. **Install dependencies**
   \`\`\`bash
   npm install
   \`\`\`

3. **Environment Setup**
   \`\`\`bash
   cp .env.example .env.local
   \`\`\`
   
   Edit `.env.local` and configure:
   \`\`\`env
   NEXT_PUBLIC_API_URL=http://localhost:3000
   \`\`\`

4. **Start the development server**
   \`\`\`bash
   npm run dev
   \`\`\`

5. **Build for production**
   \`\`\`bash
   npm run build
   npm start
   \`\`\`

## 📁 Project Structure

\`\`\`
gflows-frontend/
├── app/                          # Next.js App Router
│   ├── api/                      # API Routes
│   │   ├── gamma/               # Gamma analysis endpoints
│   │   └── flow/                # Options flow endpoints
│   ├── gamma/                   # Gamma analysis page
│   ├── flow/                    # Options flow page
│   ├── globals.css              # Global styles
│   ├── layout.tsx               # Root layout
│   └── page.tsx                 # Home page (redirects to gamma)
├── components/                   # React components
│   ├── ui/                      # shadcn/ui components
│   ├── gamma/                   # Gamma analysis components
│   ├── flow/                    # Options flow components
│   ├── app-sidebar.tsx          # Main navigation sidebar
│   └── theme-toggle.tsx         # Theme switching component
├── hooks/                       # Custom React hooks
│   ├── use-gamma-data.ts        # Gamma data fetching
│   └── use-flow-data.ts         # Flow data fetching
├── lib/                         # Utility libraries
│   ├── api/                     # API client functions
│   ├── mock-data.ts             # Mock data generators
│   └── utils.ts                 # Utility functions
├── types/                       # TypeScript type definitions
│   ├── gamma.ts                 # Gamma analysis types
│   └── flow.ts                  # Options flow types
├── public/                      # Static assets
├── package.json                 # Dependencies and scripts
├── tailwind.config.js           # Tailwind CSS configuration
├── tsconfig.json                # TypeScript configuration
└── next.config.js               # Next.js configuration
\`\`\`

## 🎯 Features Overview

### GAMMA Analysis
- **Interactive Charts**: Visualize Greek exposures across strike prices
- **Multiple Greeks**: Support for Gamma, Delta, Vanna, and Charm
- **Chart Types**: 
  - Absolute exposure view
  - Call/Put breakdown
  - Exposure profile analysis
- **Expiration Filtering**: All, Monthly, OPEX, 0DTE options
- **Data Export**: CSV export for analysis and significant points

### Options Flow
- **Real-time Data**: Live options transaction tracking
- **Advanced Filtering**: Filter by asset type, ticker, premium, quantity, volume
- **Asset Types**: Indices, ETFs, and individual stocks
- **Color-coded Transactions**: Visual distinction between buy/sell orders
- **Auto-refresh**: Configurable automatic data updates

### Technical Features
- **Responsive Design**: Mobile-first approach with Tailwind CSS
- **Theme Support**: Dark/light mode with system preference detection
- **Performance Optimized**: React hooks for efficient data fetching
- **Type Safety**: Full TypeScript implementation
- **Modern UI**: shadcn/ui component library

## 🔌 API Documentation

### Gamma Analysis Endpoints

#### GET `/api/gamma/data`
Fetch Greek exposure data for analysis.

**Parameters:**
- `ticker` (string): Stock/ETF symbol (e.g., "SPY")
- `greek` (string): Greek type ("gamma", "delta", "vanna", "charm")
- `expiry` (string): Expiration filter ("all", "monthly", "opex", "0dte")

**Response:**
\`\`\`json
{
  "ticker": "SPY",
  "greek": "gamma",
  "expiry": "all",
  "spotPrice": 450.25,
  "totalExposure": 1250.75,
  "zeroGamma": 445.50,
  "strikeData": [
    {
      "strike": 440.0,
      "callExposure": 500.25,
      "putExposure": -200.50,
      "totalExposure": 299.75
    }
  ],
  "profileData": {
    "priceLevels": [400, 410, 420, ...],
    "exposureProfile": [100, 150, 200, ...]
  },
  "lastUpdated": "2024-01-15T10:30:00Z"
}
\`\`\`

### Options Flow Endpoints

#### GET `/api/flow/data`
Fetch real-time options flow data.

**Parameters:**
- `assetType` (string): Asset category ("indices", "etfs", "stocks")
- `tickerFilter` (string, optional): Filter by specific ticker
- `premiumFilter` (number, optional): Minimum premium threshold
- `quantityFilter` (number, optional): Minimum quantity threshold
- `volumeFilter` (number, optional): Minimum volume threshold
- `limit` (number, optional): Number of records (default: 50)
- `offset` (number, optional): Pagination offset (default: 0)

**Response:**
\`\`\`json
{
  "flows": [
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "ticker": "SPY",
      "strike": 450.0,
      "expiry": "2024-01-19",
      "side": "BUY",
      "price": 2.50,
      "quantity": 100,
      "premium": 25000,
      "volume": 1500,
      "openInterest": 5000
    }
  ],
  "totalCount": 150,
  "lastUpdated": "2024-01-15T10:30:00Z"
}
\`\`\`

#### GET `/api/flow/tickers`
Get available tickers for an asset type.

**Parameters:**
- `assetType` (string): Asset category ("indices", "etfs", "stocks")

**Response:**
\`\`\`json
{
  "assetType": "etfs",
  "tickers": [
    {
      "symbol": "SPY",
      "name": "SPDR S&P 500 ETF Trust",
      "currentPrice": 450.25
    }
  ],
  "lastUpdated": "2024-01-15T10:30:00Z"
}
\`\`\`

## 🛠 Development

### Available Scripts

\`\`\`bash
# Development
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript compiler

# Testing
npm run test         # Run tests
npm run test:watch   # Run tests in watch mode
npm run test:coverage # Run tests with coverage
\`\`\`

### Development Workflow

1. **Start development server**
   \`\`\`bash
   npm run dev
   \`\`\`

2. **Make changes** to components, pages, or API routes

3. **Test changes** in the browser at `http://localhost:3000`

4. **Run linting** before committing
   \`\`\`bash
   npm run lint
   \`\`\`

5. **Build and test production** build
   \`\`\`bash
   npm run build
   npm run start
   \`\`\`

### Adding New Features

#### Adding a New Page
1. Create page component in `app/new-page/page.tsx`
2. Add navigation link in `components/app-sidebar.tsx`
3. Create necessary API routes in `app/api/`
4. Add TypeScript types in `types/`

#### Adding New API Endpoints
1. Create route handler in `app/api/[endpoint]/route.ts`
2. Add client function in `lib/api/`
3. Create custom hook in `hooks/`
4. Add TypeScript interfaces in `types/`

### Code Style Guidelines

- **TypeScript**: Use strict typing, avoid `any`
- **Components**: Use functional components with hooks
- **Styling**: Use Tailwind CSS classes, avoid inline styles
- **API**: Follow REST conventions, use proper HTTP status codes
- **Naming**: Use descriptive names, follow camelCase for variables

## 🚀 Deployment

### Vercel (Recommended)

1. **Connect repository** to Vercel
2. **Configure environment variables** in Vercel dashboard
3. **Deploy** automatically on push to main branch

\`\`\`bash
# Using Vercel CLI
npm i -g vercel
vercel --prod
\`\`\`

### Docker Deployment

\`\`\`dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
\`\`\`

\`\`\`bash
# Build and run
docker build -t gflows-frontend .
docker run -p 3000:3000 gflows-frontend
\`\`\`

### Environment Variables

Required environment variables for production:

\`\`\`env
NEXT_PUBLIC_API_URL=https://your-api-domain.com
NODE_ENV=production
\`\`\`

## 🤝 Contributing

### Getting Started

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** changes: `git commit -m 'Add amazing feature'`
4. **Push** to branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

### Development Guidelines

- Follow the existing code style and patterns
- Add TypeScript types for all new code
- Write meaningful commit messages
- Test your changes thoroughly
- Update documentation as needed

### Reporting Issues

When reporting issues, please include:
- Browser and version
- Steps to reproduce
- Expected vs actual behavior
- Screenshots if applicable
- Console errors if any

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check this README and inline code comments
- **Issues**: Open an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions

## 🔄 Changelog

### v1.0.0 (Current)
- Initial release with GAMMA analysis and Options Flow
- Modern React/Next.js architecture
- shadcn/ui component library
- Dark/light theme support
- Responsive design
- TypeScript implementation
