import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import Dashboard from "./components/dashboard/Dashboard";
import Algorithms from "./components/dashboard/Algorithms";

import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Default Dashboard */}
        <Route path="/" element={<Dashboard />} />

        {/* Algorithm Simulator */}
        <Route path="/dashboard/algorithms" element={<Algorithms />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
