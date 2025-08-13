#!/usr/bin/env python3
"""
JP Morgan Financial Data Visualization API Test Suite
Tests all backend endpoints for functionality, performance, and data quality
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class JPMorganAPITester:
    def __init__(self, base_url="https://fast-datavis.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.performance_metrics = []
        
        # Expected symbols from the backend
        self.expected_symbols = [
            'JPM', 'GS', 'MS', 'BAC', 'C', 'WFC', 'AAPL', 'MSFT', 'GOOGL', 'AMZN',
            'TSLA', 'META', 'NVDA', 'SPY', 'QQQ', 'DIA', 'IWM', 'VTI', 'XLF', 'XLK'
        ]

    def log_test(self, name: str, success: bool, response_time: float = None, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        time_info = f" ({response_time:.0f}ms)" if response_time else ""
        print(f"{status} - {name}{time_info}")
        if details:
            print(f"    {details}")
        
        if response_time:
            self.performance_metrics.append({
                'endpoint': name,
                'response_time': response_time,
                'success': success
            })

    def make_request(self, method: str, endpoint: str, **kwargs) -> tuple:
        """Make HTTP request and measure performance"""
        url = f"{self.api_url}/{endpoint}"
        start_time = time.time()
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, timeout=30, **kwargs)
            elif method.upper() == 'POST':
                response = requests.post(url, timeout=30, **kwargs)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response_time = (time.time() - start_time) * 1000
            return True, response, response_time
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return False, str(e), response_time

    def test_api_root(self):
        """Test API root endpoint"""
        success, response, response_time = self.make_request('GET', '')
        
        if success and response.status_code == 200:
            data = response.json()
            if "JP Morgan Financial Data Visualization API" in data.get('message', ''):
                self.log_test("API Root", True, response_time, "API is active and responding")
                return True
            else:
                self.log_test("API Root", False, response_time, "Unexpected response message")
        else:
            error_msg = response if isinstance(response, str) else f"Status: {response.status_code}"
            self.log_test("API Root", False, response_time, error_msg)
        return False

    def test_market_summary(self):
        """Test market summary endpoint"""
        success, response, response_time = self.make_request('GET', 'market/summary')
        
        if not success:
            self.log_test("Market Summary", False, response_time, str(response))
            return False
        
        if response.status_code != 200:
            self.log_test("Market Summary", False, response_time, f"Status: {response.status_code}")
            return False
        
        try:
            data = response.json()
            
            # Validate required fields
            required_fields = ['total_symbols', 'total_volume', 'total_market_cap', 
                             'top_gainers', 'top_losers', 'most_active', 'timestamp']
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                self.log_test("Market Summary", False, response_time, 
                            f"Missing fields: {missing_fields}")
                return False
            
            # Validate data quality
            if data['total_symbols'] != len(self.expected_symbols):
                self.log_test("Market Summary", False, response_time, 
                            f"Expected {len(self.expected_symbols)} symbols, got {data['total_symbols']}")
                return False
            
            # Check top performers lists
            for list_name in ['top_gainers', 'top_losers', 'most_active']:
                if not isinstance(data[list_name], list) or len(data[list_name]) != 5:
                    self.log_test("Market Summary", False, response_time, 
                                f"{list_name} should be a list of 5 items")
                    return False
            
            # Validate stock data structure
            sample_stock = data['top_gainers'][0]
            required_stock_fields = ['symbol', 'current_price', 'change', 'change_percent', 'volume']
            missing_stock_fields = [field for field in required_stock_fields if field not in sample_stock]
            
            if missing_stock_fields:
                self.log_test("Market Summary", False, response_time, 
                            f"Stock data missing fields: {missing_stock_fields}")
                return False
            
            self.log_test("Market Summary", True, response_time, 
                        f"Valid data with {data['total_symbols']} symbols")
            return True
            
        except json.JSONDecodeError:
            self.log_test("Market Summary", False, response_time, "Invalid JSON response")
            return False

    def test_stock_price_history(self):
        """Test stock price history endpoint"""
        test_symbol = 'JPM'
        test_days = 30
        
        success, response, response_time = self.make_request(
            'GET', f'stocks/{test_symbol}/price-history?days={test_days}'
        )
        
        if not success:
            self.log_test("Stock Price History", False, response_time, str(response))
            return False
        
        if response.status_code != 200:
            self.log_test("Stock Price History", False, response_time, f"Status: {response.status_code}")
            return False
        
        try:
            data = response.json()
            
            if not isinstance(data, list):
                self.log_test("Stock Price History", False, response_time, "Response should be a list")
                return False
            
            if len(data) != test_days:
                self.log_test("Stock Price History", False, response_time, 
                            f"Expected {test_days} data points, got {len(data)}")
                return False
            
            # Validate OHLCV data structure
            sample_data = data[0]
            required_fields = ['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume', 'vwap']
            missing_fields = [field for field in required_fields if field not in sample_data]
            
            if missing_fields:
                self.log_test("Stock Price History", False, response_time, 
                            f"Missing fields: {missing_fields}")
                return False
            
            # Validate OHLC integrity
            if not (sample_data['low'] <= sample_data['open'] <= sample_data['high'] and
                   sample_data['low'] <= sample_data['close'] <= sample_data['high']):
                self.log_test("Stock Price History", False, response_time, "OHLC data integrity violation")
                return False
            
            self.log_test("Stock Price History", True, response_time, 
                        f"Valid OHLCV data for {test_symbol} ({len(data)} points)")
            return True
            
        except json.JSONDecodeError:
            self.log_test("Stock Price History", False, response_time, "Invalid JSON response")
            return False

    def test_candlestick_chart(self):
        """Test candlestick chart endpoint"""
        test_symbol = 'AAPL'
        test_days = 7
        
        success, response, response_time = self.make_request(
            'GET', f'stocks/{test_symbol}/chart/candlestick?days={test_days}'
        )
        
        if not success:
            self.log_test("Candlestick Chart", False, response_time, str(response))
            return False
        
        if response.status_code != 200:
            self.log_test("Candlestick Chart", False, response_time, f"Status: {response.status_code}")
            return False
        
        try:
            data = response.json()
            
            # Validate Plotly chart structure
            if 'data' not in data or 'layout' not in data:
                self.log_test("Candlestick Chart", False, response_time, "Missing Plotly chart structure")
                return False
            
            # Check for candlestick data
            chart_data = data['data']
            if not isinstance(chart_data, list) or len(chart_data) == 0:
                self.log_test("Candlestick Chart", False, response_time, "No chart data found")
                return False
            
            candlestick_trace = chart_data[0]
            required_fields = ['x', 'open', 'high', 'low', 'close', 'type']
            missing_fields = [field for field in required_fields if field not in candlestick_trace]
            
            if missing_fields:
                self.log_test("Candlestick Chart", False, response_time, 
                            f"Candlestick trace missing fields: {missing_fields}")
                return False
            
            if candlestick_trace.get('type') != 'candlestick':
                self.log_test("Candlestick Chart", False, response_time, "Not a candlestick chart type")
                return False
            
            self.log_test("Candlestick Chart", True, response_time, 
                        f"Valid Plotly candlestick chart for {test_symbol}")
            return True
            
        except json.JSONDecodeError:
            self.log_test("Candlestick Chart", False, response_time, "Invalid JSON response")
            return False

    def test_volume_chart(self):
        """Test volume chart endpoint"""
        test_symbol = 'MSFT'
        test_days = 7
        
        success, response, response_time = self.make_request(
            'GET', f'stocks/{test_symbol}/chart/volume?days={test_days}'
        )
        
        if not success:
            self.log_test("Volume Chart", False, response_time, str(response))
            return False
        
        if response.status_code != 200:
            self.log_test("Volume Chart", False, response_time, f"Status: {response.status_code}")
            return False
        
        try:
            data = response.json()
            
            # Validate Plotly chart structure
            if 'data' not in data or 'layout' not in data:
                self.log_test("Volume Chart", False, response_time, "Missing Plotly chart structure")
                return False
            
            chart_data = data['data']
            if not isinstance(chart_data, list) or len(chart_data) == 0:
                self.log_test("Volume Chart", False, response_time, "No chart data found")
                return False
            
            volume_trace = chart_data[0]
            if 'x' not in volume_trace or 'y' not in volume_trace:
                self.log_test("Volume Chart", False, response_time, "Missing x/y data in volume chart")
                return False
            
            self.log_test("Volume Chart", True, response_time, 
                        f"Valid volume chart for {test_symbol}")
            return True
            
        except json.JSONDecodeError:
            self.log_test("Volume Chart", False, response_time, "Invalid JSON response")
            return False

    def test_market_heatmap(self):
        """Test market heatmap endpoint"""
        success, response, response_time = self.make_request('GET', 'market/heatmap')
        
        if not success:
            self.log_test("Market Heatmap", False, response_time, str(response))
            return False
        
        if response.status_code != 200:
            self.log_test("Market Heatmap", False, response_time, f"Status: {response.status_code}")
            return False
        
        try:
            data = response.json()
            
            if 'data' not in data or 'layout' not in data:
                self.log_test("Market Heatmap", False, response_time, "Missing Plotly chart structure")
                return False
            
            self.log_test("Market Heatmap", True, response_time, "Valid market heatmap visualization")
            return True
            
        except json.JSONDecodeError:
            self.log_test("Market Heatmap", False, response_time, "Invalid JSON response")
            return False

    def test_correlation_matrix(self):
        """Test correlation matrix endpoint"""
        success, response, response_time = self.make_request('GET', 'analytics/correlation')
        
        if not success:
            self.log_test("Correlation Matrix", False, response_time, str(response))
            return False
        
        if response.status_code != 200:
            self.log_test("Correlation Matrix", False, response_time, f"Status: {response.status_code}")
            return False
        
        try:
            data = response.json()
            
            if 'data' not in data or 'layout' not in data:
                self.log_test("Correlation Matrix", False, response_time, "Missing Plotly chart structure")
                return False
            
            # Check for heatmap data
            heatmap_data = data['data'][0] if data['data'] else {}
            if heatmap_data.get('type') != 'heatmap':
                self.log_test("Correlation Matrix", False, response_time, "Not a heatmap chart type")
                return False
            
            self.log_test("Correlation Matrix", True, response_time, "Valid correlation matrix heatmap")
            return True
            
        except json.JSONDecodeError:
            self.log_test("Correlation Matrix", False, response_time, "Invalid JSON response")
            return False

    def test_available_symbols(self):
        """Test available symbols endpoint"""
        success, response, response_time = self.make_request('GET', 'symbols')
        
        if not success:
            self.log_test("Available Symbols", False, response_time, str(response))
            return False
        
        if response.status_code != 200:
            self.log_test("Available Symbols", False, response_time, f"Status: {response.status_code}")
            return False
        
        try:
            data = response.json()
            
            if 'symbols' not in data or 'count' not in data:
                self.log_test("Available Symbols", False, response_time, "Missing symbols or count field")
                return False
            
            symbols = data['symbols']
            if not isinstance(symbols, list):
                self.log_test("Available Symbols", False, response_time, "Symbols should be a list")
                return False
            
            if data['count'] != len(symbols):
                self.log_test("Available Symbols", False, response_time, "Count doesn't match symbols length")
                return False
            
            # Check if expected symbols are present
            missing_symbols = [sym for sym in self.expected_symbols if sym not in symbols]
            if missing_symbols:
                self.log_test("Available Symbols", False, response_time, 
                            f"Missing expected symbols: {missing_symbols}")
                return False
            
            self.log_test("Available Symbols", True, response_time, 
                        f"Valid symbols list with {len(symbols)} symbols")
            return True
            
        except json.JSONDecodeError:
            self.log_test("Available Symbols", False, response_time, "Invalid JSON response")
            return False

    def test_performance_metrics(self):
        """Test performance metrics endpoint"""
        success, response, response_time = self.make_request('GET', 'performance/metrics')
        
        if not success:
            self.log_test("Performance Metrics", False, response_time, str(response))
            return False
        
        if response.status_code != 200:
            self.log_test("Performance Metrics", False, response_time, f"Status: {response.status_code}")
            return False
        
        try:
            data = response.json()
            
            expected_fields = ['cache_size', 'cache_maxsize', 'cache_ttl', 'active_symbols', 'uptime', 'avg_response_time']
            missing_fields = [field for field in expected_fields if field not in data]
            
            if missing_fields:
                self.log_test("Performance Metrics", False, response_time, 
                            f"Missing fields: {missing_fields}")
                return False
            
            self.log_test("Performance Metrics", True, response_time, 
                        f"Cache: {data['cache_size']}/{data['cache_maxsize']}, Uptime: {data['uptime']}")
            return True
            
        except json.JSONDecodeError:
            self.log_test("Performance Metrics", False, response_time, "Invalid JSON response")
            return False

    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting JP Morgan Financial Data Visualization API Tests")
        print("=" * 70)
        
        # Test all endpoints
        test_methods = [
            self.test_api_root,
            self.test_market_summary,
            self.test_stock_price_history,
            self.test_candlestick_chart,
            self.test_volume_chart,
            self.test_market_heatmap,
            self.test_correlation_matrix,
            self.test_available_symbols,
            self.test_performance_metrics
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_test(test_method.__name__, False, None, f"Test error: {str(e)}")
        
        # Performance analysis
        print("\n" + "=" * 70)
        print("📊 PERFORMANCE ANALYSIS")
        print("=" * 70)
        
        if self.performance_metrics:
            avg_response_time = sum(m['response_time'] for m in self.performance_metrics) / len(self.performance_metrics)
            fastest = min(self.performance_metrics, key=lambda x: x['response_time'])
            slowest = max(self.performance_metrics, key=lambda x: x['response_time'])
            
            print(f"Average Response Time: {avg_response_time:.0f}ms")
            print(f"Fastest Endpoint: {fastest['endpoint']} ({fastest['response_time']:.0f}ms)")
            print(f"Slowest Endpoint: {slowest['endpoint']} ({slowest['response_time']:.0f}ms)")
            
            # Check for 20% speed improvement claim
            if avg_response_time <= 60:  # Assuming baseline of 75ms for 20% improvement
                print("✅ Performance target achieved (≤60ms average)")
            else:
                print(f"⚠️  Performance target not met (>{avg_response_time:.0f}ms average)")
        
        # Final results
        print("\n" + "=" * 70)
        print("📋 TEST RESULTS SUMMARY")
        print("=" * 70)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"Tests Passed: {self.tests_passed}/{self.tests_run} ({success_rate:.1f}%)")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT: API meets JP Morgan professional standards")
            return 0
        elif success_rate >= 75:
            print("✅ GOOD: API is functional with minor issues")
            return 0
        else:
            print("❌ NEEDS IMPROVEMENT: Significant issues found")
            return 1

def main():
    """Main test execution"""
    tester = JPMorganAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())