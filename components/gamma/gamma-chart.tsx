"use client"

import { useEffect, useRef, useState } from "react"
import dynamic from 'next/dynamic'
import { Skeleton } from "@/components/ui/skeleton"
import type { GammaData } from "@/types/gamma"

// Dynamically import Plotly with no SSR
const Plot = dynamic(() => import('react-plotly.js'), {
  ssr: false,
  loading: () => <Skeleton className="h-[600px] w-full" />
})

interface GammaChartProps {
  data: GammaData | null
  chartType: string
  greekType: string
  loading: boolean
}

export function GammaChart({ data, chartType, greekType, loading }: GammaChartProps) {
  const plotRef = useRef<any>(null)
  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    setIsClient(true)
    // Resize chart on window resize
    const handleResize = () => {
      if (plotRef.current) {
        plotRef.current.resizeHandler()
      }
    }

    window.addEventListener("resize", handleResize)
    return () => window.removeEventListener("resize", handleResize)
  }, [])

  if (loading || !isClient) {
    return <Skeleton className="h-[600px] w-full" />
  }

  if (!data) {
    return <div className="h-[600px] flex items-center justify-center text-muted-foreground">No data available</div>
  }

  const getChartData = () => {
    const strikes = data.strikeData.map((d) => d.strike)
    const greekLabel = greekType.charAt(0).toUpperCase() + greekType.slice(1)

    switch (chartType) {
      case "absolute":
        return {
          data: [
            {
              x: strikes,
              y: data.strikeData.map((d) => d.totalExposure),
              type: "bar" as const,
              name: `${greekLabel} Exposure`,
              marker: { color: "rgba(31, 119, 180, 0.8)" },
              hovertemplate: "<b>Strike:</b> %{x}<br><b>Exposure:</b> $%{y:.2f}M<extra></extra>",
            },
          ],
          title: `Total ${greekLabel} Exposure: $${data.totalExposure.toFixed(2)}M`,
        }

      case "breakdown":
        return {
          data: [
            {
              x: strikes,
              y: data.strikeData.map((d) => d.callExposure),
              type: "bar" as const,
              name: `Call ${greekLabel}`,
              marker: { color: "rgba(44, 160, 44, 0.8)" },
              hovertemplate: "<b>Strike:</b> %{x}<br><b>Call Exposure:</b> $%{y:.2f}M<extra></extra>",
            },
            {
              x: strikes,
              y: data.strikeData.map((d) => d.putExposure),
              type: "bar" as const,
              name: `Put ${greekLabel}`,
              marker: { color: "rgba(214, 39, 40, 0.8)" },
              hovertemplate: "<b>Strike:</b> %{x}<br><b>Put Exposure:</b> $%{y:.2f}M<extra></extra>",
            },
          ],
          title: `Call/Put ${greekLabel} Breakdown: $${data.totalExposure.toFixed(2)}M`,
        }

      case "profile":
        return {
          data: [
            {
              x: data.profileData?.priceLevels || [],
              y: data.profileData?.exposureProfile || [],
              type: "scatter" as const,
              mode: "lines",
              name: `${greekLabel} Profile`,
              line: { color: "rgba(31, 119, 180, 1)", width: 2 },
              hovertemplate: "<b>Price:</b> %{x}<br><b>Exposure:</b> %{y:.2f}<extra></extra>",
            },
          ],
          title: `${greekLabel} Exposure Profile`,
        }

      default:
        return { data: [], title: "" }
    }
  }

  const { data: plotData, title } = getChartData()

  const layout = {
    title: {
      text: title,
      font: { size: 16 },
    },
    xaxis: {
      title: chartType === "profile" ? "Price Level" : "Strike Price",
      gridcolor: "rgba(128, 128, 128, 0.2)",
    },
    yaxis: {
      title: `${greekType.charAt(0).toUpperCase() + greekType.slice(1)} Exposure ($M)`,
      gridcolor: "rgba(128, 128, 128, 0.2)",
    },
    plot_bgcolor: "transparent",
    paper_bgcolor: "transparent",
    font: { color: "currentColor" },
    margin: { t: 60, r: 40, b: 60, l: 80 },
    barmode: chartType === "breakdown" ? "relative" : undefined,
    shapes: [
      // Spot price line
      {
        type: "line",
        x0: data.spotPrice,
        x1: data.spotPrice,
        y0: 0,
        y1: 1,
        yref: "paper",
        line: {
          color: "rgba(127, 127, 127, 0.8)",
          width: 1,
          dash: "dot",
        },
      },
      // Zero gamma line (if available)
      ...(data.zeroGamma
        ? [
            {
              type: "line" as const,
              x0: data.zeroGamma,
              x1: data.zeroGamma,
              y0: 0,
              y1: 1,
              yref: "paper" as const,
              line: {
                color: "rgba(255, 127, 14, 0.8)",
                width: 1,
                dash: "dash",
              },
            },
          ]
        : []),
      // Zero line for profile chart
      ...(chartType === "profile"
        ? [
            {
              type: "line" as const,
              x0: 0,
              x1: 1,
              xref: "paper" as const,
              y0: 0,
              y1: 0,
              line: {
                color: "rgba(127, 127, 127, 0.5)",
                width: 1,
                dash: "dash",
              },
            },
          ]
        : []),
    ],
    annotations: [
      {
        x: data.spotPrice,
        y: 1,
        yref: "paper",
        text: `Spot: $${data.spotPrice.toFixed(2)}`,
        showarrow: false,
        yshift: 10,
        font: { size: 10 },
      },
      ...(data.zeroGamma
        ? [
            {
              x: data.zeroGamma,
              y: 1,
              yref: "paper" as const,
              text: `Zero Γ: $${data.zeroGamma.toFixed(2)}`,
              showarrow: false,
              yshift: 10,
              font: { size: 10 },
            },
          ]
        : []),
    ],
  }

  const config = {
    displayModeBar: true,
    scrollZoom: true,
    modeBarButtonsToRemove: ["autoScale2d", "lasso2d", "select2d"],
    responsive: true,
  }

  return (
    <div className="w-full h-[600px]">
      <Plot
        ref={plotRef}
        data={plotData}
        layout={layout}
        config={config}
        style={{ width: "100%", height: "100%" }}
        useResizeHandler={true}
      />
    </div>
  )
}
