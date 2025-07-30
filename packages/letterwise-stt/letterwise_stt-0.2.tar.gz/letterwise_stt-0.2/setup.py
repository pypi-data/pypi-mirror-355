from setuptools import setup, find_packages

setup(
    name='letterwise_stt',
    version='0.2',
    description='Phoneme-level Speech-to-Text with AI reconstruction',
    author='AmongTheCouch Studios',
    author_email='jack-the-gamer@hotmail.com',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'letterwise_stt.data': ['words_alpha.txt'],
    },
    install_requires=[
        'vosk',
        'soundfile',
        'transformers',
        'torch',
        'pyaudio',
        'sounddevice'
    ],
    entry_points={
        'console_scripts': [
            'letterwise-stt=letterwise_stt.testing:main'
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
)
