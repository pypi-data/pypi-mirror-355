import os
import shutil
import sys
from setuptools import setup, find_packages
from setuptools.command.build_py import build_py
from wheel.bdist_wheel import bdist_wheel 


class CustomBdistWheel(bdist_wheel):
    def finalize_options(self):
        super().finalize_options()
        self.root_is_pure = False # platform-specific wheel
        self.plat_name = 'manylinux2014_x86_64' 
        

class CustomBuildPy(build_py):
    def run(self):
        super().run()

        build_lib = self.build_lib
        vidrial_build_path = os.path.join(build_lib, 'vidrial')
        
        source_release = os.path.join('vidrial', 'release')
        build_release = os.path.join(vidrial_build_path, 'release')
        
        # Build cache directories (temporary, for wheel only)
        build_jit_cache = os.path.join(vidrial_build_path, 'jit', '.jit_cache')
        build_timing_cache = os.path.join(vidrial_build_path, 'jit', '.timing_cache')
        
        if os.path.exists(source_release):
            os.makedirs(build_jit_cache, exist_ok=True)
            os.makedirs(build_timing_cache, exist_ok=True)
            
            # Copy from source release/ to build jit_cache/
            for item in os.listdir(source_release):
                item_path = os.path.join(source_release, item)
                if os.path.isdir(item_path):
                    dst_path = os.path.join(build_jit_cache, item)
                    shutil.copytree(item_path, dst_path)
                elif item.endswith('.yaml'):
                    dst_path = os.path.join(build_timing_cache, item)
                    shutil.copy2(item_path, dst_path)
            
            shutil.rmtree(build_release)
            print("Organized kernels for wheel packaging")

        # Cleanup tests
        for dir, _, files in os.walk(vidrial_build_path):
            for file in files:
                if os.path.basename(file) in ("test.py", "conftest.py", "test.cu"):
                    os.remove(os.path.join(dir, file))

setup(
    packages=find_packages(),
    cmdclass={
        'build_py': CustomBuildPy,
        'bdist_wheel': CustomBdistWheel,
    },
    zip_safe=False,
)