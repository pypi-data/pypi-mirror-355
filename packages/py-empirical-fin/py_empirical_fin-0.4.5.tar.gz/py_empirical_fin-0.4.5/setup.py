import setuptools

with open("README.md","r") as fh:
    long_description = fh.read()

setuptools.setup(
    # 包的分发名称，使用字母、数字、_、-
    name="py_empirical_fin",
     # 版本号, 版本号规范：https://www.python.org/dev/peps/pep-0440/
    version="0.4.5",
    # 作者名
    author="lester-zhang",
     # 作者邮箱
    author_email="lester.zhang99@gmail.com",
    # 包的简介描述
    description="tools for empirical finance",
    # 包的详细介绍(一般通过加载README.md)
    long_description=long_description,
    # 和上条命令配合使用，声明加载的是markdown文件
    long_description_content_type="text/markdown",
    # 项目开源地址
    url="",
     # 如果项目由多个文件组成，我们可以使用find_packages()自动发现所有包和子包，而不是手动列出每个包，在这种情况下，包列表将是example_pkg
    packages=setuptools.find_packages(),
    # 关于包的其他元数据(metadata)
    classifiers=[
         # 该软件包仅与Python3兼容
        "Programming Language :: Python :: 3",
        # 根据MIT许可证开源
        "License :: OSI Approved :: MIT License",
        # 与操作系统无关
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        'pandas',
        'numpy',
        'statsmodels',
        'python-docx'
    ],
    include_package_data=True,
    package_data={
        'empiricalfin': ['*.docx']
    },
)