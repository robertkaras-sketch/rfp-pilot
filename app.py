import base64
import json
import os
import urllib.error
import urllib.request
import streamlit as st

# Page setup
st.set_page_config(
    page_title="JanSan RFP Engine QC / Moteur d'AO JanSan",
    page_icon="📋",
    layout="wide",
)

# ----------------- LANGUAGE SELECTION & DICTIONARY ----------------- #
lang = st.sidebar.radio(
    "🌐 Langue / Language", ("Français", "English"), index=0
)

T = {
    "Français": {
        "title": "📋 Intelligence d'Appels d'Offres Jan/San & Profil Client",
        "caption": "Téléversez un devis (SEAO, municipal, corporatif) et saisissez les renseignements client/soumissionnaire pour générer une analyse de conformité ciblée.",
        "customer_section": "🏢 Informations sur le Client & le Contrat",
        "client_name": "Nom de l'organisme / Client",
        "client_name_ph": "ex. Ville de Montréal, CISSS, Hydro-Québec...",
        "facility_type": "Type de bâtiment / Installation",
        "facility_types": ["Bureaux corporatifs", "Établissement de santé / CHSLD", "Établissement scolaire / Universitaire", "Édifice municipal / Gouvernemental", "Industriel / Entrepôt", "Autre"],
        "sq_footage": "Superficie approximative (pi²)",
        "sq_footage_ph": "ex. 85 000",
        "est_budget": "Budget estimé / Valeur contractuelle",
        "est_budget_ph": "ex. 250 000 $ / an",
        "decree_status": "Assujetti au Décret d'entretien d'édifices publics ?",
        "decree_options": ["Oui (Zone 1 - Montréal/Laval)", "Oui (Zone 2 - Régions)", "Non / Exempte", "À déterminer"],
        "additional_notes": "Notes stratégiques ou exigences particulières",
        "additional_notes_ph": "ex. Soumission conjointe, contraintes d'horaires de soir, certifications ISO requises...",
        "upload_label": "Sélectionnez le fichier PDF du devis (RFP)",
        "button_text": "Lancer l'analyse du devis & conformité",
        "spinner_text": "Analyse directe du devis et du profil client en cours... (~15 secondes)",
        "success_text": "Analyse complétée avec succès !",
        "error_api_key": "Clé API manquante. Ajoutez GEMINI_API_KEY dans les Secrets Streamlit.",
        "error_generic": "Une erreur est survenue lors de l'analyse :",
        "summary_title": "📌 Synthèse & Alignement Client",
        "section_mandatory": "🚨 Critères éliminatoires (Pass / Fail)",
        "section_forms": "📎 Formulaires & Annexes obligatoires à joindre",
        "section_scoring": "📊 Grille de pointage & Évaluation technique",
        "section_standards": "🌱 Normes environnementales & Produits (SIMDUT / ÉcoLogo)",
        "impact_label": "Impact",
        "category_default": "Exigence",
        "prompt_role": "Tu es un directeur de propositions senior spécialisé dans les appels d'offres d'entretien ménager commercial et d'hygiène/salubrité (Jan/San) au Québec et au Canada (normes SEAO, CNESST, Décret d'entretien d'édifices publics, ÉcoLogo, SIMDUT).",
        "prompt_instruction": "Analyse le devis PDF ci-joint en tenant compte du profil client fourni, et retourne un objet JSON STRICT respectant cette structure :",
    },
    "English": {
        "title": "📋 Jan/San Tender Intelligence & Customer Profile",
        "caption": "Upload any commercial or public tender PDF (SEAO, Buyandsell, etc.) and enter customer/project details to extract tailored compliance matrices.",
        "customer_section": "🏢 Customer & Contract Information",
        "client_name": "Client / Issuing Organization Name",
        "client_name_ph": "e.g., City of Montreal, Health Authority, Public Works...",
        "facility_type": "Facility / Building Type",
        "facility_types": ["Corporate Offices", "Healthcare / Hospital / Long-term care", "School Board / University", "Municipal / Government Building", "Industrial / Warehouse", "Other"],
        "sq_footage": "Approximate Square Footage (sq ft)",
        "sq_footage_ph": "e.g., 85,000",
        "est_budget": "Estimated Contract Value / Budget",
        "est_budget_ph": "e.g., $250,000 / year",
        "decree_status": "Subject to Janitorial Public Building Decree / Prevailing Wage?",
        "decree_options": ["Yes (Zone 1)", "Yes (Zone 2)", "No / Exempt", "To be determined"],
        "additional_notes": "Strategic Notes / Internal Priorities",
        "additional_notes_ph": "e.g., Joint venture, night shift constraints, specific ISO certifications...",
        "upload_label": "Select the Tender PDF Document (RFP)",
        "button_text": "Analyze Tender & Compliance Matrix",
        "spinner_text": "Analyzing tender PDF and client profile via AI... (~15 seconds)",
        "success_text": "Analysis completed successfully!",
        "error_api_key": "Missing API key. Please add GEMINI_API_KEY in Streamlit Secrets.",
        "error_generic": "An error occurred during analysis:",
        "summary_title": "📌 Client Summary & Bid Alignment",
        "section_mandatory": "🚨 Mandatory Disqualifiers (Pass / Fail)",
        "section_forms": "📎 Required Forms, Bonds & Attachments",
        "section_scoring": "📊 Technical Scoring Matrix & Evaluation",
        "section_standards": "🌱 Environmental Standards & Products (WHMIS / EcoLogo / Green Seal)",
        "impact_label": "Impact",
        "category_default": "Requirement",
        "prompt_role": "You are a senior bid and proposal manager specializing in commercial janitorial, cleaning, and facility sanitation (Jan/San) tenders across Quebec and Canada (SEAO standards, CNESST/WCB, Janitorial Decree rules, EcoLogo, WHMIS).",
        "prompt_instruction": "Analyze the attached tender PDF in light of the provided customer context, and return a STRICT JSON object matching this structure:",
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
                methods = m.get("supportedGenerationMethods", [])
                if "generateContent" in methods:
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
    candidate_list = []
    for m in candidates:
        if m and m not in seen:
            seen.add(m)
            candidate_list.append(m)

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
        except urllib.error.HTTPError as e:
            last_error = e
            continue
        except Exception as e:
            last_error = e
            continue

    if last_error:
        raise last_error
    raise RuntimeError("No compatible active model could be reached.")


# ----------------- UI HEADER ----------------- #
st.title(t["title"])
st.caption(t["caption"])

# ----------------- CUSTOMER INFORMATION INPUT FORM ----------------- #
st.subheader(t["customer_section"])

c_col1, c_col2 = st.columns(2)

with c_col1:
    cust_name = st.text_input(t["client_name"], placeholder=t["client_name_ph"])
    cust_facility = st.selectbox(t["facility_type"], t["facility_types"])
    cust_sqft = st.text_input(t["sq_footage"], placeholder=t["sq_footage_ph"])

with c_col2:
    cust_budget = st.text_input(t["est_budget"], placeholder=t["est_budget_ph"])
    cust_decree = st.selectbox(t["decree_status"], t["decree_options"])
    cust_notes = st.text_area(t["additional_notes"], placeholder=t["additional_notes_ph"], height=68)

st.markdown("---")

# ----------------- FILE UPLOADER ----------------- #
uploaded_file = st.file_uploader(t["upload_label"], type=["pdf"])

if uploaded_file is not None:
    if st.button(t["button_text"], type="primary"):
        with st.spinner(t["spinner_text"]):
            try:
                # 1. Retrieve API Key
                api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
                if not api_key:
                    st.error(t["error_api_key"])
                    st.stop()

                # 2. Convert PDF to base64
                pdf_bytes = uploaded_file.read()
                pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

                # 3. Contextualize with Customer Information
                customer_context = (
                    f"--- CUSTOMER & BID CONTEXT ---\n"
                    f"Target Client: {cust_name or 'Not specified'}\n"
                    f"Facility Type: {cust_facility}\n"
                    f"Square Footage: {cust_sqft or 'Not specified'}\n"
                    f"Estimated Budget / Value: {cust_budget or 'Not specified'}\n"
                    f"Decree / Wage Standard: {cust_decree}\n"
                    f"Specific Notes: {cust_notes or 'None'}\n"
                    f"-------------------------------"
                )

                schema_dict = {
                    "client_alignment_summary": "High level evaluation of fit, scope complexity, and key risk factors based on customer info and tender requirements",
                    "mandatory_disqualifiers": [
                        {
                            "category": "Category / Catégorie",
                            "requirement": "Description",
                            "penalty_or_impact": "Disqualification / Rejet automatique",
                        }
                    ],
                    "required_attachments_and_forms": [
                        "List of mandatory forms, bonds, certificates"
                    ],
                    "technical_scoring_criteria": [
                        "Scoring criteria & points distribution"
                    ],
                    "product_and_environmental_standards": [
                        "EcoLogo, WHMIS/SIMDUT, chemical dispensing & equipment requirements"
                    ],
                }

                prompt = (
                    f"{t['prompt_role']}\n\n"
                    f"{customer_context}\n\n"
                    f"{t['prompt_instruction']}\n"
                    f"{json.dumps(schema_dict, indent=2)}"
                )

                # 4. Run Analysis
                data = run_gemini_analysis(api_key, prompt, pdf_base64)

                st.success(t["success_text"])

                # 5. Display Customer Summary Alignment
                if data.get("client_alignment_summary"):
                    st.subheader(t["summary_title"])
                    st.info(data["client_alignment_summary"])

                # 6. Display Detailed Results in 2 Columns
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader(t["section_mandatory"])
                    for item in data.get("mandatory_disqualifiers", []):
                        st.error(
                            f"**[{item.get('category', t['category_default'])}]** "
                            f"{item.get('requirement', '')}  \n"
                            f"*{t['impact_label']} : {item.get('penalty_or_impact', 'Mandatory')}*"
                        )

                    st.subheader(t["section_forms"])
                    for form in data.get("required_attachments_and_forms", []):
                        st.markdown(f"• {form}")

                with col2:
                    st.subheader(t["section_scoring"])
                    for score in data.get("technical_scoring_criteria", []):
                        st.info(f"**Pointage / Scoring:** {score}")

                    st.subheader(t["section_standards"])
                    for std in data.get("product_and_environmental_standards", []):
                        st.markdown(f"• {std}")

            except urllib.error.HTTPError as e:
                error_details = e.read().decode("utf-8")
                st.error(f"API Error ({e.code}): {error_details}")
            except Exception as e:
                st.error(f"{t['error_generic']} {str(e)}")
