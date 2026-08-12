import base64
import json
import os
import urllib.error
import urllib.request
import streamlit as st

st.set_page_config(
    page_title="JanSan RFP Pilot — Intelligence & Complete Bid Generator",
    page_icon="🏢",
    layout="wide",
)

# ----------------- LANGUAGE SELECTION & DICTIONARIES ----------------- #
lang = st.sidebar.radio("🌐 Langue / Language", ("Français", "English"), index=0)

T = {
    "Français": {
        "title": "🏢 JanSan RFP Pilot — Moteur d'Offres & Générateur de Soumissions",
        "caption": "Plateforme complète d'analyse d'appels d'offres (SEAO, municipal, corporatif) et de génération de soumissions prêtes à déposer pour entrepreneurs Jan/San.",
        "tab_profile": "1️⃣ Profil Entreprise & Grille Tarifaire",
        "tab_qual": "2️⃣ Qualification & Analyse des Écarts",
        "tab_bid": "3️⃣ Générateur de Soumission Complète",
        # Tab 1
        "profile_h": "Identité & Capacités de l'Entreprise",
        "co_name": "Raison sociale",
        "co_address": "Adresse & Territoire desservi",
        "co_certs": "Certifications & Normes détenues",
        "co_certs_opts": [
            "ISO 9001 (Système de gestion de la qualité)",
            "ISO 14001 (Gestion environnementale)",
            "CIMS / CIMS-GB (ISSA - Green Building)",
            "Produits certifiés ÉcoLogo / Green Seal",
            "Attestation CNESST / WSIB en règle",
            "Attestation Revenu Québec en règle",
            "Licence d'entrepreneur (RBQ)",
            "Personnel avec Enquête de sécurité (Fiabilité/Secret)",
        ],
        "co_ins": "Assurance responsabilité civile globale",
        "co_bond": "Capacité de cautionnement (Cautions de soumission / exécution)",
        "pricing_h": "Paramètres Financiers & Grille Tarifaire de Base",
        "rate_base": "Taux horaire préposé à l'entretien ($/h)",
        "rate_super": "Taux horaire chef d'équipe / superviseur ($/h)",
        "rate_markup": "Marge sur produits chimiques & consommables (%)",
        "custom_price_h": "Grille de prix des travaux périodiques & spécialisés",
        "custom_price_ph": "ex. Décapage/cirage: 0.35$/pi²\nLavage de tapis: 0.22$/pi²\nLavage de vitres: 0.12$/pi²\nMain d'oeuvre d'urgence 24/7: 48.00$/h",
        # Tab 2 & 3
        "upload_h": "Devis de l'Appel d'Offres (PDF)",
        "upload_lbl": "Téléversez le devis officiel (SEAO, Buyandsell, devis privé)",
        "btn_qual": "1. Analyser la Conformité & Risques (Go / No-Go)",
        "btn_bid": "2. Générer la Proposition Complète de Soumission",
        "spinner_qual": "Évaluation de la conformité et analyse des écarts en cours...",
        "spinner_bid": "Rédaction et calcul de la soumission complète en cours...",
        "err_key": "Clé API manquante. Ajoutez GEMINI_API_KEY dans les Secrets Streamlit.",
        "download_btn": "📥 Télécharger la Soumission Complète (.md)",
    },
    "English": {
        "title": "🏢 JanSan RFP Pilot — Bid Intelligence & Complete Proposal Engine",
        "caption": "End-to-end tender analysis, qualification matrix, and automated bid proposal generator for commercial cleaning & Jan/San contractors.",
        "tab_profile": "1️⃣ Company Master Profile & Rates",
        "tab_qual": "2️⃣ Qualification & Gap Matrix",
        "tab_bid": "3️⃣ Complete Bid Proposal Generator",
        # Tab 1
        "profile_h": "Contractor Credentials & Qualifications",
        "co_name": "Company Legal Name",
        "co_address": "Headquarters Address & Service Territory",
        "co_certs": "Certifications & Accreditations Held",
        "co_certs_opts": [
            "ISO 9001 (Quality Management)",
            "ISO 14001 (Environmental Management)",
            "CIMS / CIMS-GB (ISSA Green Building)",
            "EcoLogo / Green Seal Certified Chemicals",
            "WSIB / CNESST Clearance Certificate",
            "Good Standing Tax Certificates",
            "Valid General Cleaning / Contractor License",
            "Security-Cleared Staff (Reliability / Secret)",
        ],
        "co_ins": "Commercial General Liability Insurance",
        "co_bond": "Bonding Capacity (Bid Bonds / Performance Surety)",
        "pricing_h": "Financial Multipliers & Base Rate Matrix",
        "rate_base": "Base Cleaner Hourly Billing Rate ($/hr)",
        "rate_super": "Supervisor Hourly Billing Rate ($/hr)",
        "rate_markup": "Chemical & Supply Markup (%)",
        "custom_price_h": "Periodic & Specialty Services Price List",
        "custom_price_ph": "e.g., Strip & wax: $0.35/sq ft\nCarpet extraction: $0.22/sq ft\nWindow washing: $0.12/sq ft\nEmergency 24/7 dispatch: $48.00/hr",
        # Tab 2 & 3
        "upload_h": "Tender / RFP Document (PDF)",
        "upload_lbl": "Upload the official RFP document (Buyandsell, MERX, SEAO, Private)",
        "btn_qual": "1. Analyze Compliance & Gap Risks (Go / No-Go)",
        "btn_bid": "2. Generate Complete Submission Proposal",
        "spinner_qual": "Evaluating tender compliance against your contractor credentials...",
        "spinner_bid": "Generating complete itemized proposal and pricing schedules...",
        "err_key": "Missing API key. Please add GEMINI_API_KEY in Streamlit Secrets.",
        "download_btn": "📥 Download Complete Bid Document (.md)",
    },
}

