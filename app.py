import streamlit as st
import requests
import os
from bs4 import BeautifulSoup
import datetime
from datetime import date
import traceback
from openai import OpenAI
from PIL import Image
from fpdf import FPDF
import unidecode
from typing import List, Tuple, Optional
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AssemblyURLGenerator:
    DAYS = {
        0: 'lundi',
        1: 'mardi',
        2: 'mercredi',
        3: 'jeudi',
        4: 'vendredi',
        5: 'samedi',
        6: 'dimanche'
    }
    
    MONTHS = {
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
    
    SESSIONS = ["premiere", "deuxieme", "troisieme"]
    BASE_URL = "https://www.assemblee-nationale.fr/dyn/17/comptes-rendus/seance"

    @staticmethod
    def get_session_year(date_obj: date) -> str:
        """Determine the correct session year based on date."""
        year = date_obj.year
        if date_obj.month >= 9:  # New session starts in September
            return f"{year}-{year+1}"
        return f"{year-1}-{year}"

    @staticmethod
    def format_date_string(date_obj: date) -> str:
        """Format date string in French format."""
        return f"{AssemblyURLGenerator.DAYS[date_obj.weekday()]}-{date_obj.day}-{AssemblyURLGenerator.MONTHS[date_obj.month]}-{date_obj.year}"

    @classmethod
    def generate_urls(cls, date_obj: date) -> List[str]:
        """Generate all possible session URLs for a given date."""
        session_year = cls.get_session_year(date_obj)
        date_str = cls.format_date_string(date_obj)
        
        return [
            f"{cls.BASE_URL}/session-ordinaire-de-{session_year}/{session}-seance-du-{date_str}"
            for session in cls.SESSIONS
        ]

class ContentAnalyzer:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        
    def get_text_content(self, url: str) -> Optional[str]:
        """Fetch and parse content from URL with error handling."""
        try:
            response = requests.get(url, verify=False, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup.get_text()
        except Exception as e:
            logger.error(f"Error fetching content from {url}: {str(e)}")
            return None

    def get_context_window(self, text: str, word: str, window_size: int = 10) -> str:
        """Extract context window around word with specified number of words before and after."""
        word_index = text.lower().find(word.lower())
        if word_index == -1:
            return ""

        # Get text before the word
        text_before = text[:word_index].strip()
        words_before = text_before.split()[-window_size:] if text_before else []

        # Get text after the word
        text_after = text[word_index + len(word):].strip()
        words_after = text_after.split()[:window_size] if text_after else []

        # Combine the context
        context = (
            " ".join(words_before) +
            f" **{text[word_index:word_index + len(word)]}** " +
            " ".join(words_after)
        )
        
        return f"...{context.strip()}..."

    def analyze_text(self, text_content: str, date_tag: str, url_tag: str, 
                    c_words: List[str], t_words: List[str]) -> Tuple[List, List]:
        """Enhanced text analysis with context window."""
        if not text_content:
            return [], []

        c_word_results = []
        t_word_results = []

        paragraphs = text_content.split('\n\n')
        
        for paragraph in paragraphs:
            for c_word in c_words:
                if c_word.lower() in paragraph.lower():
                    context = self.get_context_window(paragraph, c_word)
                    if context:
                        c_word_results.append((c_word, f"{date_tag}\n{url_tag}\nContexte: {context}"))
                    
            for t_word in t_words:
                if t_word.lower() in paragraph.lower():
                    context = self.get_context_window(paragraph, t_word, window_size=15)
                    if context:
                        summary = self.get_summary(t_word, context)
                        if summary:
                            t_word_results.append((t_word, f"{date_tag}\n{url_tag}\n{summary}"))

        return c_word_results, t_word_results

    def get_summary(self, topic: str, context: str) -> Optional[str]:
        """Generate enhanced summaries with better prompt engineering."""
        try:
            response = self.client.chat.completions.create(
                messages=[{
                    "role": "system",
                    "content": f"""
                    En tant qu'expert en analyse parlementaire, analysez le contexte suivant 
                    concernant le sujet '{topic}'. Veuillez fournir:
                    1. Un résumé concis (2-3 lignes maximum)
                    2. Les implications potentielles (1 ligne)
                    3. Les acteurs clés mentionnés (liste courte)
                    
                    Contexte: {context}
                    """
                }],
                model="gpt-4-0125-preview",
                temperature=0.7,
                max_tokens=250
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return None

class PDFExporter:
    def __init__(self):
        self.pdf = FPDF()
        self.pdf.set_auto_page_break(auto=True, margin=15)

    def export_results(self, c_word_results: List, t_word_results: List, filename: str):
        """Enhanced PDF export with better formatting and structure."""
        self.pdf.add_page()
        self._add_header()
        self._add_timestamp()
        self._add_client_section(c_word_results)
        self._add_theme_section(t_word_results)
        self.pdf.output(filename)

    def _add_header(self):
        """Add styled header to PDF."""
        self.pdf.set_font("Arial", "B", 16)
        self.pdf.cell(0, 10, "Synthèse des débats à l'Assemblée", ln=True, align='C')
        self.pdf.ln(10)

    def _add_timestamp(self):
        """Add generation timestamp."""
        self.pdf.set_font("Arial", "I", 10)
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.pdf.cell(0, 10, f"Généré le: {timestamp}", ln=True)
        self.pdf.ln(5)

    def _add_client_section(self, results: List):
        """Add client mentions section."""
        if results:
            self.pdf.set_font("Arial", "B", 14)
            self.pdf.cell(0, 10, "Mentions", ln=True)
            self.pdf.ln(5)
            
            for client, context in results:
                self.pdf.set_font("Arial", "B", 12)
                self.pdf.cell(0, 10, unidecode.unidecode(client), ln=True)
                self.pdf.set_font("Arial", "", 10)
                self.pdf.multi_cell(0, 10, unidecode.unidecode(context))
                self.pdf.ln(5)

    def _add_theme_section(self, results: List):
        """Add thematic analysis section."""
        if results:
            self.pdf.set_font("Arial", "B", 14)
            self.pdf.cell(0, 10, "Analyse Thématique", ln=True)
            self.pdf.ln(5)
            
            for theme, analysis in results:
                self.pdf.set_font("Arial", "B", 12)
                self.pdf.cell(0, 10, unidecode.unidecode(theme), ln=True)
                self.pdf.set_font("Arial", "", 10)
                self.pdf.multi_cell(0, 10, unidecode.unidecode(analysis))
                self.pdf.ln(5)

def main():
    st.set_page_config(
        page_title="Giardini",
        page_icon="🐭",
        layout="wide"
    )

    # UI Components
    st.title("🐭 Giardini, la petite souris de l'Assemblée")
    
    # Initialize components
    url_generator = AssemblyURLGenerator()
    content_analyzer = ContentAnalyzer(st.secrets["OPENAI_API_KEY"])
    pdf_exporter = PDFExporter()

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Date de début", min_value=date(2022, 1, 1))
        c_words = st.text_input("Entités à suivre (séparées par des virgules)")
        c_words = [word.strip() for word in c_words.split(',')] if c_words else []
    
    with col2:
        end_date = st.date_input("Date de fin", min_value=start_date)
        t_words = st.text_input("Thématiques à suivre (séparées par des virgules)")
        t_words = [word.strip() for word in t_words.split(',')] if t_words else []

    if st.button("Lancer Giardini", type="primary"):
        if not c_words and not t_words:
            st.error("Veuillez spécifier au moins une entité ou une thématique à suivre.")
            return

        progress_bar = st.progress(0)
        status_text = st.empty()
        
        all_c_results = []
        all_t_results = []
        
        current_date = start_date
        total_days = (end_date - start_date).days + 1
        days_processed = 0

        while current_date <= end_date:
            urls = url_generator.generate_urls(current_date)
            
            for url in urls:
                status_text.text(f"Analyse de la séance du {current_date.strftime('%d/%m/%Y')}...")
                text_content = content_analyzer.get_text_content(url)
                
                if text_content:
                    date_tag = f"Date: {current_date.strftime('%d/%m/%Y')}"
                    url_tag = f"Source: {url}"
                    c_results, t_results = content_analyzer.analyze_text(
                        text_content, date_tag, url_tag, c_words, t_words
                    )
                    all_c_results.extend(c_results)
                    all_t_results.extend(t_results)

            days_processed += 1
            progress = int((days_processed / total_days) * 100)
            progress_bar.progress(progress)
            current_date += timedelta(days=1)

        if all_c_results or all_t_results:
            status_text.text("Génération de la synthèse PDF...")
            pdf_exporter.export_results(all_c_results, all_t_results, "synthese_debats.pdf")
            
            with open("synthese_debats.pdf", "rb") as pdf_file:
                st.download_button(
                    label="Télécharger la synthèse PDF",
                    data=pdf_file,
                    file_name="synthese_debats.pdf",
                    mime="application/pdf"
                )
            
            st.success("Analyse terminée! Vous pouvez télécharger la synthèse PDF.")
        else:
            st.warning("Aucune mention trouvée pour la période spécifiée.")

        status_text.empty()
        progress_bar.empty()

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray; font-size: 12px;'>
            Développé par TBWA Corporate | Usage Interne Uniquement
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
