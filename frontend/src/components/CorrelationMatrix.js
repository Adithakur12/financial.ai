import React, { useState, useEffect, useCallback } from 'react';
import Plot from 'react-plotly.js';
import axios from 'axios';
import { Network, RefreshCw } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CorrelationMatrix = () => {
  const [correlationData, setCorrelationData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchCorrelationData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const startTime = performance.now();
      
      const response = await axios.get(`${API}/analytics/correlation`, {
        timeout: 15000
      });
      
      const endTime = performance.now();
      console.log(`Correlation data loaded in ${Math.round(endTime - startTime)}ms`);
      
      setCorrelationData(response.data);
      
    } catch (err) {
      console.error('Error fetching correlation data:', err);
      setError('Failed to load correlation matrix');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCorrelationData();
    
    // Auto-refresh every 2 minutes
    const interval = setInterval(fetchCorrelationData, 120000);
    return () => clearInterval(interval);
  }, [fetchCorrelationData]);

  const chartConfig = {
    displayModeBar: true,
    modeBarButtonsToRemove: [
      'pan2d', 'select2d', 'lasso2d', 'resetScale2d', 'zoomOut2d'
    ],
    displaylogo: false,
    responsive: true
  };

  const layoutConfig = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: {
      family: 'Inter, system-ui, sans-serif',
      size: 11,
      color: '#374151'
    },
    margin: { l: 60, r: 30, t: 20, b: 60 },
    showlegend: false,
    hovermode: 'closest'
  };

  if (loading) {
    return (
      <div className="h-96 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Calculating correlations...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-96 flex items-center justify-center">
        <div className="text-center text-red-500">
          <Network size={48} className="mx-auto mb-4 opacity-50" />
          <p className="font-medium">{error}</p>
          <button 
            onClick={fetchCorrelationData}
            className="btn-primary mt-4 flex items-center space-x-2 mx-auto"
          >
            <RefreshCw size={14} />
            <span>Retry</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Network size={16} className="text-gray-500" />
          <span className="text-sm text-gray-600">Stock Price Correlations</span>
        </div>
        <button
          onClick={fetchCorrelationData}
          disabled={loading}
          className="text-sm text-gray-500 hover:text-gray-700 flex items-center space-x-1"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          <span>Refresh</span>
        </button>
      </div>
      
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        {correlationData && (
          <Plot
            data={correlationData.data}
            layout={{
              ...correlationData.layout,
              ...layoutConfig,
              height: 350,
              title: {
                text: 'Stock Price Correlation Matrix',
                font: { size: 14, color: '#1f2937' },
                x: 0
              }
            }}
            config={chartConfig}
            style={{ width: '100%', height: '350px' }}
            useResizeHandler={true}
          />
        )}
      </div>
      
      <div className="text-xs text-gray-500 text-center">
        Blue indicates positive correlation • Red indicates negative correlation
      </div>
    </div>
  );
};

export default CorrelationMatrix;