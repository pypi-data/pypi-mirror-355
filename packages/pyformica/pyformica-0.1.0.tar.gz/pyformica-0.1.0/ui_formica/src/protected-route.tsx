import { Navigate, Outlet } from "react-router";
import { jwtDecode } from "jwt-decode";
import { getToken } from "./lib/auth";

const isTokenValid = () => {
  const token = getToken();
  if (!token) return false;

  try {
    const { exp } = jwtDecode<{ exp: number }>(token);
    console.log(exp)
    console.log(Math.floor(Date.now() / 1000))
    return exp > Math.floor(Date.now() / 1000);
  } catch {
    return false;
  }
};

export const ProtectedRoute = () => {
  if (!isTokenValid()) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet/>
};