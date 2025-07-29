from setuptools import setup, find_packages

setup(
    name="aiZero",
    version="0.0.7a0",
    author="emhang",
    author_email="emhang@126.com",
    description="A simple and easy-to-use library that connects to common artificial intelligence interfaces, "
                "allowing for quick development of local web applications. "
                "It includes mainstream AI capabilities such as LLM text interaction, image understanding, audio understanding, image generation, speech recognition, and speech synthesis.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    python_requires='>=3.6',
    install_requires=[
        "flask>=3.0.0",
        "requests",
        "dashscope==1.13.6",
        "openai>=1.0.0",
        "pillow"
    ]
)
