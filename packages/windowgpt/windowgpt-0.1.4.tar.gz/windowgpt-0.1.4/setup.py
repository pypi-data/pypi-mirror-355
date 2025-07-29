from setuptools import setup, find_packages

setup(
    name='windowgpt',
    version='0.1.4',
    description='Send a screenshot to ChatGPT Vision with a prompt',
    author='Ed Atkinson',
    url='https://github.com/yourusername/windowgpt',
    author_email='ed.atkinson10@gmail.com',
    packages=find_packages(),
    install_requires=[
        'pyautogui',
        'pillow',
        'openai',
    ],
    entry_points={
        'console_scripts': [
            'windowgpt=windowgpt.cli:main',
        ],
    },
    python_requires='>=3.7',
)
