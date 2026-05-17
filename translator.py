import streamlit as st
import json
import os

# Language configuration
LANGUAGES = {
    "en": {"name": "English", "flag": "🇬🇧", "file": "en.json"},
    "fr": {"name": "Français", "flag": "🇫🇷", "file": "fr.json"},
    "pt": {"name": "Português", "flag": "🇵🇹", "file": "pt.json"},
    "sw": {"name": "Kiswahili", "flag": "🇹🇿", "file": "sw.json"}
}

# Load translations
_translations_cache = {}

def load_translations(lang_code):
    """Load translations for a given language"""
    if lang_code in _translations_cache:
        return _translations_cache[lang_code]
    
    file_path = os.path.join(os.path.dirname(__file__), "locales", f"{lang_code}.json")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            translations = json.load(f)
            _translations_cache[lang_code] = translations
            return translations
    except FileNotFoundError:
        # Fallback to English
        with open(os.path.join(os.path.dirname(__file__), "locales", "en.json"), 'r', encoding='utf-8') as f:
            translations = json.load(f)
            _translations_cache[lang_code] = translations
            return translations

def get_text(key, lang_code=None, **kwargs):
    """Get translated text for a given key"""
    if lang_code is None:
        lang_code = st.session_state.get("language", "en")
    
    translations = load_translations(lang_code)
    
    # Navigate nested keys (e.g., "login.title")
    parts = key.split('.')
    value = translations
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part, key)
        else:
            value = key
            break
    
    # Format with kwargs if provided
    if kwargs and isinstance(value, str):
        try:
            return value.format(**kwargs)
        except:
            return value
    
    return value

def language_selector():
    """Display language selector in sidebar"""
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🌐 Language")
        
        cols = st.columns(len(LANGUAGES))
        for idx, (code, lang) in enumerate(LANGUAGES.items()):
            with cols[idx]:
                if st.button(f"{lang['flag']} {lang['name']}", key=f"lang_{code}"):
                    st.session_state.language = code
                    st.rerun()
        
        current_lang = st.session_state.get("language", "en")
        st.caption(f"Current: {LANGUAGES[current_lang]['name']}")