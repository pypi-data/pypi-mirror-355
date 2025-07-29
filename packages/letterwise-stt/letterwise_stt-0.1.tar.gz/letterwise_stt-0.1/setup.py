from setuptools import setup, find_packages

setup(
    name='letterwise_stt',
    version='0.1',
    description='Phoneme-level Speech-to-Text with AI reconstruction',
    author='AmongTheCouch Studios',
    author_email='jack-the-gamer@hotmail.com',
    packages=find_packages(),
    install_requires=[
        'vosk',
        'soundfile',
        'transformers',
        'torch',
        'pyaudio'
    ],
    entry_points={
        'console_scripts': [
            'letterwise-stt = letterwise_stt.main:cli_entry'
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
)
