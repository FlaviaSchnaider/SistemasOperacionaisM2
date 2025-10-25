import argparse
import os
import psutil
import time
import threading
import numpy as np

def get_page_faults():
    """Retorna o total de page faults do processo atual"""
    processo = psutil.Process(os.getpid())
    falhas = getattr(processo.memory_info(), "pfaults", None)
    if falhas is not None:
        return falhas
    # fallback para Windows (psutil >= 5.9)
    memoria = processo.memory_info()
    return getattr(memoria, "page_faults", 0)


def busy_wait(milisegundos: int):
    """Espera ocupada (simular o aquecimento da CPU)"""
    tempo_final = time.perf_counter() + (milisegundos / 1000.0)
    while time.perf_counter() < tempo_final:
        pass


# Execução de um padrão de acesso à memória
def run_pattern(tamanho_mb: int, iteracoes: int, padrao: str):
    """Executa um padrão (alloc, write, read, etc.) e mede tempo + PF"""
    tamanho_em_bytes = tamanho_mb * 1024 * 1024
    quantidade_inteiros = tamanho_em_bytes // np.dtype(np.int32).itemsize

    busy_wait(300)
    falhas_antes = get_page_faults()
    tempo_inicio = time.perf_counter()

    if padrao == "alloc":
        for _ in range(iteracoes):
            bloco_memoria = np.empty(quantidade_inteiros, dtype=np.int32)
            del bloco_memoria

    elif padrao == "write":
        bloco_memoria = np.zeros(quantidade_inteiros, dtype=np.int32)
        for _ in range(iteracoes):
            bloco_memoria[:] = 1
        del bloco_memoria

    elif padrao == "read":
        bloco_memoria = np.ones(quantidade_inteiros, dtype=np.int32)
        soma = 0
        for _ in range(iteracoes):
            soma += np.sum(bloco_memoria)
        if soma == -1:
            print(soma)
        del bloco_memoria

    elif padrao == "alloc_write_free":
        for _ in range(iteracoes):
            bloco_memoria = np.zeros(quantidade_inteiros, dtype=np.int32)
            bloco_memoria[:] = 2
            del bloco_memoria

    elif padrao == "alloc_read_free":
        soma = 0
        for _ in range(iteracoes):
            bloco_memoria = np.ones(quantidade_inteiros, dtype=np.int32)
            soma += np.sum(bloco_memoria)
            del bloco_memoria
        if soma == -1:
            print(soma)
    else:
        raise ValueError(f"Padrão desconhecido: {padrao}")

    tempo_fim = time.perf_counter()
    falhas_depois = get_page_faults()

    return (tempo_fim - tempo_inicio, falhas_depois - falhas_antes)


# Função principal (multi-thread)
def main():
    parser = argparse.ArgumentParser(description="Experimento de custo de memória")
    parser.add_argument("--mb", type=int, default=32, help="Tamanho em MB por thread")
    parser.add_argument("--iters", type=int, default=100, help="Número de iterações")
    parser.add_argument(
        "--pattern",
        type=str,
        default="write",
        choices=["alloc", "write", "read", "alloc_write_free", "alloc_read_free"],
        help="Padrão de acesso à memória",
    )
    parser.add_argument("--threads", type=int, default=1, help="Número de threads")
    argumentos = parser.parse_args()

    print(f"\nConfiguração: ")
    print(f"Tamanho: {argumentos.mb} MB por thread")
    print(f"Itérações: {argumentos.iters}")
    print(f"Padrão: {argumentos.pattern}")
    print(f"Threads: {argumentos.threads}")

    falhas_processo_inicio = get_page_faults()
    tempo_global_inicio = time.perf_counter()

    resultados = []
    lista_threads = []

    def executar_thread(indice_thread):
        tempo_execucao, falhas_thread = run_pattern(argumentos.mb, argumentos.iters, argumentos.pattern)
        resultados.append((tempo_execucao, falhas_thread))
        print(f"   Thread {indice_thread}: tempo={tempo_execucao:.3f}s, page_faults={falhas_thread}")

    for i in range(argumentos.threads):
        thread = threading.Thread(target=executar_thread, args=(i,))
        lista_threads.append(thread)
        thread.start()

    for thread in lista_threads:
        thread.join()

    falhas_processo_fim = get_page_faults()
    tempo_total_execucao = time.perf_counter() - tempo_global_inicio
    falhas_processo_delta = falhas_processo_fim - falhas_processo_inicio

    soma_tempos_threads = sum(tempo for tempo, _ in resultados)
    media_tempo_thread = soma_tempos_threads / len(resultados)
    soma_falhas_threads = sum(falhas for _, falhas in resultados)

    print("\nResultados:")
    print(f"   Tempo total: {tempo_total_execucao:.4f}s")
    print(f"   Soma dos tempos (threads): {soma_tempos_threads:.4f}s")
    print(f"   Média por thread: {media_tempo_thread:.4f}s")
    print(f"   Page Faults do processo (delta global): {falhas_processo_delta}")
    print(f"   Soma dos deltas por thread: {soma_falhas_threads}")
    print("\n")


if __name__ == "__main__":
    main()
