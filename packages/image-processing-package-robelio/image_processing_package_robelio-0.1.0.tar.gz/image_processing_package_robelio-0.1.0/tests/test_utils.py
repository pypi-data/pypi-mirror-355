import pytest
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import os
from src.image_package.utils.io import load_image, save_image, image_info, batch_process
from src.image_package.utils.plot import plot_image, plot_images, plot_histogram

@pytest.fixture(autouse=True)
def cleanup():
    yield
    # Limpeza após cada teste
    import gc
    gc.collect()

@pytest.fixture
def sample_image(tmp_path):
    """Cria uma imagem de teste RGB 100x100"""
    img_path = os.path.join(tmp_path, "test_rgb.png")
    img = Image.new('RGB', (100, 100), color=(255, 0, 0))
    img.save(img_path)
    return img_path

@pytest.fixture
def sample_gray_image(tmp_path):
    """Cria uma imagem de teste em escala de cinza 100x100"""
    img_path = os.path.join(tmp_path, "test_gray.png")
    img = Image.new('L', (100, 100), color=128)
    img.save(img_path)
    return img_path

@pytest.fixture
def sample_output_dir(tmp_path):
    """Cria um diretório de saída para testes"""
    output_dir = os.path.join(tmp_path, "output")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def test_load_image(sample_image):
    """Testa o carregamento de imagem"""
    img = load_image(sample_image)
    assert isinstance(img, Image.Image)
    assert img.mode == 'RGB'
    assert img.size == (100, 100)

def test_save_image(sample_image, sample_output_dir):
    """Testa o salvamento de imagem"""
    img = load_image(sample_image)
    output_path = os.path.join(sample_output_dir, "saved.png")
    save_image(img, output_path)
    
    assert os.path.exists(output_path)
    saved_img = Image.open(output_path)
    assert saved_img.size == img.size

def test_image_info(sample_image, sample_gray_image):
    """Testa a função de informações da imagem"""
    rgb_img = load_image(sample_image)
    gray_img = load_image(sample_gray_image)
    
    rgb_info = image_info(rgb_img)
    gray_info = image_info(gray_img)
    
    assert rgb_info['mode'] == 'RGB'
    assert gray_info['mode'] == 'L'
    assert rgb_info['size'] == (100, 100)
    assert rgb_info['palette'] is None
    assert gray_info['palette'] is None 

def test_batch_process(tmp_path, sample_image, sample_gray_image):
    """Testa o processamento em lote"""
    input_dir = os.path.join(tmp_path, "input")
    os.makedirs(input_dir)
    
    # Copia imagens de teste para o diretório de entrada
    os.link(sample_image, os.path.join(input_dir, "rgb.png"))
    os.link(sample_gray_image, os.path.join(input_dir, "gray.png"))
    
    output_dir = os.path.join(tmp_path, "batch_output")
    
    def test_processor(img):
        return img.rotate(45)
    
    batch_process(input_dir, output_dir, test_processor, extension="png")
    
    
    assert len(os.listdir(output_dir)) == 2
    for filename in ['rgb.png', 'gray.png']:
        assert os.path.exists(os.path.join(output_dir, filename))

def test_plot_image(sample_image):
    """Testa a plotagem de imagem única"""
    img = load_image(sample_image)
    fig = plot_image(img, title="Test Image", show=False)
    assert fig is not None  
def test_plot_images(sample_image, sample_gray_image, monkeypatch):
    """Testa a plotagem de múltiplas imagens"""
    img1 = load_image(sample_image)
    img2 = load_image(sample_gray_image)
    
    # Mock para evitar abrir janelas durante os testes
    monkeypatch.setattr(plt, 'show', lambda: None)
    
    plot_images([img1, img2], titles=["RGB", "Grayscale"], ncols=2)

def test_plot_histogram(sample_image, sample_gray_image, monkeypatch):
    """Testa a plotagem de histograma"""
    rgb_img = load_image(sample_image)
    gray_img = load_image(sample_gray_image)
    
    
    monkeypatch.setattr(plt, 'show', lambda: None)
    
    plot_histogram(rgb_img, title="RGB Histogram")
    plot_histogram(gray_img, title="Grayscale Histogram")

def test_load_image_invalid_path():
    """Testa o tratamento de erro para caminho inválido"""
    with pytest.raises(ValueError):
        load_image("caminho/inexistente.jpg")

def test_save_image_invalid_type(tmp_path):
    """Testa o tratamento de erro para tipo inválido"""
    output_path = os.path.join(tmp_path, "invalid.txt")
    with pytest.raises(TypeError):
        save_image("não é uma imagem", output_path)