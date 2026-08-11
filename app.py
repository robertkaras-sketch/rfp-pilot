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
        "contents": [{
            "parts": [
                {"text": prompt_text},
                {
                    "inline_data": {
                        "mime_type": "application/pdf",
                        "data": pdf_b64,
                    }
                },
            ]
        }],
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

                prompt = f"""
                {t["prompt_role"]}
                
                {t["prompt_instruction"]}
                {{
                  "mandatory_disqualifiers": [
                    {{"category": "Category / Catégorie", "requirement": "Description", "penalty_or_impact": "Disqualification / Rejet automatique"}}
                  ],
                  "required_attachments_and_forms": ["List of mandatory forms, bonds, certificates / Liste des formulaires, cautions et attestations"],
                  "technical_scoring_criteria": ["Scoring criteria & points distribution / Grille de pointage et éléments notés"],
