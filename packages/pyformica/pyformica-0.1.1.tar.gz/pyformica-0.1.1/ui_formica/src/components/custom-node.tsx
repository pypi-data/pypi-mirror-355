"use client"

import { memo } from "react"
import { Handle, Position, type NodeProps } from "reactflow"
import {
  Clock,
  Database,
  Mail,
  MessageSquare,
  FileText,
  Code,
  Webhook,
  Filter,
  SplitSquareVertical,
  Zap,
  Terminal,
  Network,
  LogOut,
  GitBranch,
} from "lucide-react"

// Map of node types to their icons
const nodeIcons: Record<string, any> = {
  trigger: Zap,
  schedule: Clock,
  webhook: Webhook,
  filter: Filter,
  split: SplitSquareVertical,
  decision: GitBranch,
  "send email": Mail,
  database: Database,
  "http request": Code,
  "send message": MessageSquare,
  "create document": FileText,
  connect: Network,
  "command": Terminal,
  disconnect: LogOut,
}

// Get icon for a node based on its type or label
const getNodeIcon = (type: string, label: string) => {
  const normalizedLabel = label.toLowerCase()
  return nodeIcons[type] || nodeIcons[normalizedLabel] || Zap
}

// Node background colors based on type
const nodeColors: Record<string, string> = {
  trigger: "bg-amber-100 border-amber-300",
  operation: "bg-sky-100 border-sky-300",
  action: "bg-emerald-100 border-emerald-300",
  connection: "bg-purple-100 border-purple-300",
}

const CustomNode = ({ data, isConnectable }: NodeProps) => {
  const Icon = getNodeIcon(data.type, data.label)
  const nodeColor = nodeColors[data.type] || "bg-gray-100 border-gray-300"

  return (
    <div className={`rounded-md border-2 shadow-sm ${nodeColor} p-3 min-w-[180px]`}>
      <div className="flex items-center gap-2 mb-2">
        <Icon className="h-5 w-5" />
        <div className="font-medium text-sm">{data.label}</div>
      </div>

      {/* Input handles */}
      {data.inputs &&
        data.inputs.map((input: any, index: number) => (
          <Handle
            key={input.id || `input-${index}`}
            type="target"
            position={Position.Left}
            id={input.id || `input-${index}`}
            className="w-3 h-3 bg-blue-500"
            style={{ top: 30 + index * 20 }}
            isConnectable={isConnectable}
          />
        ))}

      {/* Output handles */}
      {data.outputs &&
        data.outputs.map((output: any, index: number) => (
          <Handle
            key={output.id || `output-${index}`}
            type="source"
            position={Position.Right}
            id={output.id || `output-${index}`}
            className="w-3 h-3 bg-blue-500"
            style={{ top: 30 + index * 20 }}
            isConnectable={isConnectable}
          />
        ))}

      {/* Optional description */}
      {data.description && <div className="text-xs text-gray-500 mt-1">{data.description}</div>}
    </div>
  )
}

export default memo(CustomNode)
