from setuptools import setup, find_packages

setup(
    name="nonebot_plugin_NobleDuel",
    version="0.3.18",
    description="一个贵族决斗小游戏",
    author="cikasaaa",
    author_email="2058550737@qq.com",
    packages=find_packages(),
    install_requires=[
        "nonebot2>=2.3.0",
        "nonebot-adapter-onebot>=2.0.0",
        "nonebot-plugin-alconna>=0.55.0",
        "nonebot-plugin-apscheduler>=0.5.0",
        "nonebot_plugin_localstore>=0.7.0",
    ],
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: AsyncIO",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Communications :: Chat",
        "Topic :: Games/Entertainment",
    ],
)