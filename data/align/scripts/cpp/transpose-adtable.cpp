#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
using namespace std;

double a[220][220][220];
double d[220][220][220];

int main() {
	ifstream fin0("a1");
	ifstream fin1("d1");
	ofstream fout0("atable");
	ofstream fout1("dtable");
	for (int i = 0; i < 220; i++) for (int j = 0; j < 220; j++) for (int k = 0; k < 220; k++) { a[i][j][k] = -1; d[i][j][k] = -1; }
	
	int a1,a2,a3,a4;
	double d1;
	while (fin0 >> a1 >> a2 >> a3 >> a4) {
		fin0 >> d1;
		a[a1][a2][a3] = d1;
	}
	while (fin1 >> a1 >> a2 >> a3 >> a4) {
		fin1 >> d1;
		d[a1][a2][a4] = d1;
	}
	for (int i = 0; i < 110; i++) for (int j = 0; j < 110; j++) for (int k = 0; k < 110; k++) if (d[k][j][i] > 0) {
		fout0 << j << " " << k << " " << i << " " << "100" << " " << d[k][j][i] << endl;
	}
	for (int i = 0; i < 110; i++) for (int j = 0; j < 110; j++) for (int k = 0; k < 110; k++) if (a[k][j][i] > 0) {
		fout1 << j << " " << k << " "  << "100" << " " << i << " " << a[k][j][i] << endl;
	}
	return 0;
}
