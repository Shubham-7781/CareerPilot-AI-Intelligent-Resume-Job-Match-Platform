import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="navbar">
      <Link to="/" className="brand">CareerPilot</Link>
      <div className="nav-links">
        {user ? (
          <>
            <Link to="/dashboard">Dashboard</Link>
            <Link to="/upload">Upload Resume</Link>
            <Link to="/jobs">Job Search</Link>
            <span className="nav-user">{user.email}</span>
            <button className="btn-link" onClick={handleLogout}>Logout</button>
          </>
        ) : (
          <>
            <Link to="/login">Login</Link>
            <Link to="/signup" className="btn-primary-sm">Sign Up</Link>
          </>
        )}
      </div>
    </nav>
  );
}
