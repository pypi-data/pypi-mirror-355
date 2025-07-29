from setuptools import find_packages, setup

# Read DOCS.md for long description
try:
    with open("DOCS.md", "r", encoding="utf-8") as f:
        long_description = f.read()
except:
    long_description = ""

setup(
    name="lam-cli",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "backoff>=2.2.1",
        "certifi>=2024.12.14",
        "charset-normalizer>=3.3.2",
        "click>=8.1.7",
        "idna>=3.7",
        "logtail-python>=0.2.2",
        "monotonic>=1.6",
        "msgpack>=1.0.8",
        "posthog>=3.4.0",
        "psutil>=5.9.0",
        "python-dateutil>=2.8.2",
        "requests>=2.32.3",
        "six>=1.16.0",
        "urllib3>=2.2.2",
    ],
    entry_points={
        "console_scripts": [
            "laminar=lam.lam:lam",
        ],
    },
    python_requires=">=3.9",
    license="GPLv3",
    author="Laminar Run, Inc.",
    author_email="connect@laminar.run",
    description="Secure data transformation tool supporting JQ and JavaScript (Bun)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/laminar-run/lam",
    project_urls={
        "Documentation": "https://docs.laminar.run",
        "Source": "https://github.com/laminar-run/lam",
        "Issue Tracker": "https://github.com/laminar-run/lam/issues",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Build Tools",
    ],
    keywords="laminar, api, integration, transformation, json, jq, javascript, bun",
)
