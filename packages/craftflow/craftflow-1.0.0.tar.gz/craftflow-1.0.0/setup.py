from setuptools import setup, find_packages

setup(
    name="craftflow",
    version="1.0.0",
    description="A powerful workflow orchestration framework",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="DengHui Zhang",
    author_email="zdh13141@gmail.com",
    url="https://github.com/scholarlords/CraftFlow",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    keywords="workflow orchestration async rag agent mcp",
    python_requires=">=3.8",
    install_requires=[],
    extras_require={
        "dev": ["pytest", "twine", "wheel"],
    },
    entry_points={
        "console_scripts": [
            "craftflow-demo=craftflow.examples.rag_system:run_rag_example",
            "craftflow-multiagent=craftflow.examples.multi_agent_system:run_multi_agent_example",
        ],
    },
    include_package_data=True,
)
