# main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from youtube_transcript_api import YouTubeTranscriptApi
from transformers import T5Tokenizer, T5ForConditionalGeneration
from youtubesearchpython import VideosSearch
from fastapi.middleware.cors import CORSMiddleware
import nltk
import torch
import re
from collections import Counter

# Download required NLTK data
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')

# Initialize FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only. In production, specify your extension's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load models and tokenizer
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tokenizer = T5Tokenizer.from_pretrained("t5-base")
model = T5ForConditionalGeneration.from_pretrained("t5-base").to(device)

# Define request and response models
class SummarizeRequest(BaseModel):
    video_id: str
    summary_size: str  # 's', 'm', 'l'
    search_query: str

class SummaryItem(BaseModel):
    time_range: str
    summary: str

class SummaryResponse(BaseModel):
    summaries: List[SummaryItem]

# Helper functions
def preprocess_subtitles(srt_data):
    subtitles = [item['text'] for item in srt_data]
    start_times = [item['start'] for item in srt_data]
    durations = [item['duration'] for item in srt_data]
    return subtitles, start_times, durations

def capitalize_sentences(summary):
    try:
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
    except Exception as e:
        print(f"Error in capitalize_sentences: {e}")
        return summary  # Return original summary if there's an error

def remove_bracketed_text(summary):
    return re.sub(r'\[.*?\]', '', summary)

def convert_to_time_format(timestamp):
    minutes = int(timestamp // 60)
    seconds = int(timestamp % 60)
    milliseconds = int((timestamp % 1) * 1000)
    return f"{minutes:02d}:{seconds:02d}:{milliseconds:03d}"

def extract_keywords(summary, search_query, num_keywords=3):
    try:
        # Clean and tokenize the text
        words = re.findall(r'\w+', summary.lower())
        word_freq = Counter(words)
        
        # Filter out common words and short words
        common_words = [word for word, _ in word_freq.most_common() 
                       if word.isalpha() and len(word) > 3]

        # Add search query terms to keywords
        search_terms = [term.lower() for term in search_query.split() 
                       if len(term) > 3]
        
        # Combine search terms with common words, avoiding duplicates
        keywords = []
        for term in search_terms + common_words:
            if term not in keywords:
                keywords.append(term)

        return keywords[:num_keywords]
    except Exception as e:
        print(f"Error extracting keywords: {e}")
        return []

def get_youtube_links(keywords):
    links = {}
    for keyword in keywords:
        videos_search = VideosSearch(keyword, limit=1)
        results = videos_search.result()
        if results['result']:
            video_id = results['result'][0]['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            links[keyword] = video_url
    return links

def add_hyperlinks(summary, links):
    for keyword, url in links.items():
        # Escape special characters in the keyword
        escaped_keyword = re.escape(keyword)
        pattern = f"\\b{escaped_keyword}\\b"
        replacement = f'<a href="{url}" target="_blank">{keyword}</a>'
        try:
            summary = re.sub(pattern, replacement, summary, flags=re.IGNORECASE)
        except Exception as e:
            print(f"Error adding hyperlink for keyword '{keyword}': {e}")
            continue
    return summary

# Main summarization endpoint
@app.post("/summarize", response_model=SummaryResponse)
def summarize(request: SummarizeRequest):
    video_id = request.video_id
    summary_size = request.summary_size.lower()
    search_query = request.search_query

    # Validate summary_size
    if summary_size not in ['s', 'm', 'l']:
        raise HTTPException(status_code=400, detail="Invalid summary size. Choose 's', 'm', or 'l'.")

    # Fetch transcript
    try:
        srt_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
    except Exception as e:
        raise HTTPException(status_code=404, detail="Transcript not found for the given video ID.")

    subtitles, start_times, durations = preprocess_subtitles(srt_data)
    video_length_seconds = start_times[-1] + durations[-1]
    video_length_minutes = video_length_seconds / 60

    # Set max_length based on summary_size
    max_length_options = {'s': 100, 'm': 200, 'l': 300}
    max_length = max_length_options[summary_size]

    # Determine number of splits based on video length
    if video_length_minutes <= 15:
        num_splits = 5
    elif video_length_minutes <= 30:
        num_splits = 10
    elif video_length_minutes <= 60:
        num_splits = 15
    else:
        num_splits = 20

    segment_length = len(subtitles) // num_splits
    summaries = []

    for i in range(num_splits):
        start_index = i * segment_length
        end_index = min(start_index + segment_length, len(subtitles))
        split_subtitles = subtitles[start_index:end_index]
        split_start_times = start_times[start_index:end_index]
        split_durations = durations[start_index:end_index]

        text = ' '.join(split_subtitles)
        inputs = tokenizer.encode("summarize: " + text, return_tensors="pt", max_length=512, truncation=True).to(device)

        summary_ids = model.generate(
            inputs,
            max_length=max_length,
            min_length=int(0.7*max_length),
            length_penalty=1.0,
            num_beams=6,
            early_stopping=True
        )
        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        summary = capitalize_sentences(remove_bracketed_text(summary))

        keywords = extract_keywords(summary, search_query)
        youtube_links = get_youtube_links(keywords)
        summary_with_links = add_hyperlinks(summary, youtube_links)

        start_time = convert_to_time_format(split_start_times[0])
        end_time = convert_to_time_format(split_start_times[-1] + split_durations[-1])
        summary_time_range = f"{start_time} - {end_time}"

        summaries.append({
            "time_range": summary_time_range,
            "summary": summary_with_links
        })

    return {"summaries": summaries}
