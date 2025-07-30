import { Textarea } from "@/components/ui/textarea"
// import {useState} from "react";
import React, {useEffect, useState} from "react";

interface RunCommandConfigProps {
  config: {
    command: string
  }
  updateConfig: (key: string, value: any) => void
}

export default function RunCommandConfig({ config, updateConfig }: RunCommandConfigProps) {
  const [command, setCommand] = useState(config.command || "")
  const handleCommandChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newCommand = e.target.value
    setCommand(newCommand)
    updateConfig("command", newCommand)
  }
  useEffect(() => {
    if (config.command !== command) {
      setCommand(config.command)
    }
  }, [config.command]);
  return (
    <div className="space-y-3">
      <div className="space-y-2">
        <label htmlFor="command" className="text-xs font-medium block">
          Command:
        </label>
        <Textarea
          id="command"
          value={command}
          onChange={handleCommandChange}
          className="text-xs min-h-[120px] resize-none font-mono"
          placeholder="Enter command to execute"
        />
      </div>
    </div>
  )
}
