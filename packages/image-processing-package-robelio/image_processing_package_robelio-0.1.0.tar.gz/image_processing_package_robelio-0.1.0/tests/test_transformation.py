from src.image_package.processing.transformation import crop, rotate, resize, flip
from PIL import Image


def test_crop():
    img = Image.new('RGB', (100, 100), 'white')
    cropped = crop(img, 10, 10, 50, 50)
    assert cropped.size == (40, 40)  # 50-10=40

def test_resize():
    img = Image.new('RGB', (100, 100), 'blue')
    resized = resize(img, 50, 50)
    assert resized.size == (50, 50)

def test_rotate():
    img = Image.new('RGB', (100, 100), 'red')
    
    rotated = rotate(img, 30, expand=False)
    assert rotated.size == (100, 100)
    
   
    rotated = rotate(img, 30, expand=True)
    assert rotated.size > (100, 100)    