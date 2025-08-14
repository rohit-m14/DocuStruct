import streamlit as st
import os
import tempfile
import pandas as pd
import json
import copy
import base64
from google import genai
from pydantic import create_model, Field
from dotenv import load_dotenv

# --- 1️⃣ PAGE CONFIG ---
st.set_page_config(
    page_title="DocuStruct",
    layout="wide",
    initial_sidebar_state="auto",
)

# --- 2️⃣ CUSTOM CSS ---
st.markdown(""" 
<style>
  /*–– App background ––*/
  [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
      background-color: #130F26;
  }
  body, [data-testid="stMarkdownContainer"] * {
      color: #FFFFFF !important;
      font-weight: 500 !important;
  }
  h1, h2, h3, h4 {
      font-weight: 700 !important;
  }
  /* cap uploader dropzone width */
  [data-testid="stFileUploadDropzone"] {
      max-width: 400px !important;
      margin: auto;
  }
  /* full-width inputs */
  [data-testid="stTextInput"] input {
      width: 100% !important;
  }
  /* styled buttons */
  button, input[type="button"], input[type="submit"],
  [data-testid="stFileUploader"] section button {
      background-color: #6D63FF !important;
      color: #FFFFFF !important;
      font-weight: 600 !important;
      border: none !important;
      border-radius: 8px !important;
      padding: 6px 12px !important;
  }
  button:hover, button:focus, button:active,
  input[type="button"]:hover, input[type="submit"]:hover,
  [data-testid="stFileUploader"] section button:hover {
      background-color: #584cde !important;
  }
  /* hide Streamlit footer & menu */
  #MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 3️⃣ HEADER & LOGO ---
logo_path = "Logo_wordmark.png"
if os.path.exists(logo_path):
    logo_b64 = base64.b64encode(open(logo_path, "rb").read()).decode()
    st.markdown(f"""
    <div style="text-align:left; margin:40px 0 10px;">
      <img src="data:image/png;base64,{logo_b64}" style="width:400px; height:auto;"/>
    </div>
    <div style="text-align:center; margin-bottom:50px;">
      <h1 style="font-size:70px; font-family:'Arial Black'; color:#FFF; margin:0;">
        DocuStruct
      </h1>
    </div>
    """, unsafe_allow_html=True)

# --- 4️⃣ ENV & CLIENT SETUP ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY") or st.text_input("Enter Google API Key:", type="password")
if not api_key:
    st.error("API key required")
    st.stop()
client = genai.Client(api_key=api_key)
model_id = "gemini-2.5-flash"

# --- BUILT-IN FIELDS ---
BUILTIN_FIELDS = {
    "Form": {
        "first_name":    "User’s given name",
        "last_name":     "User’s family name",
        "date_of_birth": "Date of birth in DD/MM/YYYY",
        "address":       "Full mailing address",
        "phone_number":  "Primary contact phone number",
        "gender":        "User’s gender (e.g. Male, Female, Other)"
    },
    "Receipt": {
        "merchant_name":    "Name of store or vendor",
        "transaction_date": "Date of purchase (DD/MM/YYYY)",
        "total_amount":     "Grand total charged",
        "tax_amount":       "Total tax applied",
        "payment_method":   "Method of payment (e.g. Visa, Cash)",
        "items":            "Line‐items purchased with price and qty"
    }
}

# --- HELPERS ---
def clean_schema(s):
    if isinstance(s, dict):
        s.pop("additionalProperties", None)
        return {k: clean_schema(v) for k, v in s.items()}
    if isinstance(s, list):
        return [clean_schema(i) for i in s]
    return s

def save_file(u):
    ext = os.path.splitext(u.name)[1]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp.write(u.getvalue()); tmp.close()
    return tmp.name

def display_file(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        b64 = base64.b64encode(open(path,"rb").read()).decode()
        st.markdown(
          f'<iframe src="data:application/pdf;base64,{b64}" '
          'width="100%" height="600px"></iframe>',
          unsafe_allow_html=True
        )
    else:
        st.image(path, use_container_width=True)

def extract_structured(path, model, dtype):
    prompt = "Extract all form fields as JSON." if dtype=="Form" else "Extract receipt details as JSON."
    schema = clean_schema(copy.deepcopy(model.model_json_schema()))
    file_obj = client.files.upload(file=path, config={"display_name":os.path.basename(path)})
    res = client.models.generate_content(
        model=model_id,
        contents=[prompt, file_obj],
        config={"response_mime_type":"application/json","response_schema":schema}
    )
    return json.loads(res.text)

# --- SESSION STATE DEFAULTS & CALLBACK ---
if 'page' not in st.session_state:
    st.session_state.page = 'upload'
if 'file_path' not in st.session_state:
    st.session_state.file_path = None
if 'result' not in st.session_state:
    st.session_state.result = None

if 'doc_type' not in st.session_state:
    st.session_state.doc_type = 'Form'

def on_doc_type_change():
    st.session_state.field_rows = [
        {"name": k, "desc": v}
        for k, v in BUILTIN_FIELDS[st.session_state.doc_type].items()
    ]

if 'field_rows' not in st.session_state:
    on_doc_type_change()

# --- MAIN: UPLOAD & CONFIGURE ---
if st.session_state.page == 'upload':

    # Document Type selector
    c1, c2, c3 = st.columns([1, 4, 1])
    with c2:
        st.markdown("<h2 style='font-size:1.5em; font-weight:600;'>Document Type</h2>", unsafe_allow_html=True)
        st.selectbox(
            "",
            list(BUILTIN_FIELDS.keys()),
            index=list(BUILTIN_FIELDS.keys()).index(st.session_state.doc_type),
            key="doc_type",
            on_change=on_doc_type_change,
            label_visibility="collapsed"
        )

    # File uploader
    c1, c2, c3 = st.columns([1, 4, 1])
    with c2:
        st.subheader("Upload Your File (PDF or PNG)")
        uploaded = st.file_uploader("", type=["pdf","png"], label_visibility="collapsed")
    if uploaded:
        st.session_state.file_path = save_file(uploaded)
        st.success("File ready for field configuration.")

    # Fields to Extract
    c1, c2, c3 = st.columns([1, 4, 1])
    with c2:
        st.subheader("Fields to Extract")
        if st.button("Reset to Default Fields"):
            on_doc_type_change()
            st.rerun()

        hdr1, hdr2, _ = st.columns([6, 18, 1])
        hdr1.markdown("**Field Name**")
        hdr2.markdown("**Description**")

        for i, row in enumerate(st.session_state.field_rows):
            col_name, col_desc, col_btn = st.columns([4, 12, 1])
            name = col_name.text_input("", value=row["name"], key=f"fname_{i}", label_visibility="collapsed")
            desc = col_desc.text_input("", value=row["desc"], key=f"fdesc_{i}", label_visibility="collapsed")
            if col_btn.button("−", key=f"rm_{i}"):
                st.session_state.field_rows.pop(i)
                st.rerun()
            st.session_state.field_rows[i] = {"name": name.strip(), "desc": desc.strip()}

        if st.button("➕ Add Field"):
            st.session_state.field_rows.append({"name": "", "desc": ""})
            st.rerun()

    # Extract Data button
    c1, c2, c3 = st.columns([3, 1, 3])
    with c2:
        if st.button("Extract Data"):
            if not st.session_state.file_path:
                st.error("Upload a file first.")
            elif not any(r['name'] for r in st.session_state.field_rows):
                st.error("Add at least one field.")
            else:
                defs = {r['name']:(str, Field(description=r['desc'])) for r in st.session_state.field_rows if r['name']}
                Dynamic = create_model('DynamicSchema', **defs)
                st.session_state.result = extract_structured(
                    st.session_state.file_path, Dynamic, st.session_state.doc_type
                )
                st.session_state.page = 'results'
                st.rerun()

# --- RESULTS VIEW ---
else:
    data = st.session_state.result or {}
    df = pd.json_normalize(data, sep='_')

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Original File")
        display_file(st.session_state.file_path)

    with col2:
        st.subheader("Extracted Data")
        if df.empty:
            st.write("No data extracted.")
        else:
            # Handle one or more records
            for rec_idx, row in df.iterrows():
                # Optional header per record
                if len(df) > 1:
                    st.markdown(f"**Record {rec_idx + 1}**")
                # Loop through each field/value
                for field, val in row.items():
                    f_col, v_col = st.columns([2, 8])
                    with f_col:
                        st.markdown(f"**{field}**")
                    with v_col:
                        st.write(val)
                st.markdown("---")  # separator between records

        # download buttons (as before)
        b1, b2, b3, b4, b5 = st.columns([2,1,1,1,2])
        with b2:
            st.download_button(
                "💾 JSON",
                json.dumps(data, indent=2),
                file_name="data.json",
                mime="application/json"
            )
        with b3:
            st.download_button(
                "💾 CSV",
                df.to_csv(index=False).encode('utf-8'),
                file_name="data.csv",
                mime="text/csv"
            )

    # Centered “Process Another File” button
    p1, p2, p3 = st.columns([3, 1, 3])
    with p2:
        if st.button("Process Another File"):
            for k in ['page','file_path','result','field_rows','doc_type']:
                st.session_state.pop(k, None)
            st.rerun()

