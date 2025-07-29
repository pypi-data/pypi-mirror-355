from setuptools import setup, find_packages

setup(
    name = 'Http-Prober',
    version = '1.0.0',
    description = 'An async http statuscode prober to enumerate status code from url(s)',
    author = 'Pevinkumar A',
    author_email = 'pevinbalaji@gmail.com',
    url = 'https://github.com/pevinkumar10/http-prober',
    packages = find_packages(),
    install_requires = [
        'aiohttp',
        'colorama'
    ],
    entry_points = {
        'console_scripts': [
            'http-prober = http_prober.modules.core:start'
        ]
    },
    classifiers = [
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
    python_requires='>=3.6',
)