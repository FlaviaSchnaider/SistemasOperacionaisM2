#include <chrono>
#include <cstdio>
#include <cstring>

class Timer
{
public:
    Timer() : start(std::chrono::steady_clock::now()) {}

    double GetElapsed()
    {
        auto end = std::chrono::steady_clock::now();
        auto duration = end - start;
        return std::chrono::duration_cast<std::chrono::nanoseconds>(duration).count() * 1.e-9;
    }

private:
    std::chrono::steady_clock::time_point start;

    Timer(const Timer &) = delete;
    Timer &operator=(const Timer &) = delete;
};

// Função para “aquecer” a CPU antes do benchmark
void BusyWait(int ms)
{
    auto end = std::chrono::steady_clock::now() + std::chrono::milliseconds(ms);
    while (std::chrono::steady_clock::now() < end)
    {
    }
}

// Função principal de benchmark
void FastMeasure()
{
    printf("Busy waiting to raise the CPU frequency...\n");
    BusyWait(500);

    const size_t sizes[] = {
        1 * 1024 * 1024,    // 1 MB
        8 * 1024 * 1024,    // 8 MB
        32 * 1024 * 1024,   // 32 MB
        128 * 1024 * 1024,  // 128 MB
        512 * 1024 * 1024,  // 512 MB
        1024 * 1024 * 1024, // 1 GB
    };
    const int numSizes = sizeof(sizes) / sizeof(sizes[0]);

    for (int s = 0; s < numSizes; ++s)
    {
        size_t bufSize = sizes[s];
        int iterationCount = (bufSize > 512 * 1024 * 1024) ? 10 : 50;

        printf("\nTestando alocacao de %zu MB \n", bufSize / (1024 * 1024));

        // 1) alocar e liberar
        {
            Timer timer;
            for (int i = 0; i < iterationCount; ++i)
            {
                int *p = new int[bufSize / sizeof(int)];
                delete[] p;
            }
            printf("%1.4f s to allocate %zu MB %d times.\n", timer.GetElapsed(), bufSize / (1024 * 1024), iterationCount);
        }

        //  2) alocar e medir delete separadamente
        {
            Timer timer;
            double deleteTime = 0.0;
            for (int i = 0; i < iterationCount; ++i)
            {
                int *p = new int[bufSize / sizeof(int)];
                Timer deleteTimer;
                delete[] p;
                deleteTime += deleteTimer.GetElapsed();
            }
            printf("%1.4f s to allocate %zu MB %d times (%1.4f s to delete).\n",
                   timer.GetElapsed(), bufSize / (1024 * 1024), iterationCount, deleteTime);
        }

        //  3) escrever repetidamente
        int *p = new int[bufSize / sizeof(int)]();
        {
            Timer timer;
            for (int i = 0; i < iterationCount; ++i)
            {
                memset(p, 1, bufSize);
            }
            double mbps = (double)(bufSize * iterationCount) / (1024.0 * 1024.0) / timer.GetElapsed();
            printf("%1.4f s to write %zu MB %d times (%1.2f MB/s)\n",
                   timer.GetElapsed(), bufSize / (1024 * 1024), iterationCount, mbps);
        }

        //  4) ler repetidamente
        {
            Timer timer;
            int sum = 0;
            for (int i = 0; i < iterationCount; ++i)
            {
                for (size_t index = 0; index < bufSize / sizeof(int); ++index)
                {
                    sum += p[index];
                }
            }
            double mbps = (double)(bufSize * iterationCount) / (1024.0 * 1024.0) / timer.GetElapsed();
            printf("%1.4f s to read %zu MB %d times (%1.2f MB/s), sum = %d\n",
                   timer.GetElapsed(), bufSize / (1024 * 1024), iterationCount, mbps, sum);
        }
        delete[] p;

        //  5) alocar, escrever e liberar
        {
            Timer timer;
            double deleteTime = 0.0;
            for (int i = 0; i < iterationCount; ++i)
            {
                int *p = new int[bufSize / sizeof(int)];
                memset(p, 1, bufSize);
                Timer deleteTimer;
                delete[] p;
                deleteTime += deleteTimer.GetElapsed();
            }
            printf("%1.4f s to allocate and write %zu MB %d times (%1.4f s to delete).\n",
                   timer.GetElapsed(), bufSize / (1024 * 1024), iterationCount, deleteTime);
        }

        //  6) alocar, ler e liberar
        {
            Timer timer;
            int sum = 0;
            for (int i = 0; i < iterationCount; ++i)
            {
                int *p = new int[bufSize / sizeof(int)];
                for (size_t index = 0; index < bufSize / sizeof(int); ++index)
                {
                    sum += p[index];
                }
                delete[] p;
            }
            printf("%1.4f s to allocate and read %zu MB %d times, sum = %d.\n",
                   timer.GetElapsed(), bufSize / (1024 * 1024), iterationCount, sum);
        }
    }
}

int main()
{
    FastMeasure();
    return 0;
}