import WorkflowBuilder from "@/components/workflow-builder"
import {useParams} from "react-router";

export default function WorkflowPage() {
  const params = useParams() as { id: string }
  return <WorkflowBuilder workflowId={params.id} />
}
