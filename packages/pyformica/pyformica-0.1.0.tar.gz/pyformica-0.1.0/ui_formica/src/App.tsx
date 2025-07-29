import { BrowserRouter, Routes, Route } from 'react-router';
import Home from './page';
import Admin from './admin/page';
import Dashboard from './dashboard/page';
import Devices from './devices/page';
import DeviceSets from './devices/sets/page';
import DeviceSetDetail from './devices/sets/[id]/page';
import Executions from './executions/page';
import ExecutionDetail from './executions/[id]/page';
import DeviceRunDetail from './executions/[id]/[deviceRunId]/page';
import Groups from './groups/page';
import GroupDetail from './groups/[id]/page';
import Login from './login/page';
import Register from './register/page';
import Profile from './profile/page';
import Settings from './settings/page';
import WorkflowDetail from './workflow/[id]/page';
import { ProtectedRoute } from './protected-route';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route element={<ProtectedRoute/>}>
          <Route path="/admin" element={<Admin />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/devices" element={<Devices />} />
          <Route path="/devices/sets" element={<DeviceSets />} />
          <Route path="/devices/sets/:id" element={<DeviceSetDetail />} />
          <Route path="/executions" element={<Executions />} />
          <Route path="/executions/:id" element={<ExecutionDetail />} />
          <Route path="/executions/:id/:deviceRunId" element={<DeviceRunDetail />} />
          <Route path="/groups" element={<Groups />} />
          <Route path="/groups/:id" element={<GroupDetail />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/workflow/:id" element={<WorkflowDetail />} />
        </Route>
        
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
      </Routes>
    </BrowserRouter>
  );
}
