import streamlit as st
import pickle
from collections import deque
import random
import csv
import os
import io  # To handle uploaded files

# Load wordlist from uploaded or local CSV
def load_wordlist(file_content=None):
    rows = []
    if file_content:
        text_io = io.StringIO(file_content)
        reader = csv.reader(text_io)
        rows = list(reader)
    else:
        with open('data/input.csv', 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)

    return [{'word': row[0], 'meaning': row[1], 'correct_streak': 0, 'hint': '', 'history': []}
            for row in rows if len(row) >= 2]


def initialize_progress(wordlist):
    queue = deque(random.sample(wordlist, len(wordlist)))
    return {'wordlist': wordlist, 'queue': queue}

def save_progress(progress):
    os.makedirs('data', exist_ok=True)
    with open('data/output.pkl', 'wb') as f:
        pickle.dump(progress, f)

def load_progress():
    try:
        with open('data/output.pkl', 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return None

def get_wrong_answers(wordlist, correct_meaning):
    wrong_answers = [w['meaning'] for w in wordlist if w['meaning'] != correct_meaning]
    return random.sample(wrong_answers, min(3, len(wrong_answers)))

def generate_options(current_word, wordlist):
    correct = current_word['meaning']
    wrongs = get_wrong_answers(wordlist, correct)
    options = [correct] + wrongs
    random.shuffle(options)
    return options

# ----------------- STREAMLIT APP -----------------

st.title("📘 Enku Vocabulary Trainer")

uploaded_file = st.file_uploader("Upload a CSV file (with 'English' and 'Vietnamese' columns)", type="csv")
use_uploaded = uploaded_file is not None

# SAFELY read uploaded file content once
if use_uploaded:
    file_content = uploaded_file.getvalue().decode("utf-8")
else:
    file_content = None
    


# Load progress and initialize
if use_uploaded:
    file_content = uploaded_file.getvalue().decode("utf-8")

    # Chỉ khởi tạo lại nếu nội dung file mới
    if st.session_state.get('uploaded_file_content') != file_content:
        st.session_state.uploaded_file_content = file_content
        wordlist = load_wordlist(file_content)
        progress = initialize_progress(wordlist)
        st.session_state.progress = progress
        st.session_state.load_new_question = True

elif 'progress' not in st.session_state:
    wordlist = load_wordlist()
    progress = initialize_progress(wordlist)
    st.session_state.progress = progress
    st.session_state.load_new_question = True


st.session_state.setdefault('show_hint_input', False)
st.session_state.setdefault('temp_hint', "")
st.session_state.setdefault('submitted', False)
st.session_state.setdefault('load_new_question', True)

if st.session_state.load_new_question:
    if st.session_state.progress['queue']:
        st.session_state.current_word = st.session_state.progress['queue'].popleft()
        st.session_state.options = generate_options(st.session_state.current_word, st.session_state.progress['wordlist'])
        st.session_state.submitted = False
        st.session_state.load_new_question = False
    else:
        st.write("🎉 All done! Congratulations on successfully completing the process of learning by heart!!")
        st.stop()

if st.session_state.current_word['hint']:
    st.info(f"💡 Hint: {st.session_state.current_word['hint']}")

st.write(f"What is the meaning of **{st.session_state.current_word['word']}**?")
with st.form(key="quiz_form"):
    selected_option = st.radio("Select the correct meaning:", st.session_state.options)
    submitted_answer = st.form_submit_button("Submit Answer")

if submitted_answer and not st.session_state.submitted:
    correct = st.session_state.current_word['meaning']
    st.session_state.submitted = True

    if selected_option == correct:
        st.success("✅ Correct!")
        st.session_state.current_word['correct_streak'] += 1
        if st.session_state.current_word['correct_streak'] < 2:
            st.session_state.progress['queue'].append(st.session_state.current_word)
    else:
        st.error(f"❌ Incorrect. The correct answer is: **{correct}**")
        st.session_state.current_word['correct_streak'] = 0
        st.session_state.progress['queue'].appendleft(st.session_state.current_word)
        st.session_state.show_hint_input = True
        st.session_state.temp_hint = ""

    save_progress(st.session_state.progress)

if st.session_state.show_hint_input:
    st.text_input("Add a hint for this word:", key="temp_hint")
    if st.button("Save Hint") and st.session_state.temp_hint.strip():
        st.session_state.current_word['hint'] = st.session_state.temp_hint.strip()
        st.session_state.show_hint_input = False
        st.session_state.progress['queue'].append(st.session_state.current_word)
        save_progress(st.session_state.progress)
        st.session_state.load_new_question = True
        st.rerun()

if st.session_state.submitted and not st.session_state.show_hint_input:
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Next"):
            st.session_state.load_new_question = True
            st.rerun()
    with col2:
        if st.button("🔄 Reset Progress"):
            if os.path.exists('data/output.pkl'):
                os.remove('data/output.pkl')
            st.rerun()

# Progress bar
total = len(st.session_state.progress['wordlist'])
learned = sum(1 for w in st.session_state.progress['wordlist'] if w['correct_streak'] >= 2)
st.markdown(f"📚 **Progress: {learned} / {total} words learned**")
