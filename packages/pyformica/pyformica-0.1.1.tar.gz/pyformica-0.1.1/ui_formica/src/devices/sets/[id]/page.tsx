import {useParams} from "react-router";
import DeviceSetDetailView from "@/components/device-set-detail-view.tsx";

export default function DeviceSetDetailPage() {
  const param = useParams() as { id: string }
  return <DeviceSetDetailView deviceSetId={param.id} />
}
