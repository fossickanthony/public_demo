import streamlit as st
from docx import Document
from PyPDF2 import PdfReader
import openai
import io
import stripe

top_9_languages = ['Arabic', 'Chinese', 'English', 'French', 'German', 'Italian', 'Japanese','Portuguese', 'Russian', 'Spanish',]
top_25_languages = top_9_languages + ['Bengali', 'Hindi', 'Korean', 'Vietnamese', 'Turkish', 'Polish', 'Thai', 'Dutch', 'Indonesian', 'Hungarian', 'Czech', 'Greek', 'Bulgarian', 'Swedish', 'Norwegian', 'Finnish']
all_languages = ['Afrikaans', 'Arabic', 'Armenian', 'Azerbaijani', 'Belarusian', 'Bosnian', 'Bulgarian', 'Catalan', 'Chinese', 'Croatian', 'Czech', 'Danish', 'Dutch', 'English', 'Estonian', 'Finnish', 'French', 'Galician', 'German', 'Greek', 'Hebrew', 'Hindi', 'Hungarian', 'Icelandic', 'Indonesian', 'Italian', 'Japanese', 'Kannada', 'Kazakh', 'Korean', 'Latvian', 'Lithuanian', 'Macedonian', 'Malay', 'Marathi', 'Maori', 'Nepali', 'Norwegian', 'Persian', 'Polish', 'Portuguese', 'Romanian', 'Russian', 'Serbian', 'Slovak', 'Slovenian', 'Spanish', 'Swahili', 'Swedish', 'Tagalog', 'Tamil', 'Thai', 'Turkish', 'Ukrainian', 'Urdu', 'Vietnamese', 'Welsh',]

def get_translation_from_model(text, persona, local_dev):
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613" if local_dev else "gpt-4", 
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

def translate_text(text, output_language, local_dev):
    import re
    words = re.findall(r'\b\w+\b', text)
    st.session_state.word_count = len(words)

    truncated = False
    if len(text) > 1000:
        text = text[:1000]
        truncated = True
    words = re.findall(r'\b\w+\b', text)
    if len(words) > 100:
        words = words[:100]
        text = ' '.join(words)
        truncated = True

    if truncated:
        print("Truncated text for demo...")
    if output_language == 'English':
        return text
        
    # print(f"About to translate: {text}")

    input_language = "English"
    translated = get_translation_from_model(text, f"You are a helpful assistant that translates {input_language} to {output_language}.", local_dev)
    # print(f"got result: {translated}")
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
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
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

def validate_email(email):
    import re
    # Define a regular expression pattern for a valid email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    # Match the pattern against the email
    return email and re.match(pattern, email) is not None

def show_translator(local_dev=False):
    st.header('STEP 1: upload a document.')
    file = st.file_uploader('Upload a document (.txt, .docx)', type=['txt', 'docx'])

    st.header('STEP 2: Select a language to translate to.')
    if st.checkbox('extended languages'):
        languages = all_languages
        target_language = st.selectbox('Select target language', languages)
    else:
        languages = top_9_languages
        target_language = st.selectbox('Select target language', languages, index=3 if local_dev else 0)

    business_email = st.text_input('Business email address')
    agreed_to_terms = st.checkbox("To continue, please agree to our [Terms of Service](https://www.fossick.ai/terms).")
    button_pressed = st.button("Quick Machine Translation")
    if agreed_to_terms and button_pressed and file:
        if not validate_email(business_email):
            st.error('Please provide a valid email address.')
        else:
            with st.spinner('Translating text...'):
                original_text = extract_text_from_file(file)
                st.session_state.file_name = file.name
                st.session_state.email = business_email
                st.session_state.target_language = target_language
                st.session_state.original_text = original_text
                st.session_state.translated_text = translate_text(original_text, target_language, local_dev)
                st.experimental_rerun()
    elif button_pressed:
        st.error("Please agree to the terms before proceeding.")

def create_checkout_session(price, quantity):
    try:
        YOUR_DOMAIN = 'https://fossick.streamlit.app/'
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                    'price': price,
                    'quantity': quantity,
                },
            ],
            mode='payment',
            success_url=YOUR_DOMAIN + '?success=true',
            cancel_url=YOUR_DOMAIN + '?cancel=true',
            automatic_tax={'enabled': True},
        )
        return checkout_session.url
    except Exception as e:
        return str(e)

def send_email(target_email, subject, body, attachments):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.application import MIMEApplication
    import os
    from_email = 'fossickorders@gmail.com'
    password = os.environ.get("FOSSICK_EMAIL_PASS")

    # Create a multipart message
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = target_email
    msg['Subject'] = subject

    # Attach the body text
    msg.attach(MIMEText(body, 'plain'))

    # Attach the files
    for attachment_path in attachments:
        with open(attachment_path, 'rb') as file:
            file_name = os.path.basename(attachment_path)
            attachment = MIMEApplication(file.read(), Name=file_name)
            msg.attach(attachment)

    # Connect and send the email
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(from_email, password)
        server.send_message(msg)

