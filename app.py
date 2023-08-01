import streamlit as st
from docx import Document
from PyPDF2 import PdfReader
import openai
import io

def get_translation_from_model(text, persona):
    completion = openai.ChatCompletion.create(
        model="gpt-4", 
        messages=[
            {"role": "system", "content": persona},
            {"role": "user", "content": text}
        ],
        temperature=0
    )
    response = completion['choices'][0]['message']['content']

    return response

def extract_text_from_file(file):
    """
    Extracts text from the uploaded file. The file can be a .txt, .docx, or .pdf file.
    """
    if file.type == 'text/plain':
        text = file.getvalue().decode()
    elif file.type == 'application/pdf':
        reader = PdfReader(file)
        text = '\n'.join(page.extract_text() for page in reader.pages)
    elif file.type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        doc = Document(file)
        text = ' '.join(paragraph.text for paragraph in doc.paragraphs)
    else:
        raise ValueError('Unsupported file type')
    return text

@st.cache_data
def translate_text(text, output_language):
    import re
    if output_language == 'English':
        return text
    original_text = text

    words = re.findall(r'\b\w+\b', text)
    words = words[:1500]
    text = ' '.join(words)
    
    # Ensure that text length does not exceed 12000
    if len(text) > 12000:
        text = text[:12000]

    if len(text) < len(original_text):
        st.write("Truncated text for demo...")
        
    input_language = "English"
    return get_translation_from_model(text, f"You are a helpful assistant that translates {input_language} to {output_language}.")

def append_to_filename(filename, string):
    import os
    base, ext = os.path.splitext(filename)
    return f"{base}_{string}.txt"

def show_terms():
    st.write("To continue, please agree to our [Terms of Service](https://www.fossick.ai/terms).")
    if st.button("I agree."):
        st.session_state.agreed_to_terms = True
        st.experimental_rerun()

def show_translator():
    file = st.file_uploader('Upload a document (.txt, .docx)', type=['txt', 'docx'])

    languages = ['Afrikaans', 'Arabic', 'Armenian', 'Azerbaijani', 'Belarusian', 'Bosnian', 'Bulgarian', 'Catalan', 'Chinese', 'Croatian', 'Czech', 'Danish', 'Dutch', 'English', 'Estonian', 'Finnish', 'French', 'Galician', 'German', 'Greek', 'Hebrew', 'Hindi', 'Hungarian', 'Icelandic', 'Indonesian', 'Italian', 'Japanese', 'Kannada', 'Kazakh', 'Korean', 'Latvian', 'Lithuanian', 'Macedonian', 'Malay', 'Marathi', 'Maori', 'Nepali', 'Norwegian', 'Persian', 'Polish', 'Portuguese', 'Romanian', 'Russian', 'Serbian', 'Slovak', 'Slovenian', 'Spanish', 'Swahili', 'Swedish', 'Tagalog', 'Tamil', 'Thai', 'Turkish', 'Ukrainian', 'Urdu', 'Vietnamese', 'Welsh']
    target_language = st.selectbox('Select target language', languages)

    if st.button("Quick Machine Translation") and file is not None:
        original_text = extract_text_from_file(file)
        
        st.write('translating text')
        translated_text = translate_text(original_text, target_language)
        st.download_button('Download translated document', io.BytesIO(translated_text.encode()), append_to_filename(file.name, target_language + '0'))

def main():
    """
    The main function of the Streamlit application. It displays the interface and handles the file upload, translation, and file download processes.
    """
    st.set_page_config(page_title='Document Translator', initial_sidebar_state="collapsed")
    st.title('Document Translator')

    if 'agreed_to_terms' not in st.session_state:
        st.session_state.agreed_to_terms = False

    if not st.session_state.agreed_to_terms:
        show_terms()    

    else:
        show_translator()

if __name__ == '__main__':
    main()
