import React from 'react';
import { Zap, Clock, Database, Wifi } from 'lucide-react';

const PerformanceMetrics = ({ metrics }) => {
  return (
    <div className="flex items-center space-x-4 text-sm">
      <div className="flex items-center space-x-2 bg-green-50 px-3 py-1 rounded-full">
        <Zap size={14} className="text-green-600" />
        <span className="font-medium text-green-800">+20% Speed</span>
      </div>
      
      <div className="flex items-center space-x-1 text-gray-600">
        <Clock size={14} />
        <span>{metrics.responseTime}ms</span>
      </div>
      
      <div className="flex items-center space-x-1 text-gray-600">
        <Database size={14} />
        <span>{metrics.dataPoints} symbols</span>
      </div>
      
      <div className="flex items-center space-x-1 text-gray-600">
        <Wifi size={14} />
        <span>{metrics.uptime} uptime</span>
      </div>
    </div>
  );
};

export default PerformanceMetrics;