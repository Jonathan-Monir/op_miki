import os
from time import sleep
import requests
from bs4 import BeautifulSoup
import streamlit as st
import zipfile
import io
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Radio button for selecting the manga version
anime = st.radio(
    "Choose a version",
    ["one piece colored", "Not Colored"],
)

# Extract URLs for specific pages
def urls_extractor(url, page):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    aa = soup.find_all('a', href=True)
    all_decorations = [decoration for decoration in aa if 'colored' in decoration['href']]
    page = last_chapter - (page - 1)
    pages_url = all_decorations[page]['href']
    
    return pages_url

# Web scraping to collect image URLs
def web_scrape(url):
    response = requests.get("https://mangaberri.com/" + url)
    soup = BeautifulSoup(response.content, 'html.parser')

    images = soup.find_all('img', src=True)
    image_urls = [image['src'] for image in images if 'One Piece Colored Manga' in image['alt']]
    st.write(f"Number of images = {len(image_urls)}")
    return image_urls

# Download an image and save it
def download_image(url, chapter, page, retries=3):
    img_name = f'chapter_{chapter}_page_{page}.jpg'
    
    if os.path.exists(img_name):
        print(f"Image {img_name} already exists, skipping download.")
        return os.path.getsize(img_name)
    
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            with open(img_name, 'wb') as f:
                f.write(response.content)
            return os.path.getsize(img_name)
        except (requests.RequestException, IOError) as e:
            st.write(response.content)
            print(f"Attempt {attempt + 1} failed for image: {img_name} - {e}")
            if attempt < retries - 1:
                sleep(2)
            else:
                raise

# Create a folder if it doesn't exist
def create_folder(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

# Convert images to CBZ format
def convert_images_to_cbz(folder_name):
    with zipfile.ZipFile(f'{folder_name}.cbz', 'w') as cbz:
        filenames = sort_filenames(os.listdir(folder_name))
        for filename in filenames:
            cbz.write(os.path.join(folder_name, filename), filename)

# Sort filenames based on page number
def sort_filenames(filenames):
    def extract_number(filename):
        match = re.search(r'page_(\d+)', filename)
        return int(match.group(1)) if match else 0
    
    return sorted(filenames, key=extract_number)

# Parallel downloading using ThreadPoolExecutor
def download_image_parallel(image_url, chapter, page_number, folder_name):
    try:
        url = "https://mangaberri.com/" + image_url
        img_size = download_image(url, chapter, page_number)
        os.rename(f'chapter_{chapter}_page_{page_number}.jpg', f'{folder_name}/chapter_{chapter}_page_{page_number}.jpg')
        return img_size
    except Exception as e:
        print(f"Failed to download image: {page_number} in chapter: {chapter} - {e}")
        return 0

# Save images to folder with threading for faster downloading
def save_images_to_folder(image_urls, folder_name, chapter, convert_to_cbz=True):
    create_folder(folder_name)
    chapter_size = 0
    num_images = len(image_urls)

    progress_bar = st.progress(0, text=f"Downloading images for Chapter {chapter}")

    # Parallel downloading using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(download_image_parallel, url, chapter, page_number, folder_name)
                   for page_number, url in enumerate(image_urls, 1)]
        
        for i, future in enumerate(as_completed(futures), 1):
            img_size = future.result()
            chapter_size += img_size
            progress = (i / num_images) * 100
            progress_bar.progress(int(progress), text=f"Downloading image {i}/{num_images}")

    progress_bar.empty()
    st.write(f"Total size for chapter {chapter}: {chapter_size / (1024 * 1024):.2f} MB")

    if convert_to_cbz:
        convert_images_to_cbz(folder_name)

    return chapter_size

# Get user inputs
min_page = st.number_input("minimum", min_value=0)
max_page = st.number_input("maximum", min_value=0)
submit_button = st.button("download")

# Fetch all manga links
response = requests.get("https://mangaberri.com/one-piece-colored-manga")
soup = BeautifulSoup(response.content, 'html.parser')
aa = soup.find_all('a', href=True)
all_decorations = [decoration for decoration in aa if 'colored' in decoration['href']]
last_chapter = int(all_decorations[1].text)

# Check if max_page exceeds the last chapter available
if last_chapter < max_page:
    st.warning(f"Max available chapter is: {last_chapter}")
    
total_size = 0
pages = range(int(min_page), int(max_page + 1))

# If submit button is clicked
if submit_button:
    if anime == "one piece colored":
        for page in pages:
            url = urls_extractor("https://mangaberri.com/one-piece-colored-manga", page)
            image_urls = web_scrape(url)
            chapter_size = save_images_to_folder(image_urls, f'from_{min_page}_to_{max_page}_{anime}', page)
            total_size += chapter_size
    else:
        for page in pages:
            if page < 10:
                url = f"https://readberserk.com/chapter/berserk-chapter-00{page}/"
            elif page < 100:
                url = f"https://readberserk.com/chapter/berserk-chapter-0{page}/"
            else:
                url = f"https://readberserk.com/chapter/berserk-chapter-{page}/"
            image_urls = web_scrape(url)
            chapter_size = save_images_to_folder(image_urls, f'from_{min_page}_to_{max_page}_{anime}', page)
            total_size += chapter_size

    output_path = f"from_{min_page}_to_{max_page}_{anime}"
    convert_images_to_cbz(output_path)

    if os.path.exists(output_path):
        with open(output_path + ".cbz", "rb") as file:
            st.download_button(
                label="Download CBZ",
                data=file,
                file_name=output_path + f'.cbz',
                mime="application/x-cbz"
            )
    else:
        st.error("The file was not  . Please try again.")
