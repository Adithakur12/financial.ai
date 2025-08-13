import React from 'react';
import { Search, ChevronDown } from 'lucide-react';

const SymbolSelector = ({ symbols, selectedSymbol, onSymbolChange }) => {
  return (
    <div className="relative">
      <div className="flex items-center space-x-2">
        <Search size={16} className="text-gray-400" />
        <select
          value={selectedSymbol}
          onChange={(e) => onSymbolChange(e.target.value)}
          className="appearance-none bg-white border border-gray-300 rounded-lg px-4 py-2 pr-8 text-sm font-medium text-gray-700 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
        >
          {symbols.map((symbol) => (
            <option key={symbol} value={symbol}>
              {symbol}
            </option>
          ))}
        </select>
        <ChevronDown size={16} className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 pointer-events-none" />
      </div>
    </div>
  );
};

export default SymbolSelector;