import {useParams} from "react-router";
import DeviceRunDetailView from "@/components/device-run-detail-view.tsx";

export default function DeviceRunDetailPage() {
  const params = useParams() as { id: string, deviceRunId: string }
  return <DeviceRunDetailView flowRunId={params.id} deviceRunId={params.deviceRunId} />
}
