from setuptools import setup, find_packages

setup(
    name="yolo-screen-stream",
    version="1.0.0",
    description="Screen capture and YOLO object detection library",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "ultralytics>=8.0.0",
        "opencv-python>=4.5.0",
        "torch>=1.9.0",
        "numpy>=1.21.0",
        "mss>=6.1.0",
        "Pillow>=8.0.0",
    ],
)