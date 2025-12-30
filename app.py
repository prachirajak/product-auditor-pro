import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from bs4 import BeautifulSoup
import re, time, io

# --- 1. PROFESSIONAL & LIVELY UI CONFIG ---
st.set_page_config(page_title="Master Data Auditor", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    /* Professional Indigo Palette */
    .stApp { background-color: #f8faff; color: #1e293b; font-family: 'Inter', sans-serif; }
    h1 { color: #4f46e5 !important; font-weight: 800 !important; letter-spacing: -1px; }
    
    /* Card Design from your HTML */
    .section-card { 
        background-color: white; 
        padding: 24px; 
        border-radius: 16px; 
        border: 1px solid #e2e8f0; 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); 
        margin-bottom: 24px; 
    }
    
    /* Lively Indigo Buttons */
    .stButton>button { 
        background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%) !important; 
        color: white !important; border-radius: 12px !important; 
        border: none !important; font-weight: 700 !important; height: 3.5em;
        transition: transform 0.2s ease;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.4); }
    
    /* Success Green Download Button */
    .stDownloadButton>button { 
        background-color: #10b981 !important; color: white !important; 
        border-radius: 12px !important; font-weight: 700 !important; width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE INTELLIGENCE ENGINE ---
@st.cache_resource
def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()), options=options)

# Your requested 20+ fields mapping
FIELD_MAP = {
    "Allergen Info": ["Allergen", "Contains", "Free from", "Allergy"],
    "Expiration Type": ["Expiration Type", "Date Code", "EXP Format"],
    "Expiry (y/n)": ["Expiry", "Expiration", "EXP Date"],
    "Shelf Life": ["Shelf life", "Storage", "Duration"],
    "CPSIA Warning": ["CPSIA", "Choking Hazard", "Small parts"],
    "Legal Disclaimer": ["Legal disclaimer", "Disclaimer", "FDA Statement"],
    "Safety Warning": ["Safety Warning", "Warning", "Precautions"],
    "Indications": ["Indications", "Recommended use", "Indications"],
    "Age Range": ["Age Range", "Adults", "Kids", "Children"],
    "Item Form": ["Item Form", "Format", "Capsule", "Tablet", "Powder"],
    "Primary Supplement Type": ["Supplement Type", "Main Ingredient"],
    "Directions": ["Directions", "How to use", "Suggested Use"],
    "Flavor": ["Flavor", "Taste", "Scent"],
    "Target Gender": ["Target Gender", "Gender", "Men", "Women"],
    "Product Benefits": ["Benefits", "Features", "Why use"],
    "Specific Uses": ["Specific Uses", "Used for"],
    "Ingredients list": ["Ingredients", "Supplement Facts", "Active Ingredients"],
    "Days of use": ["Days of use", "Supply length", "Servings"],
    "Hazmat(y/n)": ["Hazmat", "Flammable", "Dangerous Goods"],
    "Product description": ["Description", "About this item"]
}

# "Smart Guess" logic from your original code
def smart_guess_ingredients(title):
    t = str(title).lower()
    if 'magnesium' in t: return 'Magnesium Bisglycinate Chelate'
    if 'ashwagandha' in t: return 'Organic Ashwagandha Root Extract, Black Pepper'
    if 'vitamin c' in t: return 'Vitamin C (ascorbic acid)'
    if 'collagen' in t: return 'Hydrolyzed Collagen Peptides'
    return 'Microcrystalline Cellulose, Magnesium Stearate, Silica'

