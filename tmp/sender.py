import os       # criar arquivos, FIFO etc
import sys      # interações com o python
import struct   # empacotar dados em formato binário 

def ensure_fifo(path):
    try:                    # tenta criar FIFO 
        os.mkfifo(path) 
    except FileExistsError: # se já existir
        pass

def load_as_pgm_bytes(img_path):
    """  
    Retorna (w, h, maxv=255, bytes) independente de ser PNG/JPG/PGM.
    Se for PNG/JPG, converte para 'L' (8-bit grayscale).
    """
    ext = os.path.splitext(img_path)[1].lower() # extraindo metadados

    if ext == ".pgm":
        with open(img_path, "rb") as f:         # abre o arquivo em modo binário
            if f.readline().strip() != b'P5':  
                raise ValueError("PGM não está no modo binário P5")
            line = f.readline()                 # O formato PGM permite comentários começando com #. Esses são pulados
            while line.startswith(b'#'):
                line = f.readline()
            w, h = map(int, line.split())       # lê largura e alguta
            maxv = int(f.readline())            # lê valor máximo do pixel
            data = bytearray(f.read())          # lê os bytes da imagem
            if len(data) != w*h:
                raise ValueError("Tamanho do payload PGM inconsistente")
            if maxv != 255:
                data = bytearray(int(px * 255 / maxv) for px in data) # faz ajuste proporcional se valor de bytes for != 255
                maxv = 255
            return w, h, maxv, data
    else:
        try:
            from PIL import Image               # usa Pillow para abrir as imagens em python
        except ImportError:
            sys.exit(1)                         
        im = Image.open(img_path).convert("L")  # converte pra L (escala em cinza com 8 bits por pixel)
        w, h = im.size
        data = bytearray(im.tobytes())
        return w, h, 255, data                  # retorna dados com maxv = 255

def main():
    if len(sys.argv) != 3:
        print(f"Uso: {sys.argv[0]} <fifo_path> <entrada.(png|jpg|pgm)>") # caminho da imagem e tipo de arquivo
        sys.exit(1)

    fifo = sys.argv[1]
    inpath = sys.argv[2]

    ensure_fifo(fifo) # garante que o FIFO exista

    w, h, maxv, data = load_as_pgm_bytes(inpath)    # carrega a imagem obtendo os valores 

    with open(fifo, "wb") as f:                     # abre o FIFO em modo binário de escrita(wb)
        header = struct.pack("iii", w, h, maxv)     # cria cabeçalho em binário, struct gera 12bytes (3 * 4)
        f.write(header)
        f.write(data)

    print(f"[Sender] {inpath} ({w}x{h}) enviado com sucesso.")

if __name__ == "__main__":
    main()
