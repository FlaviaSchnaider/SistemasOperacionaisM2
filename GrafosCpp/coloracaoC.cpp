#include <iostream>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <string>
#include <vector>
#include <map>
#include <set>
#include <optional>
#include <algorithm>
#include <numeric>
#include <queue>
#include <functional>
#include <tuple>
#include <chrono>
using namespace std;
using Clock = chrono::steady_clock;

// ESTRUTURAS E FUNÇÕES DE UTILIDADE
struct Timer {
    Clock::time_point start = Clock::now();
    double elapsed() const {
        return chrono::duration<double>(Clock::now() - start).count();
    }
    void reset() { start = Clock::now(); }
};

// Lê grafo de arquivo (aceita formato DIMACS)
tuple<int, vector<set<int>>, map<int,int>, map<pair<int,int>, double>> carregar_grafo(const string &arquivo) {
    vector<pair<int,int>> arestas;
    map<pair<int,int>, double> pesos;
    ifstream fin(arquivo);
    if (!fin.is_open()) throw runtime_error("Erro ao abrir arquivo: " + arquivo);

    string linha;
    optional<int> n_cabecalho;
    while (getline(fin, linha)) {
        if (linha.empty() || linha[0] == 'c') continue;
        stringstream ss(linha);
        string token; ss >> token;
        if (token == "p") {
            string tipo; int n;
            ss >> tipo >> n;
            n_cabecalho = n;
            continue;
        }
        if (token == "e") ss >> token; // remove prefixo e

        int u, v; double w = 1.0;
        if (!(stringstream(token) >> u)) continue;
        if (!(ss >> v)) continue;
        ss >> w;

        if (u != v) {
            arestas.emplace_back(u, v);
            pesos[{min(u,v), max(u,v)}] = w;
        }
    }
    if (arestas.empty()) throw runtime_error("Nenhuma aresta válida encontrada.");

    set<int> vertices;
    for (auto &e : arestas) {
        vertices.insert(e.first);
        vertices.insert(e.second);
    }

    if (n_cabecalho) {
        int menor = *vertices.begin();
        int base = (menor == 0) ? 0 : 1;
        if (base == 0) for (int i = 0; i < *n_cabecalho; ++i) vertices.insert(i);
        else for (int i = 1; i <= *n_cabecalho; ++i) vertices.insert(i);
    }

    vector<int> lista(vertices.begin(), vertices.end());
    map<int,int> mapa;
    for (int i=0;i<(int)lista.size();++i) mapa[lista[i]] = i;

    int n = lista.size();
    vector<set<int>> adj(n);
    map<pair<int,int>, double> pesos_idx;
    for (auto &e : arestas) {
        int i = mapa[e.first], j = mapa[e.second];
        adj[i].insert(j); adj[j].insert(i);
        pesos_idx[{min(i,j), max(i,j)}] = pesos[{min(e.first,e.second), max(e.first,e.second)}];
    }

    return {n, adj, mapa, pesos_idx};
}

bool valido(const vector<set<int>> &adj, const vector<int> &cores) {
    for (int u=0; u<(int)adj.size(); ++u)
        for (int v : adj[u])
            if (cores[u]==cores[v]) return false;
    return true;
}

int cores_usadas(const vector<int> &cores) {
    int mx = -1;
    for (int c : cores) mx = max(mx, c);
    return mx+1;
}

// ALGORITMOS DE COLORAÇÃO
vector<int> guloso(const vector<set<int>> &adj) {
    int n = adj.size();
    vector<int> cores(n,-1);
    for (int v=0; v<n; ++v) {
        set<int> viz;
        for (int w: adj[v]) if (cores[w]!=-1) viz.insert(cores[w]);
        int c=0; while (viz.count(c)) ++c;
        cores[v]=c;
    }
    return cores;
}

vector<int> welsh_powell(const vector<set<int>> &adj) {
    int n = adj.size();
    vector<int> ordem(n); iota(ordem.begin(), ordem.end(), 0);
    sort(ordem.begin(), ordem.end(), [&](int a,int b){ return adj[a].size()>adj[b].size(); });
    vector<int> cores(n,-1);
    for (int v: ordem) {
        set<int> viz;
        for (int w: adj[v]) if (cores[w]!=-1) viz.insert(cores[w]);
        int c=0; while (viz.count(c)) ++c;
        cores[v]=c;
    }
    return cores;
}

