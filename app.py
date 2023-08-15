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

def translate_text(text, output_language):
    import re
    words = re.findall(r'\b\w+\b', text)
    st.session_state.word_count = len(words)
    if output_language == 'English':
        return text

    truncated = False
    if len(text) > 10000:
        text = text[:10000]
        truncated = True
    words = re.findall(r'\b\w+\b', text)
    if len(words) > 1000:
        words = words[:1000]
        text = ' '.join(words)
        truncated = True

    if truncated:
        st.write("Truncated text for demo...")
        
    print(f"About to translate: {text}")

    input_language = "English"
    translated = get_translation_from_model(text, f"You are a helpful assistant that translates {input_language} to {output_language}.")
    print(f"got result: {translated}")
    return translated

def append_to_filename(filename, string):
    import os
    base, ext = os.path.splitext(filename)
    return f"{base}_{string}.txt"

def show_terms():
    st.write("To continue, please agree to our [Terms of Service](https://www.fossick.ai/terms).")
    if st.button("I agree."):
        st.session_state.agreed_to_terms = True
        st.experimental_rerun()

def clean_strings(strings):
    # Using a generator expression to strip leading whitespace and filter out empty lines
    return [line.lstrip() for line in strings if line.strip()]

def download_html(url):
    import requests
    from bs4 import BeautifulSoup
    response = requests.get(url)
    response.raise_for_status() # Raise an exception if the request was unsuccessful

    soup = BeautifulSoup(response.text, 'html.parser')

    # Returning the entire text content without HTML markup
    return soup.get_text()

def get_txt_filename(url):
    from urllib.parse import urlparse
    import os

    # Parse the URL
    parsed_url = urlparse(url)
    
    # Extract the path and split it to get the file name
    path = os.path.basename(parsed_url.path)
    
    # Check if the path has an extension
    if '.' in path:
        # Replace the extension with .txt
        return os.path.splitext(path)[0] + ".txt"
    else:
        # Return index.txt if there is no extension
        return "index.txt"

def show_translator():
    st.header('STEP 1: upload a document or submit a URL.')
    col1, col2= st.columns(2)
    with col1:
        st.subheader('Upload a document')
        file = st.file_uploader('Upload a document (.txt, .docx)', type=['txt', 'docx'])
    with col2:
        st.subheader('Link to a document')
        doc_url = st.text_input('URL of .txt or .docx')

    st.header('STEP 2: Select a language to translate to.')
    if st.checkbox('extended languages'):
        languages = ['Afrikaans', 'Arabic', 'Armenian', 'Azerbaijani', 'Belarusian', 'Bosnian', 'Bulgarian', 'Catalan', 'Chinese', 'Croatian', 'Czech', 'Danish', 'Dutch', 'English', 'Estonian', 'Finnish', 'French', 'Galician', 'German', 'Greek', 'Hebrew', 'Hindi', 'Hungarian', 'Icelandic', 'Indonesian', 'Italian', 'Japanese', 'Kannada', 'Kazakh', 'Korean', 'Latvian', 'Lithuanian', 'Macedonian', 'Malay', 'Marathi', 'Maori', 'Nepali', 'Norwegian', 'Persian', 'Polish', 'Portuguese', 'Romanian', 'Russian', 'Serbian', 'Slovak', 'Slovenian', 'Spanish', 'Swahili', 'Swedish', 'Tagalog', 'Tamil', 'Thai', 'Turkish', 'Ukrainian', 'Urdu', 'Vietnamese', 'Welsh']
        target_language = st.selectbox('Select target language', languages)
    else:
        languages = ['Arabic', 'Chinese', 'English', 'French', 'German', 'Italian', 'Japanese','Portuguese', 'Russian', 'Spanish',]
        target_language = st.selectbox('Select target language', languages)

    if st.button("Quick Machine Translation") and (file or doc_url):
        if file:
            original_text = extract_text_from_file(file)
            st.session_state.file_name = file.name
        else:
            original_text = download_html(doc_url)
            # print(dir(original_text))
            # print(type(original_text))
            original_text = clean_strings(original_text.splitlines())
            original_text = '\n'.join(original_text)
            st.session_state.file_name = get_txt_filename(doc_url)
        
        st.write('translating text')
        st.session_state.target_language = target_language
        st.session_state.original_text = original_text
        st.session_state.translated_text = translate_text(original_text, target_language)
        st.experimental_rerun()

def send_email(from_email, to_email, subject, body, file_contents, file_name):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.application import MIMEApplication
    # Create a multipart message
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Attach the body text
    msg.attach(MIMEText(body, 'plain'))

    # Attach the file
    attachment = MIMEApplication(file_contents, Name=file_name)
    msg.attach(attachment)

    # Connect and send the email
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        # Login Credentials for sending the email
        # Use an application-specific password or OAuth2 for better security
        server.login(from_email, 'your-application-specific-password')
        server.send_message(msg)

    print(f"Email sent to {to_email}")

def create_mailto_url(to, subject, body):
    import urllib.parse
    # Create a dictionary of the mailto parameters
    mailto_params = {'subject': subject, 'body': body}
    # URL encode the parameters
    mailto_params_encoded = urllib.parse.urlencode(mailto_params)
    # Create the full mailto URL
    mailto_url = f'mailto:{to}?{mailto_params_encoded}'
    return mailto_url

def show_translation():
    st.download_button('Download quick translated sample', io.BytesIO(st.session_state.translated_text.encode()), append_to_filename(st.session_state.file_name, st.session_state.target_language))
    st.markdown('''# Professional Translation
For a professional translation, please give us your email address and choose the services you would like to receive.
''')
    email = st.text_input('Email address:')
    word_count = st.session_state.word_count
    translation_level = st.radio('What translation level do you need?',
        (f'Full translation single pass:       {word_count} words x $0.05/word = ${word_count*0.05}',
         f'Full translation multipass:         {word_count} words x $0.08/word = ${word_count*0.08}',
         f'Full translation with Human review: {word_count} words x $0.15/word = ${word_count*0.15}'))
    st.markdown(f'''Current human review for a {word_count} word document in {st.session_state.target_language} is 5 business days.''')
    # if st.button('Order translation'):
    # send email to Ben
    to = "anthony@fossick.ai"
    subject = "Request Fossick Quote"
    body = f"Hi Fossick,\n\nI have a {word_count} word document named {st.session_state.file_name} that I want to translate into {st.session_state.target_language} using {translation_level}."
    mailto_url = create_mailto_url(to, subject, body)
    st.markdown(f'<a href="{mailto_url}" target="_blank">Click here to request quote</a>', unsafe_allow_html=True)

def main():
    """
    The main function of the Streamlit application. It displays the interface and handles the file upload, translation, and file download processes.
    """
    st.set_page_config(page_title='Document Translator', initial_sidebar_state="collapsed")
    st.title('Document Translator')

    st.session_state.agreed_to_terms = st.session_state.get('agreed_to_terms', False)
    st.session_state.translated_text = st.session_state.get('translated_text', None)

    if not st.session_state.agreed_to_terms:
        show_terms()    
    elif not st.session_state.translated_text:
        show_translator()
    else:
        show_translation()

if __name__ == '__main__':
    main()
