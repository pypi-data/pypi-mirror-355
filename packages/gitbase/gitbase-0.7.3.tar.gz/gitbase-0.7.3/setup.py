from setuptools import setup, find_packages

setup(
    name="gitbase",
    version="0.7.3",
    author="Taireru LLC",
    author_email="tairerullc@gmail.com",
    description="GitBase is a custom database system built with Python and powered by GitHub, treating GitHub repositories as databases. It features encryption using the cryptography library, ensuring data security.",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/TaireruLLC/gitbase",
    packages=find_packages(),
    install_requires=[
        "requests",
        "cryptography",
        "altcolor>=0.0.5",
        "moviepy",
        "fancyutil>=0.0.4",
        "numpy",
        "opencv-python",
        "pyaudio",
        "wave",
        "jsonpickle"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    license="MIT",
)
