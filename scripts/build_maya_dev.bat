@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
set SRC=E:\oss\maya-dev
set BLD=E:\oss\maya-dev\build
set CM=E:\oss\project-maya\.venv\Scripts\cmake.exe
set NJ=E:\oss\project-maya\.venv\Scripts\ninja.exe
if not exist %BLD%\build.ninja (
  %CM% -G Ninja -DCMAKE_MAKE_PROGRAM=%NJ% -S %SRC% -B %BLD% -DCMAKE_BUILD_TYPE=Release -DSTRATA_ENABLE_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=120 -DSTRATA_NATIVE_EXPERTS=ON -DSTRATA_BUILD_TESTS=OFF "-DCMAKE_CUDA_COMPILER=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.1\bin\nvcc.EXE" "-DCUDAToolkit_ROOT=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.1" -DSTRATA_GGML_DIR=E:\oss\project-maya\third_party\llama.cpp || exit /b 3
)
%CM% --build %BLD% --target strata -j %1 || exit /b 4
