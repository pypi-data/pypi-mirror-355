from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='gemini-helper',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'python-dotenv',
        'openai-agent-sdk',
    ],
    description='Gemini SDK helper for OpenAI Agent SDK',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Huriya Syed',
    author_email='huriyasyed462@gmail.com',
    url='https://github.com/huriyasyed/gemini-helper',
    license='MIT', 
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License"
    ],
    python_requires='>=3.7',
)
