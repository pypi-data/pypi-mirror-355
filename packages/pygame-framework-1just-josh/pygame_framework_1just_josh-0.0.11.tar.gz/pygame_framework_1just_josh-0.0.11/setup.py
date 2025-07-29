from setuptools import setup, find_packages

setup(
    name="pygame_framework_1just_josh",
    version="0.0.11",
    author="Joshua - jjboy2245",
    description="this is a simple pygame wrapper for advanced game features with less boilerplate",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    package_data={"":["assets/*"]},
    include_package_data=True,
    license="Apache-2.0",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
    ],
    python_requires=">=3.7",
    install_requires=[
        "pygame-ce",
        "msgpack",
        "cryptography",
    ],
)