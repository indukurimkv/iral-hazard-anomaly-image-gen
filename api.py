import os
import base64
from mimetypes import guess_type
from dotenv import load_dotenv
from openai import OpenAI

import json
import requests

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI client configured for OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

def encode_image_to_base64(image_path: str) -> tuple[str, str]:
    """Encodes a local image to a base64 string and detects its MIME type."""
    mime_type, _ = guess_type(image_path)
    if not mime_type:
        mime_type = "image/jpeg"  # Default fallback
        
    with open(image_path, "rb") as image_file:
        base64_encoded = base64.b64encode(image_file.read()).decode("utf-8")
        
    return base64_encoded, mime_type

def process_multimodal_prompt(text_prompt: str, image_path: str = None) -> str:
    """
    Sends text and an optional image to a vision model to refine 
    or generate a highly descriptive prompt for the image generator.
    """
    # Using a capable, cost-effective vision model on OpenRouter
    model = "google/gemini-2.5-flash" 
    
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Based on this request: '{text_prompt}', generate a highly detailed, descriptive prompt suitable for an AI image generator (like Stable Diffusion or FLUX). Focus on style, lighting, and composition. Return ONLY the final prompt text."
                }
            ]
        }
    ]
    
    # If an image is provided, encode it and inject it into the request
    if image_path and os.path.exists(image_path):
        base64_image, mime_type = encode_image_to_base64(image_path)
        messages[0]["content"].append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime_type};base64,{base64_image}"
            }
        })
        print("successfully converted image to url")
    elif image_path:
        print(f"⚠️ Warning: Image path '{image_path}' not found. Proceeding with text only.")

    try:
        print(model, "\n", messages)
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        refined_prompt = response.choices[0].message.content.strip()
        return refined_prompt
    except Exception as e:
        print(f"❌ Error processing prompt: {e}")
        return text_prompt # Fallback to original text if API fails

# def generate_image(prompt: str, model: str = "black-forest-labs/flux.2-max") -> str:
#     """
#     Takes a text prompt and generates an image using an OpenRouter image model.
#     Returns the URL of the generated image.
#     """
#     try:
#         print(f"🎨 Sending prompt to {model}...")
#         # OpenRouter supports standard OpenAI image generation endpoints for image models
#         response = client.images.generate(
#             model=model,
#             prompt=prompt,
#             n=1,
#             size="1024x1024"
#         )
#         return response.data[0].url
#     except Exception as e:
#         print(f"❌ Error generating image: {e}")
#         return None

def generate_image(prompt: str, model: str = "google/gemini-2.5-flash-image") -> str:
    """
    Takes a text prompt and generates an image using OpenRouter's REST API.
    Returns the base64 data URL of the generated image.
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY is not set.")
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "modalities": ["image", "text"]
    }

    try:
        print(f"🎨 Sending prompt to {model} via REST API...")
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Raise exception for bad HTTP status codes
        
        result = response.json()

        # Extract the image URL from the assistant's response choices
        if result.get("choices"):
            message = result["choices"][0]["message"]
            if message.get("images"):
                # Return the first generated image URL (Base64 data URL)
                image_url = message["images"][0]["image_url"]["url"]
                return image_url
                
        print("⚠️ No image was found in the API response data.")
        return None

    except requests.exceptions.RequestException as e:
        print(f"❌ HTTP Error generating image: {e}")
        return None
    except Exception as e:
        print(f"❌ Error parsing image generation response: {e}")
        return None

def generate_image_entrypoint(text_prompt: str, input_image_path: str = None, image_model: str = "google/gemini-3.1-flash-image-preview"):
    """
    Main entrypoint function.
    Accepts text and an optional image, processes them, and generates a new image.
    """
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ Error: OPENROUTER_API_KEY not found in environment or .env file.")
        return

    print("🧠 Analyzing prompt inputs...")
    final_prompt = process_multimodal_prompt(text_prompt, input_image_path)
    print(f"📝 Optimized Image Prompt: {final_prompt}\n")
    
    image_url = generate_image(final_prompt, model=image_model)
    
    if image_url:
       print(f"✨ Success! Your image has been generated.")
       print(f"🔗 Image URL: {image_url}")
    return image_url

# --- Example Usage ---
if __name__ == "__main__":
    # Example 1: Text-only prompt
    generate_image_entrypoint(
        text_prompt="Hyper-realistic image of an indoor industrial environment after an earthquake. Looks like it was taken from DSLR camera."
    )
    
    # Example 2: Text + Image prompt (uncomment to use)
    # generate_image_entrypoint(
    #     text_prompt="Make this character look like a fantasy wizard holding a glowing staff",
    #     input_image_path="path/to/your/portrait.jpg",
    #     image_model="black-forest-labs/flux-schnell" 
    # )
