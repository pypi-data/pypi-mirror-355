"use client"

import type React from "react"
import {useCallback, useEffect, useState} from "react"
import ReactFlow, {
  addEdge,
  Background,
  type Connection,
  ConnectionLineType,
  Controls,
  type Edge,
  MiniMap,
  type Node,
  useEdgesState,
  useNodesState,
} from "reactflow"
import "reactflow/dist/style.css"

import NodeSidebar from "./node-sidebar"
import CustomNode from "./custom-node"
import {Button} from "@/components/ui/button"
import {Input} from "@/components/ui/input"
import {Select, SelectContent, SelectItem, SelectTrigger, SelectValue} from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogDescription, DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import {ArrowLeft, Clock, History, Play, Save} from "lucide-react"
import {getNodeConfigComponent} from "./node-configs"
import {format} from "date-fns"
import {getToken} from "@/lib/auth";
import applyCaseMiddleware from "axios-case-converter";
import axios from "axios";
import {useNavigate} from "react-router";
import WorkflowParameters, {type WorkflowParameter} from "@/components/workflow-parameters.tsx";
import {Tabs, TabsContent, TabsList, TabsTrigger} from "./ui/tabs"
import ParameterInputForm from "@/components/parameter-input-form.tsx";

// Define custom node types
const nodeTypes = {
  customNode: CustomNode,
}

interface DeviceSet {
  deviceSetId: string
  description: string
  devices: string[]
  groupId: string // Group this device set belongs to

}

interface FlowVersion {
  flowId: string
  version: string
  createdAt: string
  structure: {
    nodes: Node[]
    edges: Edge[]
  }
  parameters: string[]
}

interface WorkflowBuilderProps {
  workflowId: string
}

export default function WorkflowBuilder({ workflowId }: WorkflowBuilderProps) {
  const router = useNavigate()
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)
  const [workflowName, setWorkflowName] = useState("New Workflow")
  const [workflowDescription, setWorkflowDescription] = useState("Workflow description")
  const [deviceSets, setDeviceSets] = useState<DeviceSet[]>([])
  const [selectedDeviceSet, setSelectedDeviceSet] = useState<string>("")
  const [isLoading, setIsLoading] = useState(true)
  const [versions, setVersions] = useState<FlowVersion[]>([])
  const [isVersionDialogOpen, setIsVersionDialogOpen] = useState(false)
  const [versionName, setVersionName] = useState("")
  const [nodeIdError, setNodeIdError] = useState("")
  const [isVersionSelectDialogOpen, setIsVersionSelectDialogOpen] = useState(false)
  const [selectedVersionId, setSelectedVersionId] = useState<string>("")
  const API_URL = "http://localhost:8000/api"
  const token = getToken()
  const client = applyCaseMiddleware(axios.create())
  const [parameters, setParameters] = useState<WorkflowParameter[]>([])
  const [parameterValues, setParameterValues] = useState<Record<string, any>>({})
  const [activeTab, setActiveTab] = useState("canvas")

  // Load workflow data, device sets, and versions
  useEffect(() => {
    const loadData = async () => {
      try {
        // Load device sets
        const fetchDeviceSets = async () => {
          const { data } = await client.get(`${API_URL}/device-sets`,
          {
            headers: {
              "Authorization": `Bearer ${token}`,
            },
          })
          setDeviceSets(data)
        }

        // Load versions
        const fetchFlowVersions = async () => {
          const { data } = await client.get(`${API_URL}/flow-versions`,
          {
            params: {
              flowId: workflowId
            },
            headers: {
              "Authorization": `Bearer ${token}`,
            },
          })
          setVersions(data)
        }
        fetchDeviceSets()
        fetchFlowVersions()

        // Load workflow if editing an existing one
        if (workflowId === "new") {
          setIsLoading(false)
          return
        }

        // Get workflow
        const { data } = await client.get(`${API_URL}/flows/${workflowId}`,
        {
          headers: {
            "Authorization": `Bearer ${token}`,
          },
        })
        setWorkflowName(data.flowId)
        setWorkflowDescription(data.description)
        setNodes(data.savedState.nodes)
        setEdges(data.savedState.edges)
      } catch (error) {
        console.error("Error loading data:", error)
      }

      setIsLoading(false)
    }

    loadData()
  }, [workflowId, setNodes, setEdges])

  // Handle new connections between nodes
  const onConnect = useCallback(
    (connection: Connection) => {
      setEdges((eds) =>
        addEdge(
          {
            ...connection,
            type: "smoothstep",
            animated: true,
          },
          eds,
        ),
      )
    },
    [setEdges],
  )

  // Handle node selection
  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNode(node)
    setNodeIdError("")
  }, [])

  // Add a new node to the canvas
  const onAddNode = useCallback(
    (nodeType: string, nodeData: any) => {
      const newNode = {
        id: `node_${Date.now()}`,
        type: "customNode",
        position: {
          x: Math.random() * 300 + 50,
          y: Math.random() * 300 + 50,
        },
        data: {
          ...nodeData,
          type: nodeType,
        },
      }

      setNodes((nds) => nds.concat(newNode))
    },
    [setNodes],
  )

  // Update node ID
  const updateNodeId = useCallback(
    (oldId: string, newId: string) => {
      // Check if the new ID is valid
      if (!newId || newId.trim() === "") {
        setNodeIdError("Node ID cannot be empty")
        return false
      }

      // Check if the new ID already exists
      const nodeExists = nodes.some((node) => node.id === newId && node.id !== oldId)
      if (nodeExists) {
        setNodeIdError("Node ID already exists")
        return false
      }

      // Update node ID
      setNodes((nds) =>
        nds.map((node) => {
          if (node.id === oldId) {
            return {
              ...node,
              id: newId,
            }
          }
          return node
        }),
      )

      // Update edges that reference this node
      setEdges((eds) =>
        eds.map((edge) => {
          if (edge.source === oldId) {
            return {
              ...edge,
              source: newId,
            }
          }
          if (edge.target === oldId) {
            return {
              ...edge,
              target: newId,
            }
          }
          return edge
        }),
      )

      // Update selected node reference
      if (selectedNode && selectedNode.id === oldId) {
        setSelectedNode({
          ...selectedNode,
          id: newId,
        })
      }

      setNodeIdError("")
      return true
    },
    [nodes, setNodes, setEdges, selectedNode],
  )

  // Save the current workflow
  const saveWorkflow = useCallback(async () => {
    try {
      // Save workflow data
      const savedState = { nodes, edges }
      localStorage.setItem(`workflow_data_${workflowId}`, JSON.stringify(savedState))
      console.log(JSON.stringify(savedState))

      await client.patch(`${API_URL}/flows/${workflowId}`,
        { savedState },
        {
          headers: {
            "Authorization": `Bearer ${token}`,
          },
        })

      // Update workflow metadata
      const savedWorkflows = localStorage.getItem("workflows")
      const workflows = savedWorkflows ? JSON.parse(savedWorkflows) : []

      const now = new Date().toISOString()
      const existingWorkflowIndex = workflows.findIndex((w: any) => w.id === workflowId)

      if (existingWorkflowIndex >= 0) {
        // Update existing workflow
        workflows[existingWorkflowIndex] = {
          ...workflows[existingWorkflowIndex],
          name: workflowName,
          description: workflowDescription,
          deviceSetId: selectedDeviceSet,
          groupId: selectedDeviceSet, // Add groupId
          updatedAt: now,
          nodeCount: nodes.length,
        }
      } else {
        // Create new workflow
        const newWorkflow = {
          id: workflowId === "new" ? `workflow-${Date.now()}` : workflowId,
          name: workflowName,
          description: workflowDescription,
          deviceSetId: selectedDeviceSet,
          groupId: selectedDeviceSet, // Add groupId
          createdAt: now,
          updatedAt: now,
          nodeCount: nodes.length,
        }
        workflows.push(newWorkflow)

        // If this was a new workflow, update the URL to the new ID
        // if (workflowId === "new") {
        //   localStorage.setItem(`workflow_data_${newWorkflow.id}`, JSON.stringify(saved))
        //   router(`/workflow/${newWorkflow.id}`)
        // }
      }

      localStorage.setItem("workflows", JSON.stringify(workflows))
      alert("Workflow saved!")
    } catch (error) {
      console.error("Error saving workflow:", error)
      alert("Failed to save workflow")
    }
  }, [nodes, edges, workflowId, workflowName, workflowDescription, selectedDeviceSet])

  // Save a new version of the workflow
  const saveVersion = useCallback(async () => {
    try {
      const now = new Date().toISOString()

      // Create a new version
      const newVersion: FlowVersion = {
        flowId: workflowId,
        version: versionName,
        createdAt: now,
        structure: {
          nodes,
          edges,
        },
        parameters: parameters.map((param: WorkflowParameter) => param.name)
      }

      await client.post(`${API_URL}/flow-versions`,
      newVersion,
      {
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      })

      // Add to versions list
      const updatedVersions = [...versions, newVersion]
      setVersions(updatedVersions)
      localStorage.setItem(`workflow_versions_${workflowId}`, JSON.stringify(updatedVersions))

      // Reset version name
      setVersionName("")
      setIsVersionDialogOpen(false)

      // alert("Version saved!")
    } catch (error) {
      console.error("Error saving version:", error)
      alert("Failed to save version")
    }
  }, [workflowId, versionName, nodes, edges, versions, parameters])

  // Load a specific version
  const loadVersion = useCallback(
    (versionName: string) => {
      try {
        const version = versions.find((v) => v.version === versionName)
        if (!version) {
          alert("Version not found")
          return
        }

        // Load version data
        setNodes(version.structure.nodes)
        setEdges(version.structure.edges)
        if (version.parameters) {
          setParameters(version.parameters.map((p: string) => {
            return {name: p}
          }))
        }

        setIsVersionDialogOpen(false)
        // alert(`Version "${version.version}" loaded!`)
      } catch (error) {
        console.error("Error loading version:", error)
        alert("Failed to load version")
      }
    },
    [versions, setNodes, setEdges],
  )

  // Execute the workflow
  const executeWorkflow = useCallback(async (versionId: string) => {
    if (!selectedDeviceSet) {
      alert("Please select a device set before executing the workflow")
      return
    }

    try {
      // Find the selected version
      const version = versions.find((v) => v.version === versionId)
      if (!version) {
        alert("Please select a valid workflow version to execute")
        return
      }

      // Find the selected device set
      const deviceSet = deviceSets.find((set) => set.deviceSetId === selectedDeviceSet)
      if (!deviceSet) {
        alert("Selected device set not found")
        return
      }

      const flowRun = {
        flowId: workflowId,
        version: version.version,
        description: "",
        runType: "manual",
        deviceSetId: selectedDeviceSet,
        args: parameterValues
      }

      await client.post(`${API_URL}/flow-runs`,
      flowRun,
      {
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      })

      // Save the execution to localStorage
      // const savedExecutions = localStorage.getItem("executions")
      // const executions = savedExecutions ? JSON.parse(savedExecutions) : []
      // executions.push(execution)
      // localStorage.setItem("executions", JSON.stringify(executions))

      // Simulate execution (in a real app, this would be handled by a backend)
      // setTimeout(() => {
      //   // Update execution status
      //   const updatedExecutions = JSON.parse(localStorage.getItem("executions") || "[]")
      //   const executionIndex = updatedExecutions.findIndex((e: any) => e.id === executionId)
      //
      //   if (executionIndex >= 0) {
      //     updatedExecutions[executionIndex] = {
      //       ...updatedExecutions[executionIndex],
      //       status: "completed",
      //       endTime: new Date().toISOString(),
      //       deviceRuns: updatedExecutions[executionIndex].deviceRuns.map((run: any) => ({
      //         ...run,
      //         status: "completed",
      //         endTime: new Date().toISOString(),
      //         logs: [
      //           {timestamp: new Date().toISOString(), level: "info", message: "Starting execution"},
      //           {timestamp: new Date().toISOString(), level: "info", message: "Connecting to device"},
      //           {timestamp: new Date().toISOString(), level: "info", message: "Running commands"},
      //           {timestamp: new Date().toISOString(), level: "info", message: "Execution completed successfully"},
      //         ],
      //       })),
      //     }
      //     localStorage.setItem("executions", JSON.stringify(updatedExecutions))
      //   }
      // }, 5000)

      setIsVersionSelectDialogOpen(false)
      alert(`Workflow version "${version.version}" execution started!`)
      router("/executions")
    } catch (error) {
      console.error("Error executing workflow:", error)
      alert("Failed to execute workflow")
    }
  }, [workflowId, selectedDeviceSet, deviceSets, versions, router, parameterValues])

  // Open version selection dialog
  const openVersionSelectDialog = useCallback(() => {
    if (versions.length === 0) {
      alert("Please save at least one version of the workflow before executing")
      return
    }

    setSelectedVersionId(versions[versions.length - 1].version) // Select the latest version by default
    setIsVersionSelectDialogOpen(true)
  }, [versions])

  // Update node configuration
  const updateNodeConfig = useCallback(
    (nodeId: string, key: string, value: any) => {
      setNodes((nds) =>
        nds.map((node) => {
          if (node.id === nodeId) {
            // Create a new config object with the updated value
            const updatedConfig = {
              ...node.data.config,
              [key]: value,
            }

            // Return a new node object with the updated config
            return {
              ...node,
              data: {
                ...node.data,
                config: updatedConfig,
              },
            }
          }
          return node
        }),
      )
    },
    [setNodes],
  )

  if (isLoading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Workflow header - Made more compact */}
      <div className="border-b px-3 py-2 flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => router("/dashboard")} className="mr-1">
          <ArrowLeft className="h-4 w-4" />
          <span className="sr-only">Back to dashboard</span>
        </Button>

        <div className="flex-1 flex items-center gap-2">
          <div className="flex-1">
            {/* <Input
              value={workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
              className="font-medium text-base border-none h-7 p-0 focus-visible:ring-0"
              placeholder="Workflow name"
            />
            <Textarea
              value={workflowDescription}
              onChange={(e) => setWorkflowDescription(e.target.value)}
              className="text-xs text-muted-foreground border-none resize-none p-0 focus-visible:ring-0 h-5 min-h-0"
              rows={1}
              placeholder="Description"
            /> */}
            <h2 className="font-medium">{workflowName}</h2>
            <p className="text-xs text-muted-foreground">{workflowDescription}</p>
          </div>


          <div className="flex items-center gap-2">
            <Select value={selectedDeviceSet} onValueChange={setSelectedDeviceSet}>
              <SelectTrigger className="w-[180px] h-8 text-xs">
                <SelectValue placeholder="Select device set" />
              </SelectTrigger>
              <SelectContent>
                {deviceSets.length === 0 ? (
                  <SelectItem value="none" disabled>
                    No device sets available
                  </SelectItem>
                ) : (
                  deviceSets.map((set) => (
                    <SelectItem key={set.deviceSetId} value={set.deviceSetId}>
                      {set.deviceSetId} ({set.devices.length} devices)
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>

            <Dialog open={isVersionDialogOpen} onOpenChange={setIsVersionDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" size="sm" className="flex items-center gap-1 h-8">
                  <History className="h-3 w-3" />
                  Versions
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                  <DialogTitle>Workflow Versions</DialogTitle>
                  <DialogDescription>Save a new version or load a previous version of this workflow.</DialogDescription>
                </DialogHeader>

                <div className="py-4">
                  <div className="mb-4">
                    <h3 className="text-sm font-medium mb-2">Save New Version</h3>
                    <div className="flex gap-2">
                      <Input
                        placeholder="Version name"
                        value={versionName}
                        onChange={(e) => setVersionName(e.target.value)}
                        className="flex-1"
                        required={true}
                      />
                      <Button onClick={saveVersion}>Save Version</Button>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm font-medium mb-2">Previous Versions</h3>
                    {versions.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No saved versions yet.</p>
                    ) : (
                      <div className="max-h-[300px] overflow-y-auto border rounded-md">
                        {versions
                          .slice()
                          .reverse()
                          .map((version) => (
                            <div
                              key={version.version}
                              className="flex items-center justify-between p-3 border-b last:border-b-0 hover:bg-muted/50"
                            >
                              <div>
                                <div className="font-medium">{version.version}</div>
                                <div className="text-xs text-muted-foreground flex items-center gap-1">
                                  <Clock className="h-3 w-3" />
                                  {format(new Date(version.createdAt), "MMM d, yyyy HH:mm")}
                                </div>
                              </div>
                              <Button variant="outline" size="sm" onClick={() => loadVersion(version.version)}>
                                Load
                              </Button>
                            </div>
                          ))}
                      </div>
                    )}
                  </div>
                </div>
              </DialogContent>
            </Dialog>

            <Button onClick={saveWorkflow} size="sm" variant="outline" className="flex items-center gap-1 h-8">
              <Save className="h-3 w-3" />
              Save
            </Button>
            <Button
              onClick={openVersionSelectDialog}
              size="sm"
              variant="default"
              className="flex items-center gap-1 h-8"
              disabled={!selectedDeviceSet || versions.length === 0}
            >
              <Play className="h-3 w-3" />
              Run
            </Button>
          </div>
        </div>
      </div>

      {/* Workflow builder */}
      <div className="flex flex-1 overflow-hidden">
        {/* Node sidebar */}
        <NodeSidebar onAddNode={onAddNode} />

        {/* Main workflow canvas */}
        {/*<div className="flex-1 h-full">*/}
        {/*  <ReactFlow*/}
        {/*    nodes={nodes}*/}
        {/*    edges={edges}*/}
        {/*    onNodesChange={onNodesChange}*/}
        {/*    onEdgesChange={onEdgesChange}*/}
        {/*    onConnect={onConnect}*/}
        {/*    onNodeClick={onNodeClick}*/}
        {/*    nodeTypes={nodeTypes}*/}
        {/*    connectionLineType={ConnectionLineType.SmoothStep}*/}
        {/*    fitView*/}
        {/*  >*/}
        {/*    <Background />*/}
        {/*    <Controls />*/}
        {/*    <MiniMap />*/}
        {/*  </ReactFlow>*/}
        {/*</div>*/}

        <div className="flex-1 h-full flex flex-col">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="relative w-full h-full">
            <TabsList className="absolute mx-2 mt-1 z-40">
              <TabsTrigger value="canvas">Canvas</TabsTrigger>
              <TabsTrigger value="parameters">Parameters</TabsTrigger>
            </TabsList>

            <TabsContent value="canvas" className="flex-1 h-full">
              <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                onNodeClick={onNodeClick}
                nodeTypes={nodeTypes}
                connectionLineType={ConnectionLineType.SmoothStep}
                fitView
              >
                <Background />
                <Controls />
                {/* <MiniMap /> */}
              </ReactFlow>
            </TabsContent>

            <TabsContent value="parameters" className="flex-1 p-4 overflow-auto">
              <WorkflowParameters parameters={parameters} onChange={setParameters} />
            </TabsContent>
          </Tabs>
        </div>

        {/* Properties panel */}
        {selectedNode && (
          <div className="w-80 border-l p-4 overflow-auto">
            <h3 className="font-medium mb-2">{selectedNode.data.label}</h3>
            <p className="text-sm text-muted-foreground mb-4">{selectedNode.data.description}</p>

            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium mb-1">Node ID</h4>
                <div className="flex flex-col gap-1">
                  <Input
                    value={selectedNode.id}
                    onChange={(e) => updateNodeId(selectedNode.id, e.target.value)}
                    className="h-8 text-xs"
                  />
                  {nodeIdError && <p className="text-xs text-red-500">{nodeIdError}</p>}
                </div>
              </div>

              <div>
                <h4 className="text-sm font-medium mb-1">Type</h4>
                <p className="text-xs capitalize">{selectedNode.data.type}</p>
              </div>

              {/* Node specific configuration */}
              <div>
                <h4 className="text-sm font-medium mb-2">Configuration</h4>
                {getNodeConfigComponent(
                  selectedNode.data.type,
                  selectedNode.data.label,
                  selectedNode.data.config,
                  (key, value) => updateNodeConfig(selectedNode.id, key, value),
                )}
              </div>
            </div>
          </div>
        )}

        {/* Version Selection Dialog */}
        <Dialog open={isVersionSelectDialogOpen} onOpenChange={setIsVersionSelectDialogOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Select Workflow Version to Run</DialogTitle>
              <DialogDescription>Choose which saved version of the workflow you want to execute.</DialogDescription>
            </DialogHeader>
            <div className="py-4 space-y-4">
              <div className="space-y-2">
                <Label htmlFor="version-select">Workflow Version</Label>
                <Select
                  value={selectedVersionId}
                  onValueChange={(value) => {
                    setSelectedVersionId(value)
                    // Load parameters for this version
                    const version = versions.find((v) => v.version === value)
                    if (version && version.parameters) {
                      setParameters(version.parameters.map((p: string) => {
                        return {name: p}
                      }))
                    }
                  }}
                >
                  <SelectTrigger id="version-select">
                    <SelectValue placeholder="Select a version" />
                  </SelectTrigger>
                  <SelectContent>
                    {versions.map((version) => (
                      <SelectItem key={version.version} value={version.version}>
                        {version.version} ({format(new Date(version.createdAt), "MMM d, yyyy HH:mm")})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {selectedVersionId && (
                <div className="space-y-2">
                  <h3 className="text-sm font-medium">Parameters</h3>
                  <ParameterInputForm parameters={parameters} onChange={setParameterValues} />
                </div>
              )}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsVersionSelectDialogOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={() => executeWorkflow(selectedVersionId)}
                disabled={!selectedVersionId || parameters.some((p) => !parameterValues[p.name])}
              >
                Execute Workflow
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  )
}
