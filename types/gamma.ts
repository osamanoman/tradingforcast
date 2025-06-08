export interface StrikeData {
  strike: number
  callExposure: number
  putExposure: number
  totalExposure: number
}

export interface ProfileData {
  priceLevels: number[]
  exposureProfile: number[]
}

export interface GammaData {
  ticker: string
  greek: string
  expiry: string
  spotPrice: number
  totalExposure: number
  zeroGamma?: number
  strikeData: StrikeData[]
  profileData?: ProfileData
  lastUpdated: string
}
