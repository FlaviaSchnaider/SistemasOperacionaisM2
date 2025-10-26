# Coloração de Grafos - M2 (Parte 1 + Parte 2)
# Entrada: arquivo texto com grafo não direcionado, não ponderado.
# Saída: número cromático, tempo e (opcionalmente) a coloração.

import argparse
import sys
import time
import os
import csv
import le_resultados

# Leitura do grafo
def carregar_grafo(arquivo):
    arestas = []
    pesos = {}
    n_cabecalho = None

    with open(arquivo, 'r', encoding='utf-8-sig') as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith('c'):
                continue

            partes = linha.split()

            # Cabeçalho opcional
            if partes[0] == 'p' and len(partes) >= 3 and partes[2].isdigit():
                n_cabecalho = int(partes[2])
                continue

            # Remove prefixo "e" se existir
            if partes[0] == 'e':
                partes = partes[1:]

            if len(partes) < 2:
                continue

            try:
                u = int(partes[0])
                v = int(partes[1])
                w = float(partes[2]) if len(partes) >= 3 else 1.0
            except ValueError:
                continue

            if u != v:
                arestas.append((u, v))
                pesos[(min(u, v), max(u, v))] = w

    if not arestas:
        raise ValueError("Nenhuma aresta válida encontrada no arquivo.")

    # Mapeia vértices
    vertices = {v for e in arestas for v in e}
    if n_cabecalho:
        menor = min(vertices)
        base = 0 if menor == 0 else 1
        if base == 0:
            vertices |= set(range(0, n_cabecalho))
        else:
            vertices |= set(range(1, n_cabecalho + 1))

    lista_vertices = sorted(vertices)
    mapa = {v: i for i, v in enumerate(lista_vertices)}
    n = len(lista_vertices)
    adj = [set() for _ in range(n)]

    pesos_idx = {}
    for u, v in arestas:
        i, j = mapa[u], mapa[v]
        adj[i].add(j)
        adj[j].add(i)
        pesos_idx[(min(i, j), max(i, j))] = pesos[(min(u, v), max(u, v))]

    return n, adj, mapa, pesos_idx

# Algoritmos de coloração
def valido(adj, cores):
    """Verifica se a coloração é válida (nenhuma aresta tem mesmo rótulo nas duas pontas)."""
    for u in range(len(adj)):
        for v in adj[u]:
            if cores[u] == cores[v]:
                return False
    return True


def cores_usadas(cores):
    """
    Retorna número de cores distintas usadas ignorando -1 (vértices não coloridos).
    Se não houver cores válidas retorna 0.
    """
    if not cores:
        return 0
    usados = [c for c in cores if c != -1]
    return (max(usados) + 1) if usados else 0


def mostrar_colorido(cores, mapa, limite=10):
    """Imprime uma versão colorida (ANSI) se o grafo for pequeno."""
    if len(cores) > limite:
        print("(Ocultando coloração colorida, grafo grande)")
        return

    paleta = [
        "\033[31m", "\033[32m", "\033[33m", "\033[34m",
        "\033[35m", "\033[36m", "\033[91m", "\033[92m",
        "\033[93m", "\033[94m", "\033[95m", "\033[96m"
    ]
    reset = "\033[0m"

    # mapa: rótulo original -> índice ; inv: índice -> rótulo original
    inv = {v: u for u, v in mapa.items()}
    print("\nVertices coloridos:")
    for i, c in enumerate(cores):
        cor_ansi = paleta[c % len(paleta)] if c != -1 else ""
        label = inv.get(i, i)
        cor_text = f"cor {c}" if c != -1 else "sem cor"
        print(f"{cor_ansi}{label} -> {cor_text}{reset}")


def guloso(adj):
    n = len(adj)
    cores = [-1] * n
    for v in range(n):
        viz = {cores[w] for w in adj[v] if cores[w] != -1}
        cor = 0
        while cor in viz:
            cor += 1
        cores[v] = cor
    return cores


def welsh_powell(adj, mapa=None):
    n = len(adj)
    ordem = sorted(range(n), key=lambda v: len(adj[v]), reverse=True)
    cores = [-1] * n
    for v in ordem:
        viz = {cores[w] for w in adj[v] if cores[w] != -1}
        cor = 0
        while cor in viz:
            cor += 1
        cores[v] = cor
    return cores


