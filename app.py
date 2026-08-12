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
        "co_name_lbl": "Raison sociale",
        "co_name_val": "Services d'Entretien Expert-Net Inc.",
        "co_addr_lbl": "Adresse & Territoire desservi",
        "co_addr_val": "1500 Boulevard René-Lévesque O, Montréal, QC",
        "co_certs_lbl": "Certifications & Normes détenues",
        "co_certs_opts": [
            "ISO 9001 (Système de gestion de la qualité)",
            "ISO 14001 (Gestion environnementale)",
            "CIMS / CIMS-GB (ISSA - Green Building)",
            "Produits certifiés ÉcoLogo / Green Seal",
            "Attestation CNESST en règle",
            "Attestation Revenu Québec en règle",
            "Licence d'entrepreneur (RBQ)",
            "Personnel avec Enquête de sécurité (Fiabilité/Secret)",
        ],
        "co_ins_lbl": "Assurance responsabilité civile globale",
        "co_ins_opts": ["2 000 000 $ CAD", "5 000 000 $ CAD", "10 000 000 $ CAD", "20 000 000 $+ CAD"],
        "co_bond_lbl": "Capacité de cautionnement (Cautions de soumission / exécution)",
        "co_bond_opts": [
            "Capacité standard (Caution 10% + 50% MO/Matériaux)",
            "Capacité majeure (Cautions 50% / 100%)",
            "Aucune caution disponible",
        ],
        "pricing_h": "Paramètres Financiers & Grille Tarifaire de Base",
        "rate_base_lbl": "Taux horaire préposé à l'entretien ($/h)",
        "rate_super_lbl": "Taux horaire chef d'équipe / superviseur ($/h)",
        "rate_markup_lbl": "Marge sur produits chimiques & consommables (%)",
        "custom_price_h": "Grille de prix des travaux périodiques & spécialisés",
        "custom_price_val": "• Décapage et cirage de planchers vinyle (4 couches): 0.38$/pi²\n• Lavage de vitres intérieur/extérieur: 0.14$/pi²\n• Nettoyage de tapis par extraction à eau chaude: 0.24$/pi²\n• Forfait désinfection électrostatique d'urgence: 450.00$/intervention\n• Taux de main-d'oeuvre d'urgence hors horaire: 48.50$/h",
        "profile_saved": "✅ Profil maître et grille tarifaire sauvegardés.",
        # Side uploader
        "upload_h": "Devis de l'Appel d'Offres (PDF)",
        "upload_lbl": "Téléversez le devis officiel (SEAO, Buyandsell, devis privé)",
        "no_pdf_qual": "👈 Veuillez d'abord téléverser un fichier PDF d'appel d'offres dans le panneau latéral gauche.",
        "no_pdf_bid": "👈 Veuillez téléverser le devis PDF dans la barre latérale pour générer la soumission complète.",
        # Tab 2
        "btn_qual": "1. Analyser la Conformité & Risques (Go / No-Go)",
        "spinner_qual": "Évaluation de la conformité et analyse des écarts en cours...",
        "verdict_lbl": "Décision",
        "score_lbl": "Score d'adéquation",
        "gaps_h": "⚠️ Analyse des Écarts & Risques",
        "mandatory_h": "🚨 Critères Éliminatoires (Pass / Fail)",
        "forms_h": "📎 Formulaires & Cautions Obligatoires",
        "scoring_h": "📊 Grille d'Évaluation & Points",
        "req_lbl": "Exigence",
        "reject_lbl": "Rejet",
        # Tab 3
        "bid_desc": "Générez automatiquement l'ensemble de la soumission prête à être déposée, incluant le calcul des coûts, le plan de travail, les normes et la lettre de présentation.",
        "btn_bid": "2. Générer la Proposition Complète de Soumission",
        "spinner_bid": "Rédaction et calcul de la soumission complète en cours...",
        "exp_letter": "📄 Lettre Formelle de Soumission (Transmittal Letter)",
        "exp_scope": "🏢 Compréhension du Mandat & Envergure des Travaux",
        "exp_price": "💰 Grille Financière & Chiffrage de l'Offre",
        "metric_monthly": "Entretien Régulier (Mensuel)",
        "metric_annual": "Entretien Régulier (Annuel)",
        "metric_total": "Valeur Totale Année 1",
        "periodic_breakdown_h": "Détail des travaux périodiques & spécialisés calculés :",
        "exp_ops": "🛠️ Plan Opérationnel, Supervision & Contrôle Qualité",
        "exp_env": "🌱 Plan Environnemental, SIMDUT & Santé-Sécurité",
        "download_btn": "📥 Télécharger la Soumission Complète (.md)",
        "file_prefix": "Soumission",
        # Prompts & Schemas
        "prompt_role_qual": "Tu es un directeur de propositions sénior et un auditeur d'appels d'offres d'entretien ménager (Jan/San) au Québec/Canada.",
        "prompt_role_bid": "Tu es un directeur de propositions sénior en hygiène et salubrité (Jan/San) au Québec/Canada. Rédige une PROPOSITION COMPLÈTE, FORMELLE ET CHIFFRÉE DE SOUMISSION prête à être soumise au donneur d'ouvrage en français. Applique rigoureusement les taux horaires et les prix au pi² du contracteur ci-dessous aux superficies et fréquences du devis PDF.",
        "err_key": "Clé API manquante. Ajoutez GEMINI_API_KEY dans les Secrets Streamlit.",
    },
    "English": {
        "title": "🏢 JanSan RFP Pilot — Bid Intelligence & Complete Proposal Engine",
        "caption": "Complete tender analysis platform (Buyandsell, MERX, municipal, corporate) and automated submission proposal generator for Jan/San contractors.",
        "tab_profile": "1️⃣ Master Profile & Price Matrix",
        "tab_qual": "2️⃣ Qualification & Gap Matrix",
        "tab_bid": "3️⃣ Complete Bid Proposal Generator",
        # Tab 1
        "profile_h": "Contractor Credentials & Qualifications",
        "co_name_lbl": "Company Legal Name",
        "co_name_val": "Expert-Clean Facility Services Inc.",
        "co_addr_lbl": "Headquarters Address & Service Territory",
        "co_addr_val": "1500 Rene-Levesque Blvd W, Montreal, QC",
        "co_certs_lbl": "Certifications & Accreditations Held",
        "co_certs_opts": [
            "ISO 9001 (Quality Management System)",
            "ISO 14001 (Environmental Management)",
            "CIMS / CIMS-GB (ISSA - Green Building)",
            "EcoLogo / Green Seal Certified Products",
            "WSIB / CNESST Clearance Certificate",
            "Good Standing Tax Certificates (Provincial & Federal)",
            "Valid General Cleaning / Contractor License",
            "Security-Cleared Staff (Reliability / Secret)",
        ],
        "co_ins_lbl": "Commercial General Liability Insurance",
        "co_ins_opts": ["$2,000,000 CAD", "$5,000,000 CAD", "$10,000,000 CAD", "$20,000,000+ CAD"],
        "co_bond_lbl": "Bonding Capacity (Bid Bonds / Performance Surety)",
        "co_bond_opts": [
            "Standard Capacity (10% Bid Bond + 50% Labor/Materials)",
            "Major Capacity (50% / 100% Performance Bonds)",
            "No Surety / Bonding Available",
        ],
        "pricing_h": "Financial Multipliers & Base Rate Matrix",
        "rate_base_lbl": "Base Cleaner Hourly Billing Rate ($/hr)",
        "rate_super_lbl": "Supervisor / Team Lead Hourly Billing Rate ($/hr)",
        "rate_markup_lbl": "Chemical & Supply Markup (%)",
        "custom_price_h": "Periodic & Specialty Services Price List",
        "custom_price_val": "• VCT Strip & Wax (4 coats premium finish): $0.38/sq ft\n• Interior & Exterior Window Washing: $0.14/sq ft\n• Hot Water Extraction Carpet Cleaning: $0.24/sq ft\n• Emergency Electrostatic Disinfection Package: $450.00/call\n• After-hours Emergency Dispatch Rate: $48.50/hr",
        "profile_saved": "✅ Master profile and price list saved successfully.",
        # Side uploader
        "upload_h": "Tender / RFP Document (PDF)",
        "upload_lbl": "Upload official RFP document (Buyandsell, MERX, SEAO, Corporate)",
        "no_pdf_qual": "👈 Please first upload a tender PDF document in the left sidebar.",
        "no_pdf_bid": "👈 Please upload the tender PDF in the sidebar to generate the complete proposal.",
        # Tab 2
        "btn_qual": "1. Analyze Compliance & Gap Risks (Go / No-Go)",
        "spinner_qual": "Evaluating tender compliance against contractor credentials...",
        "verdict_lbl": "Verdict",
        "score_lbl": "Suitability Score",
        "gaps_h": "⚠️ Gap Analysis & Compliance Risks",
        "mandatory_h": "🚨 Mandatory Disqualifiers (Pass / Fail)",
        "forms_h": "📎 Mandatory Forms, Bonds & Schedules",
        "scoring_h": "📊 Evaluation Grid & Points Breakdown",
        "req_lbl": "Requirement",
        "reject_lbl": "Rejection",
        # Tab 3
        "bid_desc": "Automatically generate the complete, submission-ready proposal package including calculated pricing schedules, methodology, quality control, WHMIS/Eco compliance, and transmittal letter.",
        "btn_bid": "2. Generate Complete Submission Proposal",
        "spinner_bid": "Drafting complete itemized proposal and pricing schedules in English...",
        "exp_letter": "📄 Formal Transmittal & Submission Letter",
        "exp_scope": "🏢 Understanding of Mandate & Scope of Work",
        "exp_price": "💰 Calculated Pricing & Financial Breakdown",
        "metric_monthly": "Routine Cleaning (Monthly)",
        "metric_annual": "Routine Cleaning (Annual)",
        "metric_total": "Total Year 1 Contract Value",
        "periodic_breakdown_h": "Calculated Periodic & Specialty Service Schedule:",
        "exp_ops": "🛠️ Operational Plan, Supervision & Quality Assurance",
        "exp_env": "🌱 Environmental Plan, WHMIS & Health-Safety",
        "download_btn": "📥 Download Complete Bid Proposal (.md)",
        "file_prefix": "Bid_Proposal",
        # Prompts & Schemas
        "prompt_role_qual": "You are a senior proposal director and procurement evaluator for commercial cleaning and Jan/San tenders across Canada.",
        "prompt_role_bid": "You are a senior proposal director in facility hygiene and Jan/San procurement. Write a COMPLETE, FORMAL, AND ITEMIZED SUBMISSION PROPOSAL ready to submit to the client in English. Rigorously apply the contractor's hourly rates and sq ft pricing below to the tender's square footage and frequencies.",
        "err_key": "Missing API key. Please add GEMINI_API_KEY in Streamlit Secrets.",
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
        co_name = st.text_input(t["co_name_lbl"], value=t["co_name_val"])
        co_addr = st.text_input(t["co_addr_lbl"], value=t["co_addr_val"])
        co_certs = st.multiselect(
            t["co_certs_lbl"],
            t["co_certs_opts"],
            default=[t["co_certs_opts"][0], t["co_certs_opts"][3], t["co_certs_opts"][4]],
        )
    with col2:
        co_ins = st.selectbox(t["co_ins_lbl"], t["co_ins_opts"], index=1)
        co_bond = st.selectbox(t["co_bond_lbl"], t["co_bond_opts"], index=0)

    st.markdown("---")
    st.subheader(t["pricing_h"])
    pcol1, pcol2, pcol3 = st.columns(3)
    with pcol1:
        rate_base = st.number_input(t["rate_base_lbl"], min_value=15.0, max_value=200.0, value=29.50, step=0.50)
    with pcol2:
        rate_super = st.number_input(t["rate_super_lbl"], min_value=20.0, max_value=250.0, value=38.00, step=0.50)
    with pcol3:
        rate_markup = st.number_input(t["rate_markup_lbl"], min_value=0.0, max_value=100.0, value=15.0, step=1.0)

    st.markdown(f"**{t['custom_price_h']}**")
    custom_pricing = st.text_area(
        " ",
        value=t["custom_price_val"],
        height=120,
    )

    contractor_profile = {
        "company_name": co_name,
        "company_address": co_addr,
        "held_certifications": co_certs,
        "insurance_coverage": co_ins,
        "bonding_capacity": co_bond,
        "base_cleaner_rate": f"${rate_base}/hr",
        "supervisor_rate": f"${rate_super}/hr",
        "chemical_markup": f"{rate_markup}%",
        "itemized_price_list": custom_pricing,
    }
    st.session_state["contractor_profile"] = contractor_profile
    st.success(t["profile_saved"])

# ----------------- SHARED UPLOADER ----------------- #
st.sidebar.markdown("---")
st.sidebar.subheader(t["upload_h"])
uploaded_pdf = st.sidebar.file_uploader(t["upload_lbl"], type=["pdf"])

# ----------------- TAB 2: QUALIFICATION & GAP ANALYSIS ----------------- #
with tab_qual:
    if uploaded_pdf is None:
        st.info(t["no_pdf_qual"])
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
                            "executive_rationale": "Rationale explaining why this bid is or isn't a fit.",
                        },
                        "gap_analysis_missing_requirements": [
                            "Specific certification, experience threshold, or insurance limit required that contractor lacks."
                        ],
                        "mandatory_disqualifiers": [
                            {
                                "category": "Category",
                                "requirement": "Mandatory requirement details",
                                "penalty": "Disqualification / Rejection",
                            }
                        ],
                        "required_annexes_and_forms": [
                            "Mandatory submission schedules, security forms, and bid bonds to include."
                        ],
                        "scoring_matrix_summary": [
                            "Point distribution breakdown for technical scoring and pricing."
                        ],
                    }

                    prompt = (
                        f"{t['prompt_role_qual']}\n\n"
                        f"CONTRACTOR PROFILE & PRICE LIST:\n{json.dumps(contractor_profile, ensure_ascii=False, indent=2)}\n\n"
                        f"Analyze the attached RFP PDF against the contractor's profile. Return a STRICT JSON object in {lang} matching this structure:\n"
                        f"{json.dumps(schema_qual, indent=2)}"
                    )

                    data = run_gemini_analysis(api_key, prompt, pdf_base64)
                    st.session_state["qual_data"] = data

                except Exception as e:
                    st.error(f"Error: {str(e)}")

        if "qual_data" in st.session_state:
            qdata = st.session_state["qual_data"]
            verdict = qdata.get("go_no_go_verdict", {})
            st.markdown(f"### {t['verdict_lbl']} : **{verdict.get('decision', 'N/A')}** ({t['score_lbl']} : **{verdict.get('suitability_score', 'N/A')}**)")
            st.info(verdict.get("executive_rationale", ""))

            c1, c2 = st.columns(2)
            with c1:
                st.subheader(t["gaps_h"])
                for gap in qdata.get("gap_analysis_missing_requirements", []):
                    st.warning(f"• {gap}")

                st.subheader(t["mandatory_h"])
                for item in qdata.get("mandatory_disqualifiers", []):
                    st.error(f"**[{item.get('category', t['req_lbl'])}]** {item.get('requirement', '')}  \n*{item.get('penalty', t['reject_lbl'])}*")

            with c2:
                st.subheader(t["forms_h"])
                for f in qdata.get("required_annexes_and_forms", []):
                    st.markdown(f"• {f}")

                st.subheader(t["scoring_h"])
                for s in qdata.get("scoring_matrix_summary", []):
                    st.markdown(f"• {s}")

