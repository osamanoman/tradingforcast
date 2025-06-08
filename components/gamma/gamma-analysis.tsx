"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Download, RefreshCw } from "lucide-react"
import { GammaChart } from "./gamma-chart"
import { useGammaData } from "@/hooks/use-gamma-data"
import { gammaApi } from "@/lib/api/gamma-api"
import { SidebarTrigger } from "@/components/ui/sidebar"

const tickers = ["SPY", "QQQ", "IWM", "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA", "SPX"]

const greekTypes = [
  { value: "gamma", label: "Gamma" },
  { value: "delta", label: "Delta" },
  { value: "vanna", label: "Vanna" },
  { value: "charm", label: "Charm" },
]

// Get today's and tomorrow's dates for OPEX and 0DTE labels
const today = new Date()
const tomorrow = new Date(today)
tomorrow.setDate(today.getDate() + 1)

const formatDate = (date: Date) => {
  return `-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

const expiryTypes = [
  { value: "all", label: "All" },
  { value: "monthly", label: "Monthly" },
  { value: "opex", label: `OPEX${formatDate(today)}` },
  { value: "0dte", label: `0DTE${formatDate(tomorrow)}` },
]

const chartTypes = [
  { value: "absolute", label: "Absolute Exposure" },
  { value: "breakdown", label: "Call/Put Breakdown" },
  { value: "profile", label: "Exposure Profile" },
]

export function GammaAnalysis() {
  const [selectedTicker, setSelectedTicker] = useState("SPY")
  const [selectedGreek, setSelectedGreek] = useState("gamma")
  const [selectedExpiry, setSelectedExpiry] = useState("all")
  const [selectedChartType, setSelectedChartType] = useState("absolute")
  const [autoRefresh, setAutoRefresh] = useState(true)

  const { data, loading, error, refetch } = useGammaData({
    ticker: selectedTicker,
    greek: selectedGreek,
    expiry: selectedExpiry,
  })

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        refetch()
      }, 60000) // Refresh every minute
      return () => clearInterval(interval)
    }
  }, [autoRefresh, refetch])

  const handleExportData = async () => {
    if (!data) return

    try {
      const csvContent = data.strikeData
        .map((point) => `${point.strike},${point.callExposure},${point.putExposure},${point.totalExposure}`)
        .join("\n")

      const blob = new Blob([`Strike,Call Exposure,Put Exposure,Total Exposure\n${csvContent}`], { type: "text/csv" })
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `${selectedTicker}_${selectedGreek}_${selectedExpiry}_data.csv`
      a.click()
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error("Error exporting data:", error)
    }
  }

  const handleExportSignificantPoints = async () => {
    try {
      const sigPoints = await gammaApi.getSignificantPoints({
        ticker: selectedTicker,
        greek: selectedGreek,
        expiry: selectedExpiry,
      })

      const csvContent = sigPoints.points
        .map((point) => `${point.type},${point.price},${point.value},${point.description}`)
        .join("\n")

      const blob = new Blob([`Type,Price,Value,Description\n${csvContent}`], { type: "text/csv" })
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `${selectedTicker}_${selectedGreek}_${selectedExpiry}_significant_points.csv`
      a.click()
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error("Error exporting significant points:", error)
    }
  }

  return (
    <div className="flex flex-col space-y-6 p-6">
      <div className="flex items-center gap-4">
        <SidebarTrigger />
        <div>
          <h1 className="text-3xl font-bold">GAMMA Analysis</h1>
          <p className="text-muted-foreground">Options Greek Exposure Analysis</p>
        </div>
      </div>

      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle>Analysis Controls</CardTitle>
          <CardDescription>Configure your analysis parameters</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Symbol</label>
              <Select value={selectedTicker} onValueChange={setSelectedTicker}>
                <SelectTrigger>
                  <SelectValue placeholder="Select ticker" />
                </SelectTrigger>
                <SelectContent>
                  {tickers.map((ticker) => (
                    <SelectItem key={ticker} value={ticker}>
                      {ticker}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Greek</label>
              <Select value={selectedGreek} onValueChange={setSelectedGreek}>
                <SelectTrigger>
                  <SelectValue placeholder="Select Greek" />
                </SelectTrigger>
                <SelectContent>
                  {greekTypes.map((greek) => (
                    <SelectItem key={greek.value} value={greek.value}>
                      {greek.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Expiration</label>
              <div className="flex gap-1">
                {expiryTypes.map((expiry) => (
                  <Button
                    key={expiry.value}
                    variant={selectedExpiry === expiry.value ? "default" : "outline"}
                    size="sm"
                    onClick={() => setSelectedExpiry(expiry.value)}
                  >
                    {expiry.label}
                  </Button>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Chart Type</label>
              <Select value={selectedChartType} onValueChange={setSelectedChartType}>
                <SelectTrigger>
                  <SelectValue placeholder="Select chart type" />
                </SelectTrigger>
                <SelectContent>
                  {chartTypes.map((chart) => (
                    <SelectItem key={chart.value} value={chart.value}>
                      {chart.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex items-center justify-between pt-4 border-t">
            <div className="flex items-center gap-4">
              {data && (
                <>
                  <Badge variant="secondary">Spot: ${data.spotPrice.toFixed(2)}</Badge>
                  <Badge variant="secondary">Total Exposure: ${data.totalExposure.toFixed(2)}M</Badge>
                  {data.zeroGamma && <Badge variant="outline">Zero Γ: ${data.zeroGamma.toFixed(2)}</Badge>}
                </>
              )}
            </div>

            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => setAutoRefresh(!autoRefresh)}>
                <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? "animate-spin" : ""}`} />
                Auto Refresh
              </Button>
              <Button variant="outline" size="sm" onClick={handleExportData} disabled={!data}>
                <Download className="h-4 w-4 mr-2" />
                Export Data
              </Button>
              <Button variant="outline" size="sm" onClick={handleExportSignificantPoints} disabled={!data}>
                <Download className="h-4 w-4 mr-2" />
                Sig. Points
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Chart */}
      <Card>
        <CardContent className="pt-6">
          {error ? (
            <div className="text-center py-8 text-red-500">Error loading data: {error}</div>
          ) : (
            <GammaChart data={data} chartType={selectedChartType} greekType={selectedGreek} loading={loading} />
          )}
        </CardContent>
      </Card>
    </div>
  )
}
