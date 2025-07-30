from setuptools import setup, find_packages

setup(
    name="zidfsouno",            # 包名（pip install 时用）
    version="0.1.0",              # 版本号（每次发布需更新）
    author="ouhuahu",
    author_email="362654377@qq.com",
    description="工具包",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),     # 自动包含所有包
    install_requires=[            # 依赖项（如 "requests>=2.25.0"）
        "pandas",
    ],
    python_requires=">=3.10",      # Python 版本要求
    license="MIT"                # 协议（需与 LICENSE 文件一致）
    # url="https://github.com/your/repo",  # 项目主页
)