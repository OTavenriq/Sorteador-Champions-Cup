from PIL import Image

# Abre o logo existente (substitua pelo caminho correto do seu logo)
img = Image.open("SortApp/static/logoCCC.png")

# Converte para tamanho de favicon
img = img.resize((32, 32), Image.Resampling.LANCZOS)

# Salva como favicon.ico na pasta static
img.save("SortApp/static/favicon.ico")

print("Favicon gerado com sucesso!")
