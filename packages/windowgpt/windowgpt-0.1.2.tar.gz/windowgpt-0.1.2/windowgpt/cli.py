import os
import argparse
from datetime import datetime
import pyautogui
from PIL import Image
import openai
import base64
import io
import time
import sys


def take_ss():
    return pyautogui.screenshot()

def image_to_base64(img: Image.Image) -> str:
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

def query_gpt_with_image(image: Image.Image, prompt: str, api_key) -> str:
    # api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # raise EnvironmentError("OPENAI_API_KEY environment variable not set.")

        print("No OpenAI API key found.\n")
        print("Set your key by exporting it in your shell:\n  export OPENAI_API_KEY=sk-...:\n")
        sys.exit(1)

    openai.api_key = api_key

    base64_img = image_to_base64(image)

    response = openai.ChatCompletion.create(
        model="o4-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/png;base64,{base64_img}"
                    }},
                ],
            }
        ],
        max_completion_tokens=10000, # change to max_tokens=1000 for model = gpt-4o
    )
    return response.choices[0].message.content

def main():
    parser = argparse.ArgumentParser(description="Send a screenshot and prompt to ChatGPT Vision")
    parser.add_argument("--p", type=str, required=True, help="Prompt to send with screenshot")
    parser.add_argument("--s", action="store_true", help="Save the screenshot locally")
    parser.add_argument("--key", type=str, help="(Optional) Your OpenAI API key")


    args = parser.parse_args()

    print("Taking screenshot in...")
    time.sleep(1)
    print("3")
    time.sleep(1)
    print("2")
    time.sleep(1)
    print("1")
    ss = take_ss()

    if args.s:
        folder = './screenshots'
        os.makedirs(folder, exist_ok=True)
        filename = f"screenshot_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
        path = os.path.join(folder, filename)
        ss.save(path)
        print(f"Screenshot saved to: {path}")
    else:
        filename = f"screenshot_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"


    print("Sending screenshot and prompt to GPT-4o...")
    api_key = args.key or os.getenv("OPENAI_API_KEY")

    response = query_gpt_with_image(ss, args.p, api_key)
    print("GPT-4o Response:\n")
    print(response)
    with open(f"{filename.split('.')[0]}.txt", 'w') as f:
        f.write(response)
    f.close()




    