echo "### GC ###"
clang-15 -DWITHMAIN -o gc gc.c
clang-15 -shared -fPIC -o gc.so gc.c
clang-15 -emit-llvm -S gc.c

echo "### PTX ###"
llc-15 -mcpu=sm_20 kernel.ll -o kernel.ptx
clang++-15 -DWITHMAIN sample.cpp -o sample -O2 -g -I/usr/local/cuda-5.5/include -lcuda
clang++-15 sample.cpp -fPIC -shared -o sample.so -O2 -g -I/usr/local/cuda-5.5/include -lcuda

echo "### RUN CUDA ###"
./sample

echo "### RUN PYTHON ###"
python test.py
