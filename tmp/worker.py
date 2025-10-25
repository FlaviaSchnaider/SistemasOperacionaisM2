import os
import sys
import struct
import threading
import queue
import time

MODE_NEG = 0
MODE_SLICE = 1

def write_pgm(path, w, h, maxv, data):
    with open(path, "wb") as f:
        f.write(b"P5\n")
        f.write(f"{w} {h}\n".encode())
        f.write(f"{maxv}\n".encode())
        f.write(data)

def apply_negative_block(data, rs, re, w):
    for y in range(rs, re):
        off = y * w
        for x in range(w):
            i = off + x
            data[i] = 255 - data[i]

def apply_slice_block(data, rs, re, w):
    t1, t2 = 50, 100
    for y in range(rs, re):
        off = y * w
        for x in range(w):
            i = off + x
            px = data[i]
            if px <= t1 or px >= t2:
                data[i] = 255
            else:
                data[i] = px

def worker_thread(q, data, w, mode):
    while True:
        try:
            rs, re = q.get(timeout=1)
        except queue.Empty:
            return
        if mode == MODE_NEG:
            apply_negative_block(data, rs, re, w)
        else:
            apply_slice_block(data, rs, re, w)
        q.task_done()

def ensure_fifo(path):
    try:
        os.mkfifo(path)
    except FileExistsError:
        pass

def main():
    if len(sys.argv) < 4:
        print(f"Uso: {sys.argv[0]} <fifo_path> <saida.pgm> <negativo|slice> [nthreads]")
        sys.exit(1)

    fifo   = sys.argv[1]
    outpth = sys.argv[2]
    mode_s = sys.argv[3].lower()

    if mode_s == "negativo":
        mode = MODE_NEG
        nthreads = int(sys.argv[4]) if len(sys.argv) >= 5 else 4
    elif mode_s == "slice":
        mode = MODE_SLICE
        nthreads = int(sys.argv[4]) if len(sys.argv) >= 5 else 4
    else:
        print("Modo inválido (use 'negativo' ou 'slice').")
        sys.exit(1)

    ensure_fifo(fifo)

    print("[Worker] Aguardando dados do sender...")
    with open(fifo, "rb") as f:
        header = f.read(12)
        if len(header) != 12:
            print("[Worker] Cabeçalho inválido/curto.")
            sys.exit(1)
        w, h, maxv = struct.unpack("iii", header)
        payload = f.read()
        data = bytearray(payload)

    if len(data) != w * h:
        print(f"[Worker] Tamanho da imagem não confere: esperado {w*h}, recebido {len(data)}")
        sys.exit(1)

    print(f"[Worker] Recebida imagem {w}x{h}, maxv={maxv}")

    start_time = time.time()
    q = queue.Queue()

    block = max(1, h // nthreads)
    row = 0
    while row < h:
        rs = row
        re = min(h, row + block)
        q.put((rs, re))
        row = re

    threads = []
    for _ in range(nthreads):
        t = threading.Thread(target=worker_thread, args=(q, data, w, mode))
        t.start()
        threads.append(t)

    q.join()
    for t in threads:
        t.join()

    elapsed = time.time() - start_time
    print(f"[Worker] Tempo de processamento: {elapsed:.4f} s")

    write_pgm(outpth, w, h, maxv, data)
    print(f"[Worker] Imagem processada salva em {outpth}")

if __name__ == "__main__":
    main()
