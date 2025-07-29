"use client"

import { useState, useEffect } from "react"
import {useNavigate} from "react-router";
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {Search, Plus, Server, Trash2, Users} from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import MainLayout from "./main-layout"
import {getToken} from "@/lib/auth";
import applyCaseMiddleware from "axios-case-converter";
import axios from "axios";
import {Select, SelectContent, SelectItem, SelectTrigger, SelectValue} from "@/components/ui/select";

// Define device and device set types
interface Device {
  deviceId: string
  host: string
  deviceType: string
  groupId: string
}

interface DeviceSet {
  deviceSetId: string
  description: string
  devices: string[] // Array of device_ids
  groupId?: string // Group this device set belongs to
}

interface Group {
  groupId: string
  description: string
  members: string[]
}

export default function DeviceSetsView() {
  const router = useNavigate()
  const [deviceSets, setDeviceSets] = useState<DeviceSet[]>([])
  const [devices, setDevices] = useState<Device[]>([])
  const [groups, setGroups] = useState<Group[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [isAddingDeviceSet, setIsAddingDeviceSet] = useState(false)
  const [selectedGroupId, setSelectedGroupId] = useState<string>("")
  const API_URL = "http://localhost:8000/api"
  const token = getToken()
  const client = applyCaseMiddleware(axios.create())

  // New device set form state
  const [newDeviceSet, setNewDeviceSet] = useState<Partial<DeviceSet>>({
    deviceSetId: "",
    description: "",
    devices: [],
    groupId: "",
  })

  // Load device sets and devices from localStorage on component mount
  useEffect(() => {
    const loadData = async () => {
      const fetchDeviceSets = async () => {
        const { data } = await client.get(`${API_URL}/device-sets`,
        {
          headers: {
            "Authorization": `Bearer ${token}`,
          },
        })
        setDeviceSets(data)
      }
      const fetchGroups = async () => {
        const { data } = await client.get(`${API_URL}/groups`,
          {
            headers: {
              "Authorization": `Bearer ${token}`,
            },
          })
        setGroups(data)
      }
      const fetchDevices = async () => {
        const { data } = await client.get(`${API_URL}/devices`,
        {
          headers: {
            "Authorization": `Bearer ${token}`,
          },
        })
        setDevices(data)
      }

      fetchGroups()
      fetchDeviceSets()
      fetchDevices()
    }

    loadData()
  }, [])

  // Filter device sets based on search query
  const filteredDeviceSets = deviceSets.filter(
    (deviceSet) =>
      deviceSet.deviceSetId.toLowerCase().includes(searchQuery.toLowerCase()) ||
      deviceSet.description.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  // Get devices that belong to the selected group
  const filteredDevices = devices.filter((device) => (selectedGroupId ? device.groupId === selectedGroupId : true))

  // Get group name by ID
  const getGroupName = (groupId?: string) => {
    console.log("Get group name:" + groupId)
    if (!groupId) return "No Group"
    const group = groups.find((g) => g.groupId === groupId)
    return group ? group.groupId : "Unknown Group"
  }

  // Handle group selection
  const handleGroupChange = (groupId: string) => {
    setSelectedGroupId(groupId)
    setNewDeviceSet({
      ...newDeviceSet,
      groupId: groupId,
      devices: [], // Reset selected devices when group changes
    })
  }

  // Add a new device set
  const addDeviceSet = async () => {
    if (!newDeviceSet.deviceSetId) return
    console.log(newDeviceSet)
    const { data } = await client.post(`${API_URL}/device-sets`,
      newDeviceSet,
      {
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      })

    const updatedDeviceSets = [...deviceSets, data]
    setDeviceSets(updatedDeviceSets)
    localStorage.setItem("device_sets", JSON.stringify(updatedDeviceSets))

    // Reset form
    setNewDeviceSet({
      deviceSetId: "",
      description: "",
      devices: [],
      groupId: "",
    })
    setSelectedGroupId("")
    setIsAddingDeviceSet(false)
  }

  // Delete a device set
  const deleteDeviceSet = (deviceSetId: string) => {
    const updatedDeviceSets = deviceSets.filter((deviceSet) => deviceSet.deviceSetId !== deviceSetId)
    setDeviceSets(updatedDeviceSets)
    localStorage.setItem("device_sets", JSON.stringify(updatedDeviceSets))
  }

  // Toggle device selection in new device set form
  const toggleDeviceSelection = (deviceId: string) => {
    const currentDevices = newDeviceSet.devices || []
    const updatedDevices = currentDevices.includes(deviceId)
      ? currentDevices.filter((id) => id !== deviceId)
      : [...currentDevices, deviceId]

    setNewDeviceSet({ ...newDeviceSet, devices: updatedDevices })
  }

  // Reset form when dialog closes
  const handleDialogOpenChange = (open: boolean) => {
    if (!open) {
      setNewDeviceSet({
        description: "",
        devices: [],
        groupId: "",
      })
      setSelectedGroupId("")
    }
    setIsAddingDeviceSet(open)
  }

  return (
    <MainLayout>
      <div className="container mx-auto py-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Device Sets</h1>
            <p className="text-muted-foreground">Manage groups of devices for workflow execution</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => router("/devices")} className="flex items-center gap-2">
              <Server className="h-4 w-4" />
              Devices
            </Button>
            <Dialog open={isAddingDeviceSet} onOpenChange={handleDialogOpenChange}>
              <DialogTrigger asChild>
                <Button className="flex items-center gap-2">
                  <Plus className="h-4 w-4" />
                  Create Device Set
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md">
                <DialogHeader>
                  <DialogTitle>Create Device Set</DialogTitle>
                  <DialogDescription>Group devices together for workflow execution.</DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label htmlFor="set-name">Device Set ID</Label>
                    <Input
                      id="set-name"
                      value={newDeviceSet.deviceSetId}
                      onChange={(e) => setNewDeviceSet({ ...newDeviceSet, deviceSetId: e.target.value })}
                      placeholder="e.g., Production Servers"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="set-description">Description</Label>
                    <Textarea
                      id="set-description"
                      value={newDeviceSet.description}
                      onChange={(e) => setNewDeviceSet({ ...newDeviceSet, description: e.target.value })}
                      placeholder="Describe this device set"
                      rows={2}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="group">Group</Label>
                    <Select value={selectedGroupId} onValueChange={handleGroupChange}>
                      <SelectTrigger id="group">
                        <SelectValue placeholder="Select a group" />
                      </SelectTrigger>
                      <SelectContent>
                        {groups.length === 0 ? (
                          <SelectItem value="no-groups" disabled>
                            No groups available
                          </SelectItem>
                        ) : (
                          groups.map((group) => (
                            <SelectItem key={group.groupId} value={group.groupId}>
                              {group.groupId}
                            </SelectItem>
                          ))
                        )}
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground mt-1">
                      Select a group to see available devices from that group
                    </p>
                  </div>
                  {selectedGroupId && (
                    <div className="space-y-2">
                      <Label>Select Devices</Label>
                      <div className="border rounded-md p-2 max-h-60 overflow-y-auto">
                        {filteredDevices.length === 0 ? (
                          <p className="text-sm text-muted-foreground p-2">No devices available in this group</p>
                        ) : (
                          <div className="space-y-2">
                            {filteredDevices.map((device) => (
                              <div key={device.deviceId} className="flex items-center space-x-2">
                                <input
                                  type="checkbox"
                                  id={`device-${device.deviceId}`}
                                  checked={(newDeviceSet.devices || []).includes(device.deviceId)}
                                  onChange={() => toggleDeviceSelection(device.deviceId)}
                                  className="rounded border-gray-300"
                                />
                                <label htmlFor={`device-${device.deviceId}`} className="text-sm flex-1">
                                  {device.deviceId} ({device.host})
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
                  )}
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsAddingDeviceSet(false)}>
                    Cancel
                  </Button>
                  <Button
                    onClick={addDeviceSet}
                    disabled={!newDeviceSet.deviceSetId || !selectedGroupId || (newDeviceSet.devices || []).length === 0}
                  >
                    Create
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search device sets..."
            className="pl-10"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredDeviceSets.map((deviceSet) => (
            <Card key={deviceSet.deviceSetId} className="overflow-hidden">
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                  <CardTitle className="text-lg">{deviceSet.deviceSetId}</CardTitle>

                  <Button variant="ghost" size="sm" onClick={() => deleteDeviceSet(deviceSet.deviceSetId)}>
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="pb-2">
                <p className="text-sm text-muted-foreground mb-4">{deviceSet.description}</p>
                <div className="flex items-center justify-between">
                  {/* <div className="flex items-center gap-1 text-sm">

                  </div> */}
                  <div className="flex items-center gap-1 text-sm">
                    <Users className="h-4 w-4 text-muted-foreground" />
                    <Badge variant="outline" className="text-xs">
                      {getGroupName(deviceSet.groupId)}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-1 text-sm">
                    <Server className="h-4 w-4 text-muted-foreground" />
                    <span>{deviceSet.devices.length} {deviceSet.devices.length == 1 ? "device" : "devices"}</span>
                  </div>
                </div>
              </CardContent>
              <CardFooter className="pt-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full"
                  onClick={() => router(`/devices/sets/${deviceSet.deviceSetId}`)}
                >
                  View Details
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>

        {filteredDeviceSets.length === 0 && (
          <div className="text-center py-12">
            <p className="text-muted-foreground">No device sets found</p>
            {searchQuery && (
              <Button variant="link" onClick={() => setSearchQuery("")} className="mt-2">
                Clear search
              </Button>
            )}
          </div>
        )}
      </div>
    </MainLayout>
  )
}
