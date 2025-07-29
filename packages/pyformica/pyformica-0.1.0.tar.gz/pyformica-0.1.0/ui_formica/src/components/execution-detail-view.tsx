"use client"

import { useState, useEffect } from "react"
import {useNavigate} from "react-router";
import {Badge} from "./ui/badge";
import {AlertCircle, ArrowLeft, CheckCircle, Clock, XCircle} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import MainLayout from "@/components/main-layout.tsx";
import {Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import {Table, TableBody, TableCell, TableHead, TableHeader, TableRow} from "@/components/ui/table.tsx";
import { Button } from "./ui/button";

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

interface FlowRunDetailViewProps {
  flowRunId: string
}

export default function ExecutionDetailView({ flowRunId }: FlowRunDetailViewProps) {
  const router = useNavigate()
  const [flowRun, setFlowRun] = useState<FlowRun | null>(null)
  const [devices, setDevices] = useState<Record<string, any>>({})

  // Load flowRun data
  useEffect(() => {
    const loadFlowRun = () => {
      try {
        const savedFlowRuns = localStorage.getItem("flowRuns")
        if (!savedFlowRuns) {
          router("/executions")
          return
        }

        const flowRuns: FlowRun[] = JSON.parse(savedFlowRuns)
        const foundFlowRun = flowRuns.find((flowRun) => flowRun.flowRunId === flowRunId)

        if (foundFlowRun) {
          setFlowRun(foundFlowRun)
        } else {
          router("/executions")
        }
      } catch (error) {
        console.error("Error loading flowRun:", error)
        router("/executions")
      }
    }

    const loadDevices = () => {
      try {
        const savedDevices = localStorage.getItem("devices")
        if (savedDevices) {
          const deviceList = JSON.parse(savedDevices)
          const deviceMap: Record<string, any> = {}
          deviceList.forEach((device: any) => {
            deviceMap[device.device_id] = device
          })
          setDevices(deviceMap)
        }
      } catch (error) {
        console.error("Error loading devices:", error)
      }
    }

    loadFlowRun()
    loadDevices()
  }, [flowRunId, router])

  // Get status badge based on flowRun status
  const getStatusBadge = (status: string) => {
    switch (status) {
      case "queued":
        return <Badge className="bg-yellow-500">Queued</Badge>
      case "running":
        return <Badge className="bg-blue-500">Running</Badge>
      case "success":
        return <Badge className="bg-green-500">Completed</Badge>
      case "failed":
        return <Badge className="bg-red-500">Failed</Badge>
      default:
        return <Badge className="bg-gray-500">Unknown</Badge>
    }
  }

  // Get status badge based on flowRun status
  const getStatusBadgeFlowRun = (status: string) => {
    switch (status) {
      case "submitted":
        return <Badge className="bg-yellow-500">Submitted</Badge>
      case "running":
        return <Badge className="bg-blue-500">Running</Badge>
      case "finished":
        return <Badge className="bg-green-500">Finished</Badge>
      default:
        return <Badge className="bg-gray-500">Unknown</Badge>
    }
  }

  // Get status icon based on flowRun status
  const getStatusIconFlowRun = (status: string) => {
    console.log("status icon " + status)
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

  // Get status icon based on flowRun status
  const getStatusIcon = (status: string) => {
    switch (status) {
      case "queued":
        return <Clock className="h-4 w-4 text-yellow-500" />
      case "running":
        return <Clock className="h-4 w-4 text-blue-500" />
      case "success":
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case "failed":
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />
    }
  }

  if (!flowRun) {
    return (
      <MainLayout>
        <div className="container mx-auto py-6">
          <p>Loading flowRun details...</p>
        </div>
      </MainLayout>
    )
  }

  return (
    <MainLayout>
      <div className="container mx-auto py-6 space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router("/executions")}>
            <ArrowLeft className="h-5 w-5" />
            <span className="sr-only">Back to flowRuns</span>
          </Button>
          <div className="flex-1">
            <h1 className="text-2xl font-bold flex items-center gap-2">
              {getStatusIconFlowRun(flowRun.state)}
              {flowRun.flowId}
              {getStatusBadgeFlowRun(flowRun.state)}
            </h1>
            <p className="text-muted-foreground">
              FlowRun started {formatDistanceToNow(new Date(flowRun.startTime))} ago
              {flowRun.endTime &&
                ` and took ${Math.round((new Date(flowRun.endTime).getTime() - new Date(flowRun.startTime).getTime()) / 1000 / 60)} minutes`}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Workflow</CardTitle>
            </CardHeader>
            <CardContent>
              <p>{flowRun.flowId}</p>
              <p className="text-xs text-muted-foreground">ID: {flowRun.flowId}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Device Set</CardTitle>
            </CardHeader>
            <CardContent>
              <p>{flowRun.deviceSetId}</p>
              <p className="text-xs text-muted-foreground">ID: {flowRun.deviceSetId}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                {getStatusIconFlowRun(flowRun.state)}
                <span>{flowRun.state.charAt(0).toUpperCase() + flowRun.state.slice(1)}</span>
              </div>
              <p className="text-xs text-muted-foreground">
                {flowRun.deviceRuns.filter((run) => run.state === "queued").length} queued,{" "}
                {flowRun.deviceRuns.filter((run) => run.state === "success").length} success,{" "}
                {flowRun.deviceRuns.filter((run) => run.state === "running").length} running,{" "}
                {flowRun.deviceRuns.filter((run) => run.state === "failed").length} failed
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Parameters</CardTitle>
            </CardHeader>
            <CardContent>
              {flowRun.args && Object.keys(flowRun.args).length > 0 ? (
                <div className="space-y-1">
                  {Object.entries(flowRun.args).map(([key, value]) => (
                    <div key={key} className="flex justify-between text-sm">
                      <span className="font-medium">{key}:</span>
                      <span className="text-muted-foreground">
                        {typeof value === "boolean" ? (value ? "Yes" : "No") : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-muted-foreground">No parameters used</p>
              )}
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Device Runs</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {flowRun.deviceRuns.length === 0 ? "No device runs found" : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Status</TableHead>
                  <TableHead>Device</TableHead>
                  <TableHead>Host</TableHead>
                  <TableHead>Started</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead className="w-[100px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {flowRun.deviceRuns.map((deviceRun) => (
                  <TableRow
                    key={deviceRun.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => router(`/executions/${flowRun?.flowRunId}/${deviceRun.id}`)}
                  >
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(deviceRun.state)}
                        {getStatusBadge(deviceRun.state)}
                      </div>
                    </TableCell>
                    <TableCell className="font-medium">{deviceRun.deviceId}</TableCell>
                    <TableCell>{devices[deviceRun.deviceId]?.host || "Unknown"}</TableCell>
                    <TableCell>{formatDistanceToNow(new Date(deviceRun.actualStartTime))} ago</TableCell>
                    <TableCell>
                      {deviceRun.endTime
                        ? `${Math.round((new Date(deviceRun.endTime).getTime() - new Date(deviceRun.actualStartTime).getTime()) / 1000 / 60)} min`
                        : "Running..."}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          router(`/executions/${flowRun?.flowRunId}/${deviceRun.id}`)
                        }}
                      >
                        View Logs
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>)}
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  )
}
