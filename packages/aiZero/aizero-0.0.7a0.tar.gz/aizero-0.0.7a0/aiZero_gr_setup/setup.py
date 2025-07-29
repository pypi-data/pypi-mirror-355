from setuptools import setup, find_packages

setup(
    name="aiZero_gr",
    version="0.0.3a3",
    author="emhang",
    author_email="emhang@126.com",
    description="A simple and easy-to-use library that connects to common artificial intelligence interfaces (powered by Gradio), "
                "allowing for quick development of local web applications. "
                "It includes mainstream AI capabilities such as LLM text interaction, image understanding, audio understanding, image generation, speech recognition, and speech synthesis.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    python_requires='>=3.10',
    install_requires=[
        "gradio>=5.5.0",
        "requests",
        "dashscope>=1.20.0"
    ]
)
