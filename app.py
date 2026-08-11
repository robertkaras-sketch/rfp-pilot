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
        "title": (
            "📋 Intelligence d'Appels d'Offres Jan/San & Bâtiments (Québec /"
            " Canada)"
        ),
        "caption": (
            "Téléversez un devis (SEAO, municipal ou corporatif) pour extraire"
            " la matrice de conformité et les critères éliminatoires."
        ),
        "upload_label": "Sélectionnez le fichier PDF du devis (RFP)",
        "button_text": "Lancer l'analyse du devis",
        "spinner_text": (
            "Analyse directe du document PDF par l'IA en cours... (~15"
            " secondes)"
        ),
        "success_text": "Analyse complétée avec succès !",
        "error_api_key": (
            "Clé API manquante. Ajoutez GEMINI_API_KEY dans les Secrets"
            " Streamlit."
        ),
        "error_generic": "Une erreur est survenue lors de l'analyse :",
        "section_mandatory": "🚨 Critères éliminatoires (Pass / Fail)",
        "section_forms": "📎 Formulaires & Annexes obligatoires à joindre",
        "section_scoring": "📊 Grille de pointage & Évaluation technique",
        "section_standards": (
            "🌱 Normes environnementales & Produits (SIMDUT / ÉcoLogo)"
        ),
        "impact_label": "Impact",
        "category_default": "Exigence",
        "prompt_role": (
            "Tu es un directeur de propositions senior spécialisé dans les"
            " appels d'offres d'entretien ménager commercial et"
            " d'hygiène/salubrité (Jan/San) au Québec et au Canada (normes"
            " SEAO, CNESST, Décret d'entretien d'édifices publics, ÉcoLogo,"
            " SIMDUT)."
        ),
        "prompt_instruction": (
            "Analyse le devis PDF ci-joint et retourne un objet JSON STRICT en"
            " FRANÇAIS avec cette structure exacte :"
        ),
    },
    "English": {
        "title": "📋 Jan/San & Facility Tender Intelligence (Quebec / Canada)",
        "caption": (
            "Upload any commercial or public tender PDF (SEAO, Buyandsell,"
            " etc.) to instantly extract the compliance matrix and mandatory"
            " pass/fail criteria."
        ),
        "upload_label": "Select the Tender PDF Document (RFP)",
        "button_text": "Analyze Tender Document",
        "spinner_text": (
            "Analyzing PDF document directly via AI... (~15 seconds)"
        ),
        "success_text": "Analysis completed successfully!",
        "error_api_key": (
            "Missing API key. Please add GEMINI_API_KEY in Streamlit Secrets."
        ),
        "error_generic": "An error occurred during analysis:",
        "section_mandatory": "🚨 Mandatory Disqualifiers (Pass / Fail)",
        "section_forms": "📎 Required Forms, Bonds & Attachments",
        "section_scoring": "📊 Technical Scoring Matrix & Evaluation",
        "section_standards": (
            "🌱 Environmental Standards & Products (WHMIS / EcoLogo / Green"
            " Seal)"
        ),
        "impact_label": "Impact",
        "category_default": "Requirement",
        "prompt_role": (
            "You are a senior bid and proposal manager specializing in"
            " commercial janitorial, cleaning, and facility sanitation"
            " (Jan/San) tenders across Quebec and Canada (SEAO standards,"
            " CNESST/WCB, Janitorial Decree rules, EcoLogo, WHMIS)."
        ),
        "prompt_instruction": (
            "Analyze the attached tender PDF and return a STRICT JSON object in"
            " ENGLISH with this exact structure:"
        ),
    },
}

t = T[lang]

# ----------------- UI HEADER ----------------- #
st.title(t["title"])
st.caption(t["caption"])

# ----------------- FILE UPLOADER ----------------- #
uploaded_file = st.file_uploader(t["upload_label"], type=["pdf"])

if uploaded_file is not None:
    if st.button(t["button_text"], type="primary"):
        with st.spinner(t["spinner_text"]):
            try:
                # 1. Retrieve API Key
                api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get(
                    "GEMINI_API_KEY"
                )
                if not api_key:
                    st.error(t["error_api_key"])
                    st.stop()

                # 2. Convert PDF bytes directly to base64 (Zero external dependencies)
                pdf_bytes = uploaded_file.read()
                pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

                prompt = f"""
                {t["prompt_role"]}
                
                {t["prompt_instruction"]}
                {{
                  "mandatory_disqualifiers": [
                    {{"category": "Category / Catégorie", "requirement": "Description", "penalty_or_impact": "Disqualification / Rejet automatique"}}
                  ],
                  "required_attachments_and_forms": ["List of mandatory forms, bonds, certificates / Liste des formulaires, cautions et attestations"],
                  "technical_scoring_criteria": ["Scoring criteria & points distribution / Grille de pointage et éléments notés"],
                  "product_and_environmental_standards": ["EcoLogo, WHMIS/SIMDUT, chemical dispensing & equipment requirements / Normes ÉcoLogo, SIMDUT, dilution et équipements"]
                }}
                """

                # 3. Direct Gemini API Call with native inline PDF support
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": "application/pdf",
                                    "data": pdf_base64,
                                }
                            },
                        ]
                    }],
                    "generationConfig": {"responseMimeType": "application/json"},
                }

                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )

                with urllib.request.urlopen(req) as response:
                    result = json.loads(response.read().decode("utf-8"))
                    raw_text = result["candidates"][0]["content"]["parts"][0]["text"]
                    data = json.loads(raw_text)

                st.success(t["success_text"])

                # 4. Render Results in 2 Clean Columns
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader(t["section_mandatory"])
                    for item in data.get("mandatory_disqualifiers", []):
                        st.error(
                            f"**[{item.get('category', t['category_default'])}]**"
                            f" {item.get('requirement', '')}  \n*{t['impact_label']} :"
                            f" {item.get('penalty_or_impact', 'Mandatory')}*"
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
