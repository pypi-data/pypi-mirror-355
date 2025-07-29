from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="proxy_fetcher",
    version="0.1.0",
    author="Ilmir Gilmiiarov",
    author_email="ilmir_gf@mail.ru",
    description="Package for fetching and validating working HTTP/HTTPS proxies from multiple sources",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ilmir-muslim/proxy-fetcher",
    packages=find_packages(),
    install_requires=[
        'requests>=2.25.1',
        'tqdm>=4.60.0',
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Internet :: Proxy Servers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    keywords='proxy scraper validator fetcher',
    project_urls={
        "Bug Reports": "https://github.com/ilmir-muslim/proxy-fetcher/issues",
        "Source": "https://github.com/ilmir-muslim/proxy-fetcher",
    },
)