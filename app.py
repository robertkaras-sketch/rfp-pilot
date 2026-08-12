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

# ----------------- SIDEBAR SELECTION ----------------- #
lang = st.sidebar.radio("🌐 Langue / Language", ("Français", "English"), index=0)

mode_options = {
    "Français": (
        "🧹 Services d'entretien ménager (Main-d'oeuvre & Contrats)",
        "📦 Fournitures, Produits & Équipements (Articles & Catalogue)",
    ),
    "English": (
        "🧹 Jan/San Facility Services (Labor & Service Contracts)",
        "📦 Jan/San Supplies, Goods & Equipment (Itemized Product Bids)",
    ),
}

rfp_mode = st.sidebar.selectbox(
    "📋 Type de mandat / Mandate Type",
    mode_options[lang],
    index=0,
)
is_item_mode = "📦" in rfp_mode

# ----------------- TRANSLATION DICTIONARY ----------------- #
T = {
    "Français": {
        "title": "🏢 JanSan RFP Pilot — Moteur d'Offres & Soumissions Intelligentes",
        "caption": "Plateforme d'analyse et de génération de soumissions pour l'industrie Jan/San — Services d'entretien & Fournitures de produits.",
        "tab_profile": "1️⃣ Profil Entreprise & Grille de Prix",
        "tab_qual": "2️⃣ Qualification & Analyse des Écarts",
        "tab_bid": "3️⃣ Générateur de Soumission Complète",
        # Tab 1 Common
        "profile_h": "Identité de l'Entreprise & Capacités",
        "co_name_lbl": "Raison sociale de l'entreprise",
        "co_name_val": "Distributions & Services Expert-Net Inc.",
        "co_addr_lbl": "Adresse du siège / Entrepôt principal",
        "co_addr_val": "1500 Boulevard René-Lévesque O, Montréal, QC",
        "co_ins_lbl": "Assurance responsabilité civile",
        "co_ins_opts": ["2 000 000 $ CAD", "5 000 000 $ CAD", "10 000 000 $ CAD", "20 000 000 $+ CAD"],
        # Tab 1 - Services
        "co_certs_lbl_srv": "Certifications & Normes de service",
        "co_certs_opts_srv": [
            "ISO 9001 (Système de gestion de la qualité)",
            "ISO 14001 (Gestion environnementale)",
            "CIMS / CIMS-GB (ISSA - Green Building)",
            "Attestation CNESST en règle",
            "Attestation Revenu Québec en règle",
            "Licence d'entrepreneur (RBQ)",
            "Personnel avec Enquête de sécurité (Fiabilité/Secret)",
        ],
        "co_bond_lbl_srv": "Capacité de cautionnement",
        "co_bond_opts_srv": [
            "Capacité standard (Caution 10% + 50% MO/Matériaux)",
            "Capacité majeure (Cautions 50% / 100%)",
            "Aucune caution requise/disponible",
        ],
        "pricing_h_srv": "Grille de Taux Horaires & Frais de Gestion",
        "rate_base_lbl_srv": "Taux horaire préposé à l'entretien ($/h)",
        "rate_super_lbl_srv": "Taux horaire chef d'équipe / superviseur ($/h)",
        "rate_markup_lbl_srv": "Marge sur produits chimiques & consommables (%)",
        "custom_price_h_srv": "Grille de prix des travaux périodiques & spécialisés",
        "custom_price_val_srv": "• Décapage et cirage de planchers vinyle (4 couches): 0.38$/pi²\n• Lavage de vitres intérieur/extérieur: 0.14$/pi²\n• Nettoyage de tapis par extraction à eau chaude: 0.24$/pi²\n• Forfait désinfection électrostatique d'urgence: 450.00$/intervention\n• Taux de main-d'oeuvre d'urgence hors horaire: 48.50$/h",
        # Tab 1 - Items / Supply
        "co_certs_lbl_itm": "Certifications & Conformité Produits",
        "co_certs_opts_itm": [
            "Produits certifiés ÉcoLogo / Green Seal",
            "Certification FSC (Produits de papier)",
            "Approbation Santé Canada / DIN (Désinfectants)",
            "Conformité SIMDUT / FDS conformes et récentes",
            "Homologation ACIA (Usage agroalimentaire)",
            "Programme de reprise/recyclage des contenants",
        ],
        "logistics_h_itm": "Conditions de Livraison & Logistique",
        "freight_lbl_itm": "Seuil de commande pour livraison franco (gratuite)",
        "lead_time_lbl_itm": "Délai de livraison standard",
        "lead_time_opts_itm": ["24 à 48 heures ouvrables", "Même jour (urgence locale)", "3 à 5 jours ouvrables"],
        "dispenser_lbl_itm": "Programme de distributrices / Équipements",
        "dispenser_opts_itm": [
            "Prêt sans frais (Free-on-loan) avec contrat de fournitures",
            "Installation et entretien des distributrices inclus",
            "Vente d'équipements et distributrices seulement",
        ],
        "custom_price_h_itm": "Catalogue de Produits & Grille Tarifaire Maître (SKU, Format, Prix)",
        "custom_price_val_itm": "• Papier hygiénique 2 plis (ÉcoLogo, 48 rl/cs, SKU: PH-200): 38.50$/cs\n• Essuie-mains en rouleau 800 pi (FSC, 6 rl/cs, SKU: EM-800): 42.00$/cs\n• Nettoyant tout-usage concentré ÉcoLogo (4x4L, SKU: CH-101): 48.00$/cs\n• Désinfectant hospitalier virucide DIN (12x1L, SKU: DS-500): 62.00$/cs\n• Sacs à déchets réguliers 35x50 (Recyclé, 200/cs, SKU: SC-3550): 32.50$/cs\n• Savon à mains mousse certifié Éco (4x1000ml, SKU: SV-100): 44.00$/cs",
        "profile_saved": "✅ Profil maître et paramètres sauvegardés.",
        # Side uploader
        "upload_h": "Document d'Appel d'Offres (PDF)",
        "upload_lbl": "Téléversez le devis officiel (SEAO, AchatsCan, municipal, privé)",
        "no_pdf_qual": "👈 Veuillez téléverser un fichier PDF d'appel d'offres dans la barre latérale gauche.",
        "no_pdf_bid": "👈 Veuillez d'abord téléverser le document PDF pour générer la soumission.",
        # Tab 2
        "btn_qual": "1. Analyser la Conformité & Risques (Go / No-Go)",
        "spinner_qual": "Analyse du devis en cours...",
        "verdict_lbl": "Décision Recommandée",
        "score_lbl": "Score d'adéquation",
        "gaps_h": "⚠️ Analyse des Écarts & Produits Manquants",
        "mandatory_h": "🚨 Critères d'Exclusion / Exigences Obligatoires",
        "forms_h": "📎 Formulaires & Fiches Techniques (FDS/TDS) Requis",
        "scoring_h": "📊 Grille de Pointage & Pondération",
        "req_lbl": "Exigence",
        "reject_lbl": "Rejet",
        # Tab 3
        "bid_desc_srv": "Génère une proposition de service complète, chiffrée selon les superficies et fréquences, avec plan de travail et lettre de transmission.",
        "bid_desc_itm": "Génère une offre de fournitures complète avec tableau de correspondance des articles (SKU, équivalences, prix unitaires), plan logistique et engagements FDS/Éco.",
        "btn_bid": "2. Générer la Proposition Complète de Soumission",
        "spinner_bid": "Génération de la soumission complète en cours...",
        "exp_letter": "📄 Lettre Formelle de Soumission (Transmittal Letter)",
        "exp_scope_srv": "🏢 Compréhension du Mandat & Envergure des Travaux",
        "exp_scope_itm": "📦 Compréhension des Besoins d'Approvisionnement & Gamme Proposée",
        "exp_price_srv": "💰 Grille Financière & Chiffrage de l'Offre",
        "exp_price_itm": "💰 Bordereau des Prix & Table de Correspondance des Articles",
        "metric_srv_monthly": "Entretien Régulier (Mensuel)",
        "metric_srv_annual": "Entretien Régulier (Annuel)",
        "metric_srv_total": "Valeur Totale Année 1",
        "metric_itm_items": "Nombre d'articles chiffrés",
        "metric_itm_lead": "Délai moyen de livraison",
        "metric_itm_freight": "Seuil de livraison franco",
        "exp_ops_srv": "🛠️ Plan Opérationnel, Supervision & Contrôle Qualité",
        "exp_ops_itm": "🚚 Logistique, Entreposage, SLA & Gestion des Ruptures",
        "exp_env_srv": "🌱 Plan Environnemental, SIMDUT & Santé-Sécurité",
        "exp_env_itm": "🌱 Fiches Techniques, FDS, Éco-certifications & Distributrices",
        "download_btn": "📥 Télécharger la Soumission (.md)",
        "file_prefix": "Soumission",
        "err_key": "Clé API introuvable. Veuillez configurer GEMINI_API_KEY dans les Secrets Streamlit.",
    },
    "English": {
        "title": "🏢 JanSan RFP Pilot — Proposal Engine & Tender Intelligence",
        "caption": "Tender analysis and automated proposal generator for the Jan/San industry — Facility Cleaning Services & Product Supply Bids.",
        "tab_profile": "1️⃣ Master Profile & Price Matrix",
        "tab_qual": "2️⃣ Qualification & Gap Matrix",
        "tab_bid": "3️⃣ Complete Bid Proposal Generator",
        # Tab 1 Common
        "profile_h": "Contractor Credentials & Qualifications",
        "co_name_lbl": "Company Legal Name",
        "co_name_val": "Expert-Clean Supply & Facility Solutions Inc.",
        "co_addr_lbl": "Headquarters / Main Distribution Center Address",
        "co_addr_val": "1500 Rene-Levesque Blvd W, Montreal, QC",
        "co_ins_lbl": "Commercial General Liability Insurance",
        "co_ins_opts": ["$2,000,000 CAD", "$5,000,000 CAD", "$10,000,000 CAD", "$20,000,000+ CAD"],
        # Tab 1 - Services
        "co_certs_lbl_srv": "Cleaning & Service Certifications Held",
        "co_certs_opts_srv": [
            "ISO 9001 (Quality Management System)",
            "ISO 14001 (Environmental Management)",
            "CIMS / CIMS-GB (ISSA - Green Building)",
            "WSIB / CNESST Clearance Certificate",
            "Good Standing Tax Certificates",
            "Valid General Cleaning / Contractor License",
            "Security-Cleared Staff (Reliability / Secret)",
        ],
        "co_bond_lbl_srv": "Bonding Capacity (Surety Bonds)",
        "co_bond_opts_srv": [
            "Standard Capacity (10% Bid Bond + 50% Labor/Materials)",
            "Major Capacity (50% / 100% Performance Bonds)",
            "No Surety / Bonding Required",
        ],
        "pricing_h_srv": "Hourly Billing Rates & Management Fees",
        "rate_base_lbl_srv": "Base Cleaner Hourly Billing Rate ($/hr)",
        "rate_super_lbl_srv": "Supervisor / Team Lead Hourly Billing Rate ($/hr)",
        "rate_markup_lbl_srv": "Chemical & Supply Markup (%)",
        "custom_price_h_srv": "Periodic & Specialty Services Price List",
        "custom_price_val_srv": "• VCT Strip & Wax (4 coats premium finish): $0.38/sq ft\n• Interior & Exterior Window Washing: $0.14/sq ft\n• Hot Water Extraction Carpet Cleaning: $0.24/sq ft\n• Emergency Electrostatic Disinfection Package: $450.00/call\n• After-hours Emergency Dispatch Rate: $48.50/hr",
        # Tab 1 - Items / Supply
        "co_certs_lbl_itm": "Product Certifications & Environmental Accreditations",
        "co_certs_opts_itm": [
            "EcoLogo / Green Seal Certified Formulations",
            "FSC / SFI Certified Recycled Paper Products",
            "Health Canada DIN Registration (Disinfectants)",
            "WHMIS 2015 Compliant SDS Library Available",
            "CFIA / Food Contact Approved",
            "Zero-Waste Drum Return / Recycling Program",
        ],
        "logistics_h_itm": "Supply Chain & Delivery Terms",
        "freight_lbl_itm": "Prepaid Freight Order Threshold (Free Delivery)",
        "lead_time_lbl_itm": "Standard Order Delivery SLA",
        "lead_time_opts_itm": ["24 to 48 business hours", "Same-day emergency dispatch", "3 to 5 business days"],
        "dispenser_lbl_itm": "Dispenser & Equipment Program",
        "dispenser_opts_itm": [
            "Free-on-loan (FRO) dispenser placement with supply agreement",
            "Full installation and routine dispenser maintenance included",
            "Equipment sale and drop-ship only",
        ],
        "custom_price_h_itm": "Master Product Catalog & Unit Price Matrix (SKU, Pack Size, Price)",
        "custom_price_val_itm": "• 2-Ply Standard Bath Tissue (EcoLogo, 48 rls/cs, SKU: BT-200): $38.50/cs\n• Hardwound Roll Towel 800' (FSC, 6 rls/cs, SKU: RT-800): $42.00/cs\n• Neutral Multi-Surface Cleaner Concentrate (4x4L, SKU: CH-101): $48.00/cs\n• Broad-Spectrum Disinfectant DIN (12x1L, SKU: DS-500): $62.00/cs\n• Heavy Duty Trash Liners 35x50 (Recycled, 200/cs, SKU: BG-3550): $32.50/cs\n• Luxury Foam Hand Soap Eco-Certified (4x1000ml, SKU: SP-100): $44.00/cs",
        "profile_saved": "✅ Master profile and settings saved successfully.",
        # Side uploader
        "upload_h": "Tender / RFP Document (PDF)",
        "upload_lbl": "Upload official RFP (Buyandsell, MERX, SEAO, Municipal, Corporate)",
        "no_pdf_qual": "👈 Please first upload a tender PDF document in the left sidebar.",
        "no_pdf_bid": "👈 Please upload the tender PDF in the sidebar to generate the proposal.",
        # Tab 2
        "btn_qual": "1. Analyze Compliance & Gap Risks (Go / No-Go)",
        "spinner_qual": "Evaluating tender compliance...",
        "verdict_lbl": "Recommended Verdict",
        "score_lbl": "Suitability Score",
        "gaps_h": "⚠️ Product / Capability Gaps & Non-Compliance",
        "mandatory_h": "🚨 Mandatory Disqualifiers & Critical Specs",
        "forms_h": "📎 Mandatory Forms, SDS & Schedules Required",
        "scoring_h": "📊 Evaluation Grid & Points Weighting",
        "req_lbl": "Requirement",
        "reject_lbl": "Rejection",
        # Tab 3
        "bid_desc_srv": "Generates a complete cleaning proposal based on square footage and frequencies, including operational staffing and transmittal letter.",
        "bid_desc_itm": "Generates a complete Jan/San item supply proposal with product equivalency tables, case pack pricing, logistics SLA, and SDS/Eco commitments.",
        "btn_bid": "2. Generate Complete Submission Proposal",
        "spinner_bid": "Drafting complete itemized submission proposal...",
        "exp_letter": "📄 Formal Transmittal & Submission Letter",
        "exp_scope_srv": "🏢 Understanding of Mandate & Scope of Work",
        "exp_scope_itm": "📦 Understanding of Supply Requirements & Offered Line-Up",
        "exp_price_srv": "💰 Calculated Pricing & Financial Breakdown",
        "exp_price_itm": "💰 Itemized Pricing Schedule & Product Cross-Reference",
        "metric_srv_monthly": "Routine Cleaning (Monthly)",
        "metric_srv_annual": "Routine Cleaning (Annual)",
        "metric_srv_total": "Total Year 1 Contract Value",
        "metric_itm_items": "Quoted Line Items",
        "metric_itm_lead": "Standard Lead Time",
        "metric_itm_freight": "Free Freight Threshold",
        "exp_ops_srv": "🛠️ Operational Plan, Supervision & Quality Assurance",
        "exp_ops_itm": "🚚 Supply Chain Logistics, Warehousing & Backorder SLA",
        "exp_env_srv": "🌱 Environmental Plan, WHMIS & Health-Safety",
        "exp_env_itm": "🌱 Eco-Certifications, SDS Sheets & Dispenser Programs",
        "download_btn": "📥 Download Complete Bid Proposal (.md)",
        "file_prefix": "Bid_Proposal",
        "err_key": "Missing API key. Please configure GEMINI_API_KEY in Streamlit Secrets.",
    },
}

