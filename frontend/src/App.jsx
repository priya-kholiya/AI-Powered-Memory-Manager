import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import Dashboard from "./components/dashboard/Dashboard";
import Algorithms from "./components/dashboard/Algorithms";
import Login from "./components/dashboard/Login";

import "./App.css";

function App() {
  // Initialize user state from localStorage
  const [user, setUser] = useState(null);

  // Load user from localStorage on app mount
  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
  }, []);

  // Login handler
  const handleLogin = (loggedInUser) => {
    localStorage.setItem("user", JSON.stringify(loggedInUser));
    setUser(loggedInUser);
  };

  // Logout handler
  const handleLogout = () => {
    localStorage.removeItem("user");
    setUser(null);
  };

  return (
    <BrowserRouter>
      <Routes>
        {/* Login Page */}
        <Route
          path="/login"
          element={user ? <Navigate to="/" /> : <Login onLogin={handleLogin} />}
        />

        {/* Dashboard (protected) */}
        <Route
          path="/"
          element={user ? <Dashboard user={user} onLogout={handleLogout} /> : <Navigate to="/login" />}
        />

        {/* Algorithms Page (protected) */}
        <Route
          path="/dashboard/algorithms"
          element={user ? <Algorithms user={user} /> : <Navigate to="/login" />}
        />

        {/* Fallback for unknown routes */}
        <Route
          path="*"
          element={user ? <Navigate to="/" /> : <Navigate to="/login" />}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
