from setuptools import setup, find_packages

setup(
    name="HelperFunctionsLiam167",
    version="0.1.1",
    description="Reusable Plotly/Colab helpers for analytics",
    author="Liam Crowley",
    packages=find_packages(),
    install_requires=[
        "plotly", "pandas"   # Add any other dependencies here
    ],
)
