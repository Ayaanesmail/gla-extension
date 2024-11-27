# app.py
from fastapi import FastAPI
from api_lightllm import (
    lightllm_generate,
    lightllm_generate_stream,
    lightllm_get_score,
)
# Initialize the FastAPI app
app = FastAPI()

# Define global variables or dependencies
g_id_gen = ...  # Initialize your ID generator
httpserver_manager = ...  # Initialize your HTTP server manager

# Define the API routes
app.post("/generate")(lambda request: lightllm_generate(request, g_id_gen, httpserver_manager))
app.post("/generate_stream")(lambda request: lightllm_generate_stream(request, g_id_gen, httpserver_manager))
app.post("/get_score")(lambda request: lightllm_get_score(request, g_id_gen, httpserver_manager))
