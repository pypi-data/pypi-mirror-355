from distutils.core import setup
import io

# Read the contents of README.md
with io.open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='triggersms',
    version='0.1.3',
    description='TriggerSMS is a Python package for sending data to the TriggerSMS API.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=['triggersms'],
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=2.6.6',
)
