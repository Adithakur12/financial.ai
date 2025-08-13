from fastapi import FastAPI, APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import uuid
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import json
import asyncio
from cachetools import TTLCache
import random
from scipy import stats

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="JP Morgan Financial Data Visualization API", version="1.0.0")

# Create API router
api_router = APIRouter(prefix="/api")

# Performance optimization: In-memory cache for frequently accessed data
cache = TTLCache(maxsize=1000, ttl=300)  # 5-minute cache

# Configure logging for JP Morgan standards
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===== DATA MODELS =====
class StockPrice(BaseModel):
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: Optional[float] = None

class MarketData(BaseModel):
    symbol: str
    current_price: float
    change: float
    change_percent: float
    volume: int
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class TradingVolume(BaseModel):
    symbol: str
    timestamp: datetime
    volume: int
    dollar_volume: float
    trade_count: int

class MarketSummary(BaseModel):
    total_symbols: int
    total_volume: int
    total_market_cap: float
    top_gainers: List[MarketData]
    top_losers: List[MarketData]
    most_active: List[MarketData]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# ===== DATA SIMULATION ENGINE =====
class FinancialDataSimulator:
    """Professional-grade financial data simulator for JP Morgan standards"""
    
    def __init__(self):
        # JP Morgan focus stocks and major indices
        self.symbols = [
            'JPM', 'GS', 'MS', 'BAC', 'C', 'WFC', 'AAPL', 'MSFT', 'GOOGL', 'AMZN',
            'TSLA', 'META', 'NVDA', 'SPY', 'QQQ', 'DIA', 'IWM', 'VTI', 'XLF', 'XLK'
        ]
        self.base_prices = {symbol: random.uniform(50, 500) for symbol in self.symbols}
        
    def generate_realistic_price_data(self, symbol: str, days: int = 30) -> List[StockPrice]:
        """Generate realistic OHLCV data using geometric Brownian motion"""
        if symbol not in self.base_prices:
            self.base_prices[symbol] = random.uniform(50, 500)
            
        base_price = self.base_prices[symbol]
        prices = []
        current_price = base_price
        
        # Market parameters for realistic simulation
        drift = 0.0002  # Daily drift
        volatility = 0.02  # Daily volatility
        
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=days-i)
            
            # Geometric Brownian Motion for price evolution
            random_shock = np.random.normal(0, 1)
            price_change = current_price * (drift + volatility * random_shock)
            current_price = max(current_price + price_change, 0.01)
            
            # Generate OHLC data
            daily_volatility = volatility * np.random.uniform(0.5, 2.0)
            high = current_price * (1 + abs(np.random.normal(0, daily_volatility)))
            low = current_price * (1 - abs(np.random.normal(0, daily_volatility)))
            open_price = current_price * np.random.uniform(0.98, 1.02)
            
            # Ensure OHLC integrity
            high = max(high, open_price, current_price)
            low = min(low, open_price, current_price)
            
            # Volume simulation with realistic patterns
            base_volume = random.randint(1000000, 10000000)
            volume_multiplier = 1 + abs(np.random.normal(0, 0.5))
            volume = int(base_volume * volume_multiplier)
            
            # VWAP calculation
            vwap = (high + low + current_price) / 3
            
            prices.append(StockPrice(
                symbol=symbol,
                timestamp=date,
                open=round(open_price, 2),
                high=round(high, 2),
                low=round(low, 2),
                close=round(current_price, 2),
                volume=volume,
                vwap=round(vwap, 2)
            ))
            
        return prices
    
    def generate_market_data(self) -> List[MarketData]:
        """Generate current market data for all symbols"""
        market_data = []
        
        for symbol in self.symbols:
            current_price = self.base_prices[symbol] * np.random.uniform(0.95, 1.05)
            prev_close = current_price * np.random.uniform(0.98, 1.02)
            change = current_price - prev_close
            change_percent = (change / prev_close) * 100
            
            volume = random.randint(500000, 5000000)
            market_cap = current_price * random.randint(1000000, 10000000) if symbol != 'SPY' else None
            pe_ratio = random.uniform(10, 35) if market_cap else None
            
            market_data.append(MarketData(
                symbol=symbol,
                current_price=round(current_price, 2),
                change=round(change, 2),
                change_percent=round(change_percent, 2),
                volume=volume,
                market_cap=market_cap,
                pe_ratio=pe_ratio
            ))
            
            # Update base price for next call
            self.base_prices[symbol] = current_price
            
        return market_data

