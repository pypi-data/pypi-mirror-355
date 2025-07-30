import {Navigate} from "react-router";

export default function Home() {
  // Redirect to the dashboard page
  return <Navigate to={"/dashboard"} />
}
