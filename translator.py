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
        try:
            with open(os.path.join(os.path.dirname(__file__), "locales", "en.json"), 'r', encoding='utf-8') as f:
                translations = json.load(f)
                _translations_cache[lang_code] = translations
                return translations
        except:
            # Return empty dict if even English fails
            return {}

def get_text(key, lang_code=None, **kwargs):
    """Get translated text for a given key.
    
    Args:
        key: Dot-notation key (e.g., "login.title")
        lang_code: Language code (en, fr, pt, sw). Defaults to session state.
        **kwargs: Format arguments for the text
    
    Returns:
        Translated text or the key itself if not found
    """
    if lang_code is None:
        lang_code = st.session_state.get("language", "en")
    
    translations = load_translations(lang_code)
    
    # Navigate nested keys
    parts = key.split('.')
    value = translations
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part, None)
            if value is None:
                # Key not found, return the original key
                return key
        else:
            return key
    
    # If we got a dict instead of a string, return the key
    if isinstance(value, dict):
        return key
    
    # Apply formatting if kwargs provided
    if kwargs and isinstance(value, str):
        try:
            return value.format(**kwargs)
        except:
            return value
    
    return value if isinstance(value, str) else key

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

def get_theme():
    """Get current theme from session state"""
    if "theme" not in st.session_state:
        st.session_state.theme = "light"
    return st.session_state.theme

def set_theme(theme):
    """Set theme in session state"""
    st.session_state.theme = theme

def theme_selector():
    """Display theme selector in sidebar"""
    current_theme = get_theme()
    
    st.markdown("### 🎨 Theme")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("☀️ Light", key="theme_light", use_container_width=True):
            set_theme("light")
            st.rerun()
    with col2:
        if st.button("🌙 Dark", key="theme_dark", use_container_width=True):
            set_theme("dark")
            st.rerun()
    
    st.caption(f"Current: {'☀️ Light' if current_theme == 'light' else '🌙 Dark'} Mode")