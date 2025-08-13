import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import './App.css';
import FinancialDashboard from './components/FinancialDashboard';

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<FinancialDashboard />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;