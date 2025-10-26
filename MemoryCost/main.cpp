#include <chrono>
#include <cstdio>
#include <cstring>
#include <cstdlib>

//  Plataforma 
#ifdef _WIN32
    #include <windows.h>
    #include <psapi.h>
#endif

class Timer {
public:
    Timer() : start(std::chrono::steady_clock::now()) {}
    double GetElapsed() const {
        auto end = std::chrono::steady_clock::now();
        auto dur = end - start;
        return std::chrono::duration_cast<std::chrono::nanoseconds>(dur).count() * 1e-9;
    }
private:
    std::chrono::steady_clock::time_point start;
};

//  Função de page faults 
void MostrarPageFaults(const char* etapa) {
#ifdef _WIN32
    PROCESS_MEMORY_COUNTERS_EX pmc;
    if (GetProcessMemoryInfo(GetCurrentProcess(), (PROCESS_MEMORY_COUNTERS*)&pmc, sizeof(pmc))) {
        printf("[%s] Page Faults: %zu (Working Set: %.2f MB)\n",
               etapa, (size_t)pmc.PageFaultCount, pmc.WorkingSetSize / 1048576.0);
    } else {
        printf("[%s] Page Faults: (não disponível no Windows sem psapi)\n", etapa);
    }
#endif
}

//  Função para aquecer CPU 
void BusyWait(int ms) {
    auto end = std::chrono::steady_clock::now() + std::chrono::milliseconds(ms);
    while (std::chrono::steady_clock::now() < end) {}
}

//  Função principal de benchmark 
void FastMeasure() {
    printf("Busy waiting to raise CPU frequency...\n");
    BusyWait(500);

    const size_t sizes[] = {
        1 * 1024 * 1024,
        8 * 1024 * 1024,
        32 * 1024 * 1024,
        128 * 1024 * 1024,
        512 * 1024 * 1024
    };
    const int numSizes = sizeof(sizes) / sizeof(sizes[0]);

    for (int s = 0; s < numSizes; ++s) {
        size_t bufSize = sizes[s];
        int iterationCount = (bufSize > 256 * 1024 * 1024) ? 10 : 50;

        printf("\n==== Testando alocacao de %zu MB ====\n", bufSize / (1024 * 1024));

        // 1) Alocar e liberar
        {
            Timer timer;
            for (int i = 0; i < iterationCount; ++i) {
                int *p = new int[bufSize / sizeof(int)];
                delete[] p;
            }
            printf("%1.4f s to allocate %zu MB %d times.\n",
                   timer.GetElapsed(), bufSize / (1024 * 1024), iterationCount);
            MostrarPageFaults("Após alloc/free");
        }

        // 2) Escrever repetidamente
        int *p = new int[bufSize / sizeof(int)]();
        {
            Timer timer;
            for (int i = 0; i < iterationCount; ++i)
                memset(p, 1, bufSize);
            printf("%1.4f s to write %zu MB %d times.\n",
                   timer.GetElapsed(), bufSize / (1024 * 1024), iterationCount);
            MostrarPageFaults("Após escrita");
        }

        // 3) Ler repetidamente
        {
            Timer timer;
            long long sum = 0;
            for (int i = 0; i < iterationCount; ++i)
                for (size_t j = 0; j < bufSize / sizeof(int); ++j)
                    sum += p[j];
            printf("%1.4f s to read %zu MB %d times (sum=%lld)\n",
                   timer.GetElapsed(), bufSize / (1024 * 1024), iterationCount, sum);
            MostrarPageFaults("Após leitura");
        }
        delete[] p;
    }
}

int main() {
    FastMeasure();
    return 0;
}