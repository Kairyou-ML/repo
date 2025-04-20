import streamlit as st
import random
import math
from collections import deque
import pandas as pd
import datetime

def load_words_from_csv(file_path=None):
    if file_path:
        try:
            df = pd.read_csv(file_path)
            if 'English' not in df.columns or 'Vietnamese' not in df.columns:
                raise ValueError("CSV must have 'English' and 'Vietnamese' columns")
            word_list = [(row['English'].strip(), row['Vietnamese'].strip()) for _, row in df.iterrows()]
        except Exception as e:
            st.error(f"Error reading CSV: {e}. Using default word list.")
            word_list = []
    else:
        word_pairs_raw = [
            "apple - quả táo",
            "dog - con chó",
            "book - quyển sách",
            "car - xe hơi",
            "water - nước",
            "computer - máy tính",
            "house - ngôi nhà",
            "school - trường học",
            "pen - cây bút",
            "table - cái bàn"
        ]
        word_list = [(en.strip(), vi.strip()) for item in word_pairs_raw for en, vi in [item.split(" - ")]]
    
    word_data = [
        {
            'en': en,
            'vi': vi,
            'interval': 1,
            'ease': 2.5,
            'repetitions': 0,
            'next_review': datetime.datetime.now()
        }
        for en, vi in word_list
    ]
    return word_data

def create_question(word_item, all_meanings):
    correct_meaning = word_item['vi']
    wrong_meanings = random.sample([m for m in all_meanings if m != correct_meaning], 7)
    options = wrong_meanings + [correct_meaning]
    random.shuffle(options)
    return word_item['en'], options, correct_meaning

def update_spaced_repetition(word_item, quality):
    now = datetime.datetime.now()
    if quality >= 3:
        word_item['repetitions'] += 1
        if word_item['repetitions'] == 1:
            word_item['interval'] = 1
        elif word_item['repetitions'] == 2:
            word_item['interval'] = 6
        else:
            word_item['interval'] = math.ceil(word_item['interval'] * word_item['ease'])
        word_item['ease'] = max(1.3, word_item['ease'] + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        word_item['next_review'] = now + datetime.timedelta(days=word_item['interval'])
    else:
        word_item['repetitions'] = 0
        word_item['interval'] = 1
        word_item['ease'] = max(1.3, word_item['ease'] - 0.2)
        word_item['next_review'] = now
    return word_item

# Streamlit app
st.set_page_config(page_title="Enku Vocabulary", page_icon="📚", layout="centered")
st.title("📚 Enku Vocabulary Trainer")
st.markdown("Learn English-Vietnamese vocabulary with spaced repetition!")

# Initialize session state
if 'word_data' not in st.session_state:
    word_data = load_words_from_csv()  # Use None or provide path, e.g., "input.csv"
    random.shuffle(word_data)
    st.session_state.word_data = word_data
    st.session_state.queue = deque(word_data)
    st.session_state.correct_count = 0
    st.session_state.total = len(word_data)
    st.session_state.current_word = None
    st.session_state.options = None
    st.session_state.correct_meaning = None
    st.session_state.answered = False
    st.session_state.example_submitted = False

# File uploader for CSV
uploaded_file = st.file_uploader("Upload a CSV file (with 'English' and 'Vietnamese' columns)", type="csv")
if uploaded_file is not None:
    st.session_state.word_data = load_words_from_csv(uploaded_file)
    random.shuffle(st.session_state.word_data)
    st.session_state.queue = deque(st.session_state.word_data)
    st.session_state.total = len(st.session_state.word_data)
    st.session_state.correct_count = 0
    st.session_state.current_word = None
    st.session_state.answered = False
    st.session_state.example_submitted = False

# Main quiz logic
if st.session_state.queue:
    now = datetime.datetime.now()
    word_item = st.session_state.queue[0]  # Peek at the first item
    if word_item['next_review'] <= now:
        # Pop the word for review
        word_item = st.session_state.queue.popleft()
        st.session_state.current_word, st.session_state.options, st.session_state.correct_meaning = create_question(
            word_item, [item['vi'] for item in st.session_state.word_data]
        )
    else:
        st.session_state.queue.append(st.session_state.queue.popleft())  # Not due, rotate
        st.write("No words due for review yet. Try again later!")
        st.stop()

    # Display question
    st.subheader(f"Từ: {st.session_state.current_word}")
    answer = st.radio("Chọn đáp án:", st.session_state.options, key=f"answer_radio_{st.session_state.current_word}", index=None)
    st.write(f"Đáp án bạn chọn: {answer}")  # Debug line

    if not st.session_state.answered:
        if st.button("Submit"):
            st.session_state.answered = True
            if answer == st.session_state.correct_meaning:
                st.success("✅ Đúng!")
                st.session_state.correct_count += 1
                quality = 5
            else:
                st.error(f"❌ Sai! Đáp án đúng là: {st.session_state.correct_meaning}")
                quality = 0

            # Update spaced repetition
            word_item = update_spaced_repetition(word_item, quality)
            st.session_state.queue.append(word_item)

    # Handle example input for wrong answers
    if st.session_state.answered and answer != st.session_state.correct_meaning and not st.session_state.example_submitted:
        example = st.text_input("Nhập ví dụ sử dụng từ này (bắt buộc):")
        if st.button("Submit Example"):
            if example.strip():
                st.session_state.example_submitted = True
                st.success("Example submitted!")
            else:
                st.warning("⚠️ Vui lòng nhập ví dụ!")
    elif st.session_state.answered:
        if st.button("Tiếp tục"):
            st.session_state.answered = False
            st.session_state.example_submitted = False
            st.session_state.current_word = None  # Force re-render of the question

else:
    st.markdown(f"🎉 Kết thúc luyện tập! Đúng {st.session_state.correct_count}/{st.session_state.total}.")
    if st.button("Bắt đầu lại"):
        st.session_state.word_data = load_words_from_csv()
        random.shuffle(st.session_state.word_data)
        st.session_state.queue = deque(st.session_state.word_data)
        st.session_state.correct_count = 0
        st.session_state.total = len(st.session_state.word_data)
        st.session_state.current_word = None
        st.session_state.answered = False
        st.session_state.example_submitted = False