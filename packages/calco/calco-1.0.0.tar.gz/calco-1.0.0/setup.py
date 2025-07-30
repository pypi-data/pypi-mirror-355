from setuptools import setup

setup(
    name="calco",
    version="1.0.0",
    author="Your Name",
    author_email="you@example.com",
    description="High-performance math library for Python (powered by C)",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    license="MIT",
    url="https://calcolib.netlify.app",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: C",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Topic :: Scientific/Engineering :: Mathematics"
    ],
    python_requires='>=3.8',
    packages=["calco"],
    include_package_data=True,
)
