import type { GammaData, StrikeData, ProfileData } from "@/types/gamma"
import type { FlowData, OptionsFlow } from "@/types/flow"

const SPOT_PRICES: Record<string, number> = {
  SPY: 450.0,
  QQQ: 380.0,
  IWM: 200.0,
  AAPL: 175.0,
  MSFT: 330.0,
  NVDA: 480.0,
  AMZN: 145.0,
  META: 330.0,
  GOOGL: 140.0,
  TSLA: 265.0,
}

const ASSET_TICKERS = {
  indices: ["SPX", "NDX", "RUT", "VIX"],
  etfs: ["SPY", "QQQ", "IWM", "XLF", "XLE", "XLK", "XLV", "XLU"],
  stocks: ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA", "JPM"],
}

export function generateMockGammaData(ticker: string, greek: string, expiry: string): GammaData {
  const spotPrice = SPOT_PRICES[ticker] || 100
  const strikeMin = spotPrice * 0.8
  const strikeMax = spotPrice * 1.2
  const numStrikes = 30

  const strikes = Array.from(
    { length: numStrikes },
    (_, i) => strikeMin + (i * (strikeMax - strikeMin)) / (numStrikes - 1),
  )

  const strikeData: StrikeData[] = strikes.map((strike) => {
    // Generate exposure based on distance from spot
    const distance = Math.abs(strike - spotPrice) / spotPrice
    const baseExposure = Math.exp(-0.5 * Math.pow(distance / 0.05, 2)) * 1000

    let callExposure = baseExposure * (1 + Math.random() * 0.3)
    let putExposure = -baseExposure * 0.8 * (1 + Math.random() * 0.3)

    // Adjust based on Greek type
    if (greek === "delta") {
      callExposure = Math.max(0, (strike - spotPrice * 0.9) / (spotPrice * 0.2)) * 1000
      putExposure = -Math.max(0, (spotPrice * 1.1 - strike) / (spotPrice * 0.2)) * 1000
    } else if (greek === "vanna") {
      callExposure = Math.exp(-0.5 * Math.pow((strike - spotPrice * 1.05) / (spotPrice * 0.07), 2)) * 1000
      putExposure = -Math.exp(-0.5 * Math.pow((strike - spotPrice * 0.9) / (spotPrice * 0.06), 2)) * 700
    } else if (greek === "charm") {
      callExposure = Math.sin((strike - spotPrice) / (spotPrice * 0.1)) * 1000
      putExposure = -Math.sin((strike - spotPrice) / (spotPrice * 0.1) + 1) * 900
    }

    // Adjust based on expiry
    const expiryMultiplier = expiry === "monthly" ? 0.7 : expiry === "opex" ? 0.5 : expiry === "0dte" ? 0.3 : 1
    callExposure *= expiryMultiplier
    putExposure *= expiryMultiplier

    // Add noise
    callExposure += (Math.random() - 0.5) * 200
    putExposure += (Math.random() - 0.5) * 200

    return {
      strike: Number.parseFloat(strike.toFixed(2)),
      callExposure: Number.parseFloat(callExposure.toFixed(2)),
      putExposure: Number.parseFloat(putExposure.toFixed(2)),
      totalExposure: Number.parseFloat((callExposure + putExposure).toFixed(2)),
    }
  })

  // Generate profile data
  const priceLevels = Array.from({ length: 100 }, (_, i) => spotPrice * 0.7 + (i * (spotPrice * 0.6)) / 99)

  const exposureProfile = priceLevels.map((price) => {
    const normalized = (price - spotPrice) / spotPrice
    if (greek === "gamma") {
      return normalized * Math.exp(-0.5 * Math.pow(normalized / 0.1, 2)) * 10
    } else if (greek === "delta") {
      return Math.tanh(normalized / 0.05) * 5
    } else if (greek === "vanna") {
      return Math.sin(normalized / 0.08) * 3
    } else if (greek === "charm") {
      return Math.cos(normalized / 0.12) * 2
    }
    return 0
  })

  const profileData: ProfileData = {
    priceLevels,
    exposureProfile: exposureProfile.map((val) => Number.parseFloat((val + (Math.random() - 0.5) * 0.2).toFixed(2))),
  }

  // Calculate zero gamma crossing
  let zeroGamma: number | undefined
  for (let i = 0; i < exposureProfile.length - 1; i++) {
    if (exposureProfile[i] * exposureProfile[i + 1] < 0) {
      const x1 = priceLevels[i]
      const x2 = priceLevels[i + 1]
      const y1 = exposureProfile[i]
      const y2 = exposureProfile[i + 1]
      zeroGamma = x1 - (y1 * (x2 - x1)) / (y2 - y1)
      break
    }
  }

  return {
    ticker,
    greek,
    expiry,
    spotPrice,
    totalExposure: Number.parseFloat((strikeData.reduce((sum, data) => sum + data.totalExposure, 0) / 1000).toFixed(2)),
    zeroGamma: zeroGamma ? Number.parseFloat(zeroGamma.toFixed(2)) : undefined,
    strikeData,
    profileData,
    lastUpdated: new Date().toISOString(),
  }
}

export function generateMockFlowData(filters: {
  assetType: string
  tickerFilter: string
  premiumFilter: number | null
  quantityFilter: number | null
  volumeFilter: number | null
}): FlowData {
  const tickers = ASSET_TICKERS[filters.assetType as keyof typeof ASSET_TICKERS] || []
  const numFlows = 50

  let flows: OptionsFlow[] = Array.from({ length: numFlows }, (_, i) => {
    const ticker = tickers[Math.floor(Math.random() * tickers.length)]
    const spotPrice = SPOT_PRICES[ticker] || Math.random() * 200 + 50

    const now = new Date()
    const timestamp = new Date(now.getTime() - Math.random() * 2 * 60 * 60 * 1000) // Last 2 hours

    const strike = Number.parseFloat((spotPrice * (0.8 + Math.random() * 0.4)).toFixed(2))
    const price = Number.parseFloat((Math.random() * 20 + 1).toFixed(2))
    const quantity = Math.floor(Math.random() * 1000 + 10)
    const premium = price * quantity * 100
    const volume = Math.floor(Math.random() * 10000 + 100)
    const openInterest = Math.floor(Math.random() * 100000 + 1000)

    const expiryDate = new Date(now.getTime() + Math.random() * 60 * 24 * 60 * 60 * 1000) // Next 60 days
    const expiry = expiryDate.toISOString().split("T")[0]

    const side = Math.random() > 0.5 ? "BUY" : "SELL"

    return {
      timestamp: timestamp.toISOString(),
      ticker,
      strike,
      expiry,
      side,
      price,
      quantity,
      premium,
      volume,
      openInterest,
    }
  })

  // Apply filters
  if (filters.tickerFilter) {
    flows = flows.filter((flow) => flow.ticker.toLowerCase().includes(filters.tickerFilter.toLowerCase()))
  }

  if (filters.premiumFilter) {
    flows = flows.filter((flow) => flow.premium >= filters.premiumFilter!)
  }

  if (filters.quantityFilter) {
    flows = flows.filter((flow) => flow.quantity >= filters.quantityFilter!)
  }

  if (filters.volumeFilter) {
    flows = flows.filter((flow) => flow.volume >= filters.volumeFilter!)
  }

  // Sort by timestamp (newest first)
  flows.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())

  return {
    flows,
    lastUpdated: new Date().toISOString(),
  }
}
