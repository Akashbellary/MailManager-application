from setuptools import setup, find_packages

setup(
    name='emailflow',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask>=3.1.2',
        'gunicorn>=23.0.0',
        'pymongo>=4.14.1',
        'openai>=1.106.1',
        'sentence-transformers>=2.2.2',
        'python-dotenv>=1.0.1',
        'google-auth>=2.38.0',
        'google-auth-oauthlib>=1.2.1',
        'google-auth-httplib2>=0.2.0',
        'google-api-python-client>=2.155.0',
        'email-validator>=2.3.0',
        'numpy>=2.3.2',
        'psycopg2-binary>=2.9.10',
        'python-dateutil>=2.9.0.post0',
        'werkzeug>=3.1.3'
    ],
    entry_points={
        'console_scripts': [
            'emailflow=emailflow.main:main',
        ],
    },
)