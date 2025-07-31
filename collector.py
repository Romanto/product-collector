import os
import re
import json
import time
import hashlib
import aiohttp
from bs4 import BeautifulSoup
from telethon.tl.types import MessageEntityUrl, MessageEntityTextUrl
from telethon.sync import TelegramClient
from supabase import create_client, Client
from dotenv import load_dotenv
import asyncio
from datetime import datetime

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
# Load environment variables
load_dotenv()

# Supabase configuration
supabase_url: str = os.getenv('SUPABASE_URL')
supabase_key: str = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(supabase_url, supabase_key)

# Telegram configuration
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
channel_username = 't.me/haregakaniti'
output_dir = f'channel_images_{channel_username.split('/')[-1]}'
output_file = f'channel_messages_{channel_username.split('/')[-1]}.json'

# Create output directory for images
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Create client
client = TelegramClient('anon', api_id, api_hash)

def clean_urls_from_text(text: str) -> str:
    """
    Removes all URLs from the given text using regex.
    """
    if not text:
        return text
    url_pattern = r'https?://[^\s]+'
    return re.sub(url_pattern, '', text).strip()

def regex_url_extractor(text: str, urls: list):
    """
    Extracts Amazon URLs from a given text using regex.
    """
    url_pattern = r'(https?://[^\s]+)'
    found_urls = re.findall(url_pattern, text, re.IGNORECASE)
    for url in found_urls:
        if any(x for x in ['amazon', 'amzn'] if x in url.lower()):
            if url not in urls:  # Avoid duplicates
                urls.append(url)

def extract_urls(message):
    urls = []
    try:
        # From text using regex (for plain links)
        if message.text:
            regex_url_extractor(text=message.text, urls=urls)

        # From message.entities (formatted/hidden URLs)
        if message.entities:
            for entity in message.entities:
                if isinstance(entity, MessageEntityUrl):
                    offset = message.text.index('https')
                    length = entity.length
                    regex_url_extractor(text=message.text[offset:offset + length], urls=urls)
                elif isinstance(entity, MessageEntityTextUrl):
                    regex_url_extractor(text=entity.url, urls=urls)
        return urls
    except Exception as e:
        print(f"Error extracting URLs: {e}")
        return urls

async def get_amazon_category(url: str) -> tuple:
    """
    Fetches the Amazon product page and extracts the category using BeautifulSoup.
    Looks for <a class="a-link-normal a-color-tertiary">, potentially nested in <span class="a-list-item"> and <li>.
    """
    try:
        headers = {'User-Agent': USER_AGENT}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    # Look for the category in the specified <a> tag, including nested structures
                    category_tag = soup.find('a', class_='a-link-normal a-color-tertiary')
                    if category_tag:
                        category = category_tag.get_text(strip=True)
                        return category, str(response.real_url)
                    else:
                        # Fallback: check for nested structure explicitly
                        span_tag = soup.find('span', class_='a-list-item')
                        if span_tag:
                            category_tag = span_tag.find('a', class_='a-link-normal a-color-tertiary')
                            if category_tag:
                                category = category_tag.get_text(strip=True)
                                return category, str(response.real_url)
                        print(f"⚠️ No category found for {url}")
                        return None, None
                else:
                    print(f"❌ Failed to fetch URL {url}: Status {response.status}")
                    return None
    except Exception as e:
        print(f"❌ Error fetching category for {url}: {e}")
        return None

def get_image_hash(file_path):
    """
    Generate MD5 hash of an image file.
    """
    hash_md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

async def download_image(message, message_id):
    """
    Download image, hash it, and upload to Supabase storage if not already present.
    Returns the public URL and MD5 hash (image ID).
    """
    try:
        if message.photo:
            # Download image locally
            file_path = f"{output_dir}/{message_id}_temp.jpg"
            await message.download_media(file=file_path)
            
            # Generate MD5 hash (32 characters)
            image_id = get_image_hash(file_path)
            destination_path = f"images/{image_id}.jpg"
            
            # Check if file already exists in bucket
            bucket_name = "image-storage"
            try:
                existing_files = supabase.storage.from_(bucket_name).list("images")
                existing_filenames = [file['name'] for file in existing_files]
                if f"{image_id}.jpg" in existing_filenames:
                    print(f"✅ Image {image_id} already exists in {bucket_name}")
                    public_url = supabase.storage.from_(bucket_name).get_public_url(destination_path)
                    return public_url, image_id
            except Exception as e:
                print(f"⚠️ Error checking bucket: {e}")

            # Upload to Supabase
            with open(file_path, 'rb') as file:
                response = supabase.storage.from_(bucket_name).upload(
                    path=destination_path,
                    file=file,
                    file_options={"content-type": "image/jpeg"}
                )
            
            # Check for upload errors
            if hasattr(response, 'error') and response.error:
                print(f"❌ Failed to upload image {image_id}: {response.error.message}")
                return None, image_id
            
            # Get public URL
            public_url = supabase.storage.from_(bucket_name).get_public_url(destination_path)
            print(f"✅ Uploaded image {image_id} to {bucket_name}/{destination_path}")
            return public_url, image_id
    except Exception as e:
        print(f"❌ Error downloading/uploading image: {e}")
        return None, None
    return None, None

# Insert data into Supabase table
def insert_data(record: dict, table_name: str):
    try:
        data = supabase.table(table_name).insert(record).execute()
        return data
    except Exception as e:
        print(f"❌ Error inserting data to Supabase: {e}")
        return None

async def scrape_channel():
    messages_data = []

    async with client:
        async for message in client.iter_messages(channel_username, limit=100):
            # Extract Amazon URLs
            amazon_urls = extract_urls(message)
            if not amazon_urls:
                continue
            # Get category for each Amazon URL
            categories = []
            for url in amazon_urls:
                category, original_url = await get_amazon_category(url)
                if category:
                    categories = {'url': original_url, 'category': category}
                    break
            
            # Download image and get public URL and image ID
            image_url, image_id = await download_image(message, message.id)
            
            # Only include messages with Amazon URLs
            if amazon_urls:
                # Get current timestamp
                current_timestamp = datetime.utcfromtimestamp(int(time.time())).isoformat() + 'Z'
                
                if not categories:
                    return
                
                message_data = {
                    'id': message.id,
                    'created_at': current_timestamp,
                    'text': clean_urls_from_text(message.text),
                    'views': message.views,
                    'origin_item_url': categories['url'],
                    'bucket_image_url': image_url,
                    'image_id': image_id,
                    'category': categories['category'] if categories else None,
                }
                
                # Insert into Supabase
                insert_data(message_data, table_name='telegram_messages')
                
                messages_data.append(message_data)

    # Save to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(messages_data, f, indent=4, ensure_ascii=False)

    print(f"Saved {len(messages_data)} messages with Amazon URLs to {output_file}")

# Run the script
client.loop.run_until_complete(scrape_channel())