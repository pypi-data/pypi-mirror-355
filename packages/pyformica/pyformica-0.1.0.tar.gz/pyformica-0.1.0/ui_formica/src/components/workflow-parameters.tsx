"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Trash2 } from "lucide-react"

export interface WorkflowParameter {
  name: string
  defaultValue?: string
}

interface WorkflowParametersProps {
  parameters: WorkflowParameter[]
  onChange: (parameters: WorkflowParameter[]) => void
}

export default function WorkflowParameters({ parameters, onChange }: WorkflowParametersProps) {
  const [newParam, setNewParam] = useState<Partial<WorkflowParameter>>({
    name: "",
  })

  const addParameter = () => {
    if (!newParam.name) return

    const newParameter: WorkflowParameter = {
      name: newParam.name,
    }

    onChange([...parameters, newParameter])

    // Reset form
    setNewParam({
      name: "",
    })
  }

  const removeParameter = (name: string) => {
    onChange(parameters.filter((param) => param.name !== name))
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <h3 className="text-sm font-medium">Workflow Parameters</h3>
        <p className="text-xs text-muted-foreground">Define parameters that can be set when executing this workflow.</p>
      </div>

      {/* Existing parameters */}
      {parameters.length > 0 && (
        <div className="space-y-4">
          {parameters.map((param) => (
            <div key={param.name} className="border rounded-md p-3 space-y-3">
              <div className="flex justify-between items-start">
                <div className="font-medium text-sm">{param.name}</div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 text-muted-foreground"
                  onClick={() => removeParameter(param.name)}
                >
                  <Trash2 className="h-4 w-4" />
                  <span className="sr-only">Remove parameter</span>
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add new parameter form */}
      <div className="border rounded-md p-3 space-y-3">
        <h4 className="text-sm font-medium">Add Parameter</h4>
        <div className="space-y-2">
          <div className="space-y-1">
            <Label htmlFor="new-param-name" className="text-xs">
              Name
            </Label>
            <Input
              id="new-param-name"
              value={newParam.name || ""}
              onChange={(e) => setNewParam({ ...newParam, name: e.target.value })}
              className="h-8 text-xs"
              placeholder="e.g., apiKey, timeout, environment"
            />
          </div>

          <Button onClick={addParameter} className="w-full mt-2" disabled={!newParam.name}>
            Add Parameter
          </Button>
        </div>
      </div>
    </div>
  )
}
