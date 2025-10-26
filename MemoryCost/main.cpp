#include <chrono>
#include <cstdio>
#include <cstring>
#include <string>
#include <fstream>
#include <sstream>
#include <ctime>

#ifdef _WIN32
#include <windows.h>
#include <psapi.h>
#else
#include <unistd.h>
#endif

class Timer
{
public:
    Timer() : start(std::chrono::steady_clock::now()) {}
    double GetElapsed() const
    {
        auto end = std::chrono::steady_clock::now();
        auto duration = end - start;
        return std::chrono::duration_cast<std::chrono::nanoseconds>(duration).count() * 1.e-9;
    }

private:
    std::chrono::steady_clock::time_point start;
};


// Funções para medir page faults (Windows / Linux)
struct PFInfo
{
    long minor = 0;
    long major = 0;
};

PFInfo GetPageFaults()
{
    PFInfo info;
#ifdef _WIN32
    PROCESS_MEMORY_COUNTERS_EX pmc;
    if (GetProcessMemoryInfo(GetCurrentProcess(), (PROCESS_MEMORY_COUNTERS *)&pmc, sizeof(pmc)))
    {
        info.minor = (long)pmc.PageFaultCount;
        info.major = 0; // Windows não distingue minor/major
    }
#else
    std::ifstream file("/proc/self/stat");
    std::string line;
    if (file.is_open() && std::getline(file, line))
    {
        size_t open = line.find('(');
        size_t close = line.rfind(')');
        if (open != std::string::npos && close != std::string::npos && close > open)
        {
            std::string after = line.substr(close + 2);
            std::istringstream ss(after);
            std::string tmp;
            // pular 7 campos
            for (int i = 0; i < 7; ++i)
                ss >> tmp;
            ss >> info.minor; // campo 10
            ss >> tmp;        // cminflt
            ss >> info.major; // campo 12
        }
    }
#endif
    return info;
}


// CSV helper
void AppendCSV(const std::string &step, size_t mb, int iters, double totalTime, const PFInfo &pf)
{
    static bool headerWritten = false;
    static std::ofstream csv("results.csv", std::ios::app);

    if (!headerWritten)
    {
        csv << "timestamp,os,mb,iters,step,total_time_s,minflt,majflt\n";
        headerWritten = true;
    }

    // Data e hora
    std::time_t now = std::time(nullptr);
    char buf[64];
    std::strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%S", std::localtime(&now));

#ifdef _WIN32
    std::string os = "Windows";
#else
    std::string os = "Linux";
#endif

    csv << buf << "," << os << "," << mb << "," << iters << ","
        << step << "," << totalTime << ","
        << pf.minor << "," << pf.major << "\n";

    csv.flush();
}


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
        size_t mb = bufSize / (1024 * 1024);

        printf("\nTestando %zu MB\n", mb);

        // 1) alocar e liberar
        {
            PFInfo before = GetPageFaults();
            Timer timer;
            for (int i = 0; i < iterationCount; ++i)
            {
                int *p = new int[bufSize / sizeof(int)];
                delete[] p;
            }
            double elapsed = timer.GetElapsed();
            PFInfo after = GetPageFaults();
            AppendCSV("alloc_free", mb, iterationCount, elapsed,
                      {after.minor - before.minor, after.major - before.major});
        }

        // 2) alocar e medir delete separadamente
        {
            PFInfo before = GetPageFaults();
            Timer timer;
            double deleteTime = 0.0;
            for (int i = 0; i < iterationCount; ++i)
            {
                int *p = new int[bufSize / sizeof(int)];
                Timer deleteTimer;
                delete[] p;
                deleteTime += deleteTimer.GetElapsed();
            }
            double elapsed = timer.GetElapsed();
            PFInfo after = GetPageFaults();
            AppendCSV("alloc_delete", mb, iterationCount, elapsed,
                      {after.minor - before.minor, after.major - before.major});
        }

        // 3) escrever repetidamente
        int *p = new int[bufSize / sizeof(int)]();
        {
            PFInfo before = GetPageFaults();
            Timer timer;
            for (int i = 0; i < iterationCount; ++i)
                memset(p, 1, bufSize);
            double elapsed = timer.GetElapsed();
            PFInfo after = GetPageFaults();
            AppendCSV("write", mb, iterationCount, elapsed,
                      {after.minor - before.minor, after.major - before.major});
        }

        // 4) ler repetidamente
        {
            PFInfo before = GetPageFaults();
            Timer timer;
            int sum = 0;
            for (int i = 0; i < iterationCount; ++i)
                for (size_t j = 0; j < bufSize / sizeof(int); ++j)
                    sum += p[j];
            double elapsed = timer.GetElapsed();
            PFInfo after = GetPageFaults();
            AppendCSV("read", mb, iterationCount, elapsed,
                      {after.minor - before.minor, after.major - before.major});
        }
        delete[] p;

        // 5) alocar, escrever e liberar
        {
            PFInfo before = GetPageFaults();
            Timer timer;
            for (int i = 0; i < iterationCount; ++i)
            {
                int *p = new int[bufSize / sizeof(int)];
                memset(p, 1, bufSize);
                delete[] p;
            }
            double elapsed = timer.GetElapsed();
            PFInfo after = GetPageFaults();
            AppendCSV("alloc_write_delete", mb, iterationCount, elapsed,
                      {after.minor - before.minor, after.major - before.major});
        }

        // 6) alocar, ler e liberar
        {
            PFInfo before = GetPageFaults();
            Timer timer;
            int sum = 0;
            for (int i = 0; i < iterationCount; ++i)
            {
                int *p = new int[bufSize / sizeof(int)];
                for (size_t j = 0; j < bufSize / sizeof(int); ++j)
                    sum += p[j];
                delete[] p;
            }
            double elapsed = timer.GetElapsed();
            PFInfo after = GetPageFaults();
            AppendCSV("alloc_read_delete", mb, iterationCount, elapsed,
                      {after.minor - before.minor, after.major - before.major});
        }
    }
}


int main()
{
    FastMeasure();
    printf("\nResultados salvos em 'results.csv'\n");
    return 0;
}
