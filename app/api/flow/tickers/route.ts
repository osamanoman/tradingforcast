import { type NextRequest, NextResponse } from "next/server"
import type { TickersResponse } from "@/lib/api/flow-api"

// Force dynamic rendering for this route
export const dynamic = 'force-dynamic'

const ASSET_TICKERS = {
  indices: [
    { symbol: "SPX", name: "S&P 500 Index", currentPrice: 4500.25 },
    { symbol: "NDX", name: "NASDAQ 100 Index", currentPrice: 15800.75 },
    { symbol: "RUT", name: "Russell 2000 Index", currentPrice: 2000.5 },
    { symbol: "VIX", name: "CBOE Volatility Index", currentPrice: 18.25 },
  ],
  etfs: [
    { symbol: "SPY", name: "SPDR S&P 500 ETF Trust", currentPrice: 450.25 },
    { symbol: "QQQ", name: "Invesco QQQ Trust", currentPrice: 380.75 },
    { symbol: "IWM", name: "iShares Russell 2000 ETF", currentPrice: 200.5 },
    { symbol: "XLF", name: "Financial Select Sector SPDR Fund", currentPrice: 35.8 },
    { symbol: "XLE", name: "Energy Select Sector SPDR Fund", currentPrice: 85.4 },
    { symbol: "XLK", name: "Technology Select Sector SPDR Fund", currentPrice: 175.9 },
    { symbol: "XLV", name: "Health Care Select Sector SPDR Fund", currentPrice: 125.6 },
    { symbol: "XLU", name: "Utilities Select Sector SPDR Fund", currentPrice: 68.3 },
  ],
  stocks: [
    { symbol: "AAPL", name: "Apple Inc.", currentPrice: 175.25 },
    { symbol: "MSFT", name: "Microsoft Corporation", currentPrice: 330.8 },
    { symbol: "AMZN", name: "Amazon.com Inc.", currentPrice: 145.6 },
    { symbol: "GOOGL", name: "Alphabet Inc. Class A", currentPrice: 140.25 },
    { symbol: "META", name: "Meta Platforms Inc.", currentPrice: 330.45 },
    { symbol: "NVDA", name: "NVIDIA Corporation", currentPrice: 480.75 },
    { symbol: "TSLA", name: "Tesla Inc.", currentPrice: 265.3 },
    { symbol: "JPM", name: "JPMorgan Chase & Co.", currentPrice: 180.9 },
  ],
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const assetType = searchParams.get("assetType")

    console.log("Tickers API called with assetType:", assetType)

    if (!assetType) {
      return NextResponse.json(
        {
          error: {
            code: "INVALID_PARAMETERS",
            message: "Missing required parameter: assetType",
          },
        },
        {
          status: 400,
          headers: {
            "Content-Type": "application/json",
          },
        },
      )
    }

    const validAssetTypes = ["indices", "etfs", "stocks"]
    if (!validAssetTypes.includes(assetType)) {
      return NextResponse.json(
        {
          error: {
            code: "INVALID_PARAMETERS",
            message: "Invalid assetType parameter",
            details: {
              assetType: `Asset type must be one of: ${validAssetTypes.join(", ")}`,
            },
          },
        },
        {
          status: 400,
          headers: {
            "Content-Type": "application/json",
          },
        },
      )
    }

    // Simulate API delay
    await new Promise((resolve) => setTimeout(resolve, 100))

    const tickers = ASSET_TICKERS[assetType as keyof typeof ASSET_TICKERS] || []

    const response: TickersResponse = {
      assetType,
      tickers,
      lastUpdated: new Date().toISOString(),
    }

    console.log("Returning tickers:", tickers.length, "for", assetType)

    return NextResponse.json(response, {
      headers: {
        "Content-Type": "application/json",
      },
    })
  } catch (error) {
    console.error("Error in tickers API:", error)
    return NextResponse.json(
      {
        error: {
          code: "INTERNAL_ERROR",
          message: "An internal server error occurred",
        },
      },
      {
        status: 500,
        headers: {
          "Content-Type": "application/json",
        },
      },
    )
  }
}
