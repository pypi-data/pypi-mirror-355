"use client"

import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

interface HttpRequestConfigProps {
  config: {
    url: string
    method: string
    headers: string
    body: string
  }
  updateConfig: (key: string, value: any) => void
}

export default function HttpRequestConfig({ config, updateConfig }: HttpRequestConfigProps) {
  return (
    <div className="space-y-3">
      <div className="space-y-2">
        <label htmlFor="request-url" className="text-xs font-medium block">
          URL:
        </label>
        <Input
          id="request-url"
          type="text"
          value={config.url || ""}
          onChange={(e) => updateConfig("url", e.target.value)}
          className="h-8 text-xs"
          placeholder="https://api.example.com/endpoint"
        />
      </div>

      <div className="space-y-2">
        <label htmlFor="request-method" className="text-xs font-medium block">
          Method:
        </label>
        <Select value={config.method || "GET"} onValueChange={(value) => updateConfig("method", value)}>
          <SelectTrigger id="request-method" className="h-8 text-xs">
            <SelectValue placeholder="Select method" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="GET">GET</SelectItem>
            <SelectItem value="POST">POST</SelectItem>
            <SelectItem value="PUT">PUT</SelectItem>
            <SelectItem value="DELETE">DELETE</SelectItem>
            <SelectItem value="PATCH">PATCH</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <label htmlFor="request-headers" className="text-xs font-medium block">
          Headers (JSON):
        </label>
        <Textarea
          id="request-headers"
          value={config.headers || ""}
          onChange={(e) => updateConfig("headers", e.target.value)}
          className="text-xs min-h-[80px] resize-none"
          placeholder='{"Content-Type": "application/json"}'
        />
      </div>

      <div className="space-y-2">
        <label htmlFor="request-body" className="text-xs font-medium block">
          Body (JSON):
        </label>
        <Textarea
          id="request-body"
          value={config.body || ""}
          onChange={(e) => updateConfig("body", e.target.value)}
          className="text-xs min-h-[80px] resize-none"
          placeholder='{"key": "value"}'
        />
      </div>
    </div>
  )
}
