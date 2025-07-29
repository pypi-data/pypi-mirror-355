from setuptools import setup, find_packages
import os

# Читаем README если есть
here = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = 'YOLO8-based screen capture and object detection library'

setup(
    name="yolo-screen-stream",
    version="1.0.7",
    author="Alex",
    author_email="thettboy11@gmail.com",
    description="YOLO8-based screen capture and object detection library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "ultralytics>=8.0.0",
        "opencv-python>=4.5.0",
        "numpy>=1.21.0",
        "mss>=6.1.0",
        "Pillow>=8.0.0",
    ],
)