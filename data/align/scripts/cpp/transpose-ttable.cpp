#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
using namespace std;

double p[11000][11000];

int main() {
	for (int i = 0; i < 11000; i++)
		for (int j = 0; j < 11000; j++)
			p[i][j] = -1;
	ifstream fin0("t0");
	ifstream fin1("t1");
	ofstream fout("ttable");
	int a,b;
	while (fin0 >> a >> b) {
		if (a == 0) fin0 >> p[0][b];
		else break;
	}
	double tmp;
	while (fin1 >> a >> b) {
		if (b != 0) fin1 >> p[b][a];
		else fin1 >> tmp;
	}
	for (int i = 0; i < 11000; i++)
		for (int j = 0; j < 11000; j++)
			if (p[i][j] > 0.000000001)
				fout << i << " " << j << " " << p[i][j] << endl;
	return 0;
}
