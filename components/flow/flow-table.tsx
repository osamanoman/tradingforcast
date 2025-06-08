"use client"

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { type FlowData, type OptionsFlow } from "@/types/flow"
import { useMemo } from 'react';

interface FlowTableProps {
  data: FlowData | null
  loading: boolean
}

export function FlowTable({ data, loading }: FlowTableProps) {
  if (loading) {
    return <div>Loading flow data...</div>
  }

  if (!data || data.flows.length === 0) {
    return <div className="text-center py-8 text-muted-foreground">No flow data available.</div>
  }

  // Use useMemo to group flows by full timestamp (including seconds) and assign colors to timestamps with duplicates
  const datedFlowsInfo = useMemo(() => {
    // Using a map to count occurrences of each timestamp
    const timestampCounts = new Map<string, number>();
    // Map to store colors for timestamps that appear more than once
    const timestampColors = new Map<string, string>();
    const colors = ['text-blue-600', 'text-green-600', 'text-yellow-600', 'text-purple-600', 'text-pink-600', 'text-indigo-600', 'text-red-600', 'text-gray-600']; // Text colors
    let colorIndex = 0;

    data.flows.forEach(flow => {
      // Use the full timestamp string as the key
      const timestampString = new Date(flow.timestamp).toISOString().split('.')[0]; // Get YYYY-MM-DDTHH:MM:SS
      timestampCounts.set(timestampString, (timestampCounts.get(timestampString) || 0) + 1);
    });

    // Assign colors only to timestamps that appear more than once
    timestampCounts.forEach((count, timestampString) => {
        if (count > 1) {
            timestampColors.set(timestampString, colors[colorIndex % colors.length]);
            colorIndex++;
        }
    });

    // Return the map of colors keyed by timestamp string
    return timestampColors; // This map only contains colors for non-unique timestamps
  }, [data.flows]); // Recalculate only when data.flows changes

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Timestamp</TableHead>
          <TableHead>Ticker</TableHead>
          <TableHead>Strike</TableHead>
          <TableHead>Expiry</TableHead>
          <TableHead>Side</TableHead>
          <TableHead>Price</TableHead>
          <TableHead>Quantity</TableHead>
          <TableHead>Premium</TableHead>
          <TableHead>Volume</TableHead>
          <TableHead>Open Interest</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.flows.map((flow: OptionsFlow, index: number) => {
           // Get the timestamp string for the current flow
           const timestampString = new Date(flow.timestamp).toISOString().split('.')[0];
           // Get the assigned color for this timestamp, or undefined if not assigned (i.e., unique timestamp)
           const timestampCellColorClass = datedFlowsInfo.get(timestampString) || '';

           return (
             <TableRow key={index}>
               <TableCell className={timestampCellColorClass}>{new Date(flow.timestamp).toLocaleString()}</TableCell>
               <TableCell>{flow.ticker}</TableCell>
               <TableCell>
                 {flow.strike} <span className={flow.optionType === 'put' ? 'text-red-500' : flow.optionType === 'call' ? 'text-green-500' : ''}>({flow.optionType.toUpperCase()})</span>
               </TableCell>
               <TableCell>{flow.expiry}</TableCell>
               <TableCell className={flow.side === 'Bid' ? 'text-red-500' : flow.side === 'Ask' ? 'text-green-500' : ''}>
                 {flow.side}
               </TableCell>
               <TableCell>{flow.price}</TableCell>
               <TableCell>{flow.quantity}</TableCell>
               <TableCell>{flow.premium.toFixed(2)}</TableCell>
               <TableCell>{flow.volume}</TableCell>
               <TableCell>{flow.openInterest}</TableCell>
             </TableRow>
           )
        })}
      </TableBody>
    </Table>
  )
} 