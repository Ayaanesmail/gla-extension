import nltk
from youtube_transcript_api import YouTubeTranscriptApi
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from collections import defaultdict

nltk.download('punkt')
nltk.download('stopwords')

from youtube_transcript_api import YouTubeTranscriptApi
from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch
import re
import time
from collections import Counter
from youtubesearchpython import VideosSearch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

nltk.download('punkt')

import sentencepiece as spm

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

nltk.download('punkt')

tokenizer = T5Tokenizer.from_pretrained("t5-base")
model = T5ForConditionalGeneration.from_pretrained("t5-base").to(device)

def preprocess_subtitles(srt_data):
    subtitles = [item['text'] for item in srt_data]
    start_times = [item['start'] for item in srt_data]
    durations = [item['duration'] for item in srt_data]
    return subtitles, start_times, durations

def capitalize_sentences(summary):
    sentences = nltk.sent_tokenize(summary)
    capitalized_sentences = []
    for sentence in sentences:
        words = sentence.split()
        if words:
            words[0] = words[0].capitalize()
        for j, word in enumerate(words):
            if word.lower() == "i":
                words[j] = "I"
        capitalized_sentences.append(" ".join(words))
    return ' '.join(capitalized_sentences)

def remove_bracketed_text(summary):
    return re.sub(r'\[.*?\]', '', summary)

def convert_to_time_format(timestamp):
    minutes = int(timestamp // 60)
    seconds = int(timestamp % 60)
    milliseconds = int((timestamp % 1) * 1000)
    return f"{minutes:02d}:{seconds:02d}:{milliseconds:03d}"

def extract_keywords(summary, search_query, num_keywords=3):
    words = re.findall(r'\w+', summary)
    word_freq = Counter(words)
    common_words = [word for word, _ in word_freq.most_common() if word.isalpha() and len(word) > 3]

    # Add search query terms to keywords if they are not already included
    search_terms = search_query.split()
    for term in search_terms:
        if term not in common_words:
            common_words.insert(0, term)  # Prioritize search terms

    return common_words[:num_keywords]

def get_youtube_links(keywords):
    links = {}
    for keyword in keywords:
        videos_search = VideosSearch(keyword, limit=1)
        results = videos_search.result()
        if results['result']:
            video_id = results['result'][0]['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}&t=1s"
            links[keyword] = video_url
        else:
            print(f"No video found for keyword: {keyword}")  # Debugging statement
    return links

def add_hyperlinks(summary, links):
    for keyword, url in links.items():
        summary = re.sub(f"\\b{keyword}\\b", f'<a href="{url}">{keyword}</a>', summary, flags=re.IGNORECASE)
    return summary

def generate_summary(subtitles, start_times, durations, summary_size, video_length_minutes, search_query):
    if summary_size == 's':
        max_length = 200
    elif summary_size == 'm':
        max_length = 300
    elif summary_size == 'l':
        max_length = 400
    else:
        print("Invalid summary size. Please choose from: s (small), m (medium), l (large).")
        return

    if video_length_minutes <= 15:
        num_splits = 5
    elif video_length_minutes <= 30:
        num_splits = 10
    elif video_length_minutes <= 60:
        num_splits = 15
    else:
        num_splits = 20

    segment_length = len(subtitles) // num_splits

    html_content = "<html><head><title>Video Summaries</title></head><body>"

    for i in range(num_splits):
        start_index = i * segment_length
        end_index = min(start_index + segment_length, len(subtitles))
        split_subtitles = subtitles[start_index:end_index]
        split_start_times = start_times[start_index:end_index]
        split_durations = durations[start_index:end_index]

        text = ' '.join(split_subtitles)
        inputs = tokenizer.encode(
            "summarize: " + text,
            return_tensors="pt",
            max_length=512,
            truncation=True
        ).to(device)

        summary_ids = model.generate(
            inputs,
            max_length=max_length * 2,
            min_length=int(0.7 * max_length),
            length_penalty=1.0,
            num_beams=6,
            early_stopping=True
        )
        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

        summary = summary[:max_length] + (
            summary[max_length:].split('.')[:-1][0] if '.' in summary[max_length:] else ''
        )

        summary = capitalize_sentences(summary)
        summary = remove_bracketed_text(summary)

        keywords = extract_keywords(summary, search_query)
        print(f"Selected Keywords: {keywords}")  # Debugging statement

        youtube_links = get_youtube_links(keywords)
        print(f"YouTube Links: {youtube_links}")  # Debugging statement

        summary_with_links = add_hyperlinks(summary, youtube_links)

        start_time = convert_to_time_format(split_start_times[0])
        end_time = convert_to_time_format(split_start_times[-1] + split_durations[-1])
        summary_time_range = f"{start_time} - {end_time}"
        summary_text = f"\nSummary for {summary_time_range}:\n{summary_with_links}\n"

        print(summary_text)  # Print the summary in real-time

        html_content += f"<h2>Summary for {summary_time_range}</h2><p>{summary_with_links}</p>"

    html_content += "</body></html>"

    with open("summaries_with_timestamps.html", "w") as output_file:
        output_file.write(html_content)

# Measure the start time
start_time = time.time()

srt_data = YouTubeTranscriptApi.get_transcript("DK3aIvfD9Rs", languages=['en'])

subtitles, start_times, durations = preprocess_subtitles(srt_data)

video_length_seconds = start_times[-1] + durations[-1]
video_length_minutes = video_length_seconds / 60

summary_size = input("How detailed summary do you want? (s, m, l): ")
search_query = input("Enter your search query: ")

generate_summary(subtitles, start_times, durations, summary_size, video_length_minutes, search_query)

# Measure the end time and calculate the elapsed time
end_time = time.time()
elapsed_time = end_time - start_time

print(f"Time taken to generate the summary: {elapsed_time:.2f} seconds")

import requests

# Set up your API key and endpoint
api_key1 = "YOUR_API_KEY"  # Replace with your actual API key
model_id1 = "meta-llama/Llama-2-7b-hf"  # Replace with the correct model ID
api_url1 = f"https://api-inference.huggingface.co/models/{model_id1}"

headers = {
    "Authorization": f"Bearer {api_key1}",
    "Content-Type": "application/json"
}

# Input text to summarize
input_text1 = (
    "The LLaMA model is a state-of-the-art language model that has been used for various tasks, "
    "including text generation, translation, and summarization."
)

# Construct the payload
payload = {
    "inputs": input_text1,
    "parameters": {
        "max_length": 80,
        "min_length": 40,
        "num_beams": 4,
        "early_stopping": False
    }
}

# Make the request to the Hugging Face Inference API
response = requests.post(api_url1, headers=headers, json=payload)

# Check for errors
if response.status_code == 200:
    result = response.json()
    print("Summary:", result[0]["generated_text"])
else:
    print(f"Error: {response.status_code} - {response.text}")
