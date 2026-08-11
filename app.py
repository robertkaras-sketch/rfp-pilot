import json
import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from pypdf import PdfReader
import streamlit as st

# Page setup
st.set_page_config(
    page_title="JanSan RFP Engine QC", page_icon="📋", layout="wide"
)

st.title("📋 Jan/San & Facility Tender Intelligence (Québec / Canada)")
st.caption(
    "Téléversez un devis ou appel d'offres (SEAO / Corporatif) pour extraire la"
    " matrice de conformité et critères obligatoires."
)


# Define Schema
class ComplianceItem(BaseModel):
  requirement: str = Field(
      description="The specific rule, insurance threshold, bond, or condition."
  )
  category: str = Field(
      description=(
          "Category (e.g., CNESST, Assurance RG, ÉcoLogo/SIMDUT, Décret,"
          " Expérience)."
      )
  )
  penalty_or_impact: str = Field(
      description="Rejet automatique / Pénalité / Requis."
  )


class JanSanRfpExtraction(BaseModel):
  mandatory_disqualifiers: list[ComplianceItem] = Field(
      description="Critères éliminatoires stricts (pass/fail)."
  )
  technical_scoring_criteria: list[str] = Field(
      description="Grille d'évaluation technique et pointage."
  )
  product_and_environmental_standards: list[str] = Field(
      description=(
          "Normes ÉcoLogo, SIMDUT/WHMIS, fiches FDS et équipements exigés."
      )
  )
  required_attachments_and_forms: list[str] = Field(
      description=(
          "Formulaires, attestations CNESST, cautionnements et annexes requis."
      )
  )


# Upload box
uploaded_file = st.file_uploader(
    "Sélectionnez le fichier PDF du devis (RFP)", type=["pdf"]
)

if uploaded_file is not None:
  if st.button("Lancer l'analyse du devis / Analyze Tender", type="primary"):
    # Read PDF text
    with st.spinner(
        "Extraction du texte et analyse par l'IA en cours (environ 15"
        " secondes)..."
    ):
      reader = PdfReader(uploaded_file)
      pdf_text = ""
      for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
          pdf_text += f"\n--- Page {i+1} ---\n" + text

      # Gemini Client
      client = genai.Client()

      prompt = f"""
            Tu es un directeur de propositions senior spécialisé dans les appels d'offres d'entretien ménager commercial et d'hygiène/salubrité (Jan/San) au Québec et au Canada (normes SEAO, CNESST, Décret d'entretien d'édifices publics, ÉcoLogo, SIMDUT).
            Analyse le texte de devis suivant et extrait la matrice de conformité complète en JSON strict.
            
            TEXTE DE L'APPEL D'OFFRES:
            {pdf_text[:40000]}
            """

      response = client.models.generate_content(
          model="gemini-2.5-flash",
          contents=prompt,
          config=types.GenerateContentConfig(
              response_mime_type="application/json",
              response_schema=JanSanRfpExtraction,
              temperature=0.1,
          ),
      )

      data = json.loads(response.text)

    st.success("Analyse terminée avec succès !")

    # Display 2 clean columns
    col1, col2 = st.columns(2)

    with col1:
      st.subheader("🚨 Critères éliminatoires & Clauses obligatoires")
      for item in data.get("mandatory_disqualifiers", []):
        st.error(
            f"**[{item['category']}]** {item['requirement']}  \n*Impact :"
            f" {item['penalty_or_impact']}*"
        )

      st.subheader("📎 Formulaires & Annexes à joindre obligatoirement")
      for form in data.get("required_attachments_and_forms", []):
        st.markdown(f"• {form}")

    with col2:
      st.subheader("📊 Grille de pointage technique")
      for score in data.get("technical_scoring_criteria", []):
        st.info(f"**Pointage :** {score}")

      st.subheader("🌱 Normes environnementales & Produits (SIMDUT / ÉcoLogo)")
      for std in data.get("product_and_environmental_standards", []):
        st.markdown(f"• {std}")