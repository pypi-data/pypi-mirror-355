"use client"

import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"

interface EmailNodeConfigProps {
  config: {
    to: string
    subject: string
    body: string
  }
  updateConfig: (key: string, value: any) => void
}

export default function EmailNodeConfig({ config, updateConfig }: EmailNodeConfigProps) {
  return (
    <div className="space-y-3">
      <div className="space-y-2">
        <label htmlFor="email-to" className="text-xs font-medium block">
          To:
        </label>
        <Input
          id="email-to"
          type="email"
          value={config.to || ""}
          onChange={(e) => updateConfig("to", e.target.value)}
          className="h-8 text-xs"
          placeholder="recipient@example.com"
        />
      </div>

      <div className="space-y-2">
        <label htmlFor="email-subject" className="text-xs font-medium block">
          Subject:
        </label>
        <Input
          id="email-subject"
          type="text"
          value={config.subject || ""}
          onChange={(e) => updateConfig("subject", e.target.value)}
          className="h-8 text-xs"
          placeholder="Email subject"
        />
      </div>

      <div className="space-y-2">
        <label htmlFor="email-body" className="text-xs font-medium block">
          Body:
        </label>
        <Textarea
          id="email-body"
          value={config.body || ""}
          onChange={(e) => updateConfig("body", e.target.value)}
          className="text-xs min-h-[120px] resize-none"
          placeholder="Email content..."
        />
      </div>
    </div>
  )
}
