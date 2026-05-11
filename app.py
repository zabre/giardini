import streamlit as st
import requests
import zipfile
import io
import pandas as pd
import re
import time
import json
import os
import html
from lxml import etree
from bs4 import BeautifulSoup

# ==========================================
# CONFIGURATION
# ==========================================

SAVED_QUERIES_FILE = "saved_queries.json"

st.set_page_config(
    page_title="GIARDINI | Veille Parlementaire",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
}

# ==========================================
# DESIGN
# ==========================================

def inject_custom_css(theme):
    if theme == "LIGHT":
        bg_color = "#F4F4F0"
        bg_sec_color = "#EAEAE5"
        text_color = "#1A1A1A"
        border_color = "#D2D2D2"
        muted_color = "#777777"
    else:
        bg_color = "#000000"
        bg_sec_color = "#0A0A0A"
        text_color = "#FFFFFF"
        border_color = "#333333"
        muted_color = "#666666"

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Doto:wght@700;900&family=Space+Grotesk:wght@400;600;700&family=Space+Mono:ital,wght@0,400;0,700;1,400&display=swap');

    :root {{
        --bg: {bg_color};
        --bg-sec: {bg_sec_color};
        --text: {text_color};
        --border: {border_color};
        --muted: {muted_color};
        --accent: #D71921;
    }}

    html, body, [class*="css"], .stApp {{
        font-family: 'Space Grotesk', sans-serif !important;
        background-color: var(--bg) !important;
        color: var(--text) !important;
    }}

    #MainMenu {{
        visibility: hidden;
    }}

    footer {{
        visibility: hidden;
    }}

    div[data-testid="stDecoration"] {{
        display: none;
    }}

    /* IMPORTANT : ne pas cacher le header, sinon le bouton pour rouvrir la sidebar disparaît */
    header[data-testid="stHeader"] {{
        visibility: visible !important;
        background: transparent !important;
    }}

    header {{
        background: transparent !important;
    }}

    .hero-title {{
        font-family: 'Doto', sans-serif;
        font-size: 6vw;
        font-weight: 900;
        line-height: 0.9;
        letter-spacing: -2px;
        text-transform: uppercase;
        margin: 0;
        padding: 0;
        color: var(--text);
    }}

    .hero-subtitle {{
        font-family: 'Space Mono', monospace;
        font-size: 14px;
        color: var(--accent);
        text-transform: uppercase;
        letter-spacing: 4px;
        margin-bottom: 40px;
        display: block;
    }}

    .tertiary-text {{
        font-family: 'Space Mono', monospace;
        font-size: 11px;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 1px;
    }}

    .red-accent {{
        color: var(--accent) !important;
    }}

    .bool-help {{
        font-family: 'Space Mono', monospace;
        font-size: 10px;
        color: var(--muted);
        line-height: 1.6;
        padding: 8px;
        border-left: 2px solid var(--accent);
        margin-top: 6px;
    }}

    .bool-error {{
        font-family: 'Space Mono', monospace;
        font-size: 10px;
        color: var(--accent);
        padding: 6px 8px;
        border: 1px solid var(--accent);
        margin-top: 6px;
    }}

    .metric-card {{
        border: 1px solid var(--border);
        background-color: var(--bg-sec);
        padding: 14px 16px;
        margin-bottom: 10px;
    }}

    .metric-value {{
        font-family: 'Doto', sans-serif;
        font-size: 42px;
        line-height: 1;
        color: var(--text);
    }}

    .metric-label {{
        font-family: 'Space Mono', monospace;
        font-size: 10px;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 6px;
    }}

    .section-title {{
        font-family: 'Space Mono', monospace;
        font-size: 11px;
        color: var(--accent);
        text-transform: uppercase;
        letter-spacing: 1px;
        border-bottom: 1px solid var(--border);
        padding-bottom: 8px;
        margin-top: 20px;
        margin-bottom: 12px;
    }}

    .speaker-card {{
        border: 1px solid var(--border);
        padding: 18px;
        background: var(--bg);
        margin-bottom: 12px;
    }}

    .speaker-name {{
        font-family: 'Space Mono', monospace;
        color: var(--accent);
        font-size: 14px;
        font-weight: bold;
        text-transform: uppercase;
    }}

    div[data-testid="stExpander"] {{
        background-color: var(--bg) !important;
        border: 1px solid var(--border) !important;
        border-radius: 0px !important;
        box-shadow: none !important;
        margin-bottom: 10px;
    }}

    div[data-testid="stExpander"] summary {{
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        color: var(--text) !important;
    }}

    div.stTextInput > div > div > input,
    div.stTextArea textarea,
    div[data-baseweb="select"] > div {{
        border-radius: 4px !important;
        border: 1px solid var(--border) !important;
        background-color: var(--bg-sec) !important;
        font-family: 'Space Mono', monospace !important;
        font-size: 13px !important;
        color: var(--text) !important;
    }}

    div.stTextInput > div > div > input:focus {{
        border-color: var(--accent) !important;
        box-shadow: none !important;
    }}

    span[data-baseweb="tag"] {{
        background-color: var(--accent) !important;
        color: #FFF !important;
        border-radius: 0px !important;
        border: none !important;
        font-family: 'Space Mono', monospace !important;
        font-size: 11px !important;
    }}

    label[data-testid="stWidgetLabel"] {{
        font-family: 'Space Mono', monospace !important;
        font-size: 11px !important;
        color: var(--muted) !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}

    div[role="radiogroup"] label {{
        font-family: 'Space Mono', monospace !important;
        font-size: 12px !important;
        color: var(--text) !important;
    }}

    div.stButton > button,
    div.stDownloadButton > button {{
        background-color: var(--bg-sec) !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
        border-radius: 4px !important;
        font-family: 'Space Mono', monospace !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 12px !important;
    }}

    div.stButton > button:hover,
    div.stDownloadButton > button:hover {{
        border-color: var(--accent) !important;
        color: var(--accent) !important;
    }}

    mark.industrial-highlight {{
        background-color: transparent;
        color: var(--accent);
        font-weight: bold;
        border-bottom: 2px solid var(--accent);
        padding: 0 2px;
    }}

    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}

    ::-webkit-scrollbar-track {{
        background: var(--bg);
    }}

    ::-webkit-scrollbar-thumb {{
        background: var(--border);
        border-radius: 0px;
    }}

    ::-webkit-scrollbar-thumb:hover {{
        background: var(--accent);
    }}
    </style>
    """, unsafe_allow_html=True)


def section_title(label):
    st.markdown(f'<div class="section-title">[ {label} ]</div>', unsafe_allow_html=True)


def metric_card(value, label):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-value">{value}</div>
            <div class="metric-label">{label}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def safe_text(value):
    if value is None:
        return ""
    return html.escape(str(value))


# ==========================================
# UTILITAIRES
# ==========================================

def parse_french_date_to_sortable(datestr):
    months = {
        "janvier": "01",
        "février": "02",
        "mars": "03",
        "avril": "04",
        "mai": "05",
        "juin": "06",
        "juillet": "07",
        "août": "08",
        "septembre": "09",
        "octobre": "10",
        "novembre": "11",
        "décembre": "12"
    }

    match = re.search(r"(\d{1,2})\s+([a-zéû]+)\s+(\d{4})", datestr.lower())

    if match:
        return f"{match.group(3)}-{months.get(match.group(2), '00')}-{match.group(1).zfill(2)}"

    return "0000-00-00"


def get_secret_key(secret_name, default_val):
    try:
        return st.secrets[secret_name]
    except Exception:
        return default_val


def download_with_resume(url, max_retries=10, chunk_size=512 * 1024, timeout=60):
    buffer = bytearray()
    attempt = 0

    try:
        head = requests.head(url, headers=BROWSER_HEADERS, timeout=timeout)
        total_size = int(head.headers.get("Content-Length", 0))
        accepts_ranges = head.headers.get("Accept-Ranges", "none").lower() != "none"
    except Exception:
        total_size = 0
        accepts_ranges = False

    while attempt < max_retries:
        offset = len(buffer)

        if total_size > 0 and offset >= total_size:
            break

        headers = {**BROWSER_HEADERS}

        if accepts_ranges and offset > 0:
            headers["Range"] = f"bytes={offset}-"

        try:
            resp = requests.get(url, headers=headers, stream=True, timeout=timeout)

            if resp.status_code not in (200, 206):
                raise requests.exceptions.HTTPError(
                    f"HTTP {resp.status_code}",
                    response=resp
                )

            if resp.status_code == 200 and offset > 0:
                buffer = bytearray()

            for chunk in resp.iter_content(chunk_size=chunk_size):
                if chunk:
                    buffer.extend(chunk)

            break

        except (
            requests.exceptions.ChunkedEncodingError,
            requests.exceptions.ConnectionError,
            requests.exceptions.ReadTimeout
        ) as e:
            attempt += 1

            if attempt >= max_retries:
                raise RuntimeError(
                    f"[FR] Échec après {max_retries} tentatives. "
                    f"Dernière erreur : {type(e).__name__} — {e}"
                )

            wait = min(2 ** attempt, 30)
            time.sleep(wait)

    if total_size > 0 and len(buffer) < total_size:
        raise RuntimeError(
            f"[FR] Téléchargement incomplet : {len(buffer)} / {total_size} octets."
        )

    return bytes(buffer)


# ==========================================
# REQUÊTES SAUVEGARDÉES
# ==========================================

def load_saved_queries():
    if not os.path.exists(SAVED_QUERIES_FILE):
        return {}

    try:
        with open(SAVED_QUERIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_saved_queries(data):
    try:
        with open(SAVED_QUERIES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def build_simple_query(main_terms, associated_terms, excluded_terms, exact_phrase):
    positives = []

    def split_terms(raw):
        if not raw:
            return []
        return [t.strip() for t in re.split(r"[,;\n]", raw) if t.strip()]

    for term in split_terms(main_terms):
        positives.append(term)

    for term in split_terms(associated_terms):
        positives.append(term)

    if exact_phrase.strip():
        positives.append(f'"{exact_phrase.strip()}"')

    positives = list(dict.fromkeys(positives))

    if len(positives) == 0:
        return ""

    if len(positives) == 1:
        query = positives[0]
    else:
        query = "(" + " OR ".join(positives) + ")"

    excluded = split_terms(excluded_terms)

    if excluded:
        query += " NOT (" + " OR ".join(excluded) + ")"

    return query


# ==========================================
# MOTEUR BOOLÉEN
# ==========================================

class BooleanQueryError(Exception):
    pass


TOKEN_AND = "AND"
TOKEN_OR = "OR"
TOKEN_NOT = "NOT"
TOKEN_MINUS = "MINUS"
TOKEN_LPAREN = "LPAREN"
TOKEN_RPAREN = "RPAREN"
TOKEN_PHRASE = "PHRASE"
TOKEN_TERM = "TERM"
TOKEN_EOF = "EOF"


def tokenize(query: str):
    tokens = []
    i = 0
    q = query.strip()

    while i < len(q):
        if q[i].isspace():
            i += 1
            continue

        if q[i] == '"':
            j = q.find('"', i + 1)
            if j == -1:
                raise BooleanQueryError("Guillemet fermant manquant.")
            tokens.append((TOKEN_PHRASE, q[i + 1:j]))
            i = j + 1
            continue

        if q[i] == "(":
            tokens.append((TOKEN_LPAREN, "("))
            i += 1
            continue

        if q[i] == ")":
            tokens.append((TOKEN_RPAREN, ")"))
            i += 1
            continue

        if q[i] == "-" and (i == 0 or q[i - 1].isspace() or q[i - 1] == "("):
            tokens.append((TOKEN_MINUS, "-"))
            i += 1
            continue

        j = i

        while j < len(q) and not q[j].isspace() and q[j] not in '()"':
            j += 1

        word = q[i:j]
        upper = word.upper()

        if upper == "AND":
            tokens.append((TOKEN_AND, "AND"))
        elif upper == "OR":
            tokens.append((TOKEN_OR, "OR"))
        elif upper == "NOT":
            tokens.append((TOKEN_NOT, "NOT"))
        else:
            tokens.append((TOKEN_TERM, word))

        i = j

    tokens.append((TOKEN_EOF, ""))
    return tokens


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos][0]

    def consume(self, expected=None):
        tok = self.tokens[self.pos]

        if expected and tok[0] != expected:
            raise BooleanQueryError(f"Attendu '{expected}', trouvé '{tok[1]}'")

        self.pos += 1
        return tok

    def parse(self):
        node = self.parse_or()

        if self.peek() != TOKEN_EOF:
            raise BooleanQueryError("Requête mal formée.")

        return node

    def parse_or(self):
        left = self.parse_and()

        while self.peek() == TOKEN_OR:
            self.consume(TOKEN_OR)
            right = self.parse_and()
            left = ("OR", left, right)

        return left

    def parse_and(self):
        left = self.parse_not()

        while self.peek() not in (TOKEN_OR, TOKEN_RPAREN, TOKEN_EOF):
            if self.peek() == TOKEN_AND:
                self.consume(TOKEN_AND)

            right = self.parse_not()
            left = ("AND", left, right)

        return left

    def parse_not(self):
        if self.peek() in (TOKEN_NOT, TOKEN_MINUS):
            self.consume()
            return ("NOT", self.parse_primary())

        return self.parse_primary()

    def parse_primary(self):
        tok_type, tok_val = self.tokens[self.pos]

        if tok_type == TOKEN_TERM:
            self.consume()
            return ("TERM", tok_val)

        if tok_type == TOKEN_PHRASE:
            self.consume()
            return ("PHRASE", tok_val)

        if tok_type == TOKEN_LPAREN:
            self.consume(TOKEN_LPAREN)
            node = self.parse_or()
            self.consume(TOKEN_RPAREN)
            return node

        raise BooleanQueryError(f"Token inattendu : '{tok_val}'")


def build_ast(query: str):
    if not query.strip():
        return None

    return Parser(tokenize(query)).parse()


def evaluate_ast(node, text: str) -> bool:
    if node is None:
        return True

    kind = node[0]

    if kind == "TERM":
        return bool(re.search(re.escape(node[1]), text, re.IGNORECASE))

    if kind == "PHRASE":
        return bool(re.search(re.escape(node[1]), text, re.IGNORECASE))

    if kind == "AND":
        return evaluate_ast(node[1], text) and evaluate_ast(node[2], text)

    if kind == "OR":
        return evaluate_ast(node[1], text) or evaluate_ast(node[2], text)

    if kind == "NOT":
        return not evaluate_ast(node[1], text)

    return False


def collect_positive_terms(node):
    if node is None:
        return []

    kind = node[0]

    if kind in ("TERM", "PHRASE"):
        return [node[1]]

    if kind in ("AND", "OR"):
        return collect_positive_terms(node[1]) + collect_positive_terms(node[2])

    if kind == "NOT":
        return []

    return []


def boolean_search_and_highlight(df: pd.DataFrame, query: str):
    if not query.strip():
        empty = df.copy()
        empty["VerbatimHighlight"] = empty["Verbatim"]
        empty["MotsTrouves"] = ""
        empty["SearchScore"] = 0
        return empty.iloc[0:0], [], None

    try:
        ast = build_ast(query)
    except BooleanQueryError as e:
        empty = df.copy()
        empty["VerbatimHighlight"] = empty["Verbatim"]
        empty["MotsTrouves"] = ""
        empty["SearchScore"] = 0
        return empty.iloc[0:0], [], str(e)

    mask = df["Verbatim"].apply(lambda x: evaluate_ast(ast, str(x)))
    filtered = df[mask].copy()

    positive_terms = list(dict.fromkeys(collect_positive_terms(ast)))

    if positive_terms:
        pattern = "|".join(re.escape(t) for t in positive_terms)
        regex = re.compile(f"({pattern})", flags=re.IGNORECASE)

        def highlight_text(raw):
            escaped = html.escape(str(raw))
            return regex.sub(
                r'<mark class="industrial-highlight">\1</mark>',
                escaped
            )

        def found_terms(raw):
            matches = regex.findall(str(raw))
            return ", ".join(list(dict.fromkeys(m.lower() for m in matches)))

        def score_row(row):
            text = str(row["Verbatim"])
            subject = str(row.get("SujetDebat", ""))
            found = regex.findall(text)
            subject_hits = regex.findall(subject)
            length = len(text)

            score = len(found)
            score += 3 * len(subject_hits)

            if 180 <= length <= 1200:
                score += 2
            elif length > 1200:
                score += 1

            return score

        filtered["VerbatimHighlight"] = filtered["Verbatim"].apply(highlight_text)
        filtered["MotsTrouves"] = filtered["Verbatim"].apply(found_terms)
        filtered["SearchScore"] = filtered.apply(score_row, axis=1)

    else:
        filtered["VerbatimHighlight"] = filtered["Verbatim"].apply(
            lambda x: html.escape(str(x))
        )
        filtered["MotsTrouves"] = ""
        filtered["SearchScore"] = 0

    return filtered, positive_terms, None


# ==========================================
# SOURCE 1 — ASSEMBLÉE NATIONALE
# ==========================================

@st.cache_data(ttl=12 * 3600, show_spinner=False)
def fetch_and_index_fr(url):
    try:
        zip_bytes = download_with_resume(url)
    except RuntimeError as e:
        st.error(str(e))
        return None, None
    except requests.exceptions.HTTPError as e:
        st.error(f"[FR] ERREUR HTTP {e.response.status_code} : {e}")
        return None, None
    except Exception as e:
        st.error(f"[FR] ERREUR INATTENDUE : {type(e).__name__} — {e}")
        return None, None

    catalog = {}
    regex_file = re.compile(r"(S\d+\.N\d*\.xml|CRSANR.*\.xml)", re.IGNORECASE)
    ns = {"an": "http://schemas.assemblee-nationale.fr/referentiel"}

    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            for filename in z.namelist():
                if regex_file.search(filename):
                    root = etree.fromstring(z.read(filename))
                    date_nodes = root.xpath("//an:dateSeanceJour", namespaces=ns)

                    if date_nodes and date_nodes[0].text:
                        raw_date = date_nodes[0].text.strip()
                        sort_key = parse_french_date_to_sortable(raw_date)

                        if sort_key not in catalog:
                            catalog[sort_key] = {
                                "label": raw_date,
                                "files": []
                            }

                        catalog[sort_key]["files"].append(filename)

    except zipfile.BadZipFile as e:
        st.error(f"[FR] ZIP CORROMPU : {e}")
        return None, None
    except Exception as e:
        st.error(f"[FR] ERREUR PARSING INDEX : {type(e).__name__} — {e}")
        return None, None

    return zip_bytes, dict(sorted(catalog.items(), key=lambda item: item[0], reverse=True))


@st.cache_data(show_spinner=False)
def parse_selected_dates_fr(zip_bytes, selected_dates_info):
    ns = {"an": "http://schemas.assemblee-nationale.fr/referentiel"}
    data = []

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        for sort_key, info in selected_dates_info.items():
            date_label = info["label"]

            for filename in info["files"]:
                root = etree.fromstring(z.read(filename))

                moment = "SÉANCE"
                titre_nodes = (
                    root.xpath("//an:ouverture/an:titre", namespaces=ns)
                    or root.xpath("//an:titre", namespaces=ns)
                )

                if titre_nodes and titre_nodes[0].text:
                    ts = titre_nodes[0].text.lower()

                    if "première" in ts:
                        moment = "MATIN"
                    elif "deuxième" in ts:
                        moment = "APRÈS-MIDI"
                    elif "troisième" in ts:
                        moment = "NUIT"

                for para in root.xpath(".//an:paragraphe", namespaces=ns):
                    point_node = para.xpath("ancestor::an:point[1]/an:texte", namespaces=ns)
                    sujet = "".join(point_node[0].itertext()).strip() if point_node else "Sujet non défini"

                    rubrique_node = para.xpath("ancestor::an:point[1]//an:rubrique", namespaces=ns)
                    sequence = "".join(rubrique_node[0].itertext()).strip() if rubrique_node else "DÉBAT GÉNÉRAL"

                    orateur_node = para.xpath(".//an:orateurs/an:orateur/an:nom", namespaces=ns)
                    nom_orateur = (
                        orateur_node[0].text.strip()
                        if orateur_node and orateur_node[0].text
                        else "Assemblée"
                    )

                    qualite_node = para.xpath(".//an:orateurs/an:orateur/an:qualite", namespaces=ns)
                    qualite = (
                        qualite_node[0].text.strip()
                        if qualite_node and qualite_node[0].text
                        else "DÉPUTÉ.E"
                    )

                    texte_node = para.xpath(".//an:texte", namespaces=ns)

                    if not texte_node:
                        continue

                    verbatim = "".join(texte_node[0].itertext()).strip()

                    if not verbatim:
                        continue

                    italiques = para.xpath(".//an:texte//an:italique", namespaces=ns)
                    reactions = " | ".join([
                        it.text.strip()
                        for it in italiques
                        if it.text and it.text.strip()
                    ])

                    data.append({
                        "Institution": "ASSEMBLÉE NATIONALE",
                        "DateSortKey": sort_key,
                        "DateLabel": date_label,
                        "Moment": moment.upper(),
                        "SujetDebat": sujet.upper(),
                        "Sequence": sequence.upper(),
                        "NomOrateur": nom_orateur.upper(),
                        "Qualite": qualite.upper(),
                        "Verbatim": verbatim,
                        "Reactions": reactions,
                        "SourceUrl": ""
                    })

    return pd.DataFrame(data)


# ==========================================
# SOURCE 2 — PARLEMENT EUROPÉEN
# ==========================================

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_and_index_eu():
    try:
        url = "https://data.europarl.europa.eu/api/v2/plenary-session-documents"
        params = {
            "work_type": "def/ep-document-types/CRE_PLENARY",
            "limit": 1000
        }

        response = requests.get(
            url,
            params=params,
            headers={**BROWSER_HEADERS, "Accept": "application/ld+json"},
            timeout=30
        )

        response.raise_for_status()
        data = response.json().get("data", [])

    except Exception as e:
        st.error(f"[UE] ERREUR : {type(e).__name__} — {e}")
        return None, None

    catalog = {}

    for doc in data:
        doc_id = doc.get("identifier", "")

        if not doc_id or not doc_id.startswith("CRE-"):
            continue

        parts = doc_id.split("-")

        if len(parts) >= 5:
            try:
                year, month, day = parts[2], parts[3], parts[4]
                sort_key = f"{year}-{month}-{day}"
                date_label = f"{day}/{month}/{year}"

                if sort_key not in catalog:
                    catalog[sort_key] = {
                        "label": date_label,
                        "files": [doc_id]
                    }
                else:
                    catalog[sort_key]["files"].append(doc_id)

            except Exception:
                continue

    return b"eu_placeholder", dict(sorted(catalog.items(), key=lambda item: item[0], reverse=True))


@st.cache_data(show_spinner=False)
def parse_selected_dates_eu(dummy, selected_dates_info):
    data = []

    for sort_key, info in selected_dates_info.items():
        date_label = info["label"]

        for doc_id in info["files"]:
            xml_url = f"https://www.europarl.europa.eu/doceo/document/{doc_id}_FR.xml"

            try:
                resp = requests.get(xml_url, headers=BROWSER_HEADERS, timeout=30)

                if resp.status_code != 200:
                    continue

                root = etree.fromstring(resp.content)

            except Exception:
                continue

            for intervention in root.xpath("//INTERVENTION"):
                orateur_node = intervention.xpath(".//ORATEUR")

                if orateur_node:
                    nom = orateur_node[0].attrib.get("LIB", "INCONNU").replace(" | ", " ").upper()
                    groupe = orateur_node[0].attrib.get("PP", "GROUPE N/A").upper()
                else:
                    nom = "ASSEMBLÉE"
                    groupe = "PLÉNIÈRE"

                paras = intervention.xpath(".//PARA")
                verbatim = " ".join([
                    "".join(p.itertext()).strip()
                    for p in paras
                ]).strip()

                if not verbatim:
                    continue

                chapter_title = intervention.xpath("ancestor::CHAPTER/TITLE/text()")
                sujet = chapter_title[0].strip().upper() if chapter_title else "DÉBAT DE PLÉNIÈRE"

                agenda_point = intervention.xpath("ancestor::AGENDA-POINT/@number")
                sequence = f"POINT {agenda_point[0]}" if agenda_point else "N/A"

                italiques = intervention.xpath(".//I | .//i")
                reactions = " | ".join([
                    "".join(it.itertext()).strip()
                    for it in italiques
                    if "".join(it.itertext()).strip()
                ])

                data.append({
                    "Institution": "PARLEMENT EUROPÉEN",
                    "DateSortKey": sort_key,
                    "DateLabel": date_label,
                    "Moment": "PLÉNIÈRE",
                    "SujetDebat": sujet,
                    "Sequence": sequence,
                    "NomOrateur": nom,
                    "Qualite": groupe,
                    "Verbatim": verbatim,
                    "Reactions": reactions,
                    "SourceUrl": xml_url
                })

    return pd.DataFrame(data)


# ==========================================
# SOURCE 3 — CONGRÈS AMÉRICAIN
# ==========================================

@st.cache_data(ttl=12 * 3600, show_spinner=False)
def fetch_and_index_us():
    api_key = get_secret_key("CONGRESS_API_KEY", "DEMO_KEY")
    url = "https://api.congress.gov/v3/daily-congressional-record"

    params = {
        "api_key": api_key,
        "limit": 20,
        "format": "json"
    }

    try:
        response = requests.get(url, params=params, headers=BROWSER_HEADERS, timeout=30)
        response.raise_for_status()
        issues = response.json().get("dailyCongressionalRecord", [])
    except Exception as e:
        st.error(f"[US] ERREUR : {type(e).__name__} — {e}")
        return None, None

    catalog = {}

    for issue in issues:
        date_raw = issue.get("issueDate", "")[:10]

        if not date_raw:
            continue

        vol = str(issue.get("volumeNumber", ""))
        num = str(issue.get("issueNumber", ""))
        parts = date_raw.split("-")
        date_label = f"{parts[2]}/{parts[1]}/{parts[0]}" if len(parts) == 3 else date_raw

        if date_raw not in catalog:
            catalog[date_raw] = {
                "label": f"{date_label} (Vol.{vol} No.{num})",
                "files": [f"{vol}/{num}"]
            }
        else:
            catalog[date_raw]["files"].append(f"{vol}/{num}")

    return b"us_placeholder", dict(sorted(catalog.items(), key=lambda item: item[0], reverse=True))


@st.cache_data(show_spinner=False)
def parse_selected_dates_us(dummy, selected_dates_info):
    api_key = get_secret_key("CONGRESS_API_KEY", "DEMO_KEY")
    data = []

    for sort_key, info in selected_dates_info.items():
        date_label = info["label"].split(" ")[0]

        for file_id in info["files"]:
            vol, num = file_id.split("/")
            detail_url = f"https://api.congress.gov/v3/daily-congressional-record/{vol}/{num}"

            try:
                resp = requests.get(
                    detail_url,
                    params={"api_key": api_key, "format": "json"},
                    headers=BROWSER_HEADERS,
                    timeout=30
                )

                if resp.status_code != 200:
                    continue

                sections = resp.json().get("issue", {}).get("fullIssue", {}).get("sections", [])
            except Exception:
                continue

            for section in sections:
                chamber = section.get("name", "UNKNOWN")

                if chamber not in [
                    "Senate Section",
                    "House Section",
                    "Extensions of Remarks Section"
                ]:
                    continue

                for text_item in section.get("text", []):
                    if text_item.get("type") != "Formatted Text":
                        continue

                    try:
                        time.sleep(0.5)
                        source_url = text_item["url"]
                        htm_resp = requests.get(source_url, headers=BROWSER_HEADERS, timeout=30)

                        if htm_resp.status_code != 200:
                            continue

                        soup = BeautifulSoup(htm_resp.content, "html.parser")
                        full_text = soup.get_text(separator="\n")

                        blocks = re.split(
                            r"\n(?=\s{2,}(?:Mr\.|Ms\.|Mrs\.|The SPEAKER|The PRESIDENT|The CHAIR))",
                            full_text
                        )

                        for block in blocks:
                            block = block.strip()

                            if len(block) < 30:
                                continue

                            speaker_match = re.match(
                                r"((?:Mr\.|Ms\.|Mrs\.|The\s[A-Z][A-Z\s]+)[\s]+[A-Z][A-Za-z\s\.\-\']+?)[\.s]*\n?(.*)",
                                block,
                                re.DOTALL
                            )

                            if speaker_match:
                                nom_orateur = speaker_match.group(1).strip().upper()
                                verbatim = speaker_match.group(2).strip()
                            else:
                                nom_orateur = "CONGRESSIONAL RECORD"
                                verbatim = block

                            if not verbatim or len(verbatim) < 20:
                                continue

                            data.append({
                                "Institution": "CONGRÈS AMÉRICAIN",
                                "DateSortKey": sort_key,
                                "DateLabel": date_label,
                                "Moment": chamber.upper(),
                                "SujetDebat": f"{chamber.upper()} — {sort_key}",
                                "Sequence": f"VOL.{vol} NO.{num}",
                                "NomOrateur": nom_orateur,
                                "Qualite": chamber.replace(" Section", "").upper(),
                                "Verbatim": verbatim,
                                "Reactions": "",
                                "SourceUrl": source_url
                            })

                    except Exception:
                        continue

    return pd.DataFrame(data)


# ==========================================
# ANALYTIQUE / EXPORTS
# ==========================================

def apply_post_filters(df, selected_dates, selected_speakers, selected_qualities, selected_subjects):
    out = df.copy()

    if selected_dates:
        out = out[out["DateLabel"].isin(selected_dates)]

    if selected_speakers:
        out = out[out["NomOrateur"].isin(selected_speakers)]

    if selected_qualities:
        out = out[out["Qualite"].isin(selected_qualities)]

    if selected_subjects:
        out = out[out["SujetDebat"].isin(selected_subjects)]

    return out


def get_top_speakers(df):
    if df.empty:
        return pd.DataFrame(columns=["NomOrateur", "Qualite", "Mentions"])

    return (
        df.groupby(["NomOrateur", "Qualite"])
        .size()
        .reset_index(name="Mentions")
        .sort_values("Mentions", ascending=False)
    )


def get_top_values(df, column, label):
    if df.empty or column not in df.columns:
        return pd.DataFrame(columns=[label, "Mentions"])

    return (
        df.groupby(column)
        .size()
        .reset_index(name="Mentions")
        .rename(columns={column: label})
        .sort_values("Mentions", ascending=False)
    )


def get_key_quotes(df, limit=10):
    if df.empty:
        return df

    return (
        df.sort_values(["SearchScore", "DateSortKey"], ascending=[False, False])
        .head(limit)
        .copy()
    )


def prepare_export_df(df):
    columns = [
        "Institution",
        "DateLabel",
        "DateSortKey",
        "Moment",
        "NomOrateur",
        "Qualite",
        "SujetDebat",
        "Sequence",
        "MotsTrouves",
        "SearchScore",
        "Verbatim",
        "Reactions",
        "SourceUrl"
    ]

    existing = [c for c in columns if c in df.columns]
    return df[existing].copy()


def dataframe_to_xlsx_bytes(df):
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="GIARDINI")

    return output.getvalue()


def generate_html_export(df, theme, institution, query=""):
    bg_color = "#F4F4F0" if theme == "LIGHT" else "#000000"
    text_color = "#1A1A1A" if theme == "LIGHT" else "#FFFFFF"
    border_color = "#D2D2D2" if theme == "LIGHT" else "#333333"

    dates_header = "AUCUNE DATE" if df.empty else ", ".join(df["DateLabel"].dropna().unique())

    if "UE" in institution:
        source_label = "PARLEMENT EUROPÉEN"
    elif "US" in institution:
        source_label = "CONGRÈS AMÉRICAIN"
    else:
        source_label = "ASSEMBLÉE NATIONALE"

    query_label = f" // REQUÊTE: {safe_text(query).upper()}" if query else ""

    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;700&family=Space+Mono&display=swap');

body {{
    font-family: 'Space Grotesk', sans-serif;
    background: {bg_color};
    color: {text_color};
    padding: 40px;
    max-width: 950px;
    margin: 0 auto;
}}

h1 {{
    font-family: 'Space Mono', monospace;
    font-size: 14px;
    color: #D71921;
    text-transform: uppercase;
    letter-spacing: 2px;
    border-bottom: 1px solid {border_color};
    padding-bottom: 20px;
}}

.summary {{
    border: 1px solid {border_color};
    padding: 18px;
    margin: 24px 0;
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    color: #888;
    text-transform: uppercase;
}}

.item {{
    border: 1px solid {border_color};
    padding: 24px;
    margin-bottom: 20px;
}}

.orateur {{
    font-family: 'Space Mono', monospace;
    color: #D71921;
    font-weight: bold;
    margin-bottom: 4px;
    font-size: 14px;
}}

.metadata {{
    font-family: 'Space Mono', monospace;
    color: #888;
    font-size: 10px;
    margin-bottom: 16px;
    text-transform: uppercase;
    border-bottom: 1px dashed {border_color};
    padding-bottom: 12px;
}}

.verbatim {{
    font-size: 16px;
    line-height: 1.6;
    text-align: justify;
}}

mark {{
    background: transparent;
    color: #D71921;
    border-bottom: 2px solid #D71921;
    font-weight: bold;
    padding: 0 2px;
}}

.reactions {{
    font-family: 'Space Mono', monospace;
    color: #888;
    font-size: 10px;
    margin-top: 20px;
}}
</style>
</head>
<body>
<h1>GIARDINI EXPORT // {source_label} // {dates_header}{query_label} // {len(df)} MENTIONS</h1>

<div class="summary">
Source : {source_label}<br>
Dates : {dates_header}<br>
Requête : {safe_text(query)}<br>
Nombre de mentions : {len(df)}
</div>
"""

    for _, row in df.iterrows():
        html_content += f"""
<div class="item">
    <div class="orateur">{safe_text(row.get("NomOrateur", ""))} [{safe_text(row.get("Qualite", ""))}]</div>
    <div class="metadata">
        DATE : {safe_text(row.get("DateLabel", ""))} — SÉANCE : {safe_text(row.get("Moment", ""))}<br>
        SUJET : {safe_text(row.get("SujetDebat", ""))}<br>
        SÉQUENCE : {safe_text(row.get("Sequence", ""))}<br>
        SCORE : {safe_text(row.get("SearchScore", ""))}
    </div>
    <div class="verbatim">{row.get("VerbatimHighlight", safe_text(row.get("Verbatim", "")))}</div>
"""

        if row.get("Reactions", ""):
            html_content += f'<div class="reactions">RX : {safe_text(row.get("Reactions", ""))}</div>'

        if row.get("SourceUrl", ""):
            html_content += f'<div class="reactions">SOURCE : {safe_text(row.get("SourceUrl", ""))}</div>'

        html_content += "</div>"

    html_content += "</body></html>"
    return html_content


