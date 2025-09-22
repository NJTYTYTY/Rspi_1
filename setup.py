from setuptools import setup, find_packages

setup(
    name="shrimp-farm-cloud-controller",
    version="1.0.0",
    description="Shrimp Farm Cloud Controller API",
    python_requires=">=3.11,<3.13",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.115.6",
        "uvicorn[standard]==0.32.1",
        "pydantic==2.10.4",
        "python-multipart==0.0.12",
        "python-dotenv==1.0.1"
    ],
    entry_points={
        "console_scripts": [
            "cloud-app=cloud_app:main",
        ],
    },
)
