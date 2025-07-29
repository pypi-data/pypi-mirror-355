from setuptools import setup, find_packages

setup(
    name="b3dmath",
    version="0.1.1",
    description="Utility 3D Math and Geometry library for Python.",
    author="Your Name",
    author_email="bailey@bailey3d.com",
    url="https://github.com/bailey3d/b3dmath",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "scipy",
    ],
    python_requires=">=3.7",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