def audit_link(url, item_name):
    driver = get_driver()
    try:
        driver.get(url)
        time.sleep(5) # The 5-second rule for lazy loading
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        text = soup.get_text().lower()
        results = {"Source URL": url}
        
        for field, keywords in FIELD_MAP.items():
            found = False
            for k in keywords:
                if "(y/n)" in field:
                    results[field] = "Y" if k.lower() in text else "N"
                    found = True; break
                match = soup.find(string=re.compile(rf"\b{k}\b", re.I))
                if match:
                    val = match.find_next().get_text(strip=True) if match.find_next() else ""
                    results[field] = val[:400] if len(val) > 2 else "Not Found"
                    found = True; break
            
            # Smart Guess Fallback
            if not found or results[field] == "Not Found":
                if field == "Ingredients list":
                    results[field] = smart_guess_ingredients(item_name)
                    results["Source"] = "Guessed"
                else:
                    results[field] = "Not Found"
            else:
                results["Source"] = "Scraped"
        
        results["Images Found"] = len(soup.find_all('img'))
        return results
    except:
        return {"Ingredients list": smart_guess_ingredients(item_name), "Source": "Fallback"}

# --- 3. UI LAYOUT ---
st.title("🛡️ Master Data Auditor")
st.write("Intelligent specification extraction for GNC, Walmart, and HealthKart.")

# SECTION 1: BRAND SETTINGS
st.markdown('<div class="section-card">', unsafe_allow_html=True)
col_a, col_b = st.columns([1, 2])
brand_input = col_a.text_input("🏢 Global Brand Name", placeholder="e.g. GNC")
link_input = col_b.text_area("🔗 Bulk Link Paste (one per line)", placeholder="Paste multiple links here...")
st.markdown('</div>', unsafe_allow_html=True)

# SECTION 2: FILE UPLOAD
st.markdown('<div class="section-card">', unsafe_allow_html=True)
uploaded_file = st.file_uploader("📁 Upload Batch File (Includes Title, ASIN, UPC, EAN, Images)", type=["xlsx", "csv"])
st.markdown('</div>', unsafe_allow_html=True)

# SECTION 3: PROGRESS & GENERATE
if st.button("🚀 INITIALIZE NEURAL EXTRACTION"):
    # Combine links and file
    final_queue = []
    if link_input:
        for l in link_input.split('\n'):
            if l.strip(): final_queue.append({"Title": "Manual Input", "URL": l.strip()})
    
    if uploaded_file:
        df_in = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('xlsx') else pd.read_csv(uploaded_file)
        # Tolerance: detect ID, Title, and URL columns
        id_col = next((c for c in df_in.columns if any(x in c.lower() for x in ["upc", "asin", "gtin", "id"])), df_in.columns[0])
        title_col = next((c for c in df_in.columns if any(x in c.lower() for x in ["title", "name"])), df_in.columns[1])
        url_col = next((c for c in df_in.columns if any(x in c.lower() for x in ["link", "url", "website"])), None)
        
        for _, row in df_in.iterrows():
            final_queue.append({"Title": row[title_col], "URL": row[url_col] if url_col else None, "ID": row[id_col]})

    if final_queue:
        progress_bar = st.progress(0)
        status_text = st.empty()
        audit_results = []
        
        for i, item in enumerate(final_queue):
            status_text.write(f"🔍 **Scanning Node {i+1}:** {item['Title']}")
            data = audit_link(item['URL'], item['Title']) if item['URL'] else {"Ingredients list": smart_guess_ingredients(item['Title']), "Source": "Guessed"}
            data["Item Name"] = item['Title']
            data["Brand"] = brand_input
            audit_results.append(data)
            progress_bar.progress((i + 1) / len(final_queue))
            
        # VALUABLE ADDITION: Analysis Summary
        st.success(f"Audit Complete! {len(audit_results)} items processed.")
        df_out = pd.DataFrame(audit_results)
        
        # PREVIEW BAR
        st.subheader("📊 Intelligence Preview")
        st.dataframe(df_out.head(10))
        
        # DOWNLOAD BAR
        st.divider()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_out.to_excel(writer, index=False)
        st.download_button("📥 DOWNLOAD COMPLETE EXCEL REPORT", output.getvalue(), "master_audit_report.xlsx")
    else:
        st.error("Please paste links or upload a file to begin.")