def dsatur(adj):
    n = len(adj)
    cores = [-1] * n
    sat = [0] * n
    grau = [len(adj[v]) for v in range(n)]
    viz_cores = [set() for _ in range(n)]

    # inicial: escolhe vértice de maior grau
    v = max(range(n), key=lambda x: grau[x])
    cores[v] = 0
    for w in adj[v]:
        viz_cores[w].add(0)
        sat[w] = len(viz_cores[w])

    for _ in range(n - 1):
        candidatos = [i for i in range(n) if cores[i] == -1]
        if not candidatos:
            break
        v = max(candidatos, key=lambda x: (sat[x], grau[x]))
        cor = 0
        while cor in viz_cores[v]:
            cor += 1
        cores[v] = cor
        for w in adj[v]:
            if cores[w] == -1:
                viz_cores[w].add(cor)
                sat[w] = len(viz_cores[w])
    return cores


def forca_bruta(adj, limite=12):
    """
    Tenta encontrar coloração ótima por força bruta. Lança ValueError
    se n > limite para evitar explosão combinatória.
    """
    n = len(adj)
    if n > limite:
        raise ValueError(f"Força bruta bloqueada para n>{limite}")

    cores = [-1] * n

    def tenta(v, k):
        if v == n:
            return True
        proibidas = {cores[w] for w in adj[v] if cores[w] != -1}
        for c in range(k):
            if c in proibidas:
                continue
            cores[v] = c
            if tenta(v + 1, k):
                return True
            cores[v] = -1
        return False

    k = 1  # começa em 1 (caso grafo trivialmente 1-colorável)
    while True:
        cores[:] = [-1] * n
        if tenta(0, k):
            return cores
        k += 1
        if k > n:
            # pior caso: cada vértice com cor única
            return list(range(n))

# Análise automática dos resultados (Parte 2)
def prim(adj, pesos=None):
    """
    adj: lista de conjuntos de vizinhos
    pesos: dict {(u,v): peso}, se None, assume peso 1
    Retorna: lista de arestas MST, soma dos pesos
    """
    import heapq

    n = len(adj)
    if pesos is None:
        pesos = {(min(u, v), max(u, v)): 1 for u in range(n) for v in adj[u] if u < v}

    visitados = set()
    soma = 0.0
    mst_arestas = []

    # começa no vértice 0
    atual = 0
    visitados.add(atual)

    # inicializa heap com as arestas do primeiro vértice
    heap = [(pesos[(min(atual, v), max(atual, v))], atual, v) for v in adj[atual]]
    heapq.heapify(heap)

    while heap and len(visitados) < n:
        peso, u, v = heapq.heappop(heap)
        if v in visitados:
            continue

        visitados.add(v)
        soma += peso
        mst_arestas.append((u, v))

        for w in adj[v]:
            if w not in visitados:
                heapq.heappush(heap, (pesos.get((min(v, w), max(v, w)), 1), v, w))

    return mst_arestas, soma

def kruskal(n, arestas, pesos=None):
    """
    n: número de vértices
    arestas: lista de tuplas (u, v)
    pesos: dict {(u,v): peso}, se None, assume peso 1
    Retorna: lista de arestas MST e soma dos pesos
    """
    if pesos is None:
        pesos = {(min(u, v), max(u, v)): 1 for u, v in arestas}

    # ordena as arestas por peso
    arestas_ordenadas = sorted(arestas, key=lambda e: pesos.get((min(e), max(e)), 1))

    parent = list(range(n))

    def find(u):
        while parent[u] != u:
            parent[u] = parent[parent[u]]
            u = parent[u]
        return u

    def union(u, v):
        parent[find(u)] = find(v)

    mst_arestas = []
    soma = 0.0

    for u, v in arestas_ordenadas:
        if find(u) != find(v):
            union(u, v)
            mst_arestas.append((u, v))
            soma += pesos.get((min(u, v), max(u, v)), 1)

    return mst_arestas, soma

