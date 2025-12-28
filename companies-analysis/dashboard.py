"""
Dashboard Streamlit pour visualiser les opportunités d'automatisation IA

Usage:
    streamlit run dashboard.py
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
from loguru import logger

from src.strategies.ai_automation_scanner import AIAutomationScanner, SECTEURS_PRIORITAIRES

# Configuration de la page
st.set_page_config(
    page_title="AI Automation Scanner",
    page_icon="🤖",
    layout="wide"
)

# Charger les variables d'environnement
load_dotenv()

# Titre principal
st.title("🤖 Scanner d'opportunités d'automatisation IA")
st.markdown("Identifie les entreprises françaises à fort potentiel d'automatisation")

# Sidebar - Configuration
st.sidebar.header("⚙️ Configuration")

# Clé API
api_key = st.sidebar.text_input(
    "Pappers API Key",
    value=os.getenv('PAPPERS_API_KEY', ''),
    type="password",
    help="Votre clé API Pappers"
)

st.sidebar.markdown("---")
st.sidebar.subheader("Filtres de recherche")

# Sélection des secteurs
secteurs_disponibles = list(SECTEURS_PRIORITAIRES.keys())
secteurs_selectionnes = st.sidebar.multiselect(
    "Secteurs à scanner",
    options=secteurs_disponibles,
    default=['conseil', 'marketing_digital', 'saas_tech'],
    help="Secteurs d'activité à cibler"
)

# Départements
departements_input = st.sidebar.text_input(
    "Départements (optionnel)",
    placeholder="75,92,93",
    help="Départements séparés par des virgules. Laisser vide pour toute la France."
)
departements = [d.strip() for d in departements_input.split(',')] if departements_input else None

st.sidebar.markdown("---")
st.sidebar.subheader("Critères financiers")

# Critères financiers
col1, col2 = st.sidebar.columns(2)
with col1:
    min_ca = st.number_input(
        "CA min (€)",
        min_value=100000,
        max_value=10000000,
        value=1000000,
        step=100000,
        help="Chiffre d'affaires minimum"
    )
    min_ca_per_employee = st.number_input(
        "CA/salarié min (€)",
        min_value=50000,
        max_value=1000000,
        value=100000,
        step=10000,
        help="Ratio CA par salarié minimum"
    )

with col2:
    max_effectif = st.number_input(
        "Effectif max",
        min_value=1,
        max_value=50,
        value=10,
        step=1,
        help="Nombre maximum de salariés"
    )
    min_age_years = st.number_input(
        "Âge min (années)",
        min_value=0,
        max_value=10,
        value=2,
        step=1,
        help="Âge minimum de l'entreprise"
    )

# Critère de score
min_score = st.sidebar.slider(
    "Score d'automatisation minimum",
    min_value=0,
    max_value=100,
    value=50,
    step=5,
    help="Score minimum (0-100) pour afficher une opportunité"
)

# Nombre de résultats par secteur
max_results_per_sector = st.sidebar.number_input(
    "Résultats max par secteur",
    min_value=5,
    max_value=100,
    value=20,
    step=5,
    help="Nombre maximum d'entreprises à analyser par secteur"
)

# Bouton de lancement
st.sidebar.markdown("---")
run_scan = st.sidebar.button("🚀 Lancer le scan", type="primary", use_container_width=True)

# Session state pour stocker les résultats
if 'opportunities' not in st.session_state:
    st.session_state.opportunities = []

# Exécution du scan
if run_scan:
    if not api_key:
        st.error("❌ Veuillez fournir une clé API Pappers")
    elif not secteurs_selectionnes:
        st.error("❌ Veuillez sélectionner au moins un secteur")
    else:
        with st.spinner("🔍 Scan en cours..."):
            try:
                # Configuration du scanner
                config = {
                    'pappers_api_key': api_key,
                    'secteurs': secteurs_selectionnes,
                    'departements': departements,
                    'min_ca': min_ca,
                    'max_effectif': max_effectif,
                    'min_ca_per_employee': min_ca_per_employee,
                    'min_age_years': min_age_years
                }

                # Créer et lancer le scanner
                scanner = AIAutomationScanner(config)

                opportunities = []
                for secteur in secteurs_selectionnes:
                    secteur_opps = scanner.search_by_sector(secteur, max_companies=max_results_per_sector)
                    opportunities.extend(secteur_opps)

                # Filtrer par score minimum
                opportunities = [opp for opp in opportunities if opp.confidence >= min_score]

                st.session_state.opportunities = opportunities
                st.success(f"✅ Scan terminé : {len(opportunities)} opportunités détectées")

            except Exception as e:
                st.error(f"❌ Erreur lors du scan : {e}")
                logger.exception("Scan error")

# Affichage des résultats
if st.session_state.opportunities:
    opportunities = st.session_state.opportunities

    # Métriques globales
    st.markdown("---")
    st.header("📊 Résultats")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Opportunités détectées", len(opportunities))
    with col2:
        avg_score = sum(opp.confidence for opp in opportunities) / len(opportunities)
        st.metric("Score moyen", f"{avg_score:.0f}/100")
    with col3:
        avg_ca_per_employee = sum(opp.data['ca_per_employee'] for opp in opportunities) / len(opportunities)
        st.metric("CA/salarié moyen", f"{avg_ca_per_employee:,.0f}€")
    with col4:
        total_ca = sum(opp.data['ca'] for opp in opportunities)
        st.metric("CA total", f"{total_ca/1e6:.1f}M€")

    # Convertir en DataFrame
    df = pd.DataFrame([
        {
            'Entreprise': opp.data['denomination'],
            'SIREN': opp.data['siren'],
            'Score': int(opp.confidence),
            'CA': opp.data['ca'],
            'Effectif': opp.data['effectif'],
            'CA/salarié': int(opp.data['ca_per_employee']),
            'Résultat': opp.data['resultat'],
            'Marge %': f"{opp.data['marge']:.1f}",
            'Secteur': opp.data.get('secteur_hint', 'N/A'),
            'Activité': opp.data['activite'],
            'Ville': opp.data['ville'],
            'CP': opp.data['code_postal']
        }
        for opp in opportunities
    ])

    # Trier par score
    df = df.sort_values('Score', ascending=False)

    # Onglets pour différentes vues
    tab1, tab2, tab3 = st.tabs(["📋 Liste des entreprises", "📈 Analyses", "🎯 Détails"])

    with tab1:
        st.subheader("Liste des opportunités")

        # Filtres supplémentaires
        col1, col2 = st.columns(2)
        with col1:
            secteur_filter = st.multiselect(
                "Filtrer par secteur",
                options=df['Secteur'].unique().tolist(),
                default=df['Secteur'].unique().tolist()
            )
        with col2:
            ville_filter = st.multiselect(
                "Filtrer par ville",
                options=sorted(df['Ville'].unique().tolist()),
                default=df['Ville'].unique().tolist()
            )

        # Appliquer les filtres
        df_filtered = df[
            (df['Secteur'].isin(secteur_filter)) &
            (df['Ville'].isin(ville_filter))
        ]

        # Tableau avec formatage
        st.dataframe(
            df_filtered,
            use_container_width=True,
            hide_index=True,
            column_config={
                'CA': st.column_config.NumberColumn('CA', format="%.0f €"),
                'CA/salarié': st.column_config.NumberColumn('CA/salarié', format="%.0f €"),
                'Résultat': st.column_config.NumberColumn('Résultat', format="%.0f €"),
                'Score': st.column_config.ProgressColumn('Score', min_value=0, max_value=100)
            }
        )

        # Export CSV
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger en CSV",
            data=csv,
            file_name="opportunites_ia_automation.csv",
            mime="text/csv"
        )

    with tab2:
        st.subheader("Analyses visuelles")

        col1, col2 = st.columns(2)

        with col1:
            # Distribution des scores
            fig_scores = px.histogram(
                df,
                x='Score',
                nbins=20,
                title="Distribution des scores d'automatisation",
                labels={'Score': 'Score d\'automatisation', 'count': 'Nombre d\'entreprises'}
            )
            fig_scores.update_layout(showlegend=False)
            st.plotly_chart(fig_scores, use_container_width=True)

        with col2:
            # CA/salarié par secteur
            fig_ca_sector = px.box(
                df,
                x='Secteur',
                y='CA/salarié',
                title="CA/salarié par secteur",
                labels={'CA/salarié': 'CA par salarié (€)', 'Secteur': 'Secteur'}
            )
            st.plotly_chart(fig_ca_sector, use_container_width=True)

        col3, col4 = st.columns(2)

        with col3:
            # Top 10 entreprises par score
            top_10 = df.head(10)
            fig_top = px.bar(
                top_10,
                x='Score',
                y='Entreprise',
                orientation='h',
                title="Top 10 des opportunités",
                labels={'Score': 'Score d\'automatisation', 'Entreprise': ''}
            )
            fig_top.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_top, use_container_width=True)

        with col4:
            # Répartition par secteur
            secteur_counts = df['Secteur'].value_counts()
            fig_secteurs = px.pie(
                values=secteur_counts.values,
                names=secteur_counts.index,
                title="Répartition par secteur"
            )
            st.plotly_chart(fig_secteurs, use_container_width=True)

        # Scatter plot CA vs Effectif
        st.subheader("CA vs Effectif (taille = score)")
        fig_scatter = px.scatter(
            df,
            x='Effectif',
            y='CA',
            size='Score',
            color='Secteur',
            hover_data=['Entreprise', 'CA/salarié', 'Marge %'],
            title="Chiffre d'affaires vs Effectif",
            labels={'CA': 'Chiffre d\'affaires (€)', 'Effectif': 'Nombre de salariés'}
        )
        fig_scatter.update_traces(marker=dict(line=dict(width=1, color='white')))
        st.plotly_chart(fig_scatter, use_container_width=True)

    with tab3:
        st.subheader("Détails des entreprises")

        # Sélection d'une entreprise
        selected_company = st.selectbox(
            "Sélectionner une entreprise",
            options=df['Entreprise'].tolist(),
            index=0
        )

        if selected_company:
            company_data = df[df['Entreprise'] == selected_company].iloc[0]

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### Informations générales")
                st.markdown(f"**Dénomination :** {company_data['Entreprise']}")
                st.markdown(f"**SIREN :** {company_data['SIREN']}")
                st.markdown(f"**Activité :** {company_data['Activité']}")
                st.markdown(f"**Localisation :** {company_data['Ville']} ({company_data['CP']})")
                st.markdown(f"**Secteur :** {company_data['Secteur']}")

            with col2:
                st.markdown("### Données financières")
                st.markdown(f"**Chiffre d'affaires :** {company_data['CA']:,.0f} €")
                st.markdown(f"**Résultat :** {company_data['Résultat']:,.0f} €")
                st.markdown(f"**Marge :** {company_data['Marge %']} %")
                st.markdown(f"**Effectif :** {company_data['Effectif']}")
                st.markdown(f"**CA/salarié :** {company_data['CA/salarié']:,.0f} €")

            # Score détaillé
            st.markdown("### Score d'automatisation")
            score_value = company_data['Score']

            # Jauge de score
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score_value,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Score global"},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 75], 'color': "lightyellow"},
                        {'range': [75, 100], 'color': "lightgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig_gauge.update_layout(height=300)
            st.plotly_chart(fig_gauge, use_container_width=True)

            # Explication du score
            st.markdown("""
            **Composantes du score :**
            - 🎯 **Ratio CA/effectif** (40 points) : Indicateur de productivité et d'automatisation existante
            - 🏢 **Secteur d'activité** (30 points) : Potentiel d'automatisation selon le domaine
            - 💰 **Rentabilité** (15 points) : Marge bénéficiaire indiquant l'efficacité
            - 📦 **Actifs physiques** (15 points) : Moins d'immobilisations = plus automatisable
            """)

else:
    # Message d'accueil
    st.info("👈 Configurez les paramètres dans la barre latérale et lancez le scan pour détecter des opportunités")

    st.markdown("""
    ### 🎯 Qu'est-ce que ce scanner détecte ?

    Ce scanner identifie des entreprises françaises ayant un **fort potentiel d'automatisation par l'IA**, en se basant sur :

    - **Ratio CA/effectif élevé** : Signal d'une activité déjà optimisée ou facilement automatisable
    - **Secteurs à fort levier IA** : Conseil, marketing digital, SaaS, formation, courtage, services RH/finance/juridique
    - **Peu d'actifs physiques** : Favorise les activités de services immatériels
    - **Rentabilité démontrée** : Entreprises saines avec des marges positives

    ### 📊 Secteurs prioritaires

    """)

    # Affichage des secteurs avec leurs mots-clés
    for secteur, keywords in SECTEURS_PRIORITAIRES.items():
        with st.expander(f"**{secteur.replace('_', ' ').title()}**"):
            st.markdown(f"Mots-clés : {', '.join(keywords)}")

# Footer
st.markdown("---")
st.markdown("💡 *Powered by Pappers API - Scanner d'opportunités d'automatisation IA*")
