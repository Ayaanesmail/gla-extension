import warnings
warnings.filterwarnings("ignore", message="Failed to load image Python extension")
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # '2' for warnings, '3' for errors only
import torch
if not torch.cuda.is_available():
    print("CUDA is not available. Running on CPU.")



from transformers import pipeline



# Choose a model; 'gpt2-medium' or 'EleutherAI/gpt-neo-1.3B' are options
generator = pipeline('text-generation', model='EleutherAI/gpt-neo-1.3B')



#inputs required from the user
video_title = "The Water Cycle Explained"
age = 10
grade_level = 5
difficulty = "easy"




#the type of prompt that will auto generate the quiz
prompt = (
    f"Create a {difficulty} quiz for a student aged {age}, in grade {grade_level}, "
    f"based on the topic: '{video_title}'. "
    "Provide 5 multiple-choice questions with 4 options each, and indicate the correct answer."
)

outputs = generator(prompt, max_length=500, num_return_sequences=1)
quiz = outputs[0]['generated_text']
print(quiz)