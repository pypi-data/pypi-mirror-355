"use client"

import { useState, useEffect } from "react"
import {useNavigate} from "react-router";
import { Plus, Search, Trash2, Users } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardFooter } from "@/components/ui/card"
import MainLayout from "./main-layout"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { type Node, type Edge } from "reactflow"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import {getToken} from "@/lib/auth";
import applyCaseMiddleware from "axios-case-converter";
import axios from "axios";

// Define workflow type
interface Workflow {
  flowId: string
  description: string
  // updatedAt: string
  savedState: {
    nodes: Node[]
    edges: Edge[]
  }
  groupId: string
}

interface Group {
  groupId: string
  description: string
  members: string[]
}

export default function DashboardView() {
  const router = useNavigate()
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [groups, setGroups] = useState<Group[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [newWorkflow, setNewWorkflow] = useState({
    flowId: "New Workflow",
    description: "Workflow description",
    groupId: "no-group",
  })
  const API_URL = "http://localhost:8000/api"
  const token = getToken()
  const client = applyCaseMiddleware(axios.create())

  // Load workflows from localStorage on component mount
  useEffect(() => {
    // console.log(getToken())
    if (getToken() === null) router("/login")

    const loadAll = async () => {
      try {
        await client.get(`${API_URL}/users/me`,
          {
            headers: {
              "Authorization": `Bearer ${token}`,
            },
          }
        )

        const { data: flows } = await client.get(`${API_URL}/flows`,
          {
            headers: {
              "Authorization": `Bearer ${token}`,
            },
          })
        // localStorage.setItem("workflows", JSON.stringify(data))
        setWorkflows(flows)


        const { data: groups } = await client.get(`${API_URL}/groups`,
        {
          headers: {
            "Authorization": `Bearer ${token}`,
          },
        })
        setGroups(groups)
      } catch (error) {
        console.log(error)
        router("/login")
      }
    }

    loadAll()
  }, [])

  // Create a new workflow
  const createWorkflow = async () => {
    const newWorkflowItem: Partial<Workflow> = {
      flowId: newWorkflow.flowId,
      description: newWorkflow.description,
      // updatedAt: new Date().toISOString(),
      groupId: newWorkflow.groupId,
    }

    const { data } = await client.post(`${API_URL}/flows`,
      newWorkflowItem,
      {
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
      })

    const updatedWorkflows = [...workflows, data]
    setWorkflows(updatedWorkflows)
    // localStorage.setItem("workflows", JSON.stringify(updatedWorkflows))

    // Reset form and close dialog
    setNewWorkflow({
      flowId: "New Workflow",
      description: "Workflow description",
      groupId: "no-group",
    })
    setIsCreateDialogOpen(false)

    // Navigate to the new workflow
    router(`/workflow/${newWorkflowItem.flowId}`)
  }

  // Delete a workflow
  const deleteWorkflow = async (id: string) => {
    const updatedWorkflows = workflows.filter((workflow) => workflow.flowId !== id)

    await client.delete(
      `${API_URL}/flows/${id}`,
      {
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
      })
    setWorkflows(updatedWorkflows)
    // localStorage.setItem("workflows", JSON.stringify(updatedWorkflows))
  }

  // Get group name by ID
  const getGroupName = (groupId?: string) => {
    if (!groupId) return "No Group"
    const group = groups.find((g) => g.groupId === groupId)
    return group ? group.groupId : "Unknown Group"
  }

  // Filter workflows based on search query
  const filteredWorkflows = workflows.filter(
    (workflow) =>
      workflow.flowId.toLowerCase().includes(searchQuery.toLowerCase()) ||
      workflow.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      getGroupName(workflow.groupId).toLowerCase().includes(searchQuery.toLowerCase()),
  )

  return (
    <MainLayout>
      <div className="container mx-auto py-6 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">My Workflows</h1>

          <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button className="flex items-center gap-2">
                <Plus className="h-4 w-4" />
                Create Workflow
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Workflow</DialogTitle>
                <DialogDescription>Configure your new workflow before creating it.</DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="name" className="text-right">
                    Name
                  </Label>
                  <Input
                    id="name"
                    value={newWorkflow.flowId}
                    onChange={(e) => setNewWorkflow({ ...newWorkflow, flowId: e.target.value })}
                    className="col-span-3"
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="description" className="text-right">
                    Description
                  </Label>
                  <Textarea
                    id="description"
                    value={newWorkflow.description}
                    onChange={(e) => setNewWorkflow({ ...newWorkflow, description: e.target.value })}
                    className="col-span-3"
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="group" className="text-right">
                    Group
                  </Label>
                  <Select
                    value={newWorkflow.groupId}
                    onValueChange={(value) => setNewWorkflow({ ...newWorkflow, groupId: value })}
                  >
                    <SelectTrigger className="col-span-3">
                      <SelectValue placeholder="Select a group" />
                    </SelectTrigger>
                    <SelectContent>
                      {groups.map((group) => (
                        <SelectItem key={group.groupId} value={group.groupId}>
                          {group.groupId}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={createWorkflow}>Create Workflow</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search workflows..."
            className="pl-10"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredWorkflows.map((workflow) => (
            <Card key={workflow.flowId} className="overflow-hidden">
              <div
                className="h-32 bg-muted flex items-center justify-center cursor-pointer"
                onClick={() => router(`/workflow/${workflow.flowId}`)}
              >
                <div className="text-center">
                  <p className="text-xs text-muted-foreground">Click to edit</p>
                </div>
              </div>
              <CardContent className="p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-medium truncate">{workflow.flowId}</h3>
                    <p className="text-sm text-muted-foreground line-clamp-2">{workflow.description}</p>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => deleteWorkflow(workflow.flowId)}>
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              </CardContent>
              <CardFooter className="p-4 pt-0 flex justify-between text-xs text-muted-foreground">
                <div className="flex items-center">
                  <Users className="mr-1 h-3 w-3" />
                  <Badge variant="outline" className="ml-1 text-xs">
                    {getGroupName(workflow.groupId)}
                  </Badge>
                </div>
              </CardFooter>
            </Card>
          ))}
        </div>

        {filteredWorkflows.length === 0 && (
          <div className="text-center py-12">
            <p className="text-muted-foreground">No workflows found</p>
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
