# triwild-compute-wn
Process 20k TriWild data set to add winding numbers to .MSH files

## building on hpc
```
git clone --recursive https://github.com/Spenbert02/triwild-compute-wn.git
cd triwild-compute-wn
mkdir build
cmake ..
make
```

To update submodules once already cloned:
```
git submodule update --init --recursive
```