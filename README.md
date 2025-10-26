## Trabalho M2 – Paginação e Page Fault  
**Disciplina:** Sistemas Operacionais  
**Aluna:** Flávia Schnaider e Gregori da Luz Maciel 

---

## Descrição

Este trabalho tem como objetivo **analisar o comportamento da memória e da paginação** em um ambiente multitarefa, avaliando o impacto de diferentes padrões de acesso à memória, tamanhos de alocação e quantidade de threads.

O projeto foi desenvolvido em **Python**, e inclui:
- Um simulador de carga de memória (`memory_cost.py`);
- A reutilização do projeto da **M1** (`sender.py` e `worker.py`) como cenário prático para análise de **demanda de páginas de memória** e **concorrência entre processos**.

---

Como o trabalho da M1 rodava apenas no Linux, neste trabalho usamos o terminal Ubuntu no Windows.
```bash
wsl --install
cd /mnt/c/SistemasOperacionais_M2/tmp
```




### Ferramentas
- Bibliotecas padrão: `time`, `threading`, `argparse`, `bytearray`
- Ambiente: **Ubuntu via WSL**
- Monitoramento:
  - **Linux:** `ps -o min_flt,maj_flt <PID>`, `top`, `vmstat`
  - **Windows:** Process Explorer  



#### Execução – Parte 1:

```bash
python memory_cost.py --mb 64 --iters 50 --pattern write --threads 1
```

### Alocação + escrita + liberação com 4 threads
```bash
python memory_cost.py --mb 256 --iters 30 --pattern alloc_write_free --threads 4
```

### Leitura de grandes blocos em 8 threads
```bash
python memory_cost.py --mb 512 --iters 20 --pattern read --threads 8
```



## Execução – Parte 2:
### Iniciar o Worker
```bash
python worker.py /tmp/imgpipe saida.pgm negativo 4
```

### Enviar uma imagem com o sender 
```bash
python sender.py /tmp/imgpipe entrada_grande.png
```

### Executar o memory_cost.py em paralelo
```bash
python memory_cost.py --mb 512 --iters 50 --pattern alloc_write_free --threads 4
```
