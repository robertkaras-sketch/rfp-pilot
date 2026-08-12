import base64
import json
import os
import urllib.error
import urllib.request
import streamlit as st

st.set_page_config(
    page_title="JanSan RFP Pilot — Intelligence & Bid Proposal Engine",
    page_icon="🏢",
    layout="wide",
)

# ----------------- LANGUAGE CONFIG ----------------- #
lang = st.sidebar.radio("🌐 Langue / Language", ("Français", "English"), index=0)

T = {
    "Français": {
        "title": "🏢 JanSan RFP Pilot — Moteur d'Offres & Conformité Soumissionnaire",
        "caption": "Associez le profil, les certifications et la grille tarifaire de votre entreprise aux exigences du devis pour générer une analyse d'écart et une stratégie de soumission.",
        "tab_profile": "1️⃣ Profil de l'Entreprise & Grille Tarifaire",
        "tab_rfp": "2️⃣ Analyseur de Devis (RFP) & Match IA",
        "profile_header": "Informations & Capacités du Soumissionnaire",
        "company_name": "Raison sociale du contracteur",
        "c_certs": "Certifications & Normes détenues",
        "c_certs_options": [
            "ISO 9001 (Qualité)",
            "ISO 14001 (Environnement)",
            "CIMS / CIMS-GB (ISSA)",
            "Produits ÉcoLogo / Green Seal",
            "Attestation Revenu Québec / CNESST à jour",
            "Licence RBQ valide",
            "Personnel avec Enquête de sécurité (Gouv/Santé)",
        ],
        "c_insurance": "Couverture d'assurance responsabilité civile ($ CAD)",
        "c_bonding": "Capacité de cautionnement / Cautions d'exécution",
        "pricing_header": "Grille Tarifaire & Paramètres Financiers",
        "hourly_base": "Taux horaire de base proposé ($/h)",
        "hourly_super": "Taux horaire supervision ($/h)",
        "chem_equip_markup": "Marge / Majoration produits & équipements (%)",
        "custom_pricing_notes": "Liste de prix personnalisée / Remarques sur les coûts",
        "custom_pricing_ph": "ex. Lavage de vitres: 0.15$/pi², Décapage/cirage: 0.35$/pi², Forfait désinfection: 450$/intervention...",
        "upload_header": "Téléversement du Devis d'Appel d'Offres",
        "upload_label": "Sélectionnez le document PDF du devis (SEAO, Municipal, Privé)",
        "analyze_btn": "Générer la Matrice de Conformité & l'Analyse d'Écart",
        "spinner": "Analyse du devis par rapport à votre profil d'entreprise...",
        "score_title": "🎯 Recommandation & Indice de Conformité (Go / No-Go)",
        "gap_title": "⚠️ Analyse d'Écarts (Ce qu'il vous manque / Risques)",
        "pricing_fit_title": "💰 Alignement Budgétaire & Grille Tarifaire",
        "mandatory_title": "🚨 Critères Éliminatoires du Devis",
        "forms_title": "📎 Documents et Formulaires Obligatoires à Déposer",
        "err_key": "Clé API manquante. Ajoutez GEMINI_API_KEY dans les Secrets Streamlit.",
        "prompt_role": "Tu es un directeur de propositions senior et un évaluateur expert pour des contrats d'entretien ménager commercial et d'hygiène/salubrité (Jan/San) au Québec/Canada.",
        "prompt_instructions": "Compare minutieusement les exigences du devis PDF avec le profil et la grille tarifaire du contracteur ci-dessous. Retourne un JSON STRICT respectant cette structure exacte :",
    },
    "English": {
        "title": "🏢 JanSan RFP Pilot — Bid Intelligence & Proposal Engine",
        "caption": "Match your company's profile, certifications, and price list directly against tender requirements for gap analysis and automated bid qualification.",
        "tab_profile": "1️⃣ Company Profile & Price List",
        "tab_rfp": "2️⃣ RFP Analyzer & AI Matching",
        "profile_header": "Contractor Credentials & Qualifications",
        "company_name": "Contractor / Company Name",
        "c_certs": "Certifications & Accreditations Held",
        "c_certs_options": [
            "ISO 9001 (Quality)",
            "ISO 14001 (Environmental)",
            "CIMS / CIMS-GB (ISSA)",
            "EcoLogo / Green Seal Certified Products",
            "Valid Workers Comp (WSIB/CNESST) in good standing",
            "General Contractor / Cleaning License",
            "Security Cleared Personnel (Secret / Reliability)",
        ],
        "c_insurance": "Commercial General Liability Coverage ($ CAD)",
        "c_bonding": "Bonding Capacity / Surety Limits",
        "pricing_header": "Price List & Cost Multipliers",
        "hourly_base": "Base Hourly Billing Rate ($/hr)",
        "hourly_super": "Supervisory Hourly Rate ($/hr)",
        "chem_equip_markup": "Chemical & Equipment Markup (%)",
        "custom_pricing_notes": "Custom Itemized Price List & Add-on Services",
        "custom_pricing_ph": "e.g., Window washing: $0.15/sq ft, Strip & wax: $0.35/sq ft, Electrostatic disinfection: $450/visit...",
        "upload_header": "Tender PDF Upload",
        "upload_label": "Select the Tender PDF Document (Buyandsell, SEAO, Corporate RFP)",
        "analyze_btn": "Generate Compliance Matrix & Gap Analysis",
        "spinner": "Cross-referencing tender against your contractor credentials...",
        "score_title": "🎯 Bid Recommendation & Fit Score (Go / No-Go)",
        "gap_title": "⚠️ Gap Analysis & Disqualification Risks",
        "pricing_fit_title": "💰 Pricing Alignment & Applied Rates",
        "mandatory_title": "🚨 RFP Mandatory Disqualifiers",
        "forms_title": "📎 Mandatory Forms, Bonds & Schedules to Submit",
        "err_key": "Missing API key. Please add GEMINI_API_KEY in Streamlit Secrets.",
        "prompt_role": "You are a senior proposal director and procurement evaluator for commercial cleaning and janitorial/sanitation (Jan/San) tenders across Canada.",
        "prompt_instructions": "Thoroughly cross-reference the attached tender PDF with the contractor profile and price list provided below. Return a STRICT JSON object matching this structure:",
    },
}

