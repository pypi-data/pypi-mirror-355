from setuptools import setup, find_packages

setup(
    name="dvoice-tts",
    version="1.0.3",
    description="Python client for DVoice TTS API",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Khabib Sharopov",
    author_email="habibsharopov501@gmail.com",
    url="https://github.com/khabib-developer/dvoice-tts-python",
    packages=find_packages(),
    install_requires=["requests", "websocket-client"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">=3.6",
)
