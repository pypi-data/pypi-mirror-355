from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='aiguardrail',
    version='0.1.0',
    author='Shubham Mhaske',
    author_email='mhaskeshubham1200@gmail.com',
    description='Guardrails for evaluating AI-generated content',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License'
    ],
    python_requires='>=3.7',
    install_requires=[
        'pandas',
        'tiktoken',
        'detoxify',
        'textstat',
    ],
)