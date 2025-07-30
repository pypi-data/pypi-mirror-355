"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Search, Clock, CheckCircle, AlertCircle } from "lucide-react"
import { formatDistanceToNow } from "date-fns"
import MainLayout from "./main-layout"
import {getToken} from "@/lib/auth";
import applyCaseMiddleware from "axios-case-converter";
import axios from "axios";
import {useNavigate} from "react-router";

// Define flowRun types
interface DeviceRun {
  id: number
  deviceId: string
  state: "queued" | "running" | "success" | "failed"
  logicalStartTime: string
  actualStartTime: string
  endTime: string | null
  createdAt: string
  logs: Array<{
    timestamp: string
    level: "info" | "warning" | "error"
    message: string
  }>
}

interface FlowRun {
  flowId: string
  version: string
  flowRunId: string
  description: string
  deviceSetId: string
  args: string | null
  run_type: "manual" | "schedule"
  state: "running" | "submitted" | "finished"
  startTime: string
  endTime: string | null
  createdAt: string
  deviceRuns: DeviceRun[]
}

export default function FlowRunsView() {
  const router = useNavigate()
  const [flowRuns, setFlowRuns] = useState<FlowRun[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const API_URL = "http://localhost:8000/api"
  const token = getToken()
  const client = applyCaseMiddleware(axios.create())

  // Load flowRuns from localStorage on component mount
  useEffect(() => {
    const loadFlowRuns = async () => {
      const { data } = await client.get(`${API_URL}/flow-runs`,
      {
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      })
      setFlowRuns(data)
      localStorage.setItem("flowRuns", JSON.stringify(data))
    }

    loadFlowRuns()
  }, [])

  // Filter flowRuns based on search query
  const filteredFlowRuns = flowRuns.filter(
    (flowRun) =>
      flowRun.flowId.toLowerCase().includes(searchQuery.toLowerCase()) ||
      flowRun.deviceSetId.toLowerCase().includes(searchQuery.toLowerCase()) ||
      flowRun.state.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  // Get status badge based on flowRun status
  const getStatusBadge = (status: string) => {
    console.log("status badge " + status)
    switch (status) {
      case "running":
        return <Badge className="bg-blue-500">Running</Badge>
      case "finished":
        return <Badge className="bg-green-500">Completed</Badge>
      case "submitted":
        return <Badge className="bg-yellow-500">Submitted</Badge>
      default:
        return <Badge className="bg-gray-500">Unknown</Badge>
    }
  }

  // Get status icon based on flowRun status
  const getStatusIcon = (status: string) => {
    switch (status) {
      case "running":
        return <Clock className="h-4 w-4 text-blue-500" />
      case "finished":
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case "submitted":
        return <Clock className="h-4 w-4 text-yellow-500" />
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />
    }
  }

  return (
    <MainLayout>
      <div className="container mx-auto py-6 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Workflow FlowRuns</h1>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search flowRuns..."
            className="pl-10"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Status</TableHead>
                  <TableHead>Workflow</TableHead>
                  <TableHead>Device Set</TableHead>
                  <TableHead>Started</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Devices</TableHead>
                  <TableHead className="w-[100px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredFlowRuns.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-4 text-muted-foreground">
                      No flowRuns found
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredFlowRuns.map((flowRun) => (
                    <TableRow
                      key={flowRun.flowRunId}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => router(`/executions/${flowRun.flowRunId}`)}
                    >
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(flowRun.state)}
                          {getStatusBadge(flowRun.state)}
                        </div>
                      </TableCell>
                      <TableCell className="font-medium">{flowRun.flowId}</TableCell>
                      <TableCell>{flowRun.deviceSetId}</TableCell>
                      <TableCell>{formatDistanceToNow(new Date(flowRun.startTime))} ago</TableCell>
                      <TableCell>
                        {flowRun.endTime
                          ? `${Math.round((new Date(flowRun.endTime).getTime() - new Date(flowRun.startTime).getTime()) / 1000 / 60)} min`
                          : "Running..."}
                      </TableCell>
                      <TableCell>
                        {flowRun.deviceRuns.length} device{flowRun.deviceRuns.length !== 1 ? "s" : ""}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            router(`/executions/${flowRun.flowRunId}`)
                          }}
                        >
                          View Details
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  )
}
