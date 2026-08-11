import json
import os
import google.generativeai as genai
from pypdf import PdfReader
import streamlit as st

# Page setup
st.set_page_config(
    page_title="JanSan RFP Engine QC", page_icon="📋", layout="wide"
)

st.title("📋 Jan/San Tender Intelligence (Québec / Canada)")
st.caption(
    "Téléversez un devis (SEAO / Corporatif) pour extraire la matrice de"
    " conformité et les critères obligatoires."
)

# File Uploader
uploaded_file = st.file_uploader(
    "Sélectionnez le fichier PDF du devis", type=["pdf"]
)

if uploaded_file is not None:
  if st.button("Lancer l'analyse du devis", type="primary"):
    with st.spinner("Analyse du devis en cours... (~15 secondes)"):
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
          st.error(
              "Clé API manquante. Ajoutez GEMINI_API_KEY dans les Secrets"
              " Streamlit."
          )
          st.stop()

        # 3. Configure Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f"""
                Tu es un directeur de propositions senior spécialisé dans les appels d'offres d'entretien ménager commercial et d'hygiène/salubrité (Jan/San) au Québec et au Canada (normes SEAO, CNESST, Décret d'entretien d'édifices publics, ÉcoLogo, SIMDUT).
                
                Analyse le texte de devis suivant et retourne un objet JSON STRICT avec cette structure exacte :
                {{
                  "mandatory_disqualifiers": [
                    {{"category": "CNESST / Assurance / etc.", "requirement": "description", "penalty_or_impact": "Rejet automatique"}}
                  ],
                  "required_attachments_and_forms": ["Liste des formulaires et attestations requis"],
                  "technical_scoring_criteria": ["Grille de pointage et éléments notés"],
                  "product_and_environmental_standards": ["Normes ÉcoLogo, SIMDUT, équipements demandés"]
                }}
                
                TEXTE DE L'APPEL D'OFFRES:
                {pdf_text[:40000]}
                """

        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"},
        )

        data = json.loads(response.text)

        st.success("Analyse complétée avec succès !")

        # 4. Render Results
        col1, col2 = st.columns(2)

        with col1:
          st.subheader("🚨 Critères éliminatoires")
          for item in data.get("mandatory_disqualifiers", []):
            st.error(
                f"**[{item.get('category', 'Exigence')}]**"
                f" {item.get('requirement', '')}  \n*Impact :"
                f" {item.get('penalty_or_impact', 'Requis')}*"
            )

          st.subheader("📎 Formulaires & Annexes obligatoires")
          for form in data.get("required_attachments_and_forms", []):
            st.markdown(f"• {form}")

        with col2:
          st.subheader("📊 Grille de pointage technique")
          for score in data.get("technical_scoring_criteria", []):
            st.info(f"**Pointage :** {score}")

          st.subheader("🌱 Normes environnementales & Produits")
          for std in data.get("product_and_environmental_standards", []):
            st.markdown(f"• {std}")

      except Exception as e:
        st.error(f"Une erreur est survenue lors de l'analyse : {str(e)}")
