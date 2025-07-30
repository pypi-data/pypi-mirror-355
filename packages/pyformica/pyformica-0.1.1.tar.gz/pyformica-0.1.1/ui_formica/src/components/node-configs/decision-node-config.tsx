"use client"

import { useEffect, useState } from "react"
// import { Button } from "@/components/ui/button"
// import { Input } from "@/components/ui/input"
// import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
// import { Trash2, Plus } from "lucide-react"
import { Textarea } from "../ui/textarea"

// interface Condition {
//   id: string
//   field: string
//   operator: string
//   value: string
//   connector: "AND" | "OR"
// }

interface DecisionNodeConfigProps {
  config: {
    // conditions: Condition[]
    condition: string
  }
  updateConfig: (key: string, value: any) => void
}

export default function DecisionNodeConfig({ config, updateConfig }: DecisionNodeConfigProps) {
  const [condition, setCondition] = useState(config.condition || "")
  const handleConditionChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newCondition = e.target.value
    setCondition(newCondition)
    updateConfig("condition", newCondition)
  }
  useEffect(() => {
    if (config.condition !== condition) {
      setCondition(config.condition)
    }
  }, [config.condition]);
  return (
    <div className="space-y-3">
      <div className="space-y-2">
        <label htmlFor="condition" className="text-xs font-medium block">
          Condition:
        </label>
        <Textarea
          id="condition"
          value={condition}
          onChange={handleConditionChange}
          className="text-xs min-h-[120px] resize-none font-mono"
          placeholder="Enter condition to execute"
        />
      </div>
    </div>
  )
  // const [conditions, setConditions] = useState<Condition[]>(
  //   config.conditions || [{ id: "cond-1", field: "", operator: "equals", value: "", connector: "AND" }],
  // )

  // const operators = [
  //   { value: "equals", label: "Equals" },
  //   { value: "notEquals", label: "Not Equals" },
  //   { value: "contains", label: "Contains" },
  //   { value: "greaterThan", label: "Greater Than" },
  //   { value: "lessThan", label: "Less Than" },
  //   { value: "isEmpty", label: "Is Empty" },
  //   { value: "isNotEmpty", label: "Is Not Empty" },
  // ]

  // const updateCondition = (id: string, field: keyof Condition, value: string) => {
  //   const updatedConditions = conditions.map((condition) =>
  //     condition.id === id ? { ...condition, [field]: value } : condition,
  //   )
  //   setConditions(updatedConditions)
  //   updateConfig("conditions", updatedConditions)
  // }

  // const addCondition = () => {
  //   const newCondition: Condition = {
  //     id: `cond-${Date.now()}`,
  //     field: "",
  //     operator: "equals",
  //     value: "",
  //     connector: "AND",
  //   }
  //   const updatedConditions = [...conditions, newCondition]
  //   setConditions(updatedConditions)
  //   updateConfig("conditions", updatedConditions)
  // }

  // const removeCondition = (id: string) => {
  //   if (conditions.length <= 1) return
  //   const updatedConditions = conditions.filter((condition) => condition.id !== id)
  //   setConditions(updatedConditions)
  //   updateConfig("conditions", updatedConditions)
  // }

  // return (
  //   <div className="space-y-4">
  //     <div className="space-y-3">
  //       {conditions.map((condition, index) => (
  //         <div key={condition.id} className="space-y-2 pt-2 border-t first:border-t-0 first:pt-0">
  //           {index > 0 && (
  //             <div className="mb-2">
  //               <Select
  //                 value={condition.connector}
  //                 onValueChange={(value) => updateCondition(condition.id, "connector", value as "AND" | "OR")}
  //               >
  //                 <SelectTrigger className="h-7 text-xs w-20">
  //                   <SelectValue />
  //                 </SelectTrigger>
  //                 <SelectContent>
  //                   <SelectItem value="AND">AND</SelectItem>
  //                   <SelectItem value="OR">OR</SelectItem>
  //                 </SelectContent>
  //               </Select>
  //             </div>
  //           )}

  //           <div className="grid grid-cols-[1fr,auto,1fr,auto] gap-1 items-center">
  //             <Input
  //               placeholder="Field"
  //               value={condition.field}
  //               onChange={(e) => updateCondition(condition.id, "field", e.target.value)}
  //               className="h-7 text-xs"
  //             />

  //             <Select
  //               value={condition.operator}
  //               onValueChange={(value) => updateCondition(condition.id, "operator", value)}
  //             >
  //               <SelectTrigger className="h-7 text-xs w-28">
  //                 <SelectValue />
  //               </SelectTrigger>
  //               <SelectContent>
  //                 {operators.map((op) => (
  //                   <SelectItem key={op.value} value={op.value}>
  //                     {op.label}
  //                   </SelectItem>
  //                 ))}
  //               </SelectContent>
  //             </Select>

  //             <Input
  //               placeholder="Value"
  //               value={condition.value}
  //               onChange={(e) => updateCondition(condition.id, "value", e.target.value)}
  //               className="h-7 text-xs"
  //               disabled={["isEmpty", "isNotEmpty"].includes(condition.operator)}
  //             />

  //             <Button
  //               variant="ghost"
  //               size="icon"
  //               className="h-7 w-7"
  //               onClick={() => removeCondition(condition.id)}
  //               disabled={conditions.length <= 1}
  //             >
  //               <Trash2 className="h-3 w-3" />
  //               <span className="sr-only">Remove condition</span>
  //             </Button>
  //           </div>
  //         </div>
  //       ))}
  //     </div>

  //     <Button variant="outline" size="sm" className="w-full text-xs h-7" onClick={addCondition}>
  //       <Plus className="h-3 w-3 mr-1" />
  //       Add Condition
  //     </Button>
  //   </div>
  // )
}
