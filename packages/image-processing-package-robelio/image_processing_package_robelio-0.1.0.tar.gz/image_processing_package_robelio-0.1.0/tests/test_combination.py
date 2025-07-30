import pytest
from PIL import Image
from src.image_package.processing.combination import blend_images, merge_channels

@pytest.fixture(autouse=True)
def cleanup():
    yield
    
    import gc
    gc.collect()

@pytest.fixture
def sample_images():
    """ Fixture que retorna imagens de teste """
    red = Image.new('RGB', (100, 100), (255, 0, 0))
    blue = Image.new('RGB', (100, 100), (0, 0, 255))
    return red, blue

def test_blend_images(sample_images):
    """ Testa a combinação de duas imagens """
    red, blue = sample_images
    
    blended = blend_images(red, blue, 0.5)
    pixel = blended.getpixel((50, 50))
    assert 120 < pixel[0] < 140  
    assert pixel[1] == 0         
    assert 120 < pixel[2] < 140 

    
    blended = blend_images(red, blue, 0.0)
    assert blended.getpixel((50, 50)) == (255, 0, 0)

def test_merge_channels():
    """ Testa a combinação de canais de cores """
    
    red = Image.new('L', (100, 100), 100)    
    green = Image.new('L', (100, 100), 150)  
    blue = Image.new('L', (100, 100), 200)  
    
    # Combina os canais
    merged = merge_channels(red, green, blue)
    
    # Verifica o pixel central
    assert merged.getpixel((50, 50)) == (100, 150, 200)
    assert merged.mode == 'RGB'

def test_blend_images_size_mismatch():
    """ Testa o tratamento de erro para tamanhos diferentes """
    img1 = Image.new('RGB', (100, 100), (255, 0, 0))
    img2 = Image.new('RGB', (200, 200), (0, 0, 255))
    
    with pytest.raises(ValueError, match="As imagens devem ter o mesmo tamanho"):
        blend_images(img1, img2)

def test_merge_channels_invalid_mode():
    """ Testa o tratamento de erro para modos inválidos """
    valid = Image.new('L', (100, 100), 100)
    invalid = Image.new('RGB', (100, 100), (255, 0, 0))
    
    with pytest.raises(ValueError, match="grayscale"):
        merge_channels(valid, invalid, valid)