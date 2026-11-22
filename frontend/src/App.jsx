import { createContext, useContext, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { session } from "./api.js";
import Layout from "./components/Layout.jsx";
import Login from "./pages/Login.jsx";
import Verify from "./pages/Verify.jsx";
import Assistant from "./pages/Assistant.jsx";
import Employees from "./pages/Employees.jsx";
import Training from "./pages/Training.jsx";
import Policies from "./pages/Policies.jsx";
import Logs from "./pages/Logs.jsx";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

function RequireAuth({ children, admin }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (admin && user.role !== "admin") return <Navigate to="/verify" replace />;
  return children;
}

export default function App() {
  const [user, setUser] = useState(session.user);
  const auth = {
    user,
    signIn(data) {
      session.save(data);
      setUser(session.user);
    },
    signOut() {
      session.clear();
      setUser(null);
    },
  };
  const page = (el, admin = false) => (
    <RequireAuth admin={admin}>
      <Layout>{el}</Layout>
    </RequireAuth>
  );
  return (
    <AuthContext.Provider value={auth}>
      <Routes>
        <Route path="/login" element={user ? <Navigate to="/verify" replace /> : <Login />} />
        <Route path="/verify" element={page(<Verify />)} />
        <Route path="/assistant" element={page(<Assistant />)} />
        <Route path="/policies" element={page(<Policies />)} />
        <Route path="/employees" element={page(<Employees />, true)} />
        <Route path="/training" element={page(<Training />, true)} />
        <Route path="/logs" element={page(<Logs />, true)} />
        <Route path="*" element={<Navigate to={user ? "/verify" : "/login"} replace />} />
      </Routes>
    </AuthContext.Provider>
  );
}
