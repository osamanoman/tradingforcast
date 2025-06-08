import type { FlowData } from "@/types/flow"

// Use relative URLs for same-origin requests
const API_BASE_URL = ""

export interface FlowApiParams {
  assetType: string
  tickerFilter?: string
  premiumFilter?: number
  quantityFilter?: number
  volumeFilter?: number
  limit?: number
  offset?: number
}

export interface TickerInfo {
  symbol: string
  name: string
  currentPrice: number
}

export interface TickersResponse {
  assetType: string
  tickers: TickerInfo[]
  lastUpdated: string
}

export interface FlowResponse extends FlowData {
  totalCount: number
}

class FlowApi {
  async getFlowData(params: FlowApiParams): Promise<FlowResponse> {
    const searchParams = new URLSearchParams({
      assetType: params.assetType,
      limit: (params.limit || 50).toString(),
      offset: (params.offset || 0).toString(),
    })

    if (params.tickerFilter) {
      searchParams.append("tickerFilter", params.tickerFilter)
    }
    if (params.premiumFilter) {
      searchParams.append("premiumFilter", params.premiumFilter.toString())
    }
    if (params.quantityFilter) {
      searchParams.append("quantityFilter", params.quantityFilter.toString())
    }
    if (params.volumeFilter) {
      searchParams.append("volumeFilter", params.volumeFilter.toString())
    }

    const url = `${API_BASE_URL}/api/flow/data?${searchParams}`
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error("Flow API error:", errorText)
      throw new Error(`Failed to fetch flow data: ${response.status} ${response.statusText}`)
    }

    const contentType = response.headers.get("content-type")
    if (!contentType || !contentType.includes("application/json")) {
      const responseText = await response.text()
      console.error("Non-JSON response:", responseText)
      throw new Error("Server returned non-JSON response")
    }

    return response.json()
  }

  async getTickers(assetType: string): Promise<TickersResponse> {
    const searchParams = new URLSearchParams({ assetType })

    const url = `${API_BASE_URL}/api/flow/tickers?${searchParams}`
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch tickers: ${response.status} ${response.statusText}`)
    }

    return response.json()
  }
}

export const flowApi = new FlowApi()
