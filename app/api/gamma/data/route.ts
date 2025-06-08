import { type NextRequest, NextResponse } from "next/server"
import fs from 'fs/promises'
import path from 'path'

// Force dynamic rendering for this route
export const dynamic = 'force-dynamic'

// Define the path to the gamma data files relative to the project root
const GAMMA_DATA_DIR = path.join(process.cwd(), 'data/json')

interface GreekExposureData {
  callExposure: number
  putExposure: number
  totalExposure: number
}

// Interface for the raw strike data read from the JSON file
interface RawStrikeData {
  strike: number
  gamma: GreekExposureData
  delta: GreekExposureData
  vanna: GreekExposureData
  charm: GreekExposureData
}

// Interface for the strike data returned in the API response
interface ApiResponseStrikeData {
    strike: number;
    callExposure: number;
    putExposure: number;
    totalExposure: number;
}

interface RawExpiryData {
    strikeData: RawStrikeData[];
    totalExposure: number; // This is likely gamma total exposure in the raw data
    zeroGamma: number | null; // This is likely gamma zero point in the raw data
}

interface RawGammaData {
    ticker: string;
    spotPrice: number;
    expiryData: Record<string, RawExpiryData>;
    lastUpdated: string;
}

interface ApiResponseExpiryData {
    strikeData: ApiResponseStrikeData[];
    totalExposure: number;
    zeroGamma: number | null; // Note: This will still be zero gamma as per current processing script output
}

interface ApiResponseGammaData {
    ticker: string;
    greek: string;
    expiry: string;
    spotPrice: number;
    totalExposure: number;
    zeroGamma: number | null;
    strikeData: ApiResponseStrikeData[];
    lastUpdated: string;
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const ticker = searchParams.get("ticker")
    const greek = searchParams.get("greek")
    const expiry = searchParams.get("expiry")

    console.log("API called with params:", { ticker, greek, expiry })

    // Validate required parameters
    if (!ticker || !greek || !expiry) {
      return NextResponse.json(
        {
          error: {
            code: "INVALID_PARAMETERS",
            message: "Missing required parameters: ticker, greek, expiry",
            details: {
              ticker: !ticker ? "Ticker is required" : undefined,
              greek: !greek ? "Greek is required" : undefined,
              expiry: !expiry ? "Expiry is required" : undefined,
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

    // Validate parameter values
    const validGreeks = ["gamma", "delta", "vanna", "charm"]
    const validExpiries = ["all", "monthly", "opex", "0dte"]

    if (!validGreeks.includes(greek)) {
      return NextResponse.json(
        {
          error: {
            code: "INVALID_PARAMETERS",
            message: "Invalid greek parameter",
            details: {
              greek: `Greek must be one of: ${validGreeks.join(", ")}`,
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

    if (!validExpiries.includes(expiry)) {
      return NextResponse.json(
        {
          error: {
            code: "INVALID_PARAMETERS",
            message: "Invalid expiry parameter",
            details: {
              expiry: `Expiry must be one of: ${validExpiries.join(", ")}`,
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

    // Read the gamma data file for the requested ticker
    const gammaDataPath = path.join(GAMMA_DATA_DIR, `${ticker.toLowerCase()}_gamma.json`)
    
    try {
      const jsonData = await fs.readFile(gammaDataPath, 'utf-8')
      const gammaData = JSON.parse(jsonData) as RawGammaData

      // Get the expiry data
      let responseExpiryData: ApiResponseExpiryData

      // Since our JSON files only have "all" expiry data, we'll use that for all expiry types
      const rawExpiry = gammaData.expiryData["all"]
      if (!rawExpiry || !rawExpiry.strikeData) {
        throw new Error(`No strike data found for ticker ${ticker}`)
      }

      // Process the strike data for the requested greek
      const strikeData: ApiResponseStrikeData[] = rawExpiry.strikeData.map(rawStrike => {
        const greekData = rawStrike[greek as keyof Omit<RawStrikeData, 'strike'>] as GreekExposureData
        return {
          strike: rawStrike.strike,
          callExposure: greekData.callExposure,
          putExposure: greekData.putExposure,
          totalExposure: greekData.totalExposure
        }
      })

      // Sort strike data by strike price
      strikeData.sort((a, b) => a.strike - b.strike)

      responseExpiryData = {
        strikeData,
        totalExposure: rawExpiry.totalExposure,
        zeroGamma: rawExpiry.zeroGamma
      }

      // Create the response data
      const responseData: ApiResponseGammaData = {
        ticker: gammaData.ticker,
        greek,
        expiry,
        spotPrice: gammaData.spotPrice,
        totalExposure: responseExpiryData.totalExposure,
        zeroGamma: responseExpiryData.zeroGamma,
        strikeData: responseExpiryData.strikeData,
        lastUpdated: gammaData.lastUpdated
      }

      return NextResponse.json(responseData)
    } catch (error) {
      console.error("Error reading gamma data:", error)
      return NextResponse.json(
        {
          error: {
            code: "DATA_ERROR",
            message: "Error reading gamma data",
            details: error instanceof Error ? error.message : "Unknown error",
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
  } catch (error) {
    console.error("Error in gamma data API:", error)
    return NextResponse.json(
      {
        error: {
          code: "SERVER_ERROR",
          message: "Internal server error",
          details: error instanceof Error ? error.message : "Unknown error",
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
