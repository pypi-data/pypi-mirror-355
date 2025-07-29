"use client"

import type { ReactNode } from "react"
import EmailNodeConfig from "./email-node-config"
import HttpRequestConfig from "./http-request-config"
import ConnectNodeConfig from "./connect-node-config"
import RunCommandConfig from "./run-command-config"
import DecisionNodeConfig from "./decision-node-config"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"

// Generic field renderer for simple node types
function GenericNodeConfig({
  config,
  updateConfig,
  fields,
}: {
  config: Record<string, any>
  updateConfig: (key: string, value: any) => void
  fields: Array<{
    key: string
    label: string
    type: "text" | "textarea" | "number" | "email"
    placeholder?: string
  }>
}) {
  return (
    <div className="space-y-3">
      {fields.map((field) => (
        <div key={field.key} className="space-y-2">
          <Label htmlFor={`field-${field.key}`} className="text-xs">
            {field.label}:
          </Label>

          {field.type === "textarea" ? (
            <Textarea
              id={`field-${field.key}`}
              value={config[field.key] || ""}
              onChange={(e) => updateConfig(field.key, e.target.value)}
              className="text-xs min-h-[80px] resize-none"
              placeholder={field.placeholder}
            />
          ) : (
            <Input
              id={`field-${field.key}`}
              type={field.type}
              value={config[field.key] || ""}
              onChange={(e) => updateConfig(field.key, e.target.value)}
              className="h-8 text-xs"
              placeholder={field.placeholder}
            />
          )}
        </div>
      ))}
    </div>
  )
}

// Registry of node configurations
export function getNodeConfigComponent(
  nodeType: string,
  nodeName: string,
  config: any,
  updateConfig: (key: string, value: any) => void,
): ReactNode {
  // First check for exact node name matches
  switch (nodeName) {
    case "Send Email":
      return <EmailNodeConfig config={config} updateConfig={updateConfig} />
    case "HTTP Request":
      return <HttpRequestConfig config={config} updateConfig={updateConfig} />
    case "Connect":
      return <ConnectNodeConfig config={config} updateConfig={updateConfig} />
    case "Command":
      return <RunCommandConfig config={config} updateConfig={updateConfig} />
    case "Decision":
      return <DecisionNodeConfig config={config} updateConfig={updateConfig} />
    case "Database":
      return (
        <GenericNodeConfig
          config={config}
          updateConfig={updateConfig}
          fields={[
            { key: "operation", label: "Operation", type: "text", placeholder: "select, insert, update, delete" },
            { key: "query", label: "Query", type: "textarea", placeholder: "SELECT * FROM users" },
          ]}
        />
      )
    case "Send Message":
      return (
        <GenericNodeConfig
          config={config}
          updateConfig={updateConfig}
          fields={[
            { key: "channel", label: "Channel", type: "text", placeholder: "#general" },
            { key: "message", label: "Message", type: "textarea", placeholder: "Your message here" },
          ]}
        />
      )
    case "Disconnect":
      return <p className="text-xs text-muted-foreground">No configuration needed for this node.</p>
  }

  // Then check for node types
  switch (nodeType) {
    case "trigger":
      return (
        <GenericNodeConfig
          config={config}
          updateConfig={updateConfig}
          fields={[{ key: "schedule", label: "Schedule", type: "text", placeholder: "0 * * * *" }]}
        />
      )
    case "operation":
      return (
        <GenericNodeConfig
          config={config}
          updateConfig={updateConfig}
          fields={[{ key: "condition", label: "Condition", type: "text", placeholder: "data.value > 10" }]}
        />
      )
    default:
      return <p className="text-xs text-muted-foreground">This node type doesn't have configurable fields.</p>
  }
}
