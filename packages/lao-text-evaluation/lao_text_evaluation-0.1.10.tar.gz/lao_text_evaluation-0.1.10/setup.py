from setuptools import setup, find_packages

setup(
    name='lao_text_evaluation',
    version='0.1.10',
    packages=find_packages(),
    install_requires=['numpy', 'regex', 'matplotlib'],
    entry_points={
        'console_scripts': [
            'lao-ocr-eval=lao_text_evaluation.cli:main'
        ]
    },
    author='Khonepaseuth SOUNAKHEN',
    description='Lao OCR Evaluation Tools',
    license='MIT'
)