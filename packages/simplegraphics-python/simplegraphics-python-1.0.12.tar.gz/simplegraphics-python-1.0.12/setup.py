from setuptools import setup, find_packages
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
setup(
     name = 'simplegraphics-python',
     version = '1.0.12',
     description = 'A simple graphics wrapper on top of tkinter',
     long_description=long_description,
     long_description_content_type="text/markdown",
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
