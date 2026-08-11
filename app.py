import json
import os
import google.generativeai as genai
from pypdf import PdfReader
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
        "spinner_text": "Analyse du devis en cours... (~15 secondes)",
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
            "Analyse le texte de devis suivant et retourne un objet JSON"
            " STRICT en FRANÇAIS avec cette structure exacte :"
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
        "spinner_text": "Analyzing document... (~15 seconds)",
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
            "Analyze the following tender text and return a STRICT JSON object"
            " in ENGLISH with this exact structure:"
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
        # 1. Extract PDF text
        reader = PdfReader(uploaded_file)
        pdf_text = ""
        for i, page in enumerate(reader.pages):
          text = page.extract_text()
          if text:
            pdf_text += f"\n--- Page {i+1} ---\n" + text

        # 2. Retrieve API Key
        api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get(
            "GEMINI_API_KEY"
        )
        if not api_key:
          st.error(t["error_api_key"])
          st.stop()

        # 3. Configure Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

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
                
                TENDER TEXT / TEXTE DU DEVIS:
                {pdf_text[:40000]}
                """

        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"},
        )

        data = json.loads(response.text)

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

      except Exception as e:
        st.error(f"{t['error_generic']} {str(e)}")
