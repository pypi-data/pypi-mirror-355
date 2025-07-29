import GroupDetailView from "@/components/group-detail-view"
import {useParams} from "react-router";

export default function GroupDetailPage() {
  const params = useParams() as { id: string }
  return <GroupDetailView groupId={params.id} />
}
