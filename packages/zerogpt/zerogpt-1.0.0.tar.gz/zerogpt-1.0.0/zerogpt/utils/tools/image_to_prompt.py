import json
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
import fake_useragent
import os

def image_to_prompt(image_path, prompt_style='tag'):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Файл {image_path} не найден")
    with open(image_path, 'rb') as img_file:
        multipart_data = MultipartEncoder(
            fields={
                '1_image': ('image.jpg', img_file, 'image/jpeg'),
                '1_promptStyle': prompt_style,
                '0': '["$K1","n7173352t"]'
            }
        )
        headers = {
            'accept': 'text/x-component',
            'content-type': multipart_data.content_type,
            'next-action': 'fa6112528e902fdca102489e06fea745880f88e3',
            'origin': 'https://vheer.com',
            'referer': 'https://vheer.com/app/image-to-prompt',
            'user-agent': fake_useragent.UserAgent().random
        }
        response = requests.post('https://vheer.com/app/image-to-prompt', headers=headers, data=multipart_data)
        response.raise_for_status()
        return json.loads(response.text.split('1:')[-1])

image_to_prompt.__version__ = '0.0.1'