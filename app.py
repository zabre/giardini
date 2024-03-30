import streamlit as st
import requests
import os
os.environ['CURL_CA_BUNDLE'] = ''
from bs4 import BeautifulSoup
import datetime
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

# Function to generate date string based on current date and date french converter (manual lol)
def get_date_str(date):
    days_of_week = {
        0: 'lundi',
        1: 'mardi',
        2: 'mercredi',
        3: 'jeudi',
        4: 'vendredi',
        5: 'samedi',
        6: 'dimanche'
    }
    months = {
        1: 'janvier',
        2: 'février',
        3: 'mars',
        4: 'avril',
        5: 'mai',
        6: 'juin',
        7: 'juillet',
        8: 'août',
        9: 'septembre',
        10: 'octobre',
        11: 'novembre',
        12: 'décembre'
    }
    day_of_week = days_of_week[date.weekday()]
    month = months[date.month]
    return f"{day_of_week}-{date.day}-{month}-{date.year}"


# Function to analyze text and retrieve relevant content
def analyze_text(text_content, date_tag, url_tag, c_words, t_words):
    c_word_results = []
    t_word_results = []

    # Find C-Word mentions and context
    for c_word in c_words:
        index = text_content.find(c_word)
        while index != -1:
            start_index = max(0, index - 70)
            end_index = index + len(c_word) + 70
            context = text_content[start_index:end_index]
            c_word_results.append((c_word, f"{date_tag}{url_tag}{context}"))
            index = text_content.find(c_word, end_index)

    # Find T-Word mentions and context, and generate summaries using OpenAI API
    for t_word in t_words:
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

    # Add input fields for C-Words and T-Words
    c_words_input = st.text_input("Enter C-Words (comma-separated)")
    t_words_input = st.text_input("Enter T-Words (comma-separated)")

    # Convert input strings to lists
    c_words = [word.strip() for word in c_words_input.split(',')] if c_words_input else []
    t_words = [word.strip() for word in t_words_input.split(',')] if t_words_input else []

    # Add a date input field
    selected_date = st.date_input("Select a date")

    if st.button("Analyze News"):
        date_str = get_date_str(selected_date)
        url = f'https://www.assemblee-nationale.fr/dyn/16/comptes-rendus/seance/session-ordinaire-de-2023-2024/seance-du-{date_str}'
        st.write(f"Checking URL: {url}")
        text_content = get_text_content(url)
        if text_content is not None:
            date_tag = f"Date: {date_str}"
            url_tag = f"URL: {url.split('-2024/')[-1]}"
            c_word_results, t_word_results = analyze_text(text_content, date_tag, url_tag, c_words, t_words)

            # Display C-Word results
            st.subheader("C-Word Results")
            c_word_table = f'<table><tr><th>C-Word</th><th>Context</th></tr>{"".join([f"<tr><td>{c_word}</td><td>{context}</td></tr>" for c_word, context in c_word_results])}</table>'
            st.markdown(c_word_table, unsafe_allow_html=True)

            # Display T-Word results
            st.subheader("T-Word Results")
            t_word_summary = get_t_word_summary(t_word_results)
            st.markdown(t_word_summary, unsafe_allow_html=True)
        else:
            st.write("No text content found for the selected date.")

if __name__ == "__main__":
    main()
