"use client"

import { useState, useEffect, useCallback } from "react"
import type { FlowData } from "@/types/flow"
import { flowApi } from "@/lib/api/flow-api"

interface UseFlowDataProps {
  assetType: string
  tickerFilter: string
  premiumFilter: string
  quantityFilter: string
  volumeFilter: string
}

export function useFlowData({
  assetType,
  tickerFilter,
  premiumFilter,
  quantityFilter,
  volumeFilter,
}: UseFlowDataProps) {
  const [data, setData] = useState<FlowData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      const flowData = await flowApi.getFlowData({
        assetType,
        tickerFilter: tickerFilter || undefined,
        premiumFilter: premiumFilter === "all" ? undefined : Number.parseFloat(premiumFilter),
        quantityFilter: quantityFilter === "all" ? undefined : Number.parseInt(quantityFilter),
        volumeFilter: volumeFilter === "all" ? undefined : Number.parseInt(volumeFilter),
      })

      setData({
        flows: flowData.flows,
        lastUpdated: flowData.lastUpdated,
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred")
    } finally {
      setLoading(false)
    }
  }, [assetType, tickerFilter, premiumFilter, quantityFilter, volumeFilter])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return {
    data,
    loading,
    error,
    refetch: fetchData,
  }
}