# ==========================================
# APPLICATION
# ==========================================

def main():
    if "ui_theme" not in st.session_state:
        st.session_state.ui_theme = "DARK"

    inject_custom_css(st.session_state.ui_theme)

    st.markdown('<div class="hero-title">GIARDINI</div>', unsafe_allow_html=True)
    st.markdown(
        '<span class="hero-subtitle">Veille des débats parlementaires en France, en UE et aux US</span>',
        unsafe_allow_html=True
    )

    # ======================================
    # SIDEBAR — UI
    # ======================================

    st.sidebar.markdown(
        '<div class="tertiary-text red-accent">[ PARAMÈTRES UI ]</div>',
        unsafe_allow_html=True
    )

    theme_choice = st.sidebar.radio(
        "THÈME",
        ["DARK", "LIGHT"],
        index=0 if st.session_state.ui_theme == "DARK" else 1,
        horizontal=True
    )

    if theme_choice != st.session_state.ui_theme:
        st.session_state.ui_theme = theme_choice
        st.rerun()

    # ======================================
    # SIDEBAR — SOURCE
    # ======================================

    st.sidebar.markdown(
        '<br><div class="tertiary-text red-accent">[ SOURCE DES DONNÉES ]</div>',
        unsafe_allow_html=True
    )

    institution = st.sidebar.radio(
        "INSTITUTION",
        [
            "ASSEMBLÉE NATIONALE (FR)",
            "PARLEMENT EUROPÉEN (UE)",
            "CONGRÈS AMÉRICAIN (US)"
        ]
    )

    if "FR" in institution:
        spinner_msg = "SYNCHRONISATION (FR)... [ REPRISE AUTOMATIQUE SI COUPURE RÉSEAU ]"
    elif "UE" in institution:
        spinner_msg = "SYNCHRONISATION (UE)..."
    else:
        spinner_msg = "SYNCHRONISATION (US)..."

    with st.spinner(spinner_msg):
        if "FR" in institution:
            url = "https://data.assemblee-nationale.fr/static/openData/repository/17/vp/syceronbrut/syseron.xml.zip"
            source_bytes, catalog = fetch_and_index_fr(url)
        elif "UE" in institution:
            source_bytes, catalog = fetch_and_index_eu()
        else:
            source_bytes, catalog = fetch_and_index_us()

    if not source_bytes or not catalog:
        st.markdown(
            '<div class="tertiary-text red-accent">ERROR: SOURCE DE DONNÉES INACCESSIBLE.</div>',
            unsafe_allow_html=True
        )
        st.stop()

    # ======================================
    # SIDEBAR — DATES
    # ======================================

    st.sidebar.markdown(
        '<br><div class="tertiary-text red-accent">[ DATES DES SÉANCES ]</div>',
        unsafe_allow_html=True
    )

    selected_date_keys = st.sidebar.multiselect(
        "DATES",
        options=list(catalog.keys()),
        default=[list(catalog.keys())[0]] if catalog else [],
        format_func=lambda x: catalog[x]["label"].upper()
    )

    if not selected_date_keys:
        st.markdown(
            '<div class="tertiary-text red-accent">SYS.HALT: VEUILLEZ SÉLECTIONNER AU MOINS UNE DATE.</div>',
            unsafe_allow_html=True
        )
        st.stop()

    if len(selected_date_keys) > 30:
        st.sidebar.warning("Sélection importante : le parsing peut être lent dans Streamlit.")

    # ======================================
    # SIDEBAR — RECHERCHE
    # ======================================

    st.sidebar.markdown(
        '<br><div class="tertiary-text red-accent">[ MOTEUR DE RECHERCHE ]</div>',
        unsafe_allow_html=True
    )

    saved_queries = load_saved_queries()

    if saved_queries:
        selected_saved_query = st.sidebar.selectbox(
            "REQUÊTE SAUVEGARDÉE",
            ["— AUCUNE —"] + list(saved_queries.keys())
        )
    else:
        selected_saved_query = "— AUCUNE —"

    prefilled_query = ""

    if selected_saved_query != "— AUCUNE —":
        prefilled_query = saved_queries[selected_saved_query].get("query", "")

    search_mode = st.sidebar.radio(
        "MODE",
        ["SIMPLE", "BOOLÉEN AVANCÉ"],
        horizontal=False
    )

    if search_mode == "SIMPLE":
        simple_main = st.sidebar.text_input(
            "SUJET PRINCIPAL",
            placeholder="ex: nucléaire"
        )

        simple_assoc = st.sidebar.text_area(
            "TERMES ASSOCIÉS",
            placeholder="ex: EPR, réacteur, énergie",
            height=80
        )

        simple_exclude = st.sidebar.text_area(
            "TERMES À EXCLURE",
            placeholder="ex: guerre, militaire",
            height=70
        )

        simple_phrase = st.sidebar.text_input(
            "EXPRESSION EXACTE",
            placeholder="ex: transition énergétique"
        )

        bool_query = build_simple_query(
            simple_main,
            simple_assoc,
            simple_exclude,
            simple_phrase
        )

        st.sidebar.markdown(
            f"<div class='bool-help'><b>REQUÊTE GÉNÉRÉE :</b><br>{safe_text(bool_query) if bool_query else '—'}</div>",
            unsafe_allow_html=True
        )

    else:
        bool_query = st.sidebar.text_input(
            "REQUÊTE",
            value=prefilled_query,
            placeholder='EX: MACRON AND (NUCLÉAIRE OR ÉNERGIE) NOT GUERRE'
        )

        st.sidebar.markdown(
            """
            <div class='bool-help'>
            Op&eacute;rateurs support&eacute;s :<br>
            &middot; <b>AND</b> &nbsp;&mdash; les deux termes<br>
            &middot; <b>OR</b> &nbsp;&nbsp;&mdash; l'un ou l'autre<br>
            &middot; <b>NOT</b> ou <b>-</b> &mdash; exclure un terme<br>
            &middot; <b>(  )</b> &nbsp;&mdash; groupement<br>
            &middot; <b>&quot;phrase&quot;</b> &mdash; expression exacte<br>
            &middot; Sans op&eacute;rateur : AND implicite
            </div>
            """,
            unsafe_allow_html=True
        )

    with st.sidebar.expander("SAUVEGARDER LA REQUÊTE", expanded=False):
        save_name = st.text_input("NOM DE LA REQUÊTE", placeholder="ex: Veille nucléaire")

        if st.button("SAUVEGARDER"):
            if save_name.strip() and bool_query.strip():
                saved_queries[save_name.strip()] = {
                    "query": bool_query.strip(),
                    "institution": institution
                }

                ok = save_saved_queries(saved_queries)

                if ok:
                    st.success("Requête sauvegardée.")
                else:
                    st.error("Impossible de sauvegarder la requête.")
            else:
                st.warning("Nom et requête obligatoires.")

    # ======================================
    # PARSING
    # ======================================

    selected_dates_info = {k: catalog[k] for k in selected_date_keys}

    with st.spinner("PARSING DES DONNÉES..."):
        if "FR" in institution:
            df = parse_selected_dates_fr(source_bytes, selected_dates_info)
        elif "UE" in institution:
            df = parse_selected_dates_eu(source_bytes, selected_dates_info)
        else:
            df = parse_selected_dates_us(source_bytes, selected_dates_info)

    st.markdown(
        f'<div class="tertiary-text">SYS.STATUS: {len(selected_date_keys)} DATES EN MÉMOIRE | {len(df)} ENTRÉES PARSÉES.</div><br>',
        unsafe_allow_html=True
    )

    if df.empty:
        st.markdown(
            '<div class="tertiary-text red-accent">NULL: AUCUNE DONNÉE DISPONIBLE POUR CETTE SÉLECTION.</div>',
            unsafe_allow_html=True
        )
        st.stop()

    filtered_df, search_terms, bool_error = boolean_search_and_highlight(df, bool_query)

    if bool_error:
        st.sidebar.markdown(
            f"<div class='bool-error'>&#9888; ERREUR SYNTAXE: {safe_text(bool_error)}</div>",
            unsafe_allow_html=True
        )

    if not bool_query.strip():
        st.markdown(
            '<div class="tertiary-text">WAITING FOR INPUT: VEUILLEZ SAISIR UNE REQUÊTE DANS LE PANNEAU DE CONTRÔLE.</div>',
            unsafe_allow_html=True
        )
        st.stop()

    if bool_error:
        st.markdown(
            f"<div class='tertiary-text red-accent'>ERREUR DE SYNTAXE: {safe_text(bool_error)}</div>",
            unsafe_allow_html=True
        )
        st.stop()

    if filtered_df.empty:
        st.markdown(
            '<div class="tertiary-text red-accent">NULL: AUCUNE CORRESPONDANCE TROUVÉE.</div>',
            unsafe_allow_html=True
        )
        st.stop()

    # ======================================
    # FILTRES
    # ======================================

    section_title("FILTRES POST-RECHERCHE")

    f1, f2, f3, f4 = st.columns(4)

    with f1:
        filter_dates = st.multiselect(
            "DATES",
            sorted(filtered_df["DateLabel"].dropna().unique())
        )

    with f2:
        filter_speakers = st.multiselect(
            "ORATEURS",
            sorted(filtered_df["NomOrateur"].dropna().unique())
        )

    with f3:
        filter_qualities = st.multiselect(
            "QUALITÉS / GROUPES",
            sorted(filtered_df["Qualite"].dropna().unique())
        )

    with f4:
        filter_subjects = st.multiselect(
            "SUJETS",
            sorted(filtered_df["SujetDebat"].dropna().unique())
        )

    view_df = apply_post_filters(
        filtered_df,
        filter_dates,
        filter_speakers,
        filter_qualities,
        filter_subjects
    )

    if view_df.empty:
        st.markdown(
            '<div class="tertiary-text red-accent">NULL: LES FILTRES NE RETOURNENT AUCUN RÉSULTAT.</div>',
            unsafe_allow_html=True
        )
        st.stop()

    # ======================================
    # DASHBOARD
    # ======================================

    section_title("TABLEAU DE BORD")

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        metric_card(len(view_df), "Mentions")

    with m2:
        metric_card(view_df["NomOrateur"].nunique(), "Orateurs distincts")

    with m3:
        metric_card(view_df["DateSortKey"].nunique(), "Dates couvertes")

    with m4:
        metric_card(view_df["SujetDebat"].nunique(), "Sujets distincts")

    left_dash, right_dash = st.columns([2, 1])

    with left_dash:
        section_title("ÉVOLUTION TEMPORELLE")

        chart_data = (
            view_df.groupby("DateSortKey")
            .size()
            .reset_index(name="Mentions")
            .sort_values("DateSortKey")
        )

        chart_data["DateSortKey"] = pd.to_datetime(chart_data["DateSortKey"], errors="coerce")
        chart_data = chart_data.dropna(subset=["DateSortKey"]).set_index("DateSortKey")

        if not chart_data.empty:
            st.line_chart(data=chart_data, y="Mentions", color="#D71921", height=260)
        else:
            st.markdown(
                '<div class="tertiary-text">AUCUNE DONNÉE TEMPORELLE EXPLOITABLE.</div>',
                unsafe_allow_html=True
            )

    with right_dash:
        section_title("TOP ORATEURS")
        top_speakers = get_top_speakers(view_df).head(10)
        st.dataframe(top_speakers, hide_index=True, use_container_width=True)

    # ======================================
    # TABS
    # ======================================

    tab_results, tab_key_quotes, tab_speakers, tab_subjects, tab_exports = st.tabs([
        "RÉSULTATS",
        "CITATIONS CLÉS",
        "FICHE ORATEUR",
        "TOP SUJETS / GROUPES",
        "EXPORTS"
    ])

    # ======================================
    # RÉSULTATS
    # ======================================

    with tab_results:
        section_title("RÉSULTATS DÉTAILLÉS")

        st.markdown(
            '<div class="tertiary-text">COCHEZ LES EXTRAITS À INCLURE DANS UN EXPORT SÉLECTIF.</div><br>',
            unsafe_allow_html=True
        )

        sort_mode = st.radio(
            "TRI",
            ["PERTINENCE", "DATE DESCENDANTE", "ORATEUR"],
            horizontal=True
        )

        display_df = view_df.copy()

        if sort_mode == "PERTINENCE":
            display_df = display_df.sort_values(["SearchScore", "DateSortKey"], ascending=[False, False])
        elif sort_mode == "DATE DESCENDANTE":
            display_df = display_df.sort_values("DateSortKey", ascending=False)
        else:
            display_df = display_df.sort_values("NomOrateur", ascending=True)

        for idx, row in display_df.iterrows():
            expander_title = (
                f"{row['DateLabel']} | {row['NomOrateur']} ({row['Qualite']}) "
                f"| SCORE {row.get('SearchScore', 0)} | {str(row['Sequence'])[:45]}..."
            )

            with st.expander(expander_title, expanded=False):
                chk_key = f"chk_{row['DateSortKey']}_{idx}"
                st.checkbox("INCLURE DANS L'EXPORT", key=chk_key)

                st.markdown("---")

                st.markdown(
                    f"""
                    <div class='tertiary-text' style='line-height: 1.8;'>
                    DATE &nbsp;&nbsp;&nbsp;&nbsp;: {safe_text(row['DateLabel'])} — SÉANCE : {safe_text(row['Moment'])}<br>
                    ORATEUR &nbsp;: <span class='red-accent'>{safe_text(row['NomOrateur'])}</span><br>
                    RÔLE &nbsp;&nbsp;&nbsp;&nbsp;: {safe_text(row['Qualite'])}<br>
                    SUJET &nbsp;&nbsp;&nbsp;: {safe_text(row['SujetDebat'])}<br>
                    SÉQUENCE: {safe_text(row['Sequence'])}<br>
                    DÉTECTION: <span class='red-accent'>{safe_text(str(row['MotsTrouves']).upper())}</span><br>
                    SCORE &nbsp;&nbsp;&nbsp;: {safe_text(row.get('SearchScore', 0))}
                    </div><br>
                    """,
                    unsafe_allow_html=True
                )

                st.markdown(
                    f"<div style='line-height: 1.6; text-align: justify;'>{row['VerbatimHighlight']}</div>",
                    unsafe_allow_html=True
                )

                if row.get("Reactions", ""):
                    st.markdown(
                        f"<br><div class='tertiary-text'>RX: {safe_text(row['Reactions'])}</div>",
                        unsafe_allow_html=True
                    )

                if row.get("SourceUrl", ""):
                    st.markdown(
                        f"<br><div class='tertiary-text'>SOURCE: {safe_text(row['SourceUrl'])}</div>",
                        unsafe_allow_html=True
                    )

    # ======================================
    # CITATIONS CLÉS
    # ======================================

    with tab_key_quotes:
        section_title("CITATIONS CLÉS")

        st.markdown(
            """
            <div class="tertiary-text">
            Les citations clés sont classées selon un score simple : nombre d'occurrences détectées,
            présence des termes dans le sujet, longueur exploitable du verbatim.
            </div><br>
            """,
            unsafe_allow_html=True
        )

        key_quotes = get_key_quotes(view_df, limit=15)

        for _, row in key_quotes.iterrows():
            st.markdown(
                f"""
                <div class="speaker-card">
                    <div class="speaker-name">{safe_text(row['NomOrateur'])} [{safe_text(row['Qualite'])}]</div>
                    <div class="tertiary-text">
                    {safe_text(row['DateLabel'])} — {safe_text(row['SujetDebat'])} — SCORE {safe_text(row.get('SearchScore', 0))}
                    </div>
                    <br>
                    <div style="line-height:1.6; text-align:justify;">
                    {row['VerbatimHighlight']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # ======================================
    # FICHE ORATEUR
    # ======================================

    with tab_speakers:
        section_title("FICHE ORATEUR")

        speakers = sorted(view_df["NomOrateur"].dropna().unique())
        selected_speaker = st.selectbox("SÉLECTIONNER UN ORATEUR", speakers)

        speaker_df = view_df[view_df["NomOrateur"] == selected_speaker].copy()

        if not speaker_df.empty:
            s1, s2, s3, s4 = st.columns(4)

            with s1:
                metric_card(len(speaker_df), "Mentions")

            with s2:
                metric_card(speaker_df["DateSortKey"].nunique(), "Dates")

            with s3:
                metric_card(speaker_df["SujetDebat"].nunique(), "Sujets")

            with s4:
                metric_card(speaker_df["Qualite"].iloc[0], "Qualité dominante")

            st.markdown(
                f"""
                <div class="speaker-card">
                    <div class="speaker-name">{safe_text(selected_speaker)}</div>
                    <div class="tertiary-text">
                    QUALITÉ / GROUPE : {safe_text(speaker_df['Qualite'].iloc[0])}<br>
                    DATES : {safe_text(', '.join(speaker_df['DateLabel'].dropna().unique()))}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            col_a, col_b = st.columns(2)

            with col_a:
                section_title("SUJETS ABORDÉS")
                speaker_subjects = get_top_values(speaker_df, "SujetDebat", "Sujet").head(10)
                st.dataframe(speaker_subjects, hide_index=True, use_container_width=True)

            with col_b:
                section_title("MOTS TROUVÉS")
                words = []

                for value in speaker_df["MotsTrouves"].dropna():
                    for w in str(value).split(","):
                        w = w.strip()
                        if w:
                            words.append(w)

                if words:
                    word_df = pd.Series(words).value_counts().reset_index()
                    word_df.columns = ["Mot", "Occurrences"]
                    st.dataframe(word_df, hide_index=True, use_container_width=True)
                else:
                    st.markdown(
                        '<div class="tertiary-text">AUCUN MOT TROUVÉ AGRÉGÉ.</div>',
                        unsafe_allow_html=True
                    )

            section_title("VERBATIMS DE L'ORATEUR")

            for _, row in speaker_df.sort_values("DateSortKey", ascending=False).iterrows():
                with st.expander(f"{row['DateLabel']} | {str(row['SujetDebat'])[:80]}"):
                    st.markdown(
                        f"<div style='line-height:1.6; text-align:justify;'>{row['VerbatimHighlight']}</div>",
                        unsafe_allow_html=True
                    )

    # ======================================
    # TOP SUJETS / GROUPES
    # ======================================

    with tab_subjects:
        c1, c2 = st.columns(2)

        with c1:
            section_title("TOP SUJETS")
            top_subjects = get_top_values(view_df, "SujetDebat", "Sujet").head(20)
            st.dataframe(top_subjects, hide_index=True, use_container_width=True)

        with c2:
            section_title("TOP QUALITÉS / GROUPES")
            top_qualities = get_top_values(view_df, "Qualite", "Qualité / Groupe").head(20)
            st.dataframe(top_qualities, hide_index=True, use_container_width=True)

        section_title("TOP ORATEURS COMPLET")
        st.dataframe(
            get_top_speakers(view_df).head(50),
            hide_index=True,
            use_container_width=True
        )

    # ======================================
    # EXPORTS
    # ======================================

    with tab_exports:
        section_title("EXPORTS")

        export_scope = st.radio(
            "PÉRIMÈTRE D'EXPORT",
            ["RÉSULTATS FILTRÉS", "CITATIONS CLÉS", "SÉLECTION MANUELLE"],
            horizontal=True
        )

        if export_scope == "RÉSULTATS FILTRÉS":
            export_df = view_df.copy()

        elif export_scope == "CITATIONS CLÉS":
            export_df = get_key_quotes(view_df, limit=15)

        else:
            selected_indices = [
                idx for idx in view_df.index
                if st.session_state.get(f"chk_{view_df.loc[idx, 'DateSortKey']}_{idx}", False)
            ]

            if selected_indices:
                export_df = view_df.loc[selected_indices].copy()
            else:
                export_df = view_df.iloc[0:0].copy()

        st.markdown(
            f'<div class="tertiary-text">PÉRIMÈTRE ACTUEL : {len(export_df)} LIGNES.</div><br>',
            unsafe_allow_html=True
        )

        if export_df.empty:
            st.warning("Aucune donnée à exporter dans ce périmètre.")

        else:
            clean_export_df = prepare_export_df(export_df)

            suffix = "US" if "US" in institution else ("UE" if "UE" in institution else "FR")
            base_filename = f"giardini_export_{suffix}_{len(selected_date_keys)}DATES"

            html_export = generate_html_export(
                export_df,
                st.session_state.ui_theme,
                institution,
                bool_query
            )

            csv_bytes = clean_export_df.to_csv(index=False).encode("utf-8-sig")
            xlsx_bytes = dataframe_to_xlsx_bytes(clean_export_df)

            e1, e2, e3 = st.columns(3)

            with e1:
                st.download_button(
                    "EXPORT HTML",
                    data=html_export,
                    file_name=f"{base_filename}.html",
                    mime="text/html"
                )

            with e2:
                st.download_button(
                    "EXPORT CSV",
                    data=csv_bytes,
                    file_name=f"{base_filename}.csv",
                    mime="text/csv"
                )

            with e3:
                st.download_button(
                    "EXPORT XLSX",
                    data=xlsx_bytes,
                    file_name=f"{base_filename}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            section_title("APERÇU EXPORT")
            st.dataframe(clean_export_df.head(100), hide_index=True, use_container_width=True)


if __name__ == "__main__":
    main()