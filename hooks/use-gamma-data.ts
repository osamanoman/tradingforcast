"use client"

import { useState, useEffect, useCallback } from "react"
import type { GammaData } from "@/types/gamma"
import { gammaApi } from "@/lib/api/gamma-api"

interface UseGammaDataProps {
  ticker: string
  greek: string
  expiry: string
}

export function useGammaData({ ticker, greek, expiry }: UseGammaDataProps) {
  const [data, setData] = useState<GammaData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      console.log("Fetching gamma data:", { ticker, greek, expiry })
      const gammaData = await gammaApi.getGammaData({ ticker, greek, expiry })
      console.log("Received gamma data:", gammaData)
      setData(gammaData)
    } catch (err) {
      console.error("Error fetching gamma data:", err)
      setError(err instanceof Error ? err.message : "An error occurred")
    } finally {
      setLoading(false)
    }
  }, [ticker, greek, expiry])

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
