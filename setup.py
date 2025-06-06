from setuptools import setup, find_packages

setup(
    name="shl_recommender",
    version="0.1",
    packages=find_packages(include=['app*']),
    install_requires=[
        "fastapi",
        "streamlit",
        "google-generativeai",
        "pinecone",
        "python-dotenv"
    ],
)