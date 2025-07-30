from setuptools import setup, find_packages

setup(
    name="color_zone_processor",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "Pillow>=10.2.0",
        "numpy>=1.26.4",
        "scipy>=1.12.0",
    ],
    entry_points={
        'console_scripts': [
            'color-zone-processor=color_zone_processor.cli:main',
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool for processing image color zones",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/color_zone_processor",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
) 