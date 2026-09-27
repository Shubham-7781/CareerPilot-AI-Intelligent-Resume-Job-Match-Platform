import { createContext, useContext, useState, useCallback } from "react";
import { authApi } from "../api/resources";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = sessionStorage.getItem("user");
    return stored ? JSON.parse(stored) : null;
  });
  const [error, setError] = useState("");

  const login = useCallback(async (email, password) => {
    setError("");
    try {
      const { data } = await authApi.login(email, password);
      sessionStorage.setItem("access_token", data.access_token);
      sessionStorage.setItem("refresh_token", data.refresh_token);
      const fakeUser = { email };
      sessionStorage.setItem("user", JSON.stringify(fakeUser));
      setUser(fakeUser);
      return true;
    } catch (e) {
      setError(e.response?.data?.detail || "Login failed");
      return false;
    }
  }, []);

  const signup = useCallback(async (fullName, email, password) => {
    setError("");
    try {
      await authApi.signup({ full_name: fullName, email, password });
      return await login(email, password);
    } catch (e) {
      setError(e.response?.data?.detail || "Signup failed");
      return false;
    }
  }, [login]);

  const logout = useCallback(() => {
    sessionStorage.clear();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, signup, logout, error, setError }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
