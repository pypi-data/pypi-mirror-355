from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="llm7_image",
    version="2025.6.141317",
    author="Eugene Evstafev",
    author_email="support@llm7.io",
    description=(
        "Tiny helper that calls the LLM7 image-generation endpoint and "
        "returns the final image URL."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/chigwell/llm7_image",
    packages=find_packages(exclude=("tests",)),
    install_requires=["requests>=2.31,<3.0"],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    license="MIT",
    tests_require=["unittest"],
    test_suite="tests",
)