t = T[lang]

# ----------------- BULLETPROOF MODEL RUNNER ----------------- #
def run_gemini_analysis(api_key: str, prompt_text: str, pdf_b64: str) -> dict:
    discovered_models = []
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for m in data.get("models", []):
                name = m.get("name", "").replace("models/", "")
                if "generateContent" in m.get("supportedGenerationMethods", []):
                    discovered_models.append(name)
    except Exception:
        pass

    discovered_models.sort(reverse=True)
    candidates = discovered_models + [
        "gemini-2.5-pro",
        "gemini-2.0-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ]

    seen = set()
    candidate_list = [m for m in candidates if m and not (m in seen or seen.add(m))]

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text},
                    {
                        "inline_data": {
                            "mime_type": "application/pdf",
                            "data": pdf_b64,
                        }
                    },
                ]
            }
        ],
        "generationConfig": {"responseMimeType": "application/json"},
    }

    last_error = None
    for model in candidate_list:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=90) as response:
                result = json.loads(response.read().decode("utf-8"))
                raw_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                if raw_text.startswith("```"):
                    raw_text = raw_text[3:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                return json.loads(raw_text.strip())
        except Exception as e:
            last_error = e
            continue

    if last_error:
        raise last_error
    raise RuntimeError("No compatible active model could be reached.")


# ----------------- UI HEADER ----------------- #
st.title(t["title"])
st.caption(t["caption"])

tab_prof, tab_qual, tab_bid = st.tabs([t["tab_profile"], t["tab_qual"], t["tab_bid"]])

# ----------------- TAB 1: MASTER CONTRACTOR PROFILE ----------------- #
with tab_prof:
    st.subheader(t["profile_h"])
    col1, col2 = st.columns(2)
    with col1:
        co_name = st.text_input(t["co_name"], value="Services d'Entretien Expert-Net Inc.")
        co_addr = st.text_input(t["co_address"], value="1500 Boulevard René-Lévesque O, Montréal, QC")
        co_certs = st.multiselect(
            t["co_certs"],
            t["co_certs_opts"],
            default=[t["co_certs_opts"][0], t["co_certs_opts"][3], t["co_certs_opts"][4]],
        )
    with col2:
        co_ins = st.selectbox(
            t["co_ins"],
            ["2 000 000 $ CAD", "5 000 000 $ CAD", "10 000 000 $ CAD", "20 000 000 $+ CAD"],
            index=1,
        )
        co_bond = st.selectbox(
            t["co_bond"],
            ["Capacité standard (Caution 10% + 50% MO/Matériaux)", "Capacité majeure (Cautions 50% / 100%)", "Aucune caution disponible"],
            index=0,
        )

    st.markdown("---")
    st.subheader(t["pricing_h"])
    pcol1, pcol2, pcol3 = st.columns(3)
    with pcol1:
        rate_base = st.number_input(t["rate_base"], min_value=15.0, max_value=200.0, value=29.50, step=0.50)
    with pcol2:
        rate_super = st.number_input(t["rate_super"], min_value=20.0, max_value=250.0, value=38.00, step=0.50)
    with pcol3:
        rate_markup = st.number_input(t["rate_markup"], min_value=0.0, max_value=100.0, value=15.0, step=1.0)

    st.markdown(f"**{t['custom_price_h']}**")
    custom_pricing = st.text_area(
        " ",
        value="• Décapage et cirage de planchers vinyle (4 couches): 0.38$/pi²\n• Lavage de vitres intérieur/extérieur: 0.14$/pi²\n• Nettoyage de tapis par extraction à eau chaude: 0.24$/pi²\n• Forfait désinfection électrostatique d'urgence: 450.00$/intervention\n• Taux de main-d'oeuvre d'urgence hors horaire: 48.50$/h",
        height=110,
    )

    # Store master profile in session
    contractor_profile = {
        "company_name": co_name,
        "company_address": co_addr,
        "held_certifications": co_certs,
        "insurance_coverage": co_ins,
        "bonding_capacity": co_bond,
        "base_cleaner_rate": f"{rate_base}$/hr",
        "supervisor_rate": f"{rate_super}$/hr",
        "chemical_markup": f"{rate_markup}%",
        "itemized_price_list": custom_pricing,
    }
    st.session_state["contractor_profile"] = contractor_profile
    st.success("✅ Profil maître et grille tarifaire sauvegardés.")

# ----------------- SHARED UPLOADER ----------------- #
st.sidebar.markdown("---")
st.sidebar.subheader(t["upload_h"])
uploaded_pdf = st.sidebar.file_uploader(t["upload_lbl"], type=["pdf"])

# ----------------- TAB 2: QUALIFICATION & GAP ANALYSIS ----------------- #
with tab_qual:
    if uploaded_pdf is None:
        st.info("👈 Veuillez d'abord téléverser un fichier PDF d'appel d'offres dans le panneau latéral gauche.")
    else:
        if st.button(t["btn_qual"], type="primary"):
            with st.spinner(t["spinner_qual"]):
                try:
                    api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
                    if not api_key:
                        st.error(t["err_key"])
                        st.stop()

                    pdf_bytes = uploaded_pdf.read()
                    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

                    schema_qual = {
                        "go_no_go_verdict": {
                            "decision": "GO / CONDITIONAL GO / NO-GO",
                            "suitability_score": "88%",
                            "executive_rationale": "Clear rationale based on contractor certifications and capacity.",
                        },
                        "gap_analysis_missing_requirements": [
                            "Specific certification or insurance limit requested in RFP that contractor lacks or needs to obtain."
                        ],
                        "mandatory_disqualifiers": [
                            {
                                "category": "Category",
                                "requirement": "Requirement text",
                                "penalty": "Automatic Rejection",
                            }
                        ],
                        "required_annexes_and_forms": [
                            "List of mandatory schedules, security clearance forms, bid bonds to submit."
                        ],
                        "scoring_matrix_summary": [
                            "Detailed breakdown of how technical and price points are allocated."
                        ],
                    }

                    prompt = (
                        "Tu es un directeur de propositions sénior et un auditeur d'appels d'offres d'entretien ménager (Jan/San).\n"
                        f"PROFIL DU CONTRACTEUR SOUMISSIONNAIRE:\n{json.dumps(contractor_profile, ensure_ascii=False, indent=2)}\n\n"
                        "Analyse le devis PDF ci-joint et compare-le au profil du soumissionnaire. Retourne un JSON STRICT:\n"
                        f"{json.dumps(schema_qual, indent=2)}"
                    )

                    data = run_gemini_analysis(api_key, prompt, pdf_base64)
                    st.session_state["qual_data"] = data

                except Exception as e:
                    st.error(f"Erreur : {str(e)}")

        if "qual_data" in st.session_state:
            qdata = st.session_state["qual_data"]
            verdict = qdata.get("go_no_go_verdict", {})
            st.markdown(f"### Décision : **{verdict.get('decision', 'N/A')}** (Score d'adéquation : **{verdict.get('suitability_score', 'N/A')}**)")
            st.info(verdict.get("executive_rationale", ""))

            c1, c2 = st.columns(2)
            with c1:
                st.subheader("⚠️ Analyse des Écarts & Risques")
                for gap in qdata.get("gap_analysis_missing_requirements", []):
                    st.warning(f"• {gap}")

                st.subheader("🚨 Critères Éliminatoires (Pass / Fail)")
                for item in qdata.get("mandatory_disqualifiers", []):
                    st.error(f"**[{item.get('category', 'Exigence')}]** {item.get('requirement', '')}  \n*{item.get('penalty', 'Rejet')}*")

            with c2:
                st.subheader("📎 Formulaires & Cautions Obligatoires")
                for f in qdata.get("required_annexes_and_forms", []):
                    st.markdown(f"• {f}")

                st.subheader("📊 Grille d'Évaluation & Points")
                for s in qdata.get("scoring_matrix_summary", []):
                    st.markdown(f"• {s}")

# ----------------- TAB 3: COMPLETE BID PROPOSAL GENERATOR ----------------- #
with tab_bid:
    if uploaded_pdf is None:
        st.info("👈 Veuillez téléverser le devis PDF dans la barre latérale pour générer la soumission complète.")
    else:
        st.write("Générez automatiquement l'ensemble de la soumission prête à être déposée, incluant le calcul des coûts, le plan de travail, les normes et la lettre de présentation.")
        if st.button(t["btn_bid"], type="primary"):
            with st.spinner(t["spinner_bid"]):
                try:
                    api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
                    if not api_key:
                        st.error(t["err_key"])
                        st.stop()

                    uploaded_pdf.seek(0)
                    pdf_bytes = uploaded_pdf.read()
                    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

                    schema_bid = {
                        "proposal_title": "Titre complet de la proposition de soumission",
                        "transmittal_letter": "Lettre formelle de transmission / soumission adressée au client émetteur, signée au nom de l'entreprise.",
                        "executive_summary_scope": "Compréhension détaillée du mandat, superficie des lieux, horaires d'intervention et normes applicables.",
                        "calculated_pricing_table": {
                            "routine_cleaning_monthly": "Montant mensuel estimé ($ CAD)",
                            "routine_cleaning_annual": "Montant annuel estimé ($ CAD)",
                            "periodic_services_breakdown": [
                                "Description du service périodique (ex. décapage, vitres), fréquence, prix unitaire appliqué basé sur la grille du contracteur"
                            ],
                            "total_first_year_contract_value": "Valeur totale estimée de la 1ère année ($ CAD)",
                        },
                        "operational_plan_and_staffing": "Plan de main d'oeuvre, ratio superviseur/préposés, protocole d'inspection et registre de contrôle qualité.",
                        "environmental_and_safety_commitments": "Plan de conformité SIMDUT/WHMIS, fiches signalétiques, produits ÉcoLogo, équipement avec filtration HEPA.",
                        "compliance_guarantees": "Engagements formels de conformité avec les décrets/CNESST et assurances requises.",
                    }

                    prompt_bid = (
                        "Tu es un directeur de propositions sénior en hygiène et salubrité (Jan/San).\n"
                        "Rédige une PROPOSITION COMPLÈTE, FORMELLE ET CHIFFRÉE DE SOUMISSION prête à être soumise au donneur d'ouvrage.\n"
                        "Applique rigoureusement les taux horaires et les prix au pi² du contracteur ci-dessous aux superficies et fréquences du devis PDF.\n\n"
                        f"PROFIL & LISTE DE PRIX DU CONTRACTEUR:\n{json.dumps(contractor_profile, ensure_ascii=False, indent=2)}\n\n"
                        "Retourne un objet JSON STRICT respectant cette structure :\n"
                        f"{json.dumps(schema_bid, indent=2)}"
                    )

                    bid_data = run_gemini_analysis(api_key, prompt_bid, pdf_base64)
                    st.session_state["bid_data"] = bid_data

                except Exception as e:
                    st.error(f"Erreur : {str(e)}")

        if "bid_data" in st.session_state:
            b = st.session_state["bid_data"]
            st.markdown(f"## {b.get('proposal_title', 'Proposition de Soumission')}")

            # 1. Submission Letter
            with st.expander("📄 Lettre Formelle de Soumission (Transmittal Letter)", expanded=True):
                st.markdown(b.get("transmittal_letter", ""))

            # 2. Executive Scope
            with st.expander("🏢 Compréhension du Mandat & Envergure des Travaux", expanded=True):
                st.markdown(b.get("executive_summary_scope", ""))

            # 3. Calculated Pricing Schedule
            with st.expander("💰 Grille Financière & Chiffrage de l'Offre", expanded=True):
                ptable = b.get("calculated_pricing_table", {})
                m1, m2, m3 = st.columns(3)
                m1.metric("Entretien Régulier (Mensuel)", ptable.get("routine_cleaning_monthly", "N/A"))
                m2.metric("Entretien Régulier (Annuel)", ptable.get("routine_cleaning_annual", "N/A"))
                m3.metric("Valeur Totale Année 1", ptable.get("total_first_year_contract_value", "N/A"))

                st.markdown("#### Détail des travaux périodiques & spécialisés calculés :")
                for s_item in ptable.get("periodic_services_breakdown", []):
                    st.markdown(f"• {s_item}")

            # 4. Operations & Quality Control
            with st.expander("🛠️ Plan Opérationnel, Supervision & Contrôle Qualité", expanded=False):
                st.markdown(b.get("operational_plan_and_staffing", ""))

            # 5. Environmental & Safety Standards
            with st.expander("🌱 Plan Environnemental, SIMDUT & Santé-Sécurité", expanded=False):
                st.markdown(b.get("environmental_and_safety_commitments", ""))
                st.markdown("---")
                st.markdown(b.get("compliance_guarantees", ""))

            # Download compiled document
            compiled_md = f"""# {b.get('proposal_title', 'Proposition de Soumission')}

## 1. Lettre de Transmission
{b.get('transmittal_letter', '')}

---

## 2. Compréhension du Mandat & Portée des Travaux
{b.get('executive_summary_scope', '')}

---

## 3. Sommaire Financier & Grille Tarifaire
- **Entretien régulier mensuel :** {ptable.get('routine_cleaning_monthly', 'N/A')}
- **Entretien régulier annuel :** {ptable.get('routine_cleaning_annual', 'N/A')}
- **Valeur contractuelle totale estimée (Année 1) :** {ptable.get('total_first_year_contract_value', 'N/A')}

### Travaux périodiques et spécialisés :
""" + "\n".join([f"- {item}" for item in ptable.get("periodic_services_breakdown", [])]) + f"""

---

## 4. Plan Opérationnel, Supervision & Assurance Qualité
{b.get('operational_plan_and_staffing', '')}

---

## 5. Normes Environnementales, SIMDUT et Santé-Sécurité
{b.get('environmental_and_safety_commitments', '')}

{b.get('compliance_guarantees', '')}
"""
            st.download_button(
                label=t["download_btn"],
                data=compiled_md,
                file_name=f"Soumission_{co_name.replace(' ', '_')}.md",
                mime="text/markdown",
            )