t = T[lang]


# ----------------- BULLETPROOF GEMINI RUNNER ----------------- #
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

# ----------------- TAB 1: MASTER CONTRACTOR / DISTRIBUTOR PROFILE ----------------- #
with tab_prof:
    st.subheader(t["profile_h"])
    col1, col2 = st.columns(2)
    with col1:
        co_name = st.text_input(t["co_name_lbl"], value=t["co_name_val"])
        co_addr = st.text_input(t["co_addr_lbl"], value=t["co_addr_val"])

    with col2:
        co_ins = st.selectbox(t["co_ins_lbl"], t["co_ins_opts"], index=1)

    st.markdown("---")

    if not is_item_mode:
        # SERVICES MODE
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            co_certs = st.multiselect(
                t["co_certs_lbl_srv"],
                t["co_certs_opts_srv"],
                default=[t["co_certs_opts_srv"][0], t["co_certs_opts_srv"][3]],
            )
        with col_s2:
            co_bond = st.selectbox(t["co_bond_lbl_srv"], t["co_bond_opts_srv"], index=0)

        st.subheader(t["pricing_h_srv"])
        pcol1, pcol2, pcol3 = st.columns(3)
        with pcol1:
            rate_base = st.number_input(t["rate_base_lbl_srv"], min_value=15.0, max_value=200.0, value=29.50, step=0.50)
        with pcol2:
            rate_super = st.number_input(t["rate_super_lbl_srv"], min_value=20.0, max_value=250.0, value=38.00, step=0.50)
        with pcol3:
            rate_markup = st.number_input(t["rate_markup_lbl_srv"], min_value=0.0, max_value=100.0, value=15.0, step=1.0)

        st.markdown(f"**{t['custom_price_h_srv']}**")
        custom_pricing = st.text_area(
            label="Service Pricing Matrix",
            label_visibility="collapsed",
            value=t["custom_price_val_srv"],
            height=120,
        )

        contractor_profile = {
            "mandate_type": "Facility Cleaning Services",
            "company_name": co_name,
            "company_address": co_addr,
            "insurance_coverage": co_ins,
            "certifications": co_certs,
            "bonding_capacity": co_bond,
            "base_cleaner_rate": f"${rate_base}/hr",
            "supervisor_rate": f"${rate_super}/hr",
            "chemical_markup": f"{rate_markup}%",
            "specialty_price_matrix": custom_pricing,
        }

    else:
        # GOODS / ITEM SUPPLY MODE
        col_i1, col_i2 = st.columns(2)
        with col_i1:
            co_certs = st.multiselect(
                t["co_certs_lbl_itm"],
                t["co_certs_opts_itm"],
                default=[t["co_certs_opts_itm"][0], t["co_certs_opts_itm"][1], t["co_certs_opts_itm"][3]],
            )
            dispenser_prog = st.selectbox(t["dispenser_lbl_itm"], t["dispenser_opts_itm"], index=0)
        with col_i2:
            freight_threshold = st.text_input(t["freight_lbl_itm"], value="$250.00 CAD")
            lead_time = st.selectbox(t["lead_time_lbl_itm"], t["lead_time_opts_itm"], index=0)

        st.subheader(t["custom_price_h_itm"])
        custom_catalog = st.text_area(
            label="Product Catalog Matrix",
            label_visibility="collapsed",
            value=t["custom_price_val_itm"],
            height=150,
        )

        contractor_profile = {
            "mandate_type": "Jan/San Goods & Item Supply",
            "company_name": co_name,
            "company_address": co_addr,
            "insurance_coverage": co_ins,
            "product_certifications": co_certs,
            "dispenser_program": dispenser_prog,
            "free_freight_threshold": freight_threshold,
            "delivery_lead_time": lead_time,
            "master_catalog_price_list": custom_catalog,
        }

    st.session_state["contractor_profile"] = contractor_profile
    st.success(t["profile_saved"])

