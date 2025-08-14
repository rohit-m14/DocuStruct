# DocuStruct

**DocuStruct** is a Streamlit web app for extracting structured fields from documents (PDF or PNG). The app lets you configure fields to extract (forms or receipts), uploads a document, and uses a Google GenAI model to parse the document and return JSON/CSV results.

> Files included: `app.py` (Streamlit app), `Approach2.png` (pipeline/diagram, optional), and project assets such as `Logo_wordmark.png` if present.

---

## Overview

DocuStruct provides a small GUI to:
- Upload a PDF or PNG document.
- Choose a document type (built-in options: `Form`, `Receipt`).
- Configure or edit the schema (field name + description) for extraction.
- Call a Google GenAI model to extract the data as JSON according to a pydantic-generated schema.
- Display the extracted data and download it as JSON or CSV.

The app dynamically builds a Pydantic model from user-provided fields and then calls the GenAI `generate_content` endpoint with a JSON response schema so the returned content is machine-parsable.

The repository includes a diagram `Approach2.png` that illustrates the conceptual pipeline (preprocessing → augmentation → embedding/indexing → ranking). For this Streamlit app, the key steps are: upload → schema configuration → call GenAI → show results → export.

---

## Features

- Upload PDF or PNG documents for extraction.
- Two built-in doc types with example fields: `Form` and `Receipt`.
- Add, remove, and edit extraction fields at runtime.
- Clean and save uploaded files to a temporary location before processing.
- Use the Google GenAI Files + Models APIs to extract structured data.
- Download extracted results as JSON or CSV from the UI.
- Client-side UI styling (custom CSS) and a logo support.

---

## Requirements / Dependencies

Below are the main Python packages used by the app (detected from `app.py`). Install them into a virtual environment prior to running the app:

```text
streamlit
pandas
pydantic
python-dotenv
google-genai   # package that provides `from google import genai`
```

You can install these with pip:

```bash
python -m venv venv
# On Windows (Git Bash):
source venv/Scripts/activate
pip install streamlit pandas pydantic python-dotenv google-genai
```

If you already have an environment, create a `requirements.txt` after installing packages:
```bash
pip freeze > requirements.txt
```

---

## Environment Variables / API Key

The app uses the Google GenAI client and expects a Google API key. Provide it either via a `.env` file or by entering it in the UI prompt when the app starts.

Create a `.env` in the project root with the following content:

```
GOOGLE_API_KEY=your_google_api_key_here
```

**Important:** Keep the API key secret. Do not commit `.env` into source control; add it to `.gitignore`.

---

## How to run locally

From the project directory (where `app.py` lives):

```bash
# Activate your virtualenv first (see above)
streamlit run app.py
```

This will start a local Streamlit server and open a browser UI. Steps inside the app:
1. If the key prompt appears, either paste your `GOOGLE_API_KEY` or ensure `.env` is present.
2. Choose document type (`Form` or `Receipt`).
3. Upload a PDF or PNG file.
4. Edit/add fields to extract as needed.
5. Click **Extract Data** to invoke the GenAI extraction.
6. Review results and download JSON/CSV using the download buttons.

---

## How it works (implementation notes)

- `app.py` builds a **dynamic pydantic model** from user-provided fields, using `create_model` and `Field(description=...)`.
- The file upload is saved to a temporary file via `tempfile.NamedTemporaryFile` and then uploaded to the GenAI Files API (`client.files.upload`).
- The app then calls `client.models.generate_content` with:
  - `model` set to the `model_id` (`gemini-2.5-flash` by default in the code).
  - `contents` containing a short prompt string and a file object returned by `client.files.upload`.
  - `config` including `response_mime_type: application/json` and `response_schema` derived from the pydantic model.
- The response is parsed via `json.loads(res.text)` and shown to the user in table-like form using `pandas.json_normalize`.

---

## UI layout notes

- Dark theme background and customized component styles are included via inline CSS in `app.py`.
- The app shows the original document in one column and the extracted structured results in the other column.
- Results support multiple record extraction; each record is displayed separately with a separator line.
- Download buttons are provided for JSON and CSV exports.

---

## Recommended repository structure

```
DocuStruct/
├─ app.py
├─ Logo_wordmark.png          # optional
├─ Approach2.png              # diagram (optional)
├─ requirements.txt
├─ README.md
├─ .gitignore
└─ data/                      # for local datasets/artifacts (not checked in)
```

---

## Security & Cost considerations

- The app uses a hosted GenAI model (`gemini-2.5-flash`); calling this model may incur costs on your Google Cloud/GenAI billing account. Monitor usage and set quotas where possible.
- Avoid committing API keys or large model artifacts to the git repository. Use `.gitignore` for `.env`, `data/`, and model weights.

---

## Troubleshooting

- **"API key required" error**: ensure `GOOGLE_API_KEY` is set in `.env` or paste it into the UI when prompted.
- **No data extracted**: check that your schema fields match the document's visible labels; try a small set of fields first.
- **Unsupported file type**: the uploader accepts only `pdf` and `png` by default.
- **Permissions**: if running on Windows, ensure Streamlit has permission to read temporary files.

---

## Contributing

If you plan to expand this project, consider:
- Adding unit tests around schema generation and response parsing.
- Packaging extraction code into testable modules (separate logic from UI).
- Adding support for more file types (JPEG, TIFF) and OCR fallback for scanned images.
- Adding retries & better error handling around the GenAI API calls.

---

## License

Add a LICENSE file (e.g., MIT) to make the repository open-source-friendly. If you want, I can add a recommended `LICENSE` file for you.

---

If you'd like, I can write this `README.md` into the project folder and also create a `.gitignore` tailored for Python/Streamlit projects. Would you like me to write those files now?
