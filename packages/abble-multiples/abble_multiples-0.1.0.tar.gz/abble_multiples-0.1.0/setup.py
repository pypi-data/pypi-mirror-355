from setuptools import setup, find_packages
setup(
    name='abble_multiples',  
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        # 在此处列出依赖项
    ],
    author='Abble',  
    author_email='17317591875@163.com',
    description='一个用于检查2和5倍数的库。',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',  # 许可证类型
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
