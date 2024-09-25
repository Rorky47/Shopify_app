import openai
import time
import logging
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

def generate_product_content(product_title):
    prompt = f"""
    Generate a product description, tags, and category for a product titled '{product_title}'.
    Provide the output in the following structured format:
    1. Description: [Insert product description here]
    2. Tags: [Insert comma-separated tags here]
    3. Category: [Insert category here]
    """
    max_retries = 3
    retries = 0

    while retries < max_retries:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI that generates product descriptions for e-commerce."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300
            )
            return response['choices'][0]['message']['content'].strip()
        except openai.error.RateLimitError as e:
            logging.error(f"Rate limit exceeded: {e}. Retrying in 20 seconds...")
            retries += 1
            time.sleep(20)
        except openai.error.OpenAIError as e:
            logging.error(f"Failed to generate product content due to API error: {e}")
            return None
    return None

def parse_generated_content(generated_text):
    description, tags, category = None, None, None
    for line in generated_text.split('\n'):
        if line.startswith("1. Description:"):
            description = line.replace("1. Description:", "").strip()
        elif line.startswith("2. Tags:"):
            tags = line.replace("2. Tags:", "").strip()
        elif line.startswith("3. Category:"):
            category = line.replace("3. Category:", "").strip()
    return description, tags, category