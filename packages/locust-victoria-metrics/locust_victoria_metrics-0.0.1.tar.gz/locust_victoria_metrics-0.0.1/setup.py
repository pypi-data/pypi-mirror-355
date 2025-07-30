from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="locust-victoria-metrics",
    version="0.0.1",
    description="A Locust plugin to extract test results and push metrics to Victoria Metrics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Didit Setiawan",
    author_email="didit@pintu.co.id",
    url="https://github.com/dsetiawan230294/locust-victoria-metrics",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "locust>=2.29.1",
    ],
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    keywords=["locust", "loadtest", "metrics", "victoria-metrics", "locust-plugin"],
    license="MIT",
    include_package_data=True,
    project_urls={
        "Bug Tracker": "https://github.com/dsetiawan230294/locust-victoria-metrics/issues",
        "Source Code": "https://github.com/dsetiawan230294/locust-victoria-metrics",
    },
)
