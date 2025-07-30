import ExecutionDetailView from "@/components/execution-detail-view.tsx";
import {useParams} from "react-router";

export default function ExecutionDetailPage() {
  const params = useParams() as {id: string}
  return <ExecutionDetailView flowRunId={params.id} />
}
