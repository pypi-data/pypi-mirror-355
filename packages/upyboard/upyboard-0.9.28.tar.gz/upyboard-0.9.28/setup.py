import os
import re
import platform
from setuptools import setup, find_packages, Command

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

def read_version(package_name):
    package_path = os.path.join(package_name, '__init__.py')
    with open(package_path, 'r', encoding='utf-8') as f:
        version_file = f.read()

    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        if platform.system() == 'Linux' or platform.system() == 'Darwin':
            os.system('rm -rf ./build ./dist ./*.egg-info') 
        elif platform.system() == 'Windows':
            os.system('rmdir /s /q build dist upyboard.egg-info') 

PACKAGE_NAME = 'upyboard'

setup(
    name=PACKAGE_NAME,
    version=read_version(PACKAGE_NAME),
    description='This is a CLI tool for MicroPython-based embedded systems.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='chanmin.park',
    author_email='devcamp@gmail.com',
    url='https://github.com/planxstudio/upyboard',
    install_requires=['click', 'pyserial', 'genlib', 'mpy-cross'],
    packages=find_packages(),
    keywords=['micropython', 'pyserial', 'genlib'],
    python_requires='>=3.10',
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    cmdclass={
        'clean': CleanCommand,  # clean 명령어를 추가
    },
    entry_points={
        'console_scripts': [
            'upy = upyboard.upy:main',    
        ],
    },
)
