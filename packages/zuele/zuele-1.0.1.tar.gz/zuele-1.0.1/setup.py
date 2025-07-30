from setuptools import setup,find_packages

setup(
    name='zuele',
    version='1.0.1',
    author='ikun',
    author_email='2206490823@qq.com',
    description='Jieba in economy',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'zuele=zuele.main:main',  # 指定命令行入口
        ],
    },
)
