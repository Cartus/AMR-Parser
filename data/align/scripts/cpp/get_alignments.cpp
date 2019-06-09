#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <map>
#include <algorithm>
#include <sstream>

using namespace std;

vector<string> tokens;
vector<int> level;
int tree[1000][100];
int tree2[1000][100];
int deg[1000];
int p[1000];

string int2str(int a) {
	stringstream ss;
	ss << a;
	string s;
	ss >> s;
	return s;
}

void addchild(int par,int ch) {
	p[ch] = par;
	tree[par][deg[par]] = ch;
	deg[par]++;	
}

ofstream fout("Alignments.keep");

string print_tree(int r,string l) {
	string s = "";
	string tkn = tokens[r];
	for (int i = 0; i < tkn.size(); i++) if (tkn[i] == '~') {
		string stkn = tkn.substr(i+3);
		string al = "";
		for (int j = 0; j < stkn.length(); j++) {
			if (stkn[j] == ',') {
				if (tkn[0] == ':') fout << al << "-" << l << ".r" << " ";
				else fout << al << "-" << l << " ";
				al = "";
			}
			else al = al + stkn[j];
		}
		if (tkn[0] == ':') fout << al << "-" << l << ".r" << " ";
		else fout << al << "-" << l << " ";
		break;
	}
	if (tokens[r] == "/") {	s = s+"/ "+print_tree(tree[r][0],l); return s;}
	if (tokens[r][0] == ':') {	s = s+tokens[r]+" "+print_tree(tree[r][0],l); return s;}
	if (deg[r] > 0) {s = s + "(";}
	s = s+ tokens[r] + " ";
	for (int i = 0; i < deg[r]; i++) {
		if (i == 0) s = s + " " + print_tree(tree[r][i],l);
		else s = s + " " + print_tree(tree[r][i],l+"."+int2str(i));
	}
	if (deg[r] > 0) {s = s + ")";}
	return s;
}

void make_tree() {
	int par = 0;	
	for (int i = 1; i < tokens.size(); i++) {
		//cout << i << " " << tokens.size() << endl;
		if (level[i]<level[i-1]) {
			while (level[par] > level[i]) {par = p[par];}
			par = p[par];
		}
		if (level[i]>level[i-1]) {par = i;}
		if (tokens[i] == "/" || tokens[i][0] == ':') {addchild(par,i); addchild(i,i+1);}
	}
}

void parse(string s0) {
	vector<string> v;
    std::size_t prev = 0, pos;
    while ((pos = s0.find_first_of(" ()", prev)) != std::string::npos)
    {
		if (pos > prev){
			if (s0[prev] == '\"') {
				pos = prev+1;
				while (s0[pos] != '\"') pos++;
				while (s0[pos] != ')' && s0[pos] != '(' && s0[pos] != ' ') pos++;
			}
            v.push_back(s0.substr(prev, pos-prev));
		}
        if (s0[pos] == '(') v.push_back("(");
		if (s0[pos] == ')') v.push_back(")");
        prev = pos+1;
    }
    if (prev < s0.length())
        v.push_back(s0.substr(prev, std::string::npos));
	tokens.clear();
	level.clear();
	int l = 0;
	for (int i = 1; i < v.size(); i++) {
		if (v[i] == "(") {l++; continue;}
		if (v[i] == ")") {l--; continue;}
		tokens.push_back(v[i]); level.push_back(l);
	}
	for (int i = 0; i < 1000; i++) {deg[i] = 0; p[i] = -1;}
	make_tree();
}

int main() {
	ifstream fin("AMR_Aligned.keep");
	string s,tmp;
	
	while (getline(fin,s)) {
		getline(fin,s);
		parse(s);
		getline(fin,s);
		print_tree(0,"1");
		fout << endl;
	}
	return 0;
}
