from setuptools import setup, find_packages

setup(
    name="pyLOTlib",  # This is the name of your package as it will appear on PyPI
    version="0.1.4",  # Start with an initial version number
    author="Alex Cloninger",  # Your name or your organization/company name
    author_email="acloninger@ucsd.edu",  # Your contact email
    description="PyLOT provides general functionality for applying out-of-the-box machine learning methods to point-cloud-valued data or, more generally, measure-valued data.  PyLOT allows the user to embed, classify, dimension reduce, and generate data.",  # A brief description
    long_description=open("README.md").read(),  # You can include a README.md for a detailed description
    long_description_content_type="text/markdown",  # Specify the content type for long description (Markdown)
    url="https://github.com/ACloninger/pyLOT",  # URL to your GitHub repository
    packages=find_packages(),  # Automatically find all packages in your project
    install_requires=[
                    "numpy",
                    "imbalanced-learn",  # 'imblearn' is often referred to as 'imbalanced-learn' on PyPI
                    "scikit-learn",  # 'sklearn' is actually installed as 'scikit-learn'
                    "tensorflow",
                    "matplotlib",
                    "pot"],  # List your dependencies here. For example: ["numpy", "torch"]
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  # Your license type
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',  # Minimum Python version requirement
)