t = T[lang]

# ----------------- BULLETPROOF AI MODEL RUNNER ----------------- #
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
            with urllib.request.urlopen(req, timeout=60) as response:
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


# ----------------- APP LAYOUT ----------------- #
st.title(t["title"])
st.caption(t["caption"])

tab1, tab2 = st.tabs([t["tab_profile"], t["tab_rfp"]])

# ----------------- TAB 1: CONTRACTOR MASTER PROFILE ----------------- #
with tab1:
    st.subheader(t["profile_header"])
    col_p1, col_p2 = st.columns(2)

    with col_p1:
        co_name = st.text_input(t["company_name"], value="Services d'Entretien Pro-Net Inc.")
        co_certs = st.multiselect(
            t["c_certs"],
            t["c_certs_options"],
            default=[
                t["c_certs_options"][0],
                t["c_certs_options"][3],
                t["c_certs_options"][4],
            ],
        )

    with col_p2:
        co_ins = st.selectbox(
            t["c_insurance"],
            ["2 000 000 $", "5 000 000 $", "10 000 000 $", "20 000 000 $+"],
            index=1,
        )
        co_bond = st.selectbox(
            t["c_bonding"],
            ["Capacité standard (10% cautionnement)", "Capacité majeure (Cautions 50%/100%)", "Aucune caution disponible"],
            index=0,
        )

    st.markdown("---")
    st.subheader(t["pricing_header"])
    col_pr1, col_pr2, col_pr3 = st.columns(3)

    with col_pr1:
        rate_base = st.number_input(t["hourly_base"], min_value=15.0, max_value=150.0, value=28.50, step=0.50)
    with col_pr2:
        rate_super = st.number_input(t["hourly_super"], min_value=20.0, max_value=200.0, value=36.00, step=0.50)
    with col_pr3:
        rate_markup = st.number_input(t["chem_equip_markup"], min_value=0.0, max_value=100.0, value=15.0, step=1.0)

    custom_pricing = st.text_area(
        t["custom_pricing_notes"],
        placeholder=t["custom_pricing_ph"],
        value="Décapage et cirage: 0.35$/pi²\nLavage de vitres intérieur/extérieur: 0.12$/pi²\nLavage de tapis par extraction: 0.22$/pi²\nMain-d'oeuvre d'urgence 24/7: 45.00$/h",
        height=90,
    )

    st.info("💡 Vos données de profil et vos taux sont automatiquement injectés dans l'analyseur de devis.")

