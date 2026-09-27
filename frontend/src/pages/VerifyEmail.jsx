import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { authApi } from "../api/resources";

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const [status, setStatus] = useState("verifying"); // verifying | success | error

  useEffect(() => {
    if (!token) {
      setStatus("error");
      return;
    }
    authApi
      .verifyEmail(token)
      .then(() => setStatus("success"))
      .catch(() => setStatus("error"));
  }, [token]);

  return (
    <div className="auth-page">
      <div className="auth-card">
        {status === "verifying" && <p>Verifying your email...</p>}
        {status === "success" && (
          <>
            <h1>Email verified ✓</h1>
            <p className="subtitle">Your account is now fully verified.</p>
            <Link className="btn-primary" to="/login">Go to Login</Link>
          </>
        )}
        {status === "error" && (
          <>
            <h1>Verification failed</h1>
            <p className="subtitle">This link is invalid or has expired.</p>
            <Link className="btn-primary" to="/login">Back to Login</Link>
          </>
        )}
      </div>
    </div>
  );
}
