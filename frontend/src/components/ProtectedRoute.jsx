import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ children }) {
  const { user } = useAuth();
  const hasToken = !!sessionStorage.getItem("access_token");
  if (!user && !hasToken) {
    return <Navigate to="/login" replace />;
  }
  return children;
}
