from setuptools import setup, find_packages

# Read the README.md file with UTF-8 encoding
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="django-modern-captcha",
    version="0.1.2",
    author="Manish Sharma",
    author_email="manis.shr@gmail.com",
    description="A modern CAPTCHA solution for Django with behavioral analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/manish-codefyn/django-modern-captcha",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Django>=3.2",
        "numpy",
        "scikit-learn",
    ],
    classifiers=[
        "Framework :: Django",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">=3.6",
)