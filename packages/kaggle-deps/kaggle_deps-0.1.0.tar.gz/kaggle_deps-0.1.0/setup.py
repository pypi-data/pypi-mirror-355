# setup.py
from setuptools import setup, find_packages

setup(
    name='kaggle_deps',
    version='0.1.0',
    packages=find_packages(), 
    install_requires=[
        'fsspec==2023.9.1',
        'huggingface_hub==0.17.3',
        'datasets==2.13.1',
        'torch==2.0.1',
        'torchvision==0.15.2',
        'torchaudio==2.0.2',
        'transformers==4.30.1',
        'evaluate==0.4.0',
        'accelerate==0.21.0',
        'gradio==3.34.0',
        'rouge-score==0.1.2',
        'bert-score==0.3.13',
        'pyarrow==11.0.0',
        'pandas==1.5.3',
        'timm==0.9.2',
        'cloud-tpu-client==0.10',
        'kagglehub[pandas-datasets]==0.3.12',
        'tokenizers==0.13.3',
    ],
    author='mehtab',
    author_email='arbabali000001@gmail.com',
)