# ----------------- TAB 2: RFP ANALYZER & AI MATCHER ----------------- #
with tab2:
    st.subheader(t["upload_header"])
    uploaded_file = st.file_uploader(t["upload_label"], type=["pdf"])

    if uploaded_file is not None:
        if st.button(t["analyze_btn"], type="primary"):
            with st.spinner(t["spinner"]):
                try:
                    api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
                    if not api_key:
                        st.error(t["err_key"])
                        st.stop()

                    pdf_bytes = uploaded_file.read()
                    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

                    contractor_profile = {
                        "company_name": co_name,
                        "held_certifications": co_certs,
                        "insurance_limit": co_ins,
                        "bonding_capacity": co_bond,
                        "hourly_labor_rate": f"{rate_base}$/h",
                        "hourly_supervisor_rate": f"{rate_super}$/h",
                        "chemical_equipment_markup": f"{rate_markup}%",
                        "custom_price_list": custom_pricing,
                    }

                    schema_dict = {
                        "bid_recommendation": {
                            "decision": "GO / CONDITIONAL GO / NO-GO",
                            "match_percentage": "85%",
                            "executive_summary": "Brief synthesis of fit and competitiveness.",
                        },
                        "gap_analysis_risks": [
                            "List of specific certifications, bonding, or technical qualifications required by the RFP that the contractor appears to lack or need to clarify."
                        ],
                        "pricing_strategy_alignment": "Strategic advice applying contractor's hourly/sqft rates against the tender's estimated scope.",
                        "mandatory_disqualifiers": [
                            {
                                "category": "Category",
                                "requirement": "Mandatory requirement details",
                                "penalty": "Disqualification / Rejection",
                            }
                        ],
                        "required_forms_and_bonds": [
                            "List of mandatory annexes, statutory declarations, and bonds to submit"
                        ],
                    }

                    prompt = (
                        f"{t['prompt_role']}\n\n"
                        f"CONTRACTOR PROFILE & PRICE LIST:\n"
                        f"{json.dumps(contractor_profile, ensure_ascii=False, indent=2)}\n\n"
                        f"{t['prompt_instructions']}\n"
                        f"{json.dumps(schema_dict, indent=2)}"
                    )

                    data = run_gemini_analysis(api_key, prompt, pdf_base64)

                    st.success("✅ Analyse complétée avec succès!")

                    # 1. Recommendation Header
                    rec = data.get("bid_recommendation", {})
                    st.subheader(t["score_title"])
                    st.markdown(
                        f"### Résultat : **{rec.get('decision', 'INCONNU')}** (Score d'adéquation : **{rec.get('match_percentage', 'N/A')}**)"
                    )
                    st.info(rec.get("executive_summary", ""))

                    # 2. Two-Column Detailed Analysis
                    col_res1, col_res2 = st.columns(2)

                    with col_res1:
                        st.subheader(t["gap_title"])
                        for gap in data.get("gap_analysis_risks", []):
                            st.warning(f"⚠️ {gap}")

                        st.subheader(t["mandatory_title"])
                        for req in data.get("mandatory_disqualifiers", []):
                            st.error(
                                f"**[{req.get('category', 'Exigence')}]** {req.get('requirement', '')}  \n"
                                f"*{req.get('penalty', 'Rejet')}*"
                            )

                    with col_res2:
                        st.subheader(t["pricing_fit_title"])
                        st.success(data.get("pricing_strategy_alignment", "Aucune remarque spécifique."))

                        st.subheader(t["forms_title"])
                        for form in data.get("required_forms_and_bonds", []):
                            st.markdown(f"• {form}")

                except urllib.error.HTTPError as e:
                    error_details = e.read().decode("utf-8")
                    st.error(f"API Error ({e.code}): {error_details}")
                except Exception as e:
                    st.error(f"Erreur : {str(e)}")
