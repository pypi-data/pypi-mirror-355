"use client"

import { useState, useEffect } from "react"
import {useNavigate} from "react-router";
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ArrowLeft, CheckCircle, XCircle, Clock, AlertCircle, Info, AlertTriangle, AlertOctagon } from "lucide-react"
import { format } from "date-fns"
import MainLayout from "./main-layout"

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

interface DeviceRunDetailViewProps {
  flowRunId: string
  deviceRunId: string
}

export default function DeviceRunDetailView({ flowRunId, deviceRunId }: DeviceRunDetailViewProps) {
  const router = useNavigate()
  const [flowRun, setFlowRun] = useState<FlowRun | null>(null)
  const [deviceRun, setDeviceRun] = useState<DeviceRun | null>(null)
  const [device, setDevice] = useState<any>(null)

  // Load flowRun and device run data
  useEffect(() => {
    const loadData = () => {
      try {
        // Load flowRun
        const savedFlowRuns = localStorage.getItem("flowRuns")
        if (!savedFlowRuns) {
          router("/executions")
          return
        }

        const flowRuns: FlowRun[] = JSON.parse(savedFlowRuns)
        const foundFlowRun = flowRuns.find((flowRun) => flowRun.flowRunId === flowRunId)

        if (!foundFlowRun) {
          router("/executions")
          return
        }

        setFlowRun(foundFlowRun)

        // Find device run
        const foundDeviceRun = foundFlowRun.deviceRuns.find((run) => run.id.toString() === deviceRunId)
        if (!foundDeviceRun) {
          router(`/executions/${flowRunId}`)
          return
        }

        setDeviceRun(foundDeviceRun)

        // Load device details
        const savedDevices = localStorage.getItem("devices")
        if (savedDevices) {
          const devices = JSON.parse(savedDevices)
          const foundDevice = devices.find((d: any) => d.device_id === foundDeviceRun.deviceId)
          if (foundDevice) {
            setDevice(foundDevice)
          }
        }
      } catch (error) {
        console.log(error)
        router("/login")
      }
    }

    loadData()
  }, [flowRunId, deviceRunId, router])

  // Get status badge based on flowRun status
  const getStatusBadge = (status: string) => {
    switch (status) {
      case "queued":
        return <Badge className="bg-yellow-500">Queued</Badge>
      case "running":
        return <Badge className="bg-blue-500">Running</Badge>
      case "success":
        return <Badge className="bg-green-500">Success</Badge>
      case "failed":
        return <Badge className="bg-red-500">Failed</Badge>
      default:
        return <Badge className="bg-gray-500">Unknown</Badge>
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

  // Get log level icon
  const getLogLevelIcon = (level: string) => {
    switch (level) {
      case "info":
        return <Info className="h-4 w-4 text-blue-500" />
      case "warning":
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      case "error":
        return <AlertOctagon className="h-4 w-4 text-red-500" />
      default:
        return <Info className="h-4 w-4 text-gray-500" />
    }
  }

  if (!flowRun || !deviceRun) {
    return (
      <MainLayout>
        <div className="container mx-auto py-6">
          <p>Loading device run details...</p>
        </div>
      </MainLayout>
    )
  }

  return (
    <MainLayout>
      <div className="container mx-auto py-6 space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router(`/executions/${flowRunId}`)}>
            <ArrowLeft className="h-5 w-5" />
            <span className="sr-only">Back to flowRun</span>
          </Button>
          <div className="flex-1">
            <h1 className="text-2xl font-bold flex items-center gap-2">
              {getStatusIcon(deviceRun.state)}
              {deviceRun.deviceId}
              {getStatusBadge(deviceRun.state)}
            </h1>
            <p className="text-muted-foreground">
              {device ? `${device.host} (${device.device_type})` : deviceRun.deviceId}
            </p>
          </div>
        </div>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium">Device Run Logs</h2>
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1">
                  <Info className="h-4 w-4 text-blue-500" />
                  <span className="text-xs">Info</span>
                </div>
                <div className="flex items-center gap-1">
                  <AlertTriangle className="h-4 w-4 text-yellow-500" />
                  <span className="text-xs">Warning</span>
                </div>
                <div className="flex items-center gap-1">
                  <AlertOctagon className="h-4 w-4 text-red-500" />
                  <span className="text-xs">Error</span>
                </div>
              </div>
            </div>

            <div className="border rounded-md overflow-hidden">
              <div className="bg-muted p-2 text-xs font-mono">
                <div className="flex items-center justify-between">
                  <span>Device: {deviceRun.deviceId}</span>
                  <span>Started: {format(new Date(deviceRun.actualStartTime), "yyyy-MM-dd HH:mm:ss")}</span>
                </div>
              </div>
              <div className="p-4 max-h-[500px] overflow-y-auto font-mono text-sm">
                {deviceRun.logs.map((log, index) => (
                  <div
                    key={index}
                    className={`flex items-start gap-2 p-1 rounded ${
                      log.level === "error" ? "bg-red-50" : log.level === "warning" ? "bg-yellow-50" : ""
                    }`}
                  >
                    <div className="pt-0.5">{getLogLevelIcon(log.level)}</div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">
                          {/*{format(new Date(log.timestamp), "HH:mm:ss")}*/}
                        </span>
                        <span>{log.message}</span>
                      </div>
                    </div>
                  </div>
                ))}
                {deviceRun.state === "running" && (
                  <div className="flex items-center gap-2 p-1 animate-pulse">
                    <Clock className="h-4 w-4 text-blue-500" />
                    <span>FlowRun in progress...</span>
                  </div>
                )}
              </div>
              <div className="bg-muted p-2 text-xs font-mono">
                <div className="flex items-center justify-between">
                  <span>Status: {deviceRun.state.toUpperCase()}</span>
                  <span>
                    {deviceRun.endTime
                      ? `Ended: ${format(new Date(deviceRun.endTime), "yyyy-MM-dd HH:mm:ss")}`
                      : "Running..."}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  )
}