# Uteis
def medir(funcao, *args, **kwargs):
    inicio = time.perf_counter()
    res = funcao(*args, **kwargs)
    fim = time.perf_counter()
    return res, fim - inicio


def imprimir_tabela_resultados(resultados):
    print("\nResumo dos resultados:")
    print(f"{'Algoritmo':<12} {'Cores':>6} {'Tempo(s)':>12} {'Válido':>8}")
    print("-" * 44)
    for r in resultados:
        print(f"{r['alg']:<12} {r['cores']:>6} {r['tempo']:>12.6f} {str(r['valido']):>8}")
    print()


def salvar_csv_resultados(resultados, caminho):
    """
    Salva a lista de resultados (lista de dicionários) em CSV.
    Cada dicionário esperado conter: alg, cores, tempo, valido, (opcional) cores_map.
    """
    campos = ["alg", "cores", "tempo", "valido"]
    try:
        with open(caminho, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["algoritmo", "cores", "tempo", "valido"])
            for r in resultados:
                writer.writerow([r.get("alg"), r.get("cores"), r.get("tempo"), r.get("valido")])
        print(f"\nResultado salvo em CSV: {caminho}")
    except Exception as e:
        print(f"Erro ao salvar CSV em {caminho}: {e}", file=sys.stderr)


