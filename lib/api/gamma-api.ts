import type { GammaData, ProfileData } from "@/types/gamma"

// Use relative URLs for same-origin requests
const API_BASE_URL = ""

export interface GammaApiParams {
  ticker: string
  greek: string
  expiry: string
}

export interface SignificantPoint {
  type: "spot_price" | "zero_gamma" | "max_positive" | "max_negative"
  price: number
  value: number
  description: string
}

export interface SignificantPointsResponse {
  ticker: string
  greek: string
  expiry: string
  points: SignificantPoint[]
  lastUpdated: string
}

class GammaApi {
  async getGammaData(params: GammaApiParams): Promise<GammaData> {
    const searchParams = new URLSearchParams({
      ticker: params.ticker,
      greek: params.greek,
      expiry: params.expiry,
    })

    const url = `${API_BASE_URL}/api/gamma/data?${searchParams}`
    console.log("Fetching from URL:", url)

    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })

    console.log("Response status:", response.status)
    console.log("Response headers:", Object.fromEntries(response.headers.entries()))

    if (!response.ok) {
      const errorText = await response.text()
      console.error("Error response:", errorText)
      throw new Error(`Failed to fetch gamma data: ${response.status} ${response.statusText}`)
    }

    const contentType = response.headers.get("content-type")
    if (!contentType || !contentType.includes("application/json")) {
      const responseText = await response.text()
      console.error("Non-JSON response:", responseText)
      throw new Error("Server returned non-JSON response")
    }

    return response.json()
  }

  async getProfileData(params: GammaApiParams): Promise<{
    ticker: string
    greek: string
    expiry: string
    spotPrice: number
    zeroGamma?: number
    profileData: ProfileData
    lastUpdated: string
  }> {
    const searchParams = new URLSearchParams({
      ticker: params.ticker,
      greek: params.greek,
      expiry: params.expiry,
    })

    const url = `${API_BASE_URL}/api/gamma/profile?${searchParams}`
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch profile data: ${response.status} ${response.statusText}`)
    }

    return response.json()
  }

  async getSignificantPoints(params: GammaApiParams): Promise<SignificantPointsResponse> {
    const searchParams = new URLSearchParams({
      ticker: params.ticker,
      greek: params.greek,
      expiry: params.expiry,
    })

    const url = `${API_BASE_URL}/api/gamma/significant-points?${searchParams}`
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch significant points: ${response.status} ${response.statusText}`)
    }

    return response.json()
  }
}

export const gammaApi = new GammaApi()
