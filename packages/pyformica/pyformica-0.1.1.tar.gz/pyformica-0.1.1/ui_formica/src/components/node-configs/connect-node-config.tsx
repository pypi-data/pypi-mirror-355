"use client"

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

interface ConnectNodeConfigProps {
  config: {
    host: string
    connectionType: string
  }
  updateConfig: (key: string, value: any) => void
}

export default function ConnectNodeConfig({ config, updateConfig }: ConnectNodeConfigProps) {
  return (
    <div className="space-y-3">

      <div className="space-y-2">
        <label htmlFor="connect-type" className="text-xs font-medium block">
          Connection Type:
        </label>
        <Select value={config.connectionType || "SSH"} onValueChange={(value) => updateConfig("connectionType", value)}>
          <SelectTrigger id="connect-type" className="h-8 text-xs">
            <SelectValue placeholder="Select connection type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ssh">SSH</SelectItem>
            <SelectItem value="telnet">Telnet</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  )
}
