export interface OptionsFlow {
  timestamp: string
  ticker: string
  strike: number
  expiry: string
  side: string
  price: number
  quantity: number
  premium: number
  volume: number
  openInterest: number
  optionType: 'call' | 'put'
}

export interface FlowData {
  flows: OptionsFlow[]
  lastUpdated: string
}
