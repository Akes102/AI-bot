
#import the os
#import .env (keys are stored here)
#import openai 

import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env
load_dotenv()

# Get API key
api_key = os.getenv("OPENAI_API_KEY")

# Optional: check if key is loaded
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in .env file")

# Create OpenAI client
client = OpenAI(api_key=api_key)



# prompt = """Classify the sentiment of each review from 1 to 5.:
# 1. Unbelievably good!
# 2. Shoes fell apart on the second use.
# 3. The shoes look nice, but they aren't very comfortable. 
# 4. Can't wait to show them off!"""

# # Create a request to the Chat Completions endpoint
# response = client.chat.completions.create(
#   model="gpt-4o-mini",
#   messages=[{"role": "user", "content": prompt}],
#   max_completion_tokens=100
# )

# print(response.choices[0].message.content)


# # Add the example to the prompt
# prompt = """Classify sentiment as 1-5 (negative to positive):
# 1. Love these! = 5
# 2. Unbelievably good! = 
# 3. Shoes fell apart on the second use. = 
# 4. The shoes look nice, but they aren't very comfortable. = 
# 5. Can't wait to show them off! =
 
#  """

# response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], max_completion_tokens=100)
# print(response.choices[0].message.content)


# Add the final example
prompt = """Classify sentiment as 1-5 (negative to positive):
1. Comfortable, but not very pretty = 2
2. Love these! = 5
3. Unbelievably good! = 
4. Shoes fell apart on the second use. = 
5. The shoes look nice, but they aren't very comfortable. = 
6. Can't wait to show them off! = """

response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], max_completion_tokens=100)
print(response.choices[0].message.content)