# image-processing

Pacote simples para processamento básico de imagens com Python.

## Funcionalidades

- Abrir imagem  
- Salvar imagem  
- Converter imagem para tons de cinza  
- Redimensionar imagem  
- Aplicar filtro de contorno  

## Instalação

Para instalar, use o pip:

```bash
pip install image-processing
```

## Uso básico

```python
from image_processing import (
    abrir_imagem,
    salvar_imagem,
    converter_para_cinza,
    redimensionar,
    aplicar_filtro,
)

# Abrir imagem
img = abrir_imagem("minha_imagem.jpg")

# Converter para tons de cinza
img_cinza = converter_para_cinza(img)

# Salvar imagem convertida
salvar_imagem(img_cinza, "minha_imagem_cinza.jpg")

# Redimensionar imagem
img_redimensionada = redimensionar(img, 200, 200)
salvar_imagem(img_redimensionada, "minha_imagem_redimensionada.jpg")

# Aplicar filtro de contorno
img_filtrada = aplicar_filtro(img)
salvar_imagem(img_filtrada, "minha_imagem_filtrada.jpg")
```

## Requisitos

* Python 3.6 ou superior
* Pillow

## Contribuição

Contribuições são bem-vindas! Para contribuir:

1. Faça um fork do projeto
2. Crie uma branch com sua feature (`git checkout -b minha-feature`)
3. Faça commit das suas alterações (`git commit -m 'Minha nova feature'`)
4. Faça push para a branch (`git push origin minha-feature`)
5. Abra um Pull Request

## Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## Autor

João Vitor

```
