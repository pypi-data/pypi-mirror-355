from setuptools import setup, find_packages



setup(
    name="yolo-screen-stream",
    version="1.0.1",  # Увеличили версию
    author="Alex",
    author_email="thettboy11@gmail.com",
    description="Screen capture and YOLO object detection library",
    long_description_content_type="text/markdown",
    packages=["yolo_stream"],  # ИСПРАВЛЕНО: явно указываем пакет
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "ultralytics>=8.0.0",
        "opencv-python>=4.5.0",
        "torch>=1.9.0",
        "numpy>=1.21.0",
        "mss>=6.1.0",
        "Pillow>=8.0.0",
    ]
)