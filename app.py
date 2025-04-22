import requests
import streamlit as st
import urllib.parse
import pandas as pd
import io
import json
import os
import re
from datetime import datetime


def init_json_logs():
    if not os.path.exists('user_logs.json'):
        with open('user_logs.json', 'w') as f:
            json.dump([], f)


def add_log_entry(email):
    try:
        with open('user_logs.json', 'r') as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []
    logs.append({
        'email': email,
        'login_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    with open('user_logs.json', 'w') as f:
        json.dump(logs, f, indent=4)


def is_valid_zoho_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@zohocorp\.com$'
    return bool(re.match(pattern, email))


def authenticate(email):
    if is_valid_zoho_email(email):
        add_log_entry(email)
        return True
    return False


def load_css():
    st.markdown("""
        <style>
        .stApp {
            background-color: #FFFFFF;
            color: #333333;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            border-radius: 4px;
            border: none;
            padding: 8px 16px;
            transition: background-color 0.3s;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        .sidebar .sidebar-content {
            background-color: #f8f9fa;
        }
        </style>
    """, unsafe_allow_html=True)


def get_linkedin_profile(api_key, first_name, last_name, company, title=None, country=None):
    search_query = f"{first_name} {last_name} {company} site:linkedin.com/in/"
    if title:
        search_query += f" {title}"
    if country:
        search_query += f" {country}"

    params = {
        "q": search_query,
        "hl": "en",
        "gl": "us",
        "api_key": api_key
    }

    response = requests.get("https://serpapi.com/search", params=params)
    if response.status_code != 200:
        return "Error: Unable to fetch search results"

    results = response.json().get("organic_results", [])
    for result in results:
        link = result.get("link", "")
        if "linkedin.com/in/" in link:
            return link

    return "No LinkedIn profile found"


def main():
    load_css()
    init_json_logs()

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title("🔐 Login")
        with st.form("login_form"):
            email = st.text_input("Email (@zohocorp.com)")
            submit = st.form_submit_button("Login")
            if submit:
                if authenticate(email):
                    st.session_state.logged_in = True
                    st.experimental_rerun()
                else:
                    st.error("Invalid login. Please use your @zohocorp.com email.")
    else:
        st.title("LinkedIn Profile Finder")
        st.sidebar.info("© Built by the UEMS Marketing team")
        st.sidebar.success("Logged in successfully!")

        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.experimental_rerun()

        st.markdown(
            "**Instructions:**\n - Get your SerpAPI key from [SerpAPI](https://serpapi.com/) by signing up.\n - Upload a CSV or Excel file with the following columns: First Name, Last Name, Company, Title (Optional), Country (Optional).\n - Click 'Find Profiles' to retrieve LinkedIn profiles.")

        sample_data = pd.DataFrame({
            "First Name": ["John"],
            "Last Name": ["Doe"],
            "Company": ["Google"],
            "Title": ["Software Engineer"],
            "Country": ["USA"]
        })

        sample_file = io.BytesIO()
        sample_data.to_csv(sample_file, index=False)
        sample_file.seek(0)
        st.download_button("Download Sample CSV", sample_file, "sample.csv", "text/csv")

        api_key = st.text_input("Enter your SerpAPI Key", type="password")
        uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])

        if uploaded_file and api_key:
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)

            if "First Name" in df.columns and "Last Name" in df.columns and "Company" in df.columns:
                df["LinkedIn Profile"] = df.apply(
                    lambda row: get_linkedin_profile(api_key, row["First Name"], row["Last Name"], row["Company"],
                                                     row.get("Title", None), row.get("Country", None)), axis=1)
                st.write(df)

                output = io.BytesIO()
                df.to_csv(output, index=False)
                output.seek(0)
                st.download_button("Download Results", output, "linkedin_profiles.csv", "text/csv")
            else:
                st.error("Uploaded file must contain at least 'First Name', 'Last Name', and 'Company' columns.")


if __name__ == "__main__":
    main()
