
import requests
import os

def download_image(url, chapter, page):
    response = requests.get(url)
    img_name = f'chapter_{chapter}_page_{page}.jpg'
    print(page)
    with open(img_name, 'wb') as f:
        f.write(response.content)
    return os.path.getsize(img_name)  # Return the size of the downloaded image

download_image(r"https://mangaberri.com/simage.php?url=RmlINSs5Y0tENEgxa0dvSTNyaU5kV0hvcnUyZUVxT0ZmWFZJRCtnOXdrQVpWeVBhRTVtUGRjQUVlMVJBS0hoV2Y3aGN0alphSzJYTHUrb0lGZGQ0OEE9PQ%3D%3D",1,1)