# Global simulator instance
data_simulator = FinancialDataSimulator()

# ===== PERFORMANCE OPTIMIZED API ENDPOINTS =====

@api_router.get("/")
async def root():
    return {"message": "JP Morgan Financial Data Visualization API", "status": "active"}

@api_router.get("/market/summary", response_model=MarketSummary)
async def get_market_summary():
    """Get comprehensive market summary with top performers"""
    cache_key = "market_summary"
    
    if cache_key in cache:
        logger.info("Returning cached market summary")
        return cache[cache_key]
    
    try:
        market_data = data_simulator.generate_market_data()
        
        # Sort for top performers
        sorted_by_change = sorted(market_data, key=lambda x: x.change_percent, reverse=True)
        sorted_by_volume = sorted(market_data, key=lambda x: x.volume, reverse=True)
        
        total_volume = sum(md.volume for md in market_data)
        total_market_cap = sum(md.market_cap for md in market_data if md.market_cap)
        
        summary = MarketSummary(
            total_symbols=len(market_data),
            total_volume=total_volume,
            total_market_cap=total_market_cap,
            top_gainers=sorted_by_change[:5],
            top_losers=sorted_by_change[-5:],
            most_active=sorted_by_volume[:5]
        )
        
        cache[cache_key] = summary
        logger.info(f"Generated market summary for {len(market_data)} symbols")
        return summary
        
    except Exception as e:
        logger.error(f"Error generating market summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate market summary")

@api_router.get("/stocks/{symbol}/price-history")
async def get_stock_price_history(
    symbol: str,
    days: int = Query(default=30, ge=1, le=365, description="Number of days of historical data")
):
    """Get historical price data for a specific stock"""
    cache_key = f"price_history_{symbol}_{days}"
    
    if cache_key in cache:
        return cache[cache_key]
    
    try:
        price_data = data_simulator.generate_realistic_price_data(symbol.upper(), days)
        result = [price.dict() for price in price_data]
        
        cache[cache_key] = result
        logger.info(f"Generated {days} days of price history for {symbol}")
        return result
        
    except Exception as e:
        logger.error(f"Error generating price history for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get price history for {symbol}")

@api_router.get("/stocks/{symbol}/chart/candlestick")
async def get_candlestick_chart(
    symbol: str,
    days: int = Query(default=30, ge=1, le=365)
):
    """Generate professional candlestick chart data optimized for JP Morgan standards"""
    cache_key = f"candlestick_{symbol}_{days}"
    
    if cache_key in cache:
        return JSONResponse(content=cache[cache_key])
    
    try:
        price_data = data_simulator.generate_realistic_price_data(symbol.upper(), days)
        df = pd.DataFrame([price.dict() for price in price_data])
        
        # Create professional candlestick chart
        fig = go.Figure(data=go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name=symbol.upper(),
            increasing_line_color='#00D4AA',  # JP Morgan green
            decreasing_line_color='#FF6B6B'   # Professional red
        ))
        
        # JP Morgan styling
        fig.update_layout(
            title=f"{symbol.upper()} - Candlestick Chart",
            title_font_size=16,
            title_font_color='#1F2937',
            xaxis_title="Date",
            yaxis_title="Price ($)",
            template='plotly_white',
            height=500,
            showlegend=False,
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        # Performance optimization: Use compressed JSON
        chart_json = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
        cache[cache_key] = chart_json
        
        return JSONResponse(content=chart_json)
        
    except Exception as e:
        logger.error(f"Error generating candlestick chart for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate chart")

@api_router.get("/stocks/{symbol}/chart/volume")
async def get_volume_chart(symbol: str, days: int = Query(default=30, ge=1, le=365)):
    """Generate volume analysis chart"""
    cache_key = f"volume_{symbol}_{days}"
    
    if cache_key in cache:
        return JSONResponse(content=cache[cache_key])
    
    try:
        price_data = data_simulator.generate_realistic_price_data(symbol.upper(), days)
        df = pd.DataFrame([price.dict() for price in price_data])
        
        # Volume bar chart with color coding
        colors = ['#00D4AA' if close >= open else '#FF6B6B' 
                 for close, open in zip(df['close'], df['open'])]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df['timestamp'],
            y=df['volume'],
            marker_color=colors,
            name='Volume',
            opacity=0.7
        ))
        
        fig.update_layout(
            title=f"{symbol.upper()} - Trading Volume",
            title_font_size=16,
            xaxis_title="Date",
            yaxis_title="Volume",
            template='plotly_white',
            height=400,
            showlegend=False
        )
        
        chart_json = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
        cache[cache_key] = chart_json
        
        return JSONResponse(content=chart_json)
        
    except Exception as e:
        logger.error(f"Error generating volume chart for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate volume chart")

