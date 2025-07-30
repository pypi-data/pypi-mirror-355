from setuptools import setup, find_packages

setup(
    name="face_mask_sdk",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "opencv-python>=4.8.0",
        "numpy>=1.24.0",
        "ultralytics>=8.0.0",
        "mediapipe>=0.10.0",
        "scipy>=1.10.0",
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="一个用于口罩检测的Python SDK",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/face_mask_sdk",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
