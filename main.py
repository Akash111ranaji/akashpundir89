from fastapi import FastAPI
from fastapi.responses import JSONResponse, HTMLResponse
import httpx

app = FastAPI()

@app.get("/losers")
async def get_derivative_losers():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "price_change_percentage_15m_asc",
        "per_page": 250,
        "page": 1,
        "price_change_percentage": "15m"
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        data = resp.json()

    filtered = []
    for token in data:
        try:
            change = token.get("price_change_percentage_15m_in_currency")
            volume = token.get("total_volume", 0)

            # Relaxed test conditions
            if (
                change is not None and
                change < -1 and
                volume is not None and
                volume > 1000000
            ):
                filtered.append({
                    "name": token["name"],
                    "symbol": token["symbol"],
                    "price": token["current_price"],
                    "change_15m": change,
                    "volume_24h": volume,
                    "market_cap": token.get("market_cap")
                })
        except Exception:
            continue

    top_losers = filtered[:10]
    return JSONResponse(top_losers)

@app.get("/", response_class=HTMLResponse)
async def index():
    return '''
<html>
<head><title>Top Derivative Losers</title></head>
<body>
  <h1>🔻 Top 10 Derivatives Tokens (Drop ≥ 1% in 15 min, Vol > $1M)</h1>
  <ul id="list"></ul>
  <script>
    async function fetchData(){
      const res = await fetch('/losers');
      const data = await res.json();
      const list = document.getElementById('list');
      list.innerHTML = data.length
        ? data.map(t => <li><b>${t.symbol.toUpperCase()}</b> — ${t.change_15m.toFixed(2)}% | Price: $${t.price} | Vol: $${(t.volume_24h/1e6).toFixed(1)}M | MC: $${(t.market_cap/1e9).toFixed(2)}B</li>).join('')
        : '<li>No qualifying tokens</li>';
    }
    fetchData();
    setInterval(fetchData, 60000);
  </script>
</body>
</html>
'''
