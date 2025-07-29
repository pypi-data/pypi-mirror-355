import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="jvQuant",
    url="http://jvQuant.com",
    version="1.20.2",
    author="jvQuant",
    author_email="help@jvQuant.com",
    license="MIT License",
    install_requires = "websocket",
    description="Community Package Integrated Websocket quotations , CTP , and Database Client. 社区版量化工具包，集成WebSocket实时行情、CTP柜台以及在线数据库终端。支持量化交易平台所有功能，支持本地或云端使用。",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3',
)