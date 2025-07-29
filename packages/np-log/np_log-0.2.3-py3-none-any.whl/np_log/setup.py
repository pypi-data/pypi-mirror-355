from setuptools import setup, find_packages
read_me_path = r'D:\code\打包\np_log\README.md'
setup(
    name='np_log',
    packages=["np_log"],
    version = '0.2.2',
    # packages=find_packages(),
    description='日志管理器',
    long_description=open(read_me_path, encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    author='刘金林',
    author_email='2558949748@qq.com',
    url='https://github.com/Liu670/np_log',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    keywords='logging custom log configuration',
    install_requires=[
        # 依赖的包

    ],
    python_requires='>=3.5',
)