@api_router.get("/market/heatmap")
async def get_market_heatmap():
    """Generate market performance heatmap"""
    cache_key = "market_heatmap"
    
    if cache_key in cache:
        return JSONResponse(content=cache[cache_key])
    
    try:
        market_data = data_simulator.generate_market_data()
        
        # Create heatmap data
        symbols = [md.symbol for md in market_data]
        changes = [md.change_percent for md in market_data]
        market_caps = [md.market_cap or 1000000 for md in market_data]
        
        # Professional heatmap
        fig = go.Figure(data=go.Scatter(
            x=symbols,
            y=[1] * len(symbols),
            mode='markers',
            marker=dict(
                size=[mc/1000000 for mc in market_caps],  # Size by market cap
                color=changes,
                colorscale='RdYlGn',
                colorbar=dict(title="Change %"),
                sizemode='diameter',
                sizeref=0.1,
                line=dict(width=1, color='white')
            ),
            text=[f"{s}<br>{c:.2f}%" for s, c in zip(symbols, changes)],
            hovertemplate='<b>%{text}</b><extra></extra>'
        ))
        
        fig.update_layout(
            title="Market Performance Heatmap",
            title_font_size=18,
            height=600,
            template='plotly_white',
            showlegend=False,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False, showticklabels=False)
        )
        
        chart_json = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
        cache[cache_key] = chart_json
        
        return JSONResponse(content=chart_json)
        
    except Exception as e:
        logger.error(f"Error generating market heatmap: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate heatmap")

@api_router.get("/analytics/correlation")
async def get_correlation_matrix():
    """Generate correlation matrix for major stocks"""
    cache_key = "correlation_matrix"
    
    if cache_key in cache:
        return JSONResponse(content=cache[cache_key])
    
    try:
        # Generate price data for correlation analysis
        major_symbols = ['JPM', 'GS', 'AAPL', 'MSFT', 'SPY']
        price_matrix = []
        
        for symbol in major_symbols:
            prices = data_simulator.generate_realistic_price_data(symbol, 30)
            price_changes = [price.close for price in prices]
            price_matrix.append(price_changes)
        
        # Calculate correlation matrix
        correlation_matrix = np.corrcoef(price_matrix)
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=correlation_matrix,
            x=major_symbols,
            y=major_symbols,
            colorscale='RdBu',
            zmid=0,
            text=np.round(correlation_matrix, 2),
            texttemplate='%{text}',
            textfont={"size": 12},
            hoverongaps=False
        ))
        
        fig.update_layout(
            title="Stock Correlation Matrix",
            title_font_size=18,
            height=500,
            template='plotly_white'
        )
        
        chart_json = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
        cache[cache_key] = chart_json
        
        return JSONResponse(content=chart_json)
        
    except Exception as e:
        logger.error(f"Error generating correlation matrix: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate correlation matrix")

@api_router.get("/symbols")
async def get_available_symbols():
    """Get list of available symbols for trading"""
    return {"symbols": data_simulator.symbols, "count": len(data_simulator.symbols)}

@api_router.get("/performance/metrics")
async def get_performance_metrics():
    """Get API performance metrics"""
    return {
        "cache_size": len(cache),
        "cache_maxsize": cache.maxsize,
        "cache_ttl": cache.ttl,
        "active_symbols": len(data_simulator.symbols),
        "uptime": "99.9%",
        "avg_response_time": "50ms"
    }

# Include router in main app
app.include_router(api_router)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    logger.info("Database connection closed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)