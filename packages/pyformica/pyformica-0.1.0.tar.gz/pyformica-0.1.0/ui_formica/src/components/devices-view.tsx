"use client"

import { useState, useEffect } from "react"
import {useNavigate} from "react-router";
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent } from "@/components/ui/card"
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { DropdownMenu } from "@/components/ui/dropdown-menu"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Search, Plus, Trash2, Server, Key } from "lucide-react"
import MainLayout from "./main-layout"
import {getToken} from "@/lib/auth";
import applyCaseMiddleware from "axios-case-converter";
import axios from "axios";

// Define device and credential types
interface Device {
  deviceId: string
  ip: string
  deviceType: string
  groupId: string
}

interface Credential {
  id: number
  deviceId: string
  connectionType: string
  description: string
  username: string
  password: string
  port: number
  priority: number
  extra: Record<string, any>
}

interface CreateCredential {
  deviceId: string
  connectionType: string
  description: string
  username: string
  password: string
  port: number
  priority: number
  extra: Record<string, any>
}

export default function DevicesView() {
  const router = useNavigate()
  const [devices, setDevices] = useState<Device[]>([])
  const [credentials, setCredentials] = useState<Credential[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [isAddingDevice, setIsAddingDevice] = useState(false)
  const [isAddingCredential, setIsAddingCredential] = useState(false)
  // const [isUploadingFile, setIsUploadingFile] = useState(false)
  // const [, setFileContent] = useState("")
  const [groups, setGroups] = useState<string[]>([])
  const API_URL = "http://localhost:8000/api"
  const token = getToken()
  const client = applyCaseMiddleware(axios.create())

  // New device form state
  const [newDevice, setNewDevice] = useState<Partial<Device>>({
    deviceId: "",
    ip: "",
    deviceType: "router",
    groupId: "",
  })

  // New credential form state
  const [newCredential, setNewCredential] = useState<Partial<Credential>>({
    deviceId: "",
    connectionType: "ssh",
    description: "",
    username: "",
    password: "",
    port: 22,
    priority: 1,
    extra: {},
  })

  // Load devices and credentials from localStorage on component mount
  useEffect(() => {
    const fetchDevices = async () => {
      const { data } = await client.get(`${API_URL}/devices`,
      {
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      })
      setDevices(data)
    }
    const fetchCredentials = async () => {
      const { data } = await client.get(`${API_URL}/credentials`,
      {
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      })
      setCredentials(data)
    }

    fetchDevices()
    fetchCredentials()

    const loadData = () => {
      try {
        // Load devices

        // Load groups from localStorage
        const fetchGroups = async () => {
          const { data } = await client.get(`${API_URL}/groups`,
          {
            headers: {
              "Authorization": `Bearer ${token}`,
            },
          })
          setGroups(data.map((g: { groupId: string }) => g.groupId))
        }

        fetchGroups()
      } catch (error) {
        console.error("Error loading data:", error)
      }
    }

    loadData()
  }, [])

  console.log(devices)

  // Filter devices based on search query
  const filteredDevices = devices.filter(
    (device) =>
      device.deviceId.toLowerCase().includes(searchQuery.toLowerCase()) ||
      device.ip.toLowerCase().includes(searchQuery.toLowerCase()) ||
      device.deviceType.toLowerCase().includes(searchQuery.toLowerCase()) ||
      device.groupId.toLowerCase().includes(searchQuery.toLowerCase()),
  )
  console.log("filter:")
  console.log(filteredDevices)

  // Filter credentials based on search query
  const filteredCredentials = credentials.filter(
    (credential) =>
      credential.deviceId.toLowerCase().includes(searchQuery.toLowerCase()) ||
      credential.connectionType.toLowerCase().includes(searchQuery.toLowerCase()) ||
      credential.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      credential.username.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  // Add a new device
  const addDevice = async () => {
    if (!newDevice.deviceId || !newDevice.ip) return

    const device: Device = {
      deviceId: newDevice.deviceId,
      ip: newDevice.ip,
      deviceType: newDevice.deviceType || "linux",
      groupId: newDevice.groupId || "default",
    }

    console.log(device)

    const { data } = await client.post(`${API_URL}/devices`,
      device,
      {
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      })

    // const API_URL = "http://localhost:8000/api"
    // const response = await fetch(`${API_URL}/device`, {
    //   method: "POST",
    //   headers: {
    //     "Content-Type": "application/json",
    //   },
    //   body: JSON.stringify(device),
    // })
    // const new_device: Device = await response.json()
    // console.log(new_device)

    const updatedDevices = [...devices, data]
    setDevices(updatedDevices)
    localStorage.setItem("devices", JSON.stringify(updatedDevices))

    // Reset form
    setNewDevice({
      deviceId: "",
      ip: "",
      deviceType: "router",
      // group: "",
    })
    setIsAddingDevice(false)
  }

  // Add a new credential
  const addCredential = async () => {

    if (!newCredential.deviceId || !newCredential.username || !newCredential.password) return

    const createCredential: CreateCredential = {
      deviceId: newCredential.deviceId,
      connectionType: newCredential.connectionType || "ssh",
      description: newCredential.description || "",
      username: newCredential.username,
      password: newCredential.password,
      port: newCredential.port || 22,
      priority: newCredential.priority || 1,
      extra: newCredential.extra || {},
    }

    const { data } = await client.post(`${API_URL}/credentials`,
      createCredential,
      {
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
      })

    const updatedCredentials = [...credentials, data]
    setCredentials(updatedCredentials)
    localStorage.setItem("credentials", JSON.stringify(updatedCredentials))

    // Reset form
    setNewCredential({
      deviceId: "",
      connectionType: "ssh",
      description: "",
      username: "",
      password: "",
      port: 22,
      priority: 1,
      extra: {},
    })
    setIsAddingCredential(false)
  }

  // Delete a device
  const deleteDevice = async (groupId: string, deviceId: string) => {
    console.log("device_id" + deviceId)
    await client.delete(
      `${API_URL}/devices/${groupId}/${deviceId}`,
      {
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
      })

    const updatedDevices = devices.filter((device) => device.deviceId !== deviceId)
    setDevices(updatedDevices)
    localStorage.setItem("devices", JSON.stringify(updatedDevices))

    // Also delete associated credentials
    const updatedCredentials = credentials.filter(
      (credential) => !devices.find((d) => d.deviceId === deviceId && d.deviceId === credential.deviceId),
    )
    setCredentials(updatedCredentials)
    localStorage.setItem("credentials", JSON.stringify(updatedCredentials))
  }

  // Delete a credential
  const deleteCredential = async (credential_id: number) => {
    console.log("Deleting")
    await client.delete(
      `${API_URL}/credentials/${credential_id}`,
      {
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
      })
    const updatedCredentials = credentials.filter((credential) => credential.id !== credential_id)
    setCredentials(updatedCredentials)
    localStorage.setItem("credentials", JSON.stringify(updatedCredentials))
  }

  return (
    <MainLayout>
      <div className="container mx-auto py-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Devices & Credentials</h1>
            <p className="text-muted-foreground">Manage your network devices and access credentials</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => router("/devices/sets")} className="flex items-center gap-2">
              <Server className="h-4 w-4" />
              Device Sets
            </Button>
          </div>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search devices and credentials..."
            className="pl-10"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <Tabs defaultValue="devices">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="devices" className="flex items-center gap-2">
              <Server className="h-4 w-4" />
              Devices
            </TabsTrigger>
            <TabsTrigger value="credentials" className="flex items-center gap-2">
              <Key className="h-4 w-4" />
              Credentials
            </TabsTrigger>
          </TabsList>

          <TabsContent value="devices" className="space-y-4 pt-4">
            <div className="flex justify-end">
              <Dialog open={isAddingDevice} onOpenChange={setIsAddingDevice}>
                <DialogTrigger asChild>
                  <Button className="flex items-center gap-2">
                    <Plus className="h-4 w-4" />
                    Add Device
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Add New Device</DialogTitle>
                    <DialogDescription>Enter the details for the new device.</DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label htmlFor="device-id">Device ID</Label>
                      <Input
                        id="device-id"
                        value={newDevice.deviceId}
                        onChange={(e) => setNewDevice({ ...newDevice, deviceId: e.target.value })}
                        placeholder="e.g., router-01"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="ip">IP</Label>
                      <Input
                        id="ip"
                        value={newDevice.ip}
                        onChange={(e) => setNewDevice({ ...newDevice, ip: e.target.value })}
                        placeholder="e.g., 192.168.1.1"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="device-type">Device Type</Label>
                      <Select
                        value={newDevice.deviceType}
                        onValueChange={(value) => setNewDevice({ ...newDevice, deviceType: value })}
                      >
                        <SelectTrigger id="device-type">
                          <SelectValue placeholder="Select device type" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="linux">Linux</SelectItem>
                          <SelectItem value="huawei">Huawei</SelectItem>
                          <SelectItem value="juniper">Juniper</SelectItem>
                          <SelectItem value="gcom">GCOM</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="group">Group</Label>
                      <Select
                        value={newDevice.groupId}
                        onValueChange={(value) => setNewDevice({ ...newDevice, groupId: value })}
                      >
                        <SelectTrigger id="group">
                          <SelectValue placeholder="Select group" />
                        </SelectTrigger>
                        <SelectContent>
                          {groups.map((group) => (
                            <SelectItem key={group} value={group}>
                              {group}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setIsAddingDevice(false)}>
                      Cancel
                    </Button>
                    <Button onClick={addDevice}>Add Device</Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>

            <Card>
              <CardContent className="p-0">
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
                    {filteredDevices.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center py-4 text-muted-foreground">
                          No devices found
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredDevices.map((device) => (
                        <TableRow key={device.deviceId}>
                          <TableCell className="font-medium">{device.deviceId}</TableCell>
                          <TableCell>{device.ip}</TableCell>
                          <TableCell className="capitalize">{device.deviceType}</TableCell>
                          <TableCell>{device.groupId}</TableCell>
                          <TableCell>
                            <DropdownMenu>
                              <Button variant="ghost" size="sm" onClick={() => deleteDevice(device.groupId, device.deviceId)}>
                                <Trash2 className="h-4 w-4 text-red-500" />
                              </Button>
                            </DropdownMenu>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="credentials" className="space-y-4 pt-4">
            <div className="flex justify-end">
              <Dialog open={isAddingCredential} onOpenChange={setIsAddingCredential}>
                <DialogTrigger asChild>
                  <Button className="flex items-center gap-2">
                    <Plus className="h-4 w-4" />
                    Add Credential
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Add New Credential</DialogTitle>
                    <DialogDescription>Enter the access credentials for a device.</DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label htmlFor="credential-device-id">Device ID</Label>
                      <Select
                        value={newCredential.deviceId}
                        onValueChange={(value) => setNewCredential({ ...newCredential, deviceId: value })}
                      >
                        <SelectTrigger id="credential-device-id">
                          <SelectValue placeholder="Select device" />
                        </SelectTrigger>
                        <SelectContent>
                          {devices.map((device) => (
                            <SelectItem key={device.deviceId} value={device.deviceId}>
                              {device.deviceId} ({device.ip})
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="connection-type">Connection Type</Label>
                      <Select
                        value={newCredential.connectionType}
                        onValueChange={(value) => setNewCredential({ ...newCredential, connectionType: value })}
                      >
                        <SelectTrigger id="connection-type">
                          <SelectValue placeholder="Select connection type" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="ssh">SSH</SelectItem>
                          <SelectItem value="telnet">Telnet</SelectItem>
                          <SelectItem value="http">HTTP</SelectItem>
                          <SelectItem value="https">HTTPS</SelectItem>
                          <SelectItem value="snmp">SNMP</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="description">Description</Label>
                      <Input
                        id="description"
                        value={newCredential.description}
                        onChange={(e) => setNewCredential({ ...newCredential, description: e.target.value })}
                        placeholder="e.g., Admin SSH access"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="Username">Username</Label>
                      <Input
                        id="username"
                        value={newCredential.username}
                        onChange={(e) => setNewCredential({ ...newCredential, username: e.target.value })}
                        placeholder="e.g., admin"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="password">Password</Label>
                      <Input
                        id="password"
                        type="password"
                        value={newCredential.password}
                        onChange={(e) => setNewCredential({ ...newCredential, password: e.target.value })}
                        placeholder="Enter password"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="port">Port</Label>
                        <Input
                          id="port"
                          type="number"
                          value={newCredential.port}
                          onChange={(e) =>
                            setNewCredential({ ...newCredential, port: Number.parseInt(e.target.value) })
                          }
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="priority">Priority</Label>
                        <Input
                          id="priority"
                          type="number"
                          value={newCredential.priority}
                          onChange={(e) =>
                            setNewCredential({ ...newCredential, priority: Number.parseInt(e.target.value) })
                          }
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="extra">Extra (JSON)</Label>
                      <Textarea
                        id="extra"
                        value={JSON.stringify(newCredential.extra, null, 2)}
                        onChange={(e) => {
                          try {
                            const extraJson = JSON.parse(e.target.value)
                            setNewCredential({ ...newCredential, extra: extraJson })
                          } catch (error) {
                            // Allow invalid JSON during typing
                            console.log("error parsing extra field of credential")
                            console.log(error)
                          }
                        }}
                        placeholder='{"key": "value"}'
                        className="font-mono"
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setIsAddingCredential(false)}>
                      Cancel
                    </Button>
                    <Button onClick={addCredential}>Add Credential</Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>

            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Device ID</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Username</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>Priority</TableHead>
                      <TableHead className="w-[100px]">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredCredentials.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center py-4 text-muted-foreground">
                          No credentials found
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredCredentials.map((credential) => (
                        <TableRow key={credential.id}>
                          <TableCell className="font-medium">{credential.deviceId}</TableCell>
                          <TableCell>{credential.connectionType}</TableCell>
                          <TableCell>{credential.username}</TableCell>
                          <TableCell>{credential.description}</TableCell>
                          <TableCell>{credential.priority}</TableCell>
                          <TableCell>
                            <Button variant="ghost" size="sm" onClick={() => deleteCredential(credential.id)}>
                              <Trash2 className="h-4 w-4 text-red-500" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </MainLayout>
  )
}