def rodar_em_lote(pasta, limite=12):
    if not os.path.isdir(pasta):
        print(f"Erro: a pasta '{pasta}' não existe.")
        return

    pasta = os.path.abspath(pasta)
    print(f"\nExecutando na pasta: {pasta}\n")

    funcoes = {
        "greedy": guloso,
        "welsh": lambda a: welsh_powell(a, None),
        "dsatur": dsatur,
        "brute": lambda a: forca_bruta(a, limite),
    }

    resultados_csv = []

    for arquivo in os.listdir(pasta):
        if not arquivo.endswith(".txt"):
            continue
        caminho = os.path.join(pasta, arquivo)
        try:
            n, adj, mapa = carregar_grafo(caminho)
        except Exception as e:
            print(f"Erro ao ler {arquivo}: {e}")
            continue

        print(f"\n--- {arquivo} ({n} vértices) ---")
        for nome, func in funcoes.items():
            if nome == "brute" and n > limite:
                print(f"Pular {nome} (n={n} > limite={limite})")
                continue
            try:
                cores, tempo = medir(func, adj)
            except ValueError as e:
                print(f"Erro em {nome}: {e}")
                continue
            k = cores_usadas(cores)
            valido_flag = valido(adj, cores)
            resultados_csv.append([arquivo, n, nome, k, tempo, valido_flag])
            print(f"{nome}: cores={k}, tempo={tempo:.6f}s, válido={valido_flag}")

    # salva arquivo CSV com resultados de lote
    try:
        with open("resultados_lote.csv", "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["arquivo", "vertices", "algoritmo", "cores", "tempo", "valido"])
            writer.writerows(resultados_csv)
        print("\nResultados salvos em 'resultados_lote.csv'.")
    except Exception as e:
        print(f"Erro ao salvar resultados_lote.csv: {e}")

    # ANÁLISE AUTOMÁTICA 
    print("\nIniciando análise dos resultados (Parte 2)...")
    try:
        df = le_resultados.carregar_resultados("resultados_lote.csv")
        le_resultados.gerar_graficos(df)
        le_resultados.gerar_relatorio_textual(df)
        print("\nAnálise concluída! Gráficos salvos:")
        print("   - grafico_tempo.png")
        print("   - grafico_cores.png")
        print("   - grafico_dispersao.png\n")
    except Exception as e:
        print(f"\nErro ao gerar análise automática: {e}\n")



# Execução principal
def main():
    parser = argparse.ArgumentParser(description="Coloração de Grafos + MST (Parte 1 + 2)")
    DEFAULT_GRAPH_DIR = "grafos"
    parser.add_argument("--batch", help="Executa todos os algoritmos em todos os grafos de uma pasta")
    parser.add_argument("-i", "--input", help="Arquivo do grafo")
    parser.add_argument("--algo", choices=["brute", "greedy", "welsh", "dsatur"])
    parser.add_argument("--compare", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--output", help="Salvar resultado (CSV)")
    parser.add_argument("--mst", action="store_true", help="Executa algoritmos de árvore geradora mínima (Prim e Kruskal)")
    args = parser.parse_args()

    if not args.batch and not args.input:
        parser.error("Use --batch para modo em lote ou -i/--input para grafo único.")

    if args.batch:
        rodar_em_lote(args.batch or DEFAULT_GRAPH_DIR, args.limit)
        return

    try:
        n, adj, mapa, pesos = carregar_grafo(args.input)
    except Exception as e:
        print("Erro ao ler o grafo:", e, file=sys.stderr)
        sys.exit(1)

    # Parte 1 - Coloração
    if not args.mst:
        funcoes = {
            "greedy": guloso,
            "welsh": welsh_powell,
            "dsatur": dsatur,
            "brute": lambda a: forca_bruta(a, args.limit),
        }

        if args.compare:
            ordem_exec = ["greedy", "welsh", "dsatur", "brute"]
            resultados = []
            for nome in ordem_exec:
                if nome == "brute" and n > args.limit:
                    print(f"Pular força bruta: grafo tem {n} vértices (> {args.limit}).")
                    continue
                func = funcoes[nome]
                print(f"\nExecutando {nome}...")
                cores, tempo = medir(func, adj)
                k = cores_usadas(cores)
                valido_flag = valido(adj, cores)
                resultados.append({
                    "alg": nome,
                    "cores": k,
                    "tempo": tempo,
                    "valido": valido_flag,
                    "cores_map": cores
                })
                print(f"{nome}: cores={k}, tempo={tempo:.6f}s, válido={valido_flag}")

            if resultados:
                imprimir_tabela_resultados(resultados)
            return

        if args.algo:
            if args.algo == "brute" and n > args.limit:
                print(f"Grafo tem {n} vértices (> {args.limit}). Use heurísticas ou aumente --limit.", file=sys.stderr)
                sys.exit(2)

            func = funcoes[args.algo]
            cores, tempo = medir(func, adj)
            k = cores_usadas(cores)
            print(f"Algoritmo: {args.algo}")
            print(f"Vertices: {n}")
            print(f"Cores usadas: {k}")
            print(f"Tempo: {tempo:.6f}s")

            if args.verify:
                print("Coloracao valida:", "sim" if valido(adj, cores) else "não")

            if args.show and n < 10:
                inv = {v: u for u, v in mapa.items()}
                print("\nVértice -> Cor")
                for i in range(n):
                    print(f"{inv[i]} -> {cores[i]}")
                print()
                mostrar_colorido(cores, mapa)

            if args.output:
                inv = {v: u for u, v in mapa.items()}
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write("vertice,cor\n")
                    for i in range(n):
                        f.write(f"{inv[i]},{cores[i]}\n")
                print(f"\nResultado salvo em: {args.output}")

    # Parte 2 - MST
    if args.mst:
        print(f"\nExecutando MST (Prim e Kruskal) para {args.input} ({n} vértices)")

        # Prepara lista de arestas para MST
        arestas = [(u,v) for u in range(n) for v in adj[u] if u < v]

        mst_funcoes = {
            "prim": lambda: prim(adj, pesos),
            "kruskal": lambda: kruskal(n, arestas, pesos)
        }

        resultados_mst = []

        for nome, func in mst_funcoes.items():
            inicio = time.perf_counter()
            S, soma = func()
            fim = time.perf_counter()
            tempo = fim - inicio
            print(f"{nome}: soma = {soma}, tempo = {tempo:.6f}s")

            if args.show and n < 10:
                print(f"Arestas MST ({nome}):")
                for u,v in S:
                    print(f"{u} - {v}")

            # Salva resultados em lista
            resultados_mst.append({
                "alg": nome,
                "soma_arestas": soma,
                "tempo": tempo,
                "num_arestas": len(S)
            })

        # Salva CSV
        csv_file = args.output or "resultados_mst.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["algoritmo", "soma_arestas", "tempo", "num_arestas"])
            for r in resultados_mst:
                writer.writerow([r["alg"], r["soma_arestas"], r["tempo"], r["num_arestas"]])
        print(f"\nResultados MST salvos em: {csv_file}")



if __name__ == "__main__":
    main()
