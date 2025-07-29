from setuptools import setup, find_packages

setup(
    name="stage0_py_utils",
    version="0.1.8",
    description="A utility package for stage0 microservices",
    author="Mike Storey",
    author_email="leave_me_alone@example.com",
    license="MIT",
    packages=find_packages(where="."),
    python_requires=">=3.8",
    install_requires=[
        "flask",
        "pymongo",
        "discord",
        "ollama"
    ],
    extras_require={
        "dev": ["black", "pytest", "unittest"]
    },
    include_package_data=True,
)