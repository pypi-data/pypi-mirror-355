"use client"

import { useState, useEffect } from "react"
import {useNavigate} from "react-router";
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { ArrowLeft, Trash2, Plus } from "lucide-react"
import MainLayout from "./main-layout"
import {getToken} from "@/lib/auth";
import applyCaseMiddleware from "axios-case-converter";
import axios from "axios";

// Define device and device set types
interface Device {
  deviceId: string
  ip: string
  deviceType: string
  groupId: string
}

interface DeviceSet {
  deviceSetId: string
  description: string
  devices: string[] // Array of device_ids
  groupId: string // Group this device set belongs to
}

interface DeviceSetDetailViewProps {
  deviceSetId: string
}

export default function DeviceSetDetailView({ deviceSetId }: DeviceSetDetailViewProps) {
  const router = useNavigate()
  const [deviceSet, setDeviceSet] = useState<DeviceSet | null>(null)
  const [devices, setDevices] = useState<Device[]>([])
  const [isAddingDevices, setIsAddingDevices] = useState(false)
  const [selectedDevices, setSelectedDevices] = useState<string[]>([])
  const API_URL = "http://localhost:8000/api"
  const token = getToken()
  const client = applyCaseMiddleware(axios.create())
  const storedUser = localStorage.getItem("user");
  const user = storedUser ? JSON.parse(storedUser) : null;

  // Load device set and devices data
  useEffect(() => {
    const loadData = async () => {
      const { data } = await client.get(`${API_URL}/device-sets/${deviceSetId}`,
      {
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      })
      setDeviceSet(data)
      setSelectedDevices(data.devices)
      const response = await client.get(`${API_URL}/devices`,
      {
        params: {groupId: data.groupId},
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      })
      setDevices(response.data)
    }

    loadData()
  }, [deviceSetId, router])

  // Add devices to the device set
  const addDevicesToSet = async () => {
    if (!deviceSet) return

    try {
      const savedDeviceSets = localStorage.getItem("device_sets")
      if (!savedDeviceSets) return

      await client.post(`${API_URL}/device-sets/${deviceSetId}/devices`,
        {devices: selectedDevices},
        {
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`,
          },
        })

      const deviceSets: DeviceSet[] = JSON.parse(savedDeviceSets)
      const updatedDeviceSets = deviceSets.map((set) =>
        set.deviceSetId === deviceSetId
          ? {
              ...set,
              devices: selectedDevices,
            }
          : set,
      )

      localStorage.setItem("device_sets", JSON.stringify(updatedDeviceSets))
      setDeviceSet({
        ...deviceSet,
        devices: selectedDevices,
      })
      setIsAddingDevices(false)
    } catch (error) {
      console.error("Error adding devices:", error)
    }
  }

  // Remove a device from the device set
  const removeDevice = async (deviceId: string) => {
    if (!deviceSet) return

    const updatedDevices = deviceSet.devices.filter((id) => id !== deviceId)
    const updatedDeviceSet = { ...deviceSet, devices: updatedDevices }

    await client.post(`${API_URL}/device-sets/${deviceSetId}/devices`,
        {devices: updatedDevices},
        {
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`,
          },
        })

    try {
      const savedDeviceSets = localStorage.getItem("device_sets")
      if (!savedDeviceSets) return

      const deviceSets: DeviceSet[] = JSON.parse(savedDeviceSets)
      const updatedDeviceSets = deviceSets.map((set) => (set.deviceSetId === deviceSetId ? updatedDeviceSet : set))

      localStorage.setItem("device_sets", JSON.stringify(updatedDeviceSets))
      setDeviceSet(updatedDeviceSet)
      setSelectedDevices(updatedDevices)
    } catch (error) {
      console.error("Error removing device:", error)
    }
  }

  // Toggle device selection in the add devices dialog
  const toggleDeviceSelection = (deviceId: string) => {
    setSelectedDevices((current) =>
      current.includes(deviceId) ? current.filter((id) => id !== deviceId) : [...current, deviceId],
    )
  }

  if (!deviceSet) {
    return (
      <MainLayout>
        <div className="container mx-auto py-6">
          <p>Loading device set details...</p>
        </div>
      </MainLayout>
    )
  }

  // Get device details for the current device set
  const deviceDetails = devices.filter((device) => deviceSet.devices.includes(device.deviceId))

  return (
    <MainLayout>
      <div className="container mx-auto py-6 space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router("/devices/sets")}>
            <ArrowLeft className="h-5 w-5" />
            <span className="sr-only">Back to device sets</span>
          </Button>
          <div className="flex-1">
              <div>
                <h1 className="text-2xl font-bold">{deviceSet.deviceSetId}</h1>
                <p className="text-muted-foreground">{deviceSet.description}</p>
              </div>
          </div>
        </div>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium">Devices ({deviceSet.devices.length})</h2>
              {(user.isSuperuser || user.role === "admin") && (<Dialog open={isAddingDevices} onOpenChange={setIsAddingDevices}>
                <DialogTrigger asChild>
                  <Button size="sm" className="flex items-center gap-2">
                    <Plus className="h-4 w-4" />
                    Add Devices
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Add Devices</DialogTitle>
                    <DialogDescription>Select devices to add to this device set.</DialogDescription>
                  </DialogHeader>
                  <div className="py-4">
                    <div className="border rounded-md p-2 max-h-60 overflow-y-auto">
                      {devices.length === 0 ? (
                        <p className="text-sm text-muted-foreground p-2">No devices available</p>
                      ) : (
                        <div className="space-y-2">
                          {devices.map((device) => (
                            <div key={device.deviceId} className="flex items-center space-x-2">
                              <input
                                type="checkbox"
                                id={`device-${device.deviceId}`}
                                checked={selectedDevices.includes(device.deviceId)}
                                onChange={() => toggleDeviceSelection(device.deviceId)}
                                className="rounded border-gray-300"
                              />
                              <label htmlFor={`device-${device.deviceId}`} className="text-sm flex-1">
                                {device.deviceId} ({device.ip})
                              </label>
                              <Badge variant="outline" className="text-xs">
                                {device.deviceType}
                              </Badge>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setIsAddingDevices(false)}>
                      Cancel
                    </Button>
                    <Button onClick={addDevicesToSet}>Save</Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>)}
            </div>

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Device ID</TableHead>
                  <TableHead>IP</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Group</TableHead>
                  <TableHead className="w-[100px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {deviceDetails.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-4 text-muted-foreground">
                      No devices in this set
                    </TableCell>
                  </TableRow>
                ) : (
                  deviceDetails.map((device) => (
                    <TableRow key={device.deviceId}>
                      <TableCell className="font-medium">{device.deviceId}</TableCell>
                      <TableCell>{device.ip}</TableCell>
                      <TableCell className="capitalize">{device.deviceType}</TableCell>
                      <TableCell>{device.groupId}</TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => removeDevice(device.deviceId)}
                          disabled={!user.isSuperuser && user.role === "operator"}
                        >
                          <Trash2 className="h-4 w-4" />
                          <span className="sr-only">Remove</span>
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