# ----------------- SIDEBAR UPLOADER ----------------- #
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
                            "executive_rationale": "Clear rationale explaining whether the contractor/distributor meets the tender requirements.",
                        },
                        "gap_analysis_missing_requirements": [
                            "Specific product spec, certification, missing SKU, or delivery term requirement that may present risk."
                        ],
                        "mandatory_disqualifiers": [
                            {
                                "category": "Category",
                                "requirement": "Mandatory requirement details",
                                "penalty": "Disqualification / Rejection",
                            }
                        ],
                        "required_annexes_and_forms": [
                            "Mandatory schedules, technical data sheets (TDS), SDS sheets, or surety forms to be attached."
                        ],
                        "scoring_matrix_summary": [
                            "Points weighting and criteria breakdown for technical score vs. pricing."
                        ],
                    }

                    if is_item_mode:
                        role_qual = (
                            f"You are a senior procurement auditor specializing in Jan/San product supply, institutional consumable goods, and equipment tenders in Canada. "
                            f"Analyze the attached tender PDF against the vendor's catalog and logistics capabilities in {lang}."
                        )
                    else:
                        role_qual = (
                            f"You are a senior proposal auditor specializing in commercial cleaning, building maintenance, and Jan/San service tenders in Canada. "
                            f"Analyze the attached tender PDF against the contractor's credentials and pricing in {lang}."
                        )

                    prompt = (
                        f"{role_qual}\n\n"
                        f"VENDOR / CONTRACTOR MASTER PROFILE:\n{json.dumps(contractor_profile, ensure_ascii=False, indent=2)}\n\n"
                        f"Return a STRICT JSON object matching this structure in {lang}:\n"
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
