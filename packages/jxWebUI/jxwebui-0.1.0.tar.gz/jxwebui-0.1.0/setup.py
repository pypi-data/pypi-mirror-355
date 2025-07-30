from setuptools import setup, find_packages
 
setup(
    name='jxWebUI',  # 你的库名
    version='0.1.0',    # 版本号
    packages=find_packages(include=["jxWebUI", "jxWebUI.ui_web", "jxWebUI.ui_web.web", "jxWebUI.ui_web.descr", "jxWebUI.ui_web.demo"]),  # 自动查找包
    include_package_data=True,  # 包含非Python文件
    package_dir={
        "jxWebUI": "jxWebUI",  # 指定包根目录
    },
    package_data={
        "": ["docs/**/*","web/**/*", ]
    },
    exclude_package_data={
        "": [".idea/", "__pycache__/"],  # 全局排除
        "jxWebUI": ["__pycache__/"],  # 全局排除
    },
    install_requires=[  # 依赖项
        'importlib_resources==6.4.5',
        'pycryptodome',
        'pytz',
        'apscheduler',
        'antlr4-python3-runtime==4.7.2',
        'tornado',
    ],
    author='徐晓轶',
    author_email='andrew@pythonpi.top',
    description='简单易用的python Web UI库',
    url='https://blog.csdn.net/jxandrew?type=blog',  # 项目的URL
    python_requires=">=3.8",
)
