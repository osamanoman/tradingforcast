"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { RefreshCw, Filter } from "lucide-react"
import { FlowTable } from "./flow-table"
import { useFlowData } from "@/hooks/use-flow-data"
import { useTickers } from "@/hooks/use-tickers"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { type TickerInfo } from "@/lib/api/flow-api"

const assetTypes = [
  { value: "indices", label: "Indices" },
  { value: "etfs", label: "ETFs" },
  { value: "stocks", label: "Stocks" },
]

const premiumFilters = [
  { value: "all", label: "All" },
  { value: "10000", label: "> $10K" },
  { value: "50000", label: "> $50K" },
  { value: "100000", label: "> $100K" },
  { value: "500000", label: "> $500K" },
  { value: "1000000", label: "> $1M" },
]

const quantityFilters = [
  { value: "all", label: "All" },
  { value: "100", label: "> 100" },
  { value: "500", label: "> 500" },
  { value: "1000", label: "> 1000" },
]

const volumeFilters = [
  { value: "all", label: "All" },
  { value: "100", label: "> 100" },
  { value: "500", label: "> 500" },
  { value: "1000", label: "> 1000" },
  { value: "5000", label: "> 5000" },
]

export function FlowAnalysis() {
  const [assetType, setAssetType] = useState("indices")
  const [tickerFilter, setTickerFilter] = useState("all")
  const [premiumFilter, setPremiumFilter] = useState("all")
  const [quantityFilter, setQuantityFilter] = useState("all")
  const [volumeFilter, setVolumeFilter] = useState("all")
  const [autoRefresh, setAutoRefresh] = useState(true)

  const { data: tickersData } = useTickers(assetType)

  const { data, loading, error, refetch } = useFlowData({
    assetType,
    tickerFilter: tickerFilter === "all" ? "" : tickerFilter,
    premiumFilter,
    quantityFilter,
    volumeFilter,
  })

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        refetch()
      }, 30000) // Refresh every 30 seconds
      return () => clearInterval(interval)
    }
  }, [autoRefresh, refetch])

  // Reset ticker filter when asset type changes
  useEffect(() => {
    setTickerFilter("all")
  }, [assetType])

  const totalPremium = data?.flows.reduce((sum, flow) => sum + flow.premium, 0) || 0
  const buyFlows = data?.flows.filter((flow) => flow.side.toLowerCase().includes("buy")).length || 0
  const sellFlows = data?.flows.filter((flow) => flow.side.toLowerCase().includes("sell")).length || 0

  return (
    <div className="flex flex-col space-y-6 p-6">
      <div className="flex items-center gap-4">
        <SidebarTrigger />
        <div>
          <h1 className="text-3xl font-bold">Options Flow</h1>
          <p className="text-muted-foreground">Real-time options flow analysis</p>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Flow Filters
          </CardTitle>
          <CardDescription>Filter options flow data by various parameters</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Asset Type</label>
              <Select value={assetType} onValueChange={setAssetType}>
                <SelectTrigger>
                  <SelectValue placeholder="Select asset type" />
                </SelectTrigger>
                <SelectContent>
                  {assetTypes.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Ticker</label>
              <Select value={tickerFilter} onValueChange={setTickerFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Select ticker" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  {tickersData?.tickers.map((ticker: TickerInfo) => (
                    <SelectItem key={ticker.symbol} value={ticker.symbol}>
                      {ticker.symbol}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Premium</label>
              <Select value={premiumFilter} onValueChange={setPremiumFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Select premium filter" />
                </SelectTrigger>
                <SelectContent>
                  {premiumFilters.map((filter) => (
                    <SelectItem key={filter.value} value={filter.value}>
                      {filter.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Quantity</label>
              <Select value={quantityFilter} onValueChange={setQuantityFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Select quantity filter" />
                </SelectTrigger>
                <SelectContent>
                  {quantityFilters.map((filter) => (
                    <SelectItem key={filter.value} value={filter.value}>
                      {filter.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Volume</label>
              <Select value={volumeFilter} onValueChange={setVolumeFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Select volume filter" />
                </SelectTrigger>
                <SelectContent>
                  {volumeFilters.map((filter) => (
                    <SelectItem key={filter.value} value={filter.value}>
                      {filter.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex items-center justify-between pt-4 border-t">
            <div className="flex items-center gap-4">
              <Badge variant="secondary">Total Premium: ${(totalPremium / 1000000).toFixed(2)}M</Badge>
              <Badge variant="outline" className="text-green-500">
                Buy Orders: {buyFlows}
              </Badge>
              <Badge variant="outline" className="text-red-500">
                Sell Orders: {sellFlows}
              </Badge>
            </div>

            <Button variant="outline" size="sm" onClick={() => setAutoRefresh(!autoRefresh)}>
              <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? "animate-spin" : ""}`} />
              Auto Refresh
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Flow Table */}
      <Card>
        <CardHeader>
          <CardTitle>Live Options Flow</CardTitle>
          <CardDescription>Real-time options transactions with filtering and analysis</CardDescription>
        </CardHeader>
        <CardContent>
          {error ? (
            <div className="text-center py-8 text-red-500">Error loading flow data: {error}</div>
          ) : (
            <FlowTable data={data} loading={loading} />
          )}
        </CardContent>
      </Card>
    </div>
  )
}
