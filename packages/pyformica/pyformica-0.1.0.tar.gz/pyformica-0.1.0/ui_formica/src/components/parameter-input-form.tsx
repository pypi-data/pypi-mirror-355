"use client"

import { useState, useEffect } from "react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import type { WorkflowParameter } from "./workflow-parameters"

interface ParameterInputFormProps {
  parameters: WorkflowParameter[]
  onChange: (values: Record<string, any>) => void
}

export default function ParameterInputForm({ parameters, onChange }: ParameterInputFormProps) {
  const [paramValues, setParamValues] = useState<Record<string, any>>({})

  // Initialize parameter values with defaults
  useEffect(() => {
    const initialValues: Record<string, any> = {}
    parameters.forEach((param) => {
      initialValues[param.name] = ""
    })
    setParamValues(initialValues)
    onChange(initialValues)
  }, [parameters, onChange])

  const updateParamValue = (paramId: string, value: any) => {
    const updatedValues = { ...paramValues, [paramId]: value }
    setParamValues(updatedValues)
    onChange(updatedValues)
  }

  if (parameters.length === 0) {
    return <p className="text-sm text-muted-foreground">This workflow has no parameters.</p>
  }

  return (
    <div className="space-y-4">
      {parameters.map((param) => (
        <div key={param.name} className="space-y-2">
          <div className="flex justify-between items-baseline">
            <Label htmlFor={`param-input-${param.name}`} className="text-sm font-medium">
              {param.name}
            </Label>
          </div>
          {(
            <Input
              id={`param-input-${param.name}`}
              value={paramValues[param.name] || ""}
              onChange={(e) => updateParamValue(param.name, e.target.value)}
              placeholder={`Enter ${param.name}`}
            />
          )}
        </div>
      ))}
    </div>
  )
}