vector<int> dsatur(const vector<set<int>> &adj) {
    int n = adj.size();
    vector<int> cores(n,-1), grau(n), sat(n,0);
    vector<set<int>> viz_cores(n);
    for (int i=0;i<n;++i) grau[i]=adj[i].size();

    int v = max_element(grau.begin(), grau.end())-grau.begin();
    cores[v]=0;
    for (int w: adj[v]) { viz_cores[w].insert(0); sat[w]=viz_cores[w].size(); }

    for (int step=1; step<n; ++step) {
        vector<int> candidatos;
        for (int i=0;i<n;++i) if (cores[i]==-1) candidatos.push_back(i);
        if (candidatos.empty()) break;
        v = *max_element(candidatos.begin(), candidatos.end(), [&](int a,int b){
            if (sat[a]!=sat[b]) return sat[a]<sat[b];
            return grau[a]<grau[b];
        });
        int c=0; while (viz_cores[v].count(c)) ++c;
        cores[v]=c;
        for (int w: adj[v]) if (cores[w]==-1) { viz_cores[w].insert(c); sat[w]=viz_cores[w].size(); }
    }
    return cores;
}

// MST — Prim e Kruskal
pair<vector<pair<int,int>>, double> prim(const vector<set<int>> &adj, const map<pair<int,int>,double> &pesos) {
    int n=adj.size();
    vector<int> visitado(n,0);
    vector<pair<int,int>> mst;
    double soma=0;
    visitado[0]=1;
    using Edge = tuple<double,int,int>;
    priority_queue<Edge,vector<Edge>,greater<Edge>> pq;
    for (int v: adj[0]) pq.push({pesos.at({min(0,v),max(0,v)}),0,v});

    while(!pq.empty() && mst.size()<n-1){
        auto [w,u,v]=pq.top(); pq.pop();
        if(visitado[v]) continue;
        visitado[v]=1; mst.push_back({u,v}); soma+=w;
        for(int x: adj[v]) if(!visitado[x]) pq.push({pesos.at({min(v,x),max(v,x)}),v,x});
    }
    return {mst,soma};
}

pair<vector<pair<int,int>>, double> kruskal(int n, const vector<pair<int,int>> &arestas, const map<pair<int,int>,double> &pesos){
    vector<int> pai(n); iota(pai.begin(),pai.end(),0);
    function<int(int)> find=[&](int u){return pai[u]==u?u:pai[u]=find(pai[u]);};
    auto unite=[&](int a,int b){pai[find(a)]=find(b);};

    vector<pair<int,int>> mst;
    double soma=0;
    vector<pair<pair<int,int>,double>> ord;
    for(auto &e: arestas) ord.push_back({e,pesos.at({min(e.first,e.second),max(e.first,e.second)})});
    sort(ord.begin(),ord.end(),[](auto &a,auto &b){return a.second<b.second;});
    for(auto &x: ord){
        auto [u,v]=x.first; double w=x.second;
        if(find(u)!=find(v)){ unite(u,v); mst.push_back({u,v}); soma+=w; }
    }
    return {mst,soma};
}

int main(int argc, char **argv){
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    if(argc<3){
        cerr << "Uso: ./coloracao <arquivo> <algoritmo> [--mst]\n";
        return 1;
    }

    string arquivo = argv[1];
    string alg = argv[2];
    bool mst_mode = (alg == "mst" || (argc>=4 && string(argv[3])=="--mst"));

    try {
        int n; vector<set<int>> adj; map<int,int> mapa; map<pair<int,int>,double> pesos;
        tie(n,adj,mapa,pesos) = carregar_grafo(arquivo);

        if(!mst_mode){
            vector<int> cores;
            Timer t;
            if(alg=="greedy") cores=guloso(adj);
            else if(alg=="welsh") cores=welsh_powell(adj);
            else if(alg=="dsatur") cores=dsatur(adj);
            else { cerr<<"Algoritmo invalido.\n"; return 2; }
            double tempo=t.elapsed();
            cout<<"Vertices: "<<n<<"\n";
            cout<<"Cores usadas: "<<cores_usadas(cores)<<"\n";
            cout<<"Tempo: "<<tempo<<"s\n";
            cout<<"Coloracao valida: "<<(valido(adj,cores)?"sim":"não")<<"\n";
        } else {
            cout<<"Executando Prim e Kruskal...\n";
            vector<pair<int,int>> arestas;
            for(int i=0;i<n;++i) for(int j: adj[i]) if(i<j) arestas.push_back({i,j});
            auto [mst1,s1]=prim(adj,pesos);
            auto [mst2,s2]=kruskal(n,arestas,pesos);
            cout<<"Prim: soma="<<s1<<"\n";
            cout<<"Kruskal: soma="<<s2<<"\n";
        }

    } catch(exception &e){
        cerr<<"Erro: "<<e.what()<<"\n";
        return 3;
    }

    return 0;
}