# ----------------- TAB 3: COMPLETE BID PROPOSAL GENERATOR ----------------- #
with tab_bid:
    if uploaded_pdf is None:
        st.info(t["no_pdf_bid"])
    else:
        st.write(t["bid_desc"])
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
                        "proposal_title": "Full formal title of the submission proposal",
                        "transmittal_letter": "Complete formal transmittal cover letter addressed to the issuing client, signed on behalf of the contractor.",
                        "executive_summary_scope": "Comprehensive understanding of the mandate, facility square footage, operating hours, frequencies, and standards.",
                        "calculated_pricing_table": {
                            "routine_cleaning_monthly": "$X,XXX.XX CAD",
                            "routine_cleaning_annual": "$XX,XXX.XX CAD",
                            "periodic_services_breakdown": [
                                "Detailed periodic task (e.g. strip & wax, windows), frequency, applied unit rate based on contractor's price list"
                            ],
                            "total_first_year_contract_value": "$XXX,XXX.XX CAD",
                        },
                        "operational_plan_and_staffing": "Staffing plan, supervisor-to-cleaner ratios, shift schedules, inspection workflows, and QA logbook protocol.",
                        "environmental_and_safety_commitments": "WHMIS/SIMDUT compliance plan, SDS availability, EcoLogo chemical commitments, HEPA equipment standard.",
                        "compliance_guarantees": "Formal declarations of compliance with labor decrees, CNESST/WSIB, and requested insurance coverage.",
                    }

                    prompt_bid = (
                        f"{t['prompt_role_bid']}\n\n"
                        f"CONTRACTOR PROFILE & PRICE LIST:\n{json.dumps(contractor_profile, ensure_ascii=False, indent=2)}\n\n"
                        f"Write the entire proposal in {lang}. Return a STRICT JSON object matching this structure:\n"
                        f"{json.dumps(schema_bid, indent=2)}"
                    )

                    bid_data = run_gemini_analysis(api_key, prompt_bid, pdf_base64)
                    st.session_state["bid_data"] = bid_data

                except Exception as e:
                    st.error(f"Error: {str(e)}")

        if "bid_data" in st.session_state:
            b = st.session_state["bid_data"]
            st.markdown(f"## {b.get('proposal_title', 'Proposal Document')}")

            # 1. Submission Letter
            with st.expander(t["exp_letter"], expanded=True):
                st.markdown(b.get("transmittal_letter", ""))

            # 2. Executive Scope
            with st.expander(t["exp_scope"], expanded=True):
                st.markdown(b.get("executive_summary_scope", ""))

            # 3. Calculated Pricing Schedule
            with st.expander(t["exp_price"], expanded=True):
                ptable = b.get("calculated_pricing_table", {})
                m1, m2, m3 = st.columns(3)
                m1.metric(t["metric_monthly"], ptable.get("routine_cleaning_monthly", "N/A"))
                m2.metric(t["metric_annual"], ptable.get("routine_cleaning_annual", "N/A"))
                m3.metric(t["metric_total"], ptable.get("total_first_year_contract_value", "N/A"))

                st.markdown(f"#### {t['periodic_breakdown_h']}")
                for s_item in ptable.get("periodic_services_breakdown", []):
                    st.markdown(f"• {s_item}")

            # 4. Operations & Quality Control
            with st.expander(t["exp_ops"], expanded=False):
                st.markdown(b.get("operational_plan_and_staffing", ""))

            # 5. Environmental & Safety Standards
            with st.expander(t["exp_env"], expanded=False):
                st.markdown(b.get("environmental_and_safety_commitments", ""))
                st.markdown("---")
                st.markdown(b.get("compliance_guarantees", ""))

            # Download compiled document
            if lang == "English":
                compiled_md = f"""# {b.get('proposal_title', 'Commercial Bid Proposal')}

## 1. Formal Transmittal Cover Letter
{b.get('transmittal_letter', '')}

---

## 2. Understanding of Mandate & Scope of Work
{b.get('executive_summary_scope', '')}

---

## 3. Financial Summary & Pricing Schedule
- **Routine Cleaning (Monthly):** {ptable.get('routine_cleaning_monthly', 'N/A')}
- **Routine Cleaning (Annual):** {ptable.get('routine_cleaning_annual', 'N/A')}
- **Total Estimated First-Year Value:** {ptable.get('total_first_year_contract_value', 'N/A')}

### Periodic & Specialty Service Schedule:
