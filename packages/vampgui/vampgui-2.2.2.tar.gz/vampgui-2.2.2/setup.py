

import sys
from setuptools import setup, find_packages
from vampgui.version import __version__

# Custom function to check for tkinter

print("****************************************************************\n")
print("tkinter is not installed. Please install it to use this package.")
print("")
print("For Debian-based systems, run:    sudo apt-get install python3-tk")
print("For Red Hat-based systems, run:   sudo dnf install python3-tkinter")
print("For Arch Linux, run: sudo pacman -S tk")
print("\n*****************************************************************")


setup(
    name='vampgui',
    version=__version__,
    author='G. Benabdellah',
    author_email='ghlam.benabdellah@gmail.com',
    description='Interface graphic to vampire "Atomistic simulation of magnetic materials"',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/ghlam14/vampgui',  # Replace with your project's URL
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'vampgui': ['background.png', 'logo.png', 'vam.ico'],
    },
    install_requires=[
        'matplotlib',
        'Pillow',
        'numpy',
        'tk',
        'pymatgen',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
    entry_points={
        'console_scripts': [
            'vampgui = vampgui.main:main',
        ],
    },
)


