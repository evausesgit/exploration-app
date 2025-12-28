"""
Dashboard Streamlit pour visualiser les opportunités de trading
"""

import sys
from pathlib import Path

# Ajoute le dossier racine au Python path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

from src.data.storage import OpportunityStorage
from src.strategies.arbitrage import CryptoArbitrageScanner
from src.core.opportunity import OpportunityType


# Configuration de la page
st.set_page_config(
    page_title="Crypto Opportunity Scanner",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)


class Dashboard:
    """Dashboard principal"""

    def __init__(self):
        self.storage = OpportunityStorage()

    def run(self):
        """Lance le dashboard"""
        st.title("💰 Crypto Opportunity Scanner")
        st.markdown("Scanner d'opportunités d'arbitrage et de trading crypto")

        # Sidebar
        self._render_sidebar()

        # Main content
        tab1, tab2, tab3, tab4 = st.tabs([
            "🔍 Scan en Direct",
            "📊 Opportunités Récentes",
            "📈 Analyses",
            "⚙️ Paramètres"
        ])

        with tab1:
            self._render_live_scan()

        with tab2:
            self._render_recent_opportunities()

        with tab3:
            self._render_analytics()

        with tab4:
            self._render_settings()

    def _render_sidebar(self):
        """Sidebar avec infos et contrôles"""
        st.sidebar.header("📊 Statistiques")

        stats = self.storage.get_statistics()

        st.sidebar.metric(
            "Total Opportunités",
            f"{stats['total_opportunities']:,}"
        )

        st.sidebar.metric(
            "Profit Moyen",
            f"{stats['average_profit']:.2f}%"
        )

        # Top symboles
        st.sidebar.subheader("🔝 Top Symboles")
        for item in stats['top_symbols'][:5]:
            st.sidebar.text(f"{item['symbol']}: {item['count']}")

    def _render_live_scan(self):
        """Tab pour lancer un scan en direct"""
        st.header("🔍 Scanner en Direct")

        col1, col2 = st.columns([3, 1])

        with col1:
            st.info("Cliquez sur 'Lancer Scan' pour détecter les opportunités actuelles")

        with col2:
            scan_button = st.button("🚀 Lancer Scan", type="primary", use_container_width=True)

        if scan_button:
            with st.spinner("Scan en cours des exchanges..."):
                # Lance le scanner
                scanner = CryptoArbitrageScanner({
                    'min_profit': 0.3,
                    'min_confidence': 40
                })

                opportunities = scanner.run_scan()

                if opportunities:
                    # Sauvegarde
                    self.storage.save_batch(opportunities)

                    st.success(f"✅ {len(opportunities)} opportunités détectées !")

                    # Affiche les résultats
                    self._display_opportunities_table(opportunities)

                else:
                    st.warning("Aucune opportunité trouvée pour le moment")

    def _render_recent_opportunities(self):
        """Tab avec opportunités récentes"""
        st.header("📊 Opportunités Récentes")

        # Filtres
        col1, col2, col3 = st.columns(3)

        with col1:
            min_profit = st.slider("Profit minimum (%)", 0.0, 5.0, 0.5, 0.1)

        with col2:
            min_confidence = st.slider("Confiance minimum", 0, 100, 50, 5)

        with col3:
            limit = st.selectbox("Nombre de résultats", [20, 50, 100, 200], index=1)

        # Récupère les opportunités
        opportunities = self.storage.get_best_opportunities(
            min_profit=min_profit,
            min_confidence=min_confidence,
            limit=limit
        )

        if opportunities:
            st.success(f"📈 {len(opportunities)} opportunités trouvées")

            # Convertit en DataFrame
            df = self._opportunities_to_dataframe(opportunities)

            # Affiche la table
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "profit_potential": st.column_config.NumberColumn(
                        "Profit (%)",
                        format="%.2f%%"
                    ),
                    "confidence": st.column_config.ProgressColumn(
                        "Confiance",
                        format="%d",
                        min_value=0,
                        max_value=100
                    ),
                    "timestamp": st.column_config.DatetimeColumn(
                        "Date",
                        format="DD/MM/YY HH:mm"
                    )
                }
            )

            # Graphique de distribution
            st.subheader("Distribution des Profits")
            fig = px.histogram(
                df,
                x="profit_potential",
                nbins=30,
                title="Distribution des Profits Potentiels"
            )
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("Aucune opportunité trouvée avec ces critères")

    def _render_analytics(self):
        """Tab avec analyses et graphiques"""
        st.header("📈 Analyses")

        # Récupère les données récentes
        recent = self.storage.get_recent(limit=500)

        if not recent:
            st.info("Pas encore de données. Lancez un scan d'abord !")
            return

        df = self._opportunities_to_dataframe(recent)

        # Parse data JSON
        df['buy_exchange'] = df['data'].apply(
            lambda x: json.loads(x).get('buy_exchange', 'N/A') if isinstance(x, str) else 'N/A'
        )
        df['sell_exchange'] = df['data'].apply(
            lambda x: json.loads(x).get('sell_exchange', 'N/A') if isinstance(x, str) else 'N/A'
        )

        # Graphiques
        col1, col2 = st.columns(2)

        with col1:
            # Top symboles par profit
            st.subheader("Top Symboles par Profit Moyen")
            top_symbols = df.groupby('symbol')['profit_potential'].agg(['mean', 'count']).reset_index()
            top_symbols = top_symbols[top_symbols['count'] >= 3].nlargest(10, 'mean')

            fig = px.bar(
                top_symbols,
                x='symbol',
                y='mean',
                title="Profit Moyen par Symbole",
                labels={'mean': 'Profit Moyen (%)', 'symbol': 'Symbole'}
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Distribution par exchange
            st.subheader("Exchanges les Plus Rentables")

            exchange_pairs = df.apply(
                lambda row: f"{row['buy_exchange']} → {row['sell_exchange']}",
                axis=1
            ).value_counts().head(10)

            fig = px.pie(
                values=exchange_pairs.values,
                names=exchange_pairs.index,
                title="Paires d'Exchanges les Plus Fréquentes"
            )
            st.plotly_chart(fig, use_container_width=True)

        # Timeline
        st.subheader("Opportunités dans le Temps")
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df_timeline = df.set_index('timestamp').resample('1H')['profit_potential'].agg(['mean', 'count'])

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_timeline.index,
            y=df_timeline['mean'],
            mode='lines+markers',
            name='Profit Moyen',
            yaxis='y'
        ))
        fig.add_trace(go.Bar(
            x=df_timeline.index,
            y=df_timeline['count'],
            name='Nombre',
            yaxis='y2',
            opacity=0.3
        ))

        fig.update_layout(
            title="Évolution Temporelle des Opportunités",
            yaxis=dict(title="Profit Moyen (%)"),
            yaxis2=dict(title="Nombre", overlaying='y', side='right'),
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)

    def _render_settings(self):
        """Tab de paramètres"""
        st.header("⚙️ Paramètres")

        st.subheader("Configuration du Scanner")

        col1, col2 = st.columns(2)

        with col1:
            st.text_input("Exchanges", value="binance, kraken, coinbase", help="Exchanges à scanner (séparés par virgule)")
            st.number_input("Profit Minimum (%)", value=0.5, min_value=0.0, max_value=10.0, step=0.1)
            st.number_input("Confiance Minimum", value=50, min_value=0, max_value=100, step=5)

        with col2:
            st.multiselect(
                "Symboles à Scanner",
                ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT', 'ADA/USDT'],
                default=['BTC/USDT', 'ETH/USDT']
            )
            st.checkbox("Inclure frais de retrait", value=True)
            st.number_input("Volume Minimum 24h (USD)", value=1000000, step=100000)

        st.button("💾 Sauvegarder Configuration", type="primary")

        st.info("💡 Conseils: Commencez avec des paramètres conservateurs (profit > 0.5%) pour éviter les faux signaux")

    def _display_opportunities_table(self, opportunities):
        """Affiche un tableau d'opportunités"""
        if not opportunities:
            return

        data = []
        for opp in opportunities:
            data.append({
                'Symbole': opp.symbol,
                'Achat': opp.data.get('buy_exchange', 'N/A'),
                'Vente': opp.data.get('sell_exchange', 'N/A'),
                'Profit (%)': f"{opp.profit_potential:.2f}%",
                'Confiance': f"{opp.confidence:.0f}",
                'Prix Achat': f"${opp.data.get('buy_price', 0):,.2f}",
                'Prix Vente': f"${opp.data.get('sell_price', 0):,.2f}",
            })

        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)

    def _opportunities_to_dataframe(self, opportunities: list) -> pd.DataFrame:
        """Convertit une liste d'opportunités en DataFrame"""
        if not opportunities:
            return pd.DataFrame()

        # Si ce sont des dicts (depuis DB)
        if isinstance(opportunities[0], dict):
            return pd.DataFrame(opportunities)

        # Si ce sont des objets Opportunity
        data = [opp.to_dict() for opp in opportunities]
        return pd.DataFrame(data)


def main():
    """Point d'entrée du dashboard"""
    dashboard = Dashboard()
    dashboard.run()


if __name__ == "__main__":
    main()
