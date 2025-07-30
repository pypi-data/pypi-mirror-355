from setuptools import setup, find_packages

setup(
    name="blackbox_schemas",
    version="0.1.1",
    packages=find_packages(),
    install_requires=[
        "pydantic>=1.9.0,<2.0.0",
    ],
    author="BlackBox AI",
    author_email="sandeep.makwana@odm.ai",
    description="Consolidated Pydantic schemas for BlackBox LLM operations",
    keywords="pydantic, schemas, llm, blackbox",
    url="https://github.com/isandeepmakwana1/blackbox-schemas",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.8",
)
