from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="oss_internal",
    version="1.4.1",
    author="Guan Xingjian",
    author_email="edward@aputure.com",
    description="An internal utility package for Aliyun OSS operations.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_dir={"": "src"}, 
    packages=find_packages(where="src"),
    install_requires=[
        "aiohappyeyeballs",
        "aiohttp",
        "aiosignal",
        "aliyun-python-sdk-core",
        "aliyun-python-sdk-kms",
        "asyncio-oss",
        "attrs",
        "certifi",
        "cffi",
        "charset-normalizer",
        "crcmod",
        "cryptography",
        "frozenlist",
        "idna",
        "jmespath",
        "multidict",
        "oss2",
        "propcache",
        "pycparser",
        "pycryptodome",
        "requests",
        "six",
        "tqdm",
        "urllib3",
        "yarl"
    ],
    python_requires=">=3.11",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
    ],
    license="MIT",
    include_package_data=True
)
