import { type NextRequest, NextResponse } from "next/server"
import type { FlowResponse } from "@/lib/api/flow-api"
import { type OptionsFlow } from "@/types/flow"
import fs from 'fs/promises'
import path from 'path'

// Force dynamic rendering for this route
export const dynamic = 'force-dynamic'

// Define the path to the JSON files relative to the project root
const LATEST_FLOWS_FILE_PATH = path.join(process.cwd(), 'gflows-main/data/json/option_flows_latest.json');
const POLYGON_OPTIONS_FILE_PATH = path.join(process.cwd(), 'gflows-main/data/json/polygon_options_data.json');
const ETFS_FLOWS_FILE_PATH = path.join(process.cwd(), 'gflows-main/data/json/option_flows_20250604_172412.json');

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const assetType = searchParams.get("assetType")
    const tickerFilter = searchParams.get("tickerFilter") || ""
    const premiumFilter = searchParams.get("premiumFilter")
    const quantityFilter = searchParams.get("quantityFilter")
    const volumeFilter = searchParams.get("volumeFilter")
    const limit = Number.parseInt(searchParams.get("limit") || "50")
    const offset = Number.parseInt(searchParams.get("offset") || "0")

    console.log("Flow API called with params:", {
      assetType,
      tickerFilter,
      premiumFilter,
      quantityFilter,
      volumeFilter,
    })

    let allFlows: OptionsFlow[] = []
    let filePathToRead = LATEST_FLOWS_FILE_PATH;
    let fileIdentifier = 'latest flows';

    // Choose the file path based on assetType
    if (assetType === 'stocks') {
        filePathToRead = POLYGON_OPTIONS_FILE_PATH;
        fileIdentifier = 'stocks options';
    } else if (assetType === 'etfs') {
        filePathToRead = ETFS_FLOWS_FILE_PATH;
        fileIdentifier = 'ETFs flows';
    }

    console.log(`Fetching ${assetType} data from: ${filePathToRead} (${fileIdentifier})`);

    try {
      const jsonData = await fs.readFile(filePathToRead, 'utf-8')
      const parsedData = JSON.parse(jsonData)

      if (Array.isArray(parsedData)) {
        allFlows = parsedData.map(item => ({
          timestamp: item.Timestamp,
          ticker: item.Ticker,
          strike: item.Contract ? parseFloat(item.Contract.split(' ')[0]) : 0,
          expiry: item.Contract ? item.Contract.split(' ')[2] : '',
          side: item.Side,
          price: parseFloat(item.Price),
          quantity: parseInt(String(item.Quantity).replace(/,/g, ''), 10),
          premium: parseFloat(String(item.Premium).replace(/[^0-9.-]+/g,"")),
          volume: parseInt(String(item.Volume).replace(/,/g, ''), 10),
          openInterest: parseInt(String(item["Open Interest"]).replace(/,/g, ''), 10),
          spot: item.Spot === "N/A" ? 0 : parseFloat(item.Spot),
          optionType: item.Contract 
            ? (item.Contract.split(' ')[1]?.toLowerCase() === 'call' ? 'call' : 'put')
            : 'put'
        }))
      } else {
        console.error(`JSON data in ${path.basename(filePathToRead)} is not an array:`, parsedData)
        return NextResponse.json(
          {
            error: {
              code: "DATA_FORMAT_ERROR",
              message: `Unexpected data format in ${path.basename(filePathToRead)} file`,
            },
          },
          { status: 500, headers: { "Content-Type": "application/json" } },
        )
      }
    } catch (fileError: any) {
      console.error(`Error reading or parsing JSON file ${path.basename(filePathToRead)}:`, fileError)
      if (fileError.code === 'ENOENT') {
        console.log(`${path.basename(filePathToRead)} not found, returning empty data.`)
        allFlows = []
      } else {
        return NextResponse.json(
          {
            error: {
              code: "FILE_READ_ERROR",
              message: `Could not read options flow data file ${path.basename(filePathToRead)}`,
              details: fileError.message,
            },
          },
          { status: 500, headers: { "Content-Type": "application/json" } },
        )
      }
    }

    let filteredFlows = allFlows
    if (tickerFilter) {
      filteredFlows = filteredFlows.filter(flow => flow.ticker.toLowerCase().includes(tickerFilter.toLowerCase()))
    }
    if (premiumFilter && premiumFilter !== 'all') {
      const minPremium = Number.parseFloat(premiumFilter)
      if (!isNaN(minPremium)) {
        filteredFlows = filteredFlows.filter(flow => flow.premium >= minPremium)
      }
    }
    if (quantityFilter && quantityFilter !== 'all') {
      const minQuantity = Number.parseInt(quantityFilter)
      if (!isNaN(minQuantity)) {
        filteredFlows = filteredFlows.filter(flow => flow.quantity >= minQuantity)
      }
    }
    if (volumeFilter && volumeFilter !== 'all') {
      const minVolume = Number.parseInt(volumeFilter)
      if (!isNaN(minVolume)) {
        filteredFlows = filteredFlows.filter(flow => flow.volume >= minVolume)
      }
    }

    const totalCount = filteredFlows.length
    const paginatedFlows = filteredFlows.slice(offset, offset + limit)

    const response: FlowResponse = {
      flows: paginatedFlows,
      totalCount,
      lastUpdated: new Date().toISOString(),
    }

    console.log("Returning flow data:", response.flows.length, "flows (total:", totalCount, ")")

    return NextResponse.json(response, {
      headers: {
        "Content-Type": "application/json",
      },
    })
  } catch (error: any) {
    console.error("Error in flow data API:", error)
    return NextResponse.json(
      {
        error: {
          code: "INTERNAL_ERROR",
          message: "An internal server error occurred",
          details: error.message,
        },
      },
      { status: 500, headers: { "Content-Type": "application/json" } },
    )
  }
}
