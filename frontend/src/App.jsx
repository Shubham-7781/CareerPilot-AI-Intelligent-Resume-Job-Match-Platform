import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import VerifyEmail from "./pages/VerifyEmail";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import Dashboard from "./pages/Dashboard";
import Upload from "./pages/Upload";
import ResumeDetail from "./pages/ResumeDetail";
import JobSearch from "./pages/JobSearch";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Navbar />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/verify-email" element={<VerifyEmail />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route
            path="/dashboard"
            element={<ProtectedRoute><Dashboard /></ProtectedRoute>}
          />
          <Route
            path="/upload"
            element={<ProtectedRoute><Upload /></ProtectedRoute>}
          />
          <Route
            path="/resumes/:id"
            element={<ProtectedRoute><ResumeDetail /></ProtectedRoute>}
          />
          <Route
            path="/jobs"
            element={<ProtectedRoute><JobSearch /></ProtectedRoute>}
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
