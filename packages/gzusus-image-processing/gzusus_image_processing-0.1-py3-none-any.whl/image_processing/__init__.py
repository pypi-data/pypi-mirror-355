from PIL import Image, ImageFilter

def abrir_imagem(caminho):
    """Abre uma imagem a partir do caminho especificado."""
    return Image.open(caminho)

def salvar_imagem(imagem, caminho):
    """Salva a imagem modificada no caminho especificado."""
    imagem.save(caminho)

def converter_para_cinza(imagem):
    """Converte a imagem para tons de cinza."""
    return imagem.convert("L")

def redimensionar(imagem, largura, altura):
    """Redimensiona a imagem para a largura e altura especificadas."""
    return imagem.resize((largura, altura))

def aplicar_filtro(imagem):
    """Aplica um filtro de contorno à imagem."""
    return imagem.filter(ImageFilter.CONTOUR)
