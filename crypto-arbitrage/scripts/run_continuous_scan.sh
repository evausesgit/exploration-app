#!/bin/bash

# Script pour lancer le scan continu en arrière-plan
# Usage: ./scripts/run_continuous_scan.sh (depuis la racine du projet)

echo "🚀 Starting Continuous Crypto Arbitrage Scanner..."
echo "=================================================="
echo ""
echo "📊 Configuration:"
echo "   - Exchanges: 10 (binance, kraken, coinbase, kucoin, bybit, okx, gateio, huobi, bitfinex, mexc)"
echo "   - Symbols: 25 crypto pairs"
echo "   - Scan interval: 45 seconds"
echo "   - Min profit: 0.3%"
echo ""
echo "💾 Data will be saved to: data/opportunities.db"
echo "📝 Logs will be saved to: logs/scanner.log"
echo ""
echo "⏰ Recommended: Let it run for 24-48h to accumulate good data!"
echo ""
echo "=================================================="
echo ""

# Créer les dossiers si nécessaire
mkdir -p data logs

# Lancer le scan continu en arrière-plan
# Se déplace à la racine du projet pour exécuter
cd "$(dirname "$0")/.."
nohup python3.9 scripts/main.py --watch > logs/continuous_scan.log 2>&1 &

# Sauvegarder le PID
PID=$!
echo $PID > .scanner_pid

echo "✅ Scanner started successfully!"
echo ""
echo "📊 Process ID: $PID"
echo "📝 Logs: logs/continuous_scan.log"
echo ""
echo "Commands:"
echo "   - View live logs: tail -f logs/continuous_scan.log"
echo "   - View scanner logs: tail -f logs/scanner.log"
echo "   - Stop scanner: kill $PID"
echo "   - Analyze results: python3.9 scripts/analyze_opportunities.py"
echo ""
echo "🎯 Happy hunting for opportunities! 💰"
