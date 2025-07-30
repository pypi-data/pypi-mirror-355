from setuptools import find_packages, setup

setup(
    name="desim-python",
    version="0.0.1",
    description="A Discrete Event Simulation (DES) framework for modeling systems where state changes occur at discrete points in time.",
    long_description=open("./readme.md").read(),
    long_description_content_type="text/markdown",
    author="Luis Enrique Arias Curbelo",
    author_email="lariasec@gmail.com",
    url="https://github.com/larias95/desim-python",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Games/Entertainment :: Simulation",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Mathematics",
    ],
    license="MIT License",
    license_files=["LICENSE"],
    keywords=["DES", "discrete", "event", "queue", "simulation", "statistics"],
)
