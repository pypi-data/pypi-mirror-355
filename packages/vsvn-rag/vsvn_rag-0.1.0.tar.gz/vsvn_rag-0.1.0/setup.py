from setuptools import setup, find_packages
with open("README.md", encoding="utf-8", errors="ignore") as f:
    long_description = f.read()

setup(
    name="vsvn_rag",
    version="0.1.0",
    packages=find_packages(include=["vsvn_rag", "vsvn_rag.*"]),
    install_requires=[
        "PyYAML",
        "PyPDF2",
        "numpy",
        "scikit-learn"
    ],
    author="VSVN_AI TEAM",
    description="Modular Retrieval-Augmented Generation System",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
