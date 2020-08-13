from PyQt5 import uic
import glob

for fname in glob.glob("*.ui"):
    fin = open(fname, 'r')
    fout = open(fname.replace(".ui", ".py"), 'w')
    uic.compileUi(fin, fout, execute=False)
    fin.close()
    fout.close()
