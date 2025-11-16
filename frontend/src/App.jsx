import React, { useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import Dashboard from "./components/dashboard/Dashboard";
import Algorithms from "./components/dashboard/Algorithms";
import Login from "./components/dashboard/Login";

import "./App.css";

function App() {
  const [user, setUser] = useState(
    JSON.parse(localStorage.getItem("user")) || null
  );

  return (
    <BrowserRouter>

      <Routes>
        {/* Login Route */}
        <Route
          path="/login"
          element={
            user ? <Navigate to="/" /> : <Login onLogin={setUser} />
          }
        />

        {/* Protected Dashboard */}
        <Route
          path="/"
          element={
            user ? <Dashboard user={user} /> : <Navigate to="/login" />
          }
        />

        {/* Protected Algorithms Page */}
        <Route
          path="/dashboard/algorithms"
          element={
            user ? <Algorithms /> : <Navigate to="/login" />
          }
        />

        {/* If user goes to an unknown route */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>

    </BrowserRouter>
  );
}

export default App;
