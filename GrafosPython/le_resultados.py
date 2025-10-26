import pandas as pd
import matplotlib.pyplot as plt

def carregar_resultados(arquivo_csv):
    """Lê o arquivo CSV e retorna um DataFrame pandas."""
    return pd.read_csv(arquivo_csv)

def analisar_resultados(df):
    """Calcula estatísticas médias por algoritmo."""
    resumo = df.groupby("algoritmo").agg({
        "tempo": "mean",
        "cores": "mean",
        "valido": lambda x: (x == True).mean() * 100
    }).rename(columns={"valido": "taxa_validez (%)"})
    resumo["tempo"] = resumo["tempo"] * 1000  # converter segundos para milissegundos
    return resumo

def gerar_graficos(df):
    """Gera gráficos de análise comparativa."""
    resumo = analisar_resultados(df)

    # Tempo médio por algoritmo
    plt.figure()
    resumo["tempo"].plot(kind="bar", title="Tempo médio por algoritmo (ms)")
    plt.ylabel("Tempo (ms)")
    plt.tight_layout()
    plt.savefig("grafico_tempo.png")
    plt.close()

    # Cores médias por algoritmo
    plt.figure()
    resumo["cores"].plot(kind="bar", title="Número médio de cores por algoritmo", color="orange")
    plt.ylabel("Número médio de cores")
    plt.tight_layout()
    plt.savefig("grafico_cores.png")
    plt.close()

    # Dispersão: vértices × tempo
    plt.figure()
    for alg in df["algoritmo"].unique():
        subset = df[df["algoritmo"] == alg]
        plt.scatter(subset["vertices"], subset["tempo"] * 1000, label=alg)
    plt.title("Tempo de execução x Número de vértices")
    plt.xlabel("Vértices")
    plt.ylabel("Tempo (ms)")
    plt.legend()
    plt.tight_layout()
    plt.savefig("grafico_dispersao.png")
    plt.close()

def gerar_relatorio_textual(df):
    """Imprime no terminal um resumo interpretativo."""
    resumo = analisar_resultados(df)
    print("\n=== Análise dos Resultados ===\n")
    print(resumo)
    print("\nConclusões:")
    mais_rapido = resumo["tempo"].idxmin()
    menos_cores = resumo["cores"].idxmin()
    mais_preciso = resumo["taxa_validez (%)"].idxmax()
    print(f"Algoritmo mais rápido: {mais_rapido} ({resumo.loc[mais_rapido, 'tempo']:.3f} ms)")
    print(f"Algoritmo com menos cores: {menos_cores} ({resumo.loc[menos_cores, 'cores']:.2f})")
    print(f"Algoritmo mais consistente: {mais_preciso} ({resumo.loc[mais_preciso, 'taxa_validez (%)']:.1f}%)")

if __name__ == "__main__":
    arquivo = "resultados_lote.csv"
    df = carregar_resultados(arquivo)
    gerar_graficos(df)
    gerar_relatorio_textual(df)
    print("\nGráficos salvos: grafico_tempo.png, grafico_cores.png, grafico_dispersao.png")
