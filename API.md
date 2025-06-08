# API Documentation

This document provides comprehensive documentation for the G|Flows Frontend API endpoints.

## Base URL

\`\`\`
Development: http://localhost:3000/api
Production: https://your-domain.com/api
\`\`\`

## Authentication

Currently, the API uses mock data and doesn't require authentication. For production use with real data, implement authentication as needed.

## Error Handling

All API endpoints return consistent error responses:

\`\`\`json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {
      "field": "Additional error details"
    }
  }
}
\`\`\`

### HTTP Status Codes

- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found
- `500` - Internal Server Error

## Gamma Analysis API

### Get Gamma Data

Retrieve Greek exposure data for analysis.

**Endpoint:** `GET /api/gamma/data`

**Parameters:**

| Parameter | Type   | Required | Description                                    |
|-----------|--------|----------|------------------------------------------------|
| ticker    | string | Yes      | Stock/ETF symbol (e.g., "SPY", "AAPL")       |
| greek     | string | Yes      | Greek type: "gamma", "delta", "vanna", "charm" |
| expiry    | string | Yes      | Expiration: "all", "monthly", "opex", "0dte"  |

**Example Request:**
\`\`\`bash
curl "http://localhost:3000/api/gamma/data?ticker=SPY&greek=gamma&expiry=all"
\`\`\`

**Example Response:**
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
    },
    {
      "strike": 445.0,
      "callExposure": 750.30,
      "putExposure": -150.25,
      "totalExposure": 600.05
    }
  ],
  "profileData": {
    "priceLevels": [400, 410, 420, 430, 440, 450, 460, 470, 480, 490, 500],
    "exposureProfile": [100, 150, 200, 250, 300, 350, 300, 250, 200, 150, 100]
  },
  "lastUpdated": "2024-01-15T10:30:00Z"
}
\`\`\`

**Response Fields:**

| Field         | Type     | Description                           |
|---------------|----------|---------------------------------------|
| ticker        | string   | Requested ticker symbol               |
| greek         | string   | Requested Greek type                  |
| expiry        | string   | Requested expiration filter           |
| spotPrice     | number   | Current spot price                    |
| totalExposure | number   | Total exposure in millions            |
| zeroGamma     | number   | Zero gamma crossing point (optional)  |
| strikeData    | array    | Array of strike-level data            |
| profileData   | object   | Price level exposure profile          |
| lastUpdated   | string   | ISO timestamp of last update         |

## Options Flow API

### Get Flow Data

Retrieve real-time options flow data with filtering.

**Endpoint:** `GET /api/flow/data`

**Parameters:**

| Parameter      | Type   | Required | Description                                    |
|----------------|--------|----------|------------------------------------------------|
| assetType      | string | Yes      | Asset type: "indices", "etfs", "stocks"       |
| tickerFilter   | string | No       | Filter by specific ticker                      |
| premiumFilter  | number | No       | Minimum premium threshold                      |
| quantityFilter | number | No       | Minimum quantity threshold                     |
| volumeFilter   | number | No       | Minimum volume threshold                       |
| limit          | number | No       | Number of records (default: 50, max: 100)     |
| offset         | number | No       | Pagination offset (default: 0)                |

**Example Request:**
\`\`\`bash
curl "http://localhost:3000/api/flow/data?assetType=etfs&premiumFilter=10000&limit=25"
\`\`\`

**Example Response:**
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
    },
    {
      "timestamp": "2024-01-15T10:29:45Z",
      "ticker": "QQQ",
      "strike": 380.0,
      "expiry": "2024-01-26",
      "side": "SELL",
      "price": 3.75,
      "quantity": 50,
      "premium": 18750,
      "volume": 2000,
      "openInterest": 8500
    }
  ],
  "totalCount": 150,
  "lastUpdated": "2024-01-15T10:30:00Z"
}
\`\`\`

**Flow Object Fields:**

| Field        | Type   | Description                    |
|--------------|--------|--------------------------------|
| timestamp    | string | ISO timestamp of transaction   |
| ticker       | string | Underlying symbol              |
| strike       | number | Option strike price            |
| expiry       | string | Option expiration date         |
| side         | string | Transaction side (BUY/SELL)    |
| price        | number | Option price per contract      |
| quantity     | number | Number of contracts            |
| premium      | number | Total premium (price × quantity × 100) |
| volume       | number | Daily volume                   |
| openInterest | number | Open interest                  |

### Get Tickers

Retrieve available tickers for an asset type.

**Endpoint:** `GET /api/flow/tickers`

**Parameters:**

| Parameter | Type   | Required | Description                              |
|-----------|--------|----------|------------------------------------------|
| assetType | string | Yes      | Asset type: "indices", "etfs", "stocks" |

**Example Request:**
\`\`\`bash
curl "http://localhost:3000/api/flow/tickers?assetType=etfs"
\`\`\`

**Example Response:**
\`\`\`json
{
  "assetType": "etfs",
  "tickers": [
    {
      "symbol": "SPY",
      "name": "SPDR S&P 500 ETF Trust",
      "currentPrice": 450.25
    },
    {
      "symbol": "QQQ",
      "name": "Invesco QQQ Trust",
      "currentPrice": 380.75
    },
    {
      "symbol": "IWM",
      "name": "iShares Russell 2000 ETF",
      "currentPrice": 200.50
    }
  ],
  "lastUpdated": "2024-01-15T10:30:00Z"
}
\`\`\`

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Development**: 100 requests per minute per IP
- **Production**: 1000 requests per minute per IP

Rate limit headers are included in responses:

\`\`\`
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248000
\`\`\`

## Data Freshness

- **Gamma Data**: Updated every 5 minutes during market hours
- **Flow Data**: Real-time updates (sub-second latency)
- **Ticker Data**: Updated daily at market open

## Pagination

For endpoints that support pagination:

\`\`\`json
{
  "data": [...],
  "pagination": {
    "limit": 50,
    "offset": 0,
    "totalCount": 150,
    "hasMore": true
  }
}
\`\`\`

## WebSocket API (Future)

For real-time updates, a WebSocket API will be available:

\`\`\`javascript
const ws = new WebSocket('wss://your-domain.com/ws');

// Subscribe to flow updates
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'flow',
  filters: {
    assetType: 'etfs',
    premiumFilter: 10000
  }
}));

// Receive real-time updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('New flow:', data);
};
\`\`\`

## SDK Usage

For easier integration, use the provided API client:

\`\`\`typescript
import { gammaApi, flowApi } from '@/lib/api';

// Fetch gamma data
const gammaData = await gammaApi.getGammaData({
  ticker: 'SPY',
  greek: 'gamma',
  expiry: 'all'
});

// Fetch flow data
const flowData = await flowApi.getFlowData({
  assetType: 'etfs',
  premiumFilter: 10000
});
\`\`\`

## Error Examples

### Invalid Parameters
\`\`\`json
{
  "error": {
    "code": "INVALID_PARAMETERS",
    "message": "Invalid greek parameter",
    "details": {
      "greek": "Greek must be one of: gamma, delta, vanna, charm"
    }
  }
}
\`\`\`

### Rate Limit Exceeded
\`\`\`json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "details": {
      "retryAfter": 60
    }
  }
}
\`\`\`

### Internal Server Error
\`\`\`json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An internal server error occurred"
  }
}
\`\`\`

This API documentation provides all the information needed to integrate with the G|Flows Frontend API endpoints.
