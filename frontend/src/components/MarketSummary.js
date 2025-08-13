import React from 'react';
import { TrendingUp, TrendingDown, Activity } from 'lucide-react';

const MarketSummary = ({ marketData }) => {
  if (!marketData) {
    return (
      <div className="financial-card">
        <h2 className="text-lg font-bold text-gray-900 mb-4">Market Summary</h2>
        <div className="space-y-4">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="loading-shimmer h-16 w-full"></div>
          ))}
        </div>
      </div>
    );
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const formatVolume = (volume) => {
    return new Intl.NumberFormat('en-US', {
      notation: 'compact',
      maximumFractionDigits: 1
    }).format(volume);
  };

  const StockRow = ({ stock, icon: Icon, iconColor }) => (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors duration-200">
      <div className="flex items-center space-x-3">
        <Icon size={20} className={`text-${iconColor}-500`} />
        <div>
          <p className="font-semibold text-gray-900">{stock.symbol}</p>
          <p className="text-sm text-gray-600">{formatCurrency(stock.current_price)}</p>
        </div>
      </div>
      <div className="text-right">
        <p className={`font-semibold ${
          stock.change >= 0 ? 'metric-change-positive' : 'metric-change-negative'
        }`}>
          {stock.change >= 0 ? '+' : ''}{stock.change_percent.toFixed(2)}%
        </p>
        <p className="text-sm text-gray-600">Vol: {formatVolume(stock.volume)}</p>
      </div>
    </div>
  );

  return (
    <div className="financial-card">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-bold text-gray-900">Market Summary</h2>
        <div className="performance-indicator performance-positive">
          <span className="status-online"></span>
          Live
        </div>
      </div>

      {/* Market Overview Stats */}
      <div className="grid grid-cols-1 gap-4 mb-6">
        <div className="bg-blue-50 p-4 rounded-lg">
          <p className="text-sm font-medium text-blue-800 mb-1">Total Symbols</p>
          <p className="text-2xl font-bold text-blue-900">{marketData.total_symbols}</p>
        </div>
        
        <div className="bg-purple-50 p-4 rounded-lg">
          <p className="text-sm font-medium text-purple-800 mb-1">Market Cap</p>
          <p className="text-xl font-bold text-purple-900">
            {new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: 'USD',
              notation: 'compact',
              maximumFractionDigits: 1
            }).format(marketData.total_market_cap)}
          </p>
        </div>
        
        <div className="bg-green-50 p-4 rounded-lg">
          <p className="text-sm font-medium text-green-800 mb-1">Total Volume</p>
          <p className="text-xl font-bold text-green-900">
            {formatVolume(marketData.total_volume)}
          </p>
        </div>
      </div>

      {/* Top Gainers Section */}
      <div className="mb-6">
        <h3 className="text-md font-semibold text-gray-900 mb-3 flex items-center">
          <TrendingUp className="mr-2 text-green-500" size={18} />
          Top Gainers
        </h3>
        <div className="space-y-2">
          {marketData.top_gainers.slice(0, 3).map((stock, index) => (
            <StockRow 
              key={`gainer-${index}`} 
              stock={stock} 
              icon={TrendingUp} 
              iconColor="green" 
            />
          ))}
        </div>
      </div>

      {/* Top Losers Section */}
      <div className="mb-6">
        <h3 className="text-md font-semibold text-gray-900 mb-3 flex items-center">
          <TrendingDown className="mr-2 text-red-500" size={18} />
          Top Losers
        </h3>
        <div className="space-y-2">
          {marketData.top_losers.slice(0, 3).map((stock, index) => (
            <StockRow 
              key={`loser-${index}`} 
              stock={stock} 
              icon={TrendingDown} 
              iconColor="red" 
            />
          ))}
        </div>
      </div>

      {/* Most Active Section */}
      <div>
        <h3 className="text-md font-semibold text-gray-900 mb-3 flex items-center">
          <Activity className="mr-2 text-orange-500" size={18} />
          Most Active
        </h3>
        <div className="space-y-2">
          {marketData.most_active.slice(0, 3).map((stock, index) => (
            <StockRow 
              key={`active-${index}`} 
              stock={stock} 
              icon={Activity} 
              iconColor="orange" 
            />
          ))}
        </div>
      </div>

      {/* Last Updated */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-500 text-center">
          Last updated: {new Date(marketData.timestamp).toLocaleString()}
        </p>
      </div>
    </div>
  );
};

export default MarketSummary;