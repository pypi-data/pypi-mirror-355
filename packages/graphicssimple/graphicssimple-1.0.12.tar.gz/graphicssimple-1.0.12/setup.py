from setuptools import setup, find_packages

setup(
     name = 'graphicssimple',
     version = '1.0.12',
     description = 'A simple graphics wrapper on top of tkinter',
     long_description = '#SimpleGraphics is a friendly tool for learning to code and make art. It is a free and open-source Python library built by an inclusive, nurturing community. SimpleGraphics is a Python library that provides high level drawing functionality to help you quickly create simulations and interactive art using Python.',
     author = 'Ben Stephenson',
     author_email = 'ben.stephenson@ucalgary.ca',
     maintainer =  'Grygoriy Gromko',
     maintainer_email = 'gr.gromko@gmail.com',
     url= 'https://cspages.ucalgary.ca/~bdstephe/217_P24/',
     packages=find_packages(),
     classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.1.0',
)
