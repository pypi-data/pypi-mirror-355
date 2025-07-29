from setuptools import setup, find_packages

setup(
    name="game-vision",
    version="1.0.0",
    author="Alex",
    author_email="thettboy11@gmail.com",
    description="Easy-to-use wrapper for training and inference of game object detection models (YOLOv8)",
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "torch>=1.9.0",
        "ultralytics>=8.0.0",
        "opencv-python>=4.5.0",
        "numpy>=1.21.0",
        "onnxruntime>=1.12.0",
    ],
    extras_require={
        "gpu": ["onnxruntime-gpu>=1.12.0"],
        "dev": [
            "pytest>=6.0",
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=0.900",
        ],
    },
    keywords="yolo object-detection computer-vision game ai machine-learning",
)