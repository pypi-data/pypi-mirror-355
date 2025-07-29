"use client"

import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Terminal,
  Network,
  LogOut,
  GitBranch,
} from "lucide-react"

// Node categories and their items
const nodeCategories = [
  {
    name: "Operations",
    items: [
      {
        type: "operation",
        name: "Decision",
        icon: GitBranch,
        description: "Route based on multiple conditions",
        inputs: [{ id: "in-1", label: "Input" }],
        outputs: [
          { id: "out-1", label: "True" },
          { id: "out-2", label: "False" },
        ],
        config: {
          condition: "",
        },
      },
    ],
  },
  {
    name: "Connection",
    items: [
      {
        type: "connection",
        name: "Connect",
        icon: Network,
        description: "Connect to a remote system",
        inputs: [{ id: "in-1", label: "Input" }],
        outputs: [{ id: "out-1", label: "Output" }],
        config: { connectionType: "SSH" },
      },
      {
        type: "connection",
        name: "Command",
        icon: Terminal,
        description: "Execute a command on connected system",
        inputs: [{ id: "in-1", label: "Input" }],
        outputs: [{ id: "out-1", label: "Output" }],
        config: { command: "" },
      },
      {
        type: "connection",
        name: "Disconnect",
        icon: LogOut,
        description: "Disconnect from remote system",
        inputs: [{ id: "in-1", label: "Input" }],
        outputs: [{ id: "out-1", label: "Output" }],
        config: {},
      },
    ],
  },
]

interface NodeSidebarProps {
  onAddNode: (nodeType: string, nodeData: any) => void
}

export default function NodeSidebar({ onAddNode }: NodeSidebarProps) {
  return (
    <div className="w-64 border-r bg-muted/40">
      <div className="p-4 border-b">
        <h2 className="font-medium">Nodes</h2>
        <p className="text-xs text-muted-foreground">Drag nodes to the canvas</p>
      </div>
      <ScrollArea className="h-[calc(100vh-10rem)]">
        <div className="p-4 space-y-6">
          {nodeCategories.map((category) => (
            <div key={category.name}>
              <h3 className="text-sm font-medium mb-2">{category.name}</h3>
              <div className="space-y-1">
                {category.items.map((item) => (
                  <Button
                    key={item.name}
                    variant="ghost"
                    className="w-full justify-start text-sm px-2 py-1 h-auto"
                    onClick={() =>
                      onAddNode(item.type, {
                        label: item.name,
                        description: item.description,
                        inputs: item.inputs,
                        outputs: item.outputs,
                        config: item.config,
                      })
                    }
                  >
                    <item.icon className="h-4 w-4 mr-2" />
                    {item.name}
                  </Button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  )
}
