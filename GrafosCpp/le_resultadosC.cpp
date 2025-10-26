#include <iostream>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <string>
#include <vector>
#include <map>
#include <algorithm>
using namespace std;

struct Registro {
    string arquivo, algoritmo;
    int vertices; double cores, tempo; bool valido;
};

int main() {
    ifstream fin("resultados_lote.csv");
    if (!fin.is_open()) {
        cerr << "Arquivo resultados_lote.csv não encontrado.\n";
        return 1;
    }

    string line;
    getline(fin,line); // cabeçalho
    vector<Registro> dados;
    while (getline(fin,line)) {
        stringstream ss(line);
        string arq, verts, alg, cores, tempo, val;
        getline(ss, arq, ',');
        getline(ss, verts, ',');
        getline(ss, alg, ',');
        getline(ss, cores, ',');
        getline(ss, tempo, ',');
        getline(ss, val, ',');
        Registro r;
        r.arquivo=arq; r.algoritmo=alg;
        r.vertices=stoi(verts);
        r.cores=stod(cores);
        r.tempo=stod(tempo);
        r.valido=(val=="True" || val=="1" || val=="true");
        dados.push_back(r);
    }

    map<string, vector<Registro>> grupos;
    for (auto &r: dados) grupos[r.algoritmo].push_back(r);

    cout << "\nAnálise dos Resultados\n";
    cout << left << setw(12) << "Algoritmo" << setw(15) << "Tempo Medio(ms)"
         << setw(15) << "Cores Medias" << setw(15) << "Validez(%)" << "\n";
    cout << string(60,'-') << "\n";

    for (auto &[alg, vec]: grupos) {
        double t=0,c=0,v=0;
        for(auto &r:vec){t+=r.tempo;c+=r.cores;v+=r.valido;}
        t/=vec.size(); c/=vec.size(); v=v*100.0/vec.size();
        cout << setw(12)<<alg<<setw(15)<<t*1000<<setw(15)<<c<<setw(15)<<v<<"\n";
    }

    return 0;
}