def show_translation():
    # st.markdown('# Quick sample translation')
    # st.markdown(st.session_state.translated_text)
    st.download_button('Download quick translated sample', io.BytesIO(st.session_state.translated_text.encode()), append_to_filename(st.session_state.file_name, st.session_state.target_language))
    word_count = st.session_state.word_count
    mul_url = create_checkout_session('price_1NpSAkFXbHqY0SmV1NPuYGjA', word_count)
    hum_url = create_checkout_session('price_1NpSBMFXbHqY0SmVaVMYdIqG', word_count)
    leg_url = create_checkout_session('price_1NpSBlFXbHqY0SmVhIZjAEcT', word_count)
    st.markdown(f'''# Professional Translation
Please choose your translation level:''')
    st.markdown(f'''| Level    | [Full translation multipass]({mul_url}) | [Full translation with Human review]({hum_url}) | [Legal translation review]({leg_url})* |
| -------- | ------- | ------- | ------- |
| Word count  | {word_count} words    | {word_count} words    | {word_count} words    | 
| Price per word | x \\$0.08/word     | x \\$0.15/word     | x \\$0.50/word     |
| Total    | [\\${round(word_count*0.08, 2):0.2f}]({mul_url})    | [\\${round(word_count*0.15, 2):0.2f}]({hum_url})    | [\\${round(word_count*0.50, 2):0.2f}]({leg_url})*    |''')

    time_to_review = 3 if st.session_state.target_language in top_9_languages else 5
    st.markdown(f'Current human review for a {word_count} word document in {st.session_state.target_language} is {time_to_review} business days.')
    st.markdown(f'*Legal translation review: have your translated document read through by a lawyer fluent in your target language to improve linguistic consistency. Linguistic review only. Legal advice is never provided by or through Fossick. Legal review will take up to an additional 5 business days. For details, please refer to: [Terms of Service - Non-practice](https://www.fossick.ai/terms/#non-practice-href)')
    send_email('anthony@fossick.ai', f'Fossick Order for {st.session_state.word_count}', f'Email:{st.session_state.email}\nFilename:{st.session_state.file_name}\nTarget language:{st.session_state.target_language}\nOriginal text:{st.session_state.original_text}', [])

def show_translation_old():
    '''* [Full translation single pass]({sin_url}):       {word_count} words x \\$0.05/word = \\${round(word_count*0.05, 2):0.2f}
    * [Full translation multipass]({mul_url}):         {word_count} words x \\$0.08/word = \\${round(word_count*0.08, 2):0.2f}
    * [Full translation with Human review]({hum_url}): {word_count} words x \\$0.15/word = \\${round(word_count*0.15, 2):0.2f}
    * [Legal translation review]({leg_url}):*          {word_count} words x \\$0.50/word = \\${round(word_count*0.50, 2):0.2f}
    '''
    st.download_button('Download quick translated sample', io.BytesIO(st.session_state.translated_text.encode()), append_to_filename(st.session_state.file_name, st.session_state.target_language))
    st.markdown('''# Professional Translation
For a professional translation, please give us your email address and choose the services you would like to receive.
''')
    email = st.text_input('Email address:')
    word_count = st.session_state.word_count
    translation_level = st.radio('What translation level do you need?',
        (f'Full translation single pass:       {word_count} words x \\$0.05/word = \\${round(word_count*0.05, 2):0.2f}',
         f'Full translation multipass:         {word_count} words x \\$0.08/word = \\${round(word_count*0.08, 2):0.2f}',
         f'Full translation with Human review: {word_count} words x \\$0.15/word = \\${round(word_count*0.15, 2):0.2f}',
         f'Legal translation review:*          {word_count} words x \\$0.50/word = \\${round(word_count*0.50, 2):0.2f}'))
    time_to_review = 3 if st.session_state.target_language in top_9_languages else 5
    st.markdown(f'Current human review for a {word_count} word document in {st.session_state.target_language} is {time_to_review} business days.')
    st.markdown(f'*Legal translation review: have your translated document read through by a lawyer fluent in your target language to improve linguistic consistency. Linguistic review only. Legal advice is never provided by or through Fossick. Legal review will take up to an additional 5 business days. For details, please refer to: [Terms of Service - Non-practice](https://www.fossick.ai/terms/#non-practice-href)')
    checkout_url = create_checkout_session('price_1NpSBlFXbHqY0SmVhIZjAEcT', word_count)
    print(checkout_url)
    st.markdown(f'[Checkout]({checkout_url})')
    if st.button('Request Full Translation'):
        if not validate_email(email):
            st.error('Please provide a valid email address.')
        else:
            send_email('translate@fossick.ai', f'Fossick Order for {email}', f'Email:{email}\nLevel:{translation_level}\nFilename:{st.session_state.file_name}\nTarget language:{st.session_state.target_language}\nOriginal text:{st.session_state.original_text}', [])
            st.balloons()

def show_success_page():
    st.header("We're on it!")
    st.balloons()

def main():
    """
    The main function of the Streamlit application. It displays the interface and handles the file upload, translation, and file download processes.
    """
    st.set_page_config(page_title='Document Translator', initial_sidebar_state="collapsed")
    st.title('Document Translator')

    import os
    dev_env = False # os.getenv("LOCAL_FOSSICK_DEV", "False") == "True"
    # print(dev_env)
    stripe.api_key = os.getenv("STRIPE_API_KEY", 'sk_test_51Na0TDFXbHqY0SmVllzcYxHIHAhiBGhe7dhFadNZQF7LBjLKBNOHNP1EVDWzwdoEhvMGGQvKJnCaHTS0e91eBH6I00dJKlHS33')
    

    # query string param for language
    params = st.experimental_get_query_params()
    if 'lang' in params:
        # do something with language
        pass
    if 'success' in params:
        show_success_page()

    st.session_state.translated_text = st.session_state.get('translated_text', None)

    if not st.session_state.translated_text:
        show_translator(dev_env)
    else:
        show_translation()

if __name__ == '__main__':
    main()
