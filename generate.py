import json
import base64
import io
from PIL import Image

from pathlib import Path
from os import makedirs
import time

from api import generate_image_entrypoint as gen_img

OUTPUT_PATH = './out/'

def save_img(img_bytes: bytes):
    filename = time.strftime("%m_%d_%Y_%I_%M_%S_%p.png")
    path = Path(OUTPUT_PATH)
    try:
        makedirs(path.absolute(), exist_ok=True)
        path = path.joinpath(f"./{filename}").absolute().resolve()

        # Ensure we have bytes for decoding
        if isinstance(img_bytes, str):
            base64_bytes_to_decode = img_bytes.encode('utf-8')
        else: # Assuming input is bytes
             base64_bytes_to_decode = img_bytes
    
        # Decode the Base64 data
        image_data = base64.decodebytes(base64_bytes_to_decode)
    
        # Create an in-memory binary stream from the decoded bytes
        image_bytes_io = io.BytesIO(image_data)
    
        # Open the image using Pillow from the in-memory stream
        img = Image.open(image_bytes_io)
    
        # You can now optionally process the image with Pillow, e.g., resize:
        # img = img.resize((100, 100))
    
        # Save the image (Pillow determines format from extension, or specify with format='PNG')
        img.save(path, format='png')
        # Alternatively, explicitly set format:
        # img.save('another_image.gif', format='GIF')
    
        print(f"Image successfully decoded using Pillow and saved to {path}")
    
    except FileNotFoundError: # Pillow raises FileNotFoundError if it can't identify format
         print(f"Pillow Error: Could not identify image file format from Base64 data.")
    except base64.binascii.Error as e:
        print(f"Base64 Decoding Error: {e}.")
    except Exception as e:
        print(f"An error occurred: {e}")

def get_img(prompt: str):
    data_url = gen_img(prompt)
    try:
        # Check if the string is a data URL and extract the raw base64 data
        if "base64," in data_url:
            # Splits at 'base64,' and takes everything after it
            header, base64_data = data_url.split("base64,", 1)
        else:
            # Fallback if the string is already raw base64 data
            base64_data = data_url

        # Clean up any accidental whitespace or newlines
        base64_data = base64_data.strip()

        save_img(base64_data)
        return True

    except Exception as e:
        print(f"❌ Failed to save image: {e}")
        return False

if __name__ == "__main__":
    with open("./prompts.txt", "r") as file:
        while line := file.readline().strip():
            get_img(line)
            cntd = input("Continue? [y]/n: ")
            if "n" in cntd.lower():
                break
