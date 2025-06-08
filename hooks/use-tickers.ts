"use client"

import { useState, useEffect, useCallback } from "react"
import type { TickersResponse, TickerInfo } from "@/lib/api/flow-api"
import { flowApi } from "@/lib/api/flow-api"

export function useTickers(assetType: string) {
  const [data, setData] = useState<TickersResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchTickers = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const tickersData = await flowApi.getTickers(assetType)
      setData(tickersData)
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred")
    } finally {
      setLoading(false)
    }
  }, [assetType])

  useEffect(() => {
    fetchTickers()
  }, [fetchTickers])

  return {
    data,
    loading,
    error,
    refetch: fetchTickers,
  }
} 