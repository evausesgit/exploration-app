"""
Script d'analyse des opportunités trouvées
Génère un rapport complet des opportunités d'arbitrage
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path


def analyze_opportunities(db_path: str = "data/opportunities.db"):
    """
    Analyse les opportunités stockées dans la base de données

    Args:
        db_path: Chemin vers la DB SQLite
    """
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        print("Run a scan first with: python main.py --scan")
        return

    # Connexion à la DB
    conn = sqlite3.connect(db_path)

    # Charge toutes les opportunités
    df = pd.read_sql_query("SELECT * FROM opportunities", conn)

    if df.empty:
        print("📊 No opportunities found in database yet.")
        print("\n💡 Tips:")
        print("   - Run a scan with: python main.py --scan")
        print("   - Or run continuous scanning: python main.py --watch")
        conn.close()
        return

    print("=" * 80)
    print("📊 CRYPTO ARBITRAGE OPPORTUNITIES REPORT")
    print("=" * 80)
    print(f"\n📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📈 Total opportunities found: {len(df)}")

    # Statistiques générales
    print("\n" + "=" * 80)
    print("📈 GENERAL STATISTICS")
    print("=" * 80)

    print(f"\n🔍 Opportunity Types:")
    if 'opportunity_type' in df.columns:
        type_counts = df['opportunity_type'].value_counts()
        for opp_type, count in type_counts.items():
            print(f"   - {opp_type}: {count}")

    print(f"\n💰 Profit Statistics:")
    if 'profit_potential' in df.columns:
        print(f"   - Average profit: {df['profit_potential'].mean():.2f}%")
        print(f"   - Median profit: {df['profit_potential'].median():.2f}%")
        print(f"   - Max profit: {df['profit_potential'].max():.2f}%")
        print(f"   - Min profit: {df['profit_potential'].min():.2f}%")

    print(f"\n📊 Confidence Statistics:")
    if 'confidence' in df.columns:
        print(f"   - Average confidence: {df['confidence'].mean():.1f}/100")
        print(f"   - High confidence (>70): {len(df[df['confidence'] > 70])} opportunities")
        print(f"   - Medium confidence (50-70): {len(df[(df['confidence'] >= 50) & (df['confidence'] <= 70)])} opportunities")

    # Top opportunités
    print("\n" + "=" * 80)
    print("🏆 TOP 10 OPPORTUNITIES (by profit)")
    print("=" * 80)

    top_10 = df.nlargest(10, 'profit_potential')
    for i, row in top_10.iterrows():
        print(f"\n{row.name + 1}. {row['symbol']}")
        print(f"   💰 Profit: {row['profit_potential']:.2f}%")
        print(f"   📊 Confidence: {row['confidence']:.0f}/100")
        print(f"   🏷️  Strategy: {row['strategy']}")
        if 'created_at' in row:
            print(f"   ⏰ Found at: {row['created_at']}")

    # Opportunités par symbole
    print("\n" + "=" * 80)
    print("💎 MOST PROFITABLE SYMBOLS")
    print("=" * 80)

    if 'symbol' in df.columns:
        symbol_stats = df.groupby('symbol').agg({
            'profit_potential': ['count', 'mean', 'max'],
            'confidence': 'mean'
        }).round(2)

        symbol_stats.columns = ['Count', 'Avg Profit %', 'Max Profit %', 'Avg Confidence']
        symbol_stats = symbol_stats.sort_values('Max Profit %', ascending=False).head(10)

        print("\n", symbol_stats.to_string())

    # Opportunités récentes (dernières 24h)
    print("\n" + "=" * 80)
    print("⏰ RECENT OPPORTUNITIES (Last 24h)")
    print("=" * 80)

    if 'created_at' in df.columns:
        df['created_at'] = pd.to_datetime(df['created_at'])
        recent = df[df['created_at'] > datetime.now() - timedelta(hours=24)]
        print(f"\n📊 {len(recent)} opportunities found in the last 24 hours")

        if not recent.empty:
            print(f"\n   Best recent opportunity:")
            best_recent = recent.nlargest(1, 'profit_potential').iloc[0]
            print(f"   • {best_recent['symbol']}")
            print(f"   • Profit: {best_recent['profit_potential']:.2f}%")
            print(f"   • Confidence: {best_recent['confidence']:.0f}/100")

    # Recommandations
    print("\n" + "=" * 80)
    print("💡 RECOMMENDATIONS")
    print("=" * 80)

    high_confidence_profitable = df[(df['confidence'] > 70) & (df['profit_potential'] > 0.5)]

    if len(high_confidence_profitable) > 0:
        print(f"\n✅ {len(high_confidence_profitable)} HIGH-QUALITY opportunities found!")
        print("\n   Top 3 to explore:")
        for i, row in high_confidence_profitable.nlargest(3, 'profit_potential').iterrows():
            print(f"\n   {i+1}. {row['symbol']}")
            print(f"      💰 {row['profit_potential']:.2f}% profit")
            print(f"      📊 {row['confidence']:.0f}/100 confidence")
    else:
        print("\n⚠️  No high-confidence opportunities found yet.")
        print("\n   Suggestions:")
        print("   1. Run continuous scanning for 24-48h to accumulate more data")
        print("   2. Adjust min_profit threshold in config.yaml")
        print("   3. Add more exchanges to increase arbitrage possibilities")

    # Analyse temporelle
    print("\n" + "=" * 80)
    print("📊 TEMPORAL ANALYSIS")
    print("=" * 80)

    if 'created_at' in df.columns:
        df['hour'] = df['created_at'].dt.hour
        hourly = df.groupby('hour')['profit_potential'].agg(['count', 'mean'])
        print("\n   Opportunities by hour of day:")
        print("\n", hourly.to_string())

    conn.close()

    print("\n" + "=" * 80)
    print("✨ Analysis complete!")
    print("=" * 80)
    print("\n📝 Next steps:")
    print("   1. Review the top opportunities listed above")
    print("   2. Manually verify prices on exchanges")
    print("   3. Start with small test amounts (€50-100)")
    print("   4. Track actual vs theoretical profit")
    print("\n🚀 Happy trading! (But always DYOR - Do Your Own Research)")
    print("=" * 80)


if __name__ == "__main__":
    analyze_opportunities()
