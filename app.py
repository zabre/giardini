import streamlit as st
import requests
import os
os.environ['CURL_CA_BUNDLE'] = ''
from bs4 import BeautifulSoup
import datetime
import locale
import traceback
from openai import OpenAI

client = OpenAI(
    api_key="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",  # Replace with your API key
)

# Define C-Words and T-Words
C_WORDS = ['edf', 'systeme u', 'plastic omnium', 'danone', 'vey', 'netflix', 'emirates', 'eiffage', 'grt gaz', 'legrand']
T_WORDS = ['avocat', 'énergie', 'automobile', 'autoroute', 'retraite', "sécurité", "vie"]

# Function to get text content from webpage
def get_text_content(url):
    print("Getting text content from URL...")
    try:
        response = requests.get(url, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = soup.get_text()
        print("Text content retrieved")
        return text_content
    except Exception as e:
        print(f"Error retrieving text content: {e}")
        traceback.print_exc()
        return None

# Function to generate date string based on current date
def get_date_str(include_yesterday=False):
    # Set the locale to French
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')

    if include_yesterday:
        # Get yesterday's date
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        date_str = yesterday.strftime('%A %d %B %Y')
    else:
        # Get today's date
        today = datetime.date.today()
        date_str = today.strftime('%A %d %B %Y')

    date_str = date_str.lower()
    date_str = date_str.replace(' ', '-')
    return date_str

# Function to analyze text and retrieve relevant content
def analyze_text(text_content, date_tag, url_tag):
    c_word_results = []
    t_word_results = []

    # Find C-Word mentions and context
    for c_word in C_WORDS:
        index = text_content.find(c_word)
        while index != -1:
            start_index = max(0, index - 70)
            end_index = index + len(c_word) + 70
            context = text_content[start_index:end_index]
            c_word_results.append((c_word, f"{date_tag}{url_tag}{context}"))
            index = text_content.find(c_word, end_index)

    # Find T-Word mentions and context, and generate summaries using OpenAI API
    for t_word in T_WORDS:
        index = text_content.find(t_word)
        while index != -1:
            start_index = max(0, index - 100)
            end_index = index + len(t_word) + 100
            context = text_content[start_index:end_index]
            summary = get_summary(t_word, context)
            if summary is not None:
                t_word_results.append((t_word, f"{date_tag}{url_tag}{summary}"))
            index = text_content.find(t_word, end_index)

    return c_word_results, t_word_results

# Function to send a request to OpenAI API
def get_summary(t_word, context):
    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"""
                    You are a helpful assistant that can summarize text related to a specific topic.
                    Here is some context related to the topic '{t_word}':
                    {context}
                    Please provide a summary of the context related to the topic '{t_word}', analyzing each point separately. 
                    Answer in French only.
                    """
                }],
            model="gpt-4-0125-preview",
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        print(f"Error retrieving summary for {t_word}: {e}")
        return None

def get_t_word_summary(t_word_results):
    t_word_summary = ""
    t_word_contexts = {}

    # Concatenate contexts related to the same T-Word
    for t_word, context in t_word_results:
        if t_word in t_word_contexts:
            t_word_contexts[t_word] += context
        else:
            t_word_contexts[t_word] = context

    # Get summary for each T-Word and its contexts
    for t_word, context in t_word_contexts.items():
        summary = get_summary(t_word, context)
        t_word_summary += f"<h3>{t_word}</h3><p>{summary}</p>"

    return t_word_summary

def main():
    st.set_page_config(page_title="French National Assembly News Analyzer")
    st.title("French National Assembly News Analyzer")

    # Add a checkbox to include yesterday's date
    include_yesterday = st.checkbox("Include yesterday's date")

    if st.button("Analyze News"):
        date_str = get_date_str(include_yesterday=include_yesterday)
        urls = [
            f'https://www.assemblee-nationale.fr/dyn/16/comptes-rendus/seance/session-ordinaire-de-2023-2024/premiere-seance-du-{date_str}',
            f'https://www.assemblee-nationale.fr/dyn/16/comptes-rendus/seance/session-ordinaire-de-2023-2024/deuxieme-seance-du-{date_str}',
            f'https://www.assemblee-nationale.fr/dyn/16/comptes-rendus/seance/session-ordinaire-de-2023-2024/troisieme-seance-du-{date_str}'
        ]
        c_word_results = []
        t_word_results = []
        for url in urls:
            st.write(f"Checking URL: {url}")
            text_content = get_text_content(url)
            if text_content is not None:
                date_tag = f"Date: {date_str}"
                url_tag = f"URL: {url.split('-2024/')[-1]}"
                c_results, t_results = analyze_text(text_content, date_tag, url_tag)
                c_word_results.extend(c_results)
                t_word_results.extend(t_results)
            else:
                st.write("Skipping URL (text content not retrieved)")

        # Display C-Word results
        st.subheader("C-Word Results")
        c_word_table = f'<table><tr><th>C-Word</th><th>Context</th></tr>{"".join([f"<tr><td>{c_word}</td><td>{context}</td></tr>" for c_word, context in c_word_results])}</table>'
        st.markdown(c_word_table, unsafe_allow_html=True)

        # Display T-Word results
        st.subheader("T-Word Results")
        t_word_summary = get_t_word_summary(t_word_results)
        st.markdown(t_word_summary, unsafe_allow_html=True)

if __name__ == "__main__":
    main()