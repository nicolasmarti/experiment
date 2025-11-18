#include <iostream>
#include <fstream>
#include <cassert>
#include "cuda.h"


void checkCudaErrors(CUresult err) {
  assert(err == CUDA_SUCCESS);
}

/// main - Program entry point
int exec_kernel(unsigned long int n) {
  CUdevice    device;
  CUmodule    cudaModule;
  CUcontext   context;
  CUfunction  function;
  CUlinkState linker;
  int         devCount;

  // CUDA initialization
  checkCudaErrors(cuInit(0));
  checkCudaErrors(cuDeviceGetCount(&devCount));
  checkCudaErrors(cuDeviceGet(&device, 0));

  char name[128];
  checkCudaErrors(cuDeviceGetName(name, 128, device));
  std::cout << "Using CUDA Device [0]: " << name << "\n";

  int devMajor, devMinor;
  checkCudaErrors(cuDeviceComputeCapability(&devMajor, &devMinor, device));
  std::cout << "Device Compute Capability: "
            << devMajor << "." << devMinor << "\n";
  if (devMajor < 2) {
    std::cerr << "ERROR: Device 0 is not SM 2.0 or greater\n";
    return 1;
  }

  std::ifstream t("kernel.ptx");
  if (!t.is_open()) {
    std::cerr << "kernel.ptx not found\n";
    return 1;
  }
  std::string str((std::istreambuf_iterator<char>(t)),
		  std::istreambuf_iterator<char>());

  // Create driver context
  checkCudaErrors(cuCtxCreate(&context, 0, device));

  // Create module for object
  checkCudaErrors(cuModuleLoadDataEx(&cudaModule, str.c_str(), 0, 0, 0));

  // Get kernel function
  checkCudaErrors(cuModuleGetFunction(&function, cudaModule, "kernel"));

  // Device data
  CUdeviceptr devBufferA;
  CUdeviceptr devBufferB;
  CUdeviceptr devBufferC;

  checkCudaErrors(cuMemAlloc(&devBufferA, sizeof(float)*n));
  checkCudaErrors(cuMemAlloc(&devBufferB, sizeof(float)*n));
  checkCudaErrors(cuMemAlloc(&devBufferC, sizeof(float)*n));

  float* hostA = new float[n];
  float* hostB = new float[n];
  float* hostC = new float[n];

  // Populate input
  for (unsigned i = 0; i != n; ++i) {
    hostA[i] = (float)i;
    hostB[i] = (float)(2*i);
    hostC[i] = 0.0f;
  }

  checkCudaErrors(cuMemcpyHtoD(devBufferA, &hostA[0], sizeof(float)*n));
  checkCudaErrors(cuMemcpyHtoD(devBufferB, &hostB[0], sizeof(float)*n));


  unsigned blockSizeX = n;
  unsigned blockSizeY = 1;
  unsigned blockSizeZ = 1;
  unsigned gridSizeX  = 1;
  unsigned gridSizeY  = 1;
  unsigned gridSizeZ  = 1;

  // Kernel parameters
  void *KernelParams[] = { &devBufferA, &devBufferB, &devBufferC };

  std::cout << "Launching kernel\n";

  // Kernel launch
  checkCudaErrors(cuLaunchKernel(function, gridSizeX, gridSizeY, gridSizeZ,
                                 blockSizeX, blockSizeY, blockSizeZ,
                                 0, NULL, KernelParams, NULL));

  // Retrieve device data
  checkCudaErrors(cuMemcpyDtoH(&hostC[0], devBufferC, sizeof(float)*n));


  std::cout << "Results:\n";
  for (unsigned i = 0; i != n; ++i) {
    std::cout << hostA[i] << " + " << hostB[i] << " = " << hostC[i] << "\n";
  }


  // Clean up after ourselves
  delete [] hostA;
  delete [] hostB;
  delete [] hostC;

  // Clean-up
  checkCudaErrors(cuMemFree(devBufferA));
  checkCudaErrors(cuMemFree(devBufferB));
  checkCudaErrors(cuMemFree(devBufferC));
  checkCudaErrors(cuModuleUnload(cudaModule));
  checkCudaErrors(cuCtxDestroy(context));

  return 0;
}

extern "C" int exec(unsigned long int n) {
  return exec_kernel(n);  
}

#ifdef WITHMAIN

int main(int argc, char **argv){
  return exec_kernel(16);
}

#endif
