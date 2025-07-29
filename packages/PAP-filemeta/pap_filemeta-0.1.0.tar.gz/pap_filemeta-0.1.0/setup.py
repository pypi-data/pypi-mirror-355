# # # setup.py
# # from setuptools import setup, find_packages

# # setup(
# #     name='filemeta',
# #     version='0.1.1',
# #     packages=find_packages(),
# #     include_package_data=True,
# #     install_requires=[
# #         'SQLAlchemy',
# #         'Click',
# #         'psycopg2-binary', # Or remove if only using SQLite
# #     ],
# #     entry_points={
# #         'console_scripts': [
# #             'filemeta=filemeta.cli:cli',
# #         ],
# #     },
# #     author='Your Name', # Replace with your name
# #     author_email='your.email@example.com', # Replace with your email
# #     description='A CLI tool for managing server file metadata.',
# #     long_description='', # Temporarily set to empty string as README.md doesn't exist yet
# #     long_description_content_type='text/markdown',
# #     url='https://github.com/yourusername/filemeta_project', # Replace with your project's URL
# #     classifiers=[
# #         'Programming Language :: Python :: 3',
# #         'License :: OSI Approved :: MIT License', # Or choose another license
# #         'Operating System :: OS Independent',
# #     ],
# #     python_requires='>=3.7',
# # )
# # setup.py
# from setuptools import setup, find_packages

# setup(
#     name='pranavik928-filemeta',
#     version='0.1.0',
#     packages=find_packages(),
#     include_package_data=True,
#     install_requires=[
#         'SQLAlchemy',
#         'Click',
#         'psycopg2-binary', # Or remove if only using SQLite
#     ],
#     entry_points={
#         'console_scripts': [
#             'filemeta=filemeta.cli:cli',
#         ],
#     },
#     author='Your Name', # Replace with your name
#     author_email='your.email@example.com', # Replace with your email
#     description='A CLI tool for managing server file metadata.',
#     long_description='', # Temporarily set to empty string as README.md doesn't exist yet
#     long_description_content_type='text/markdown',
#     url='https://github.com/yourusername/filemeta_project', # Replace with your project's URL
#     classifiers=[
#         'Programming Language :: Python :: 3',
#         'License :: OSI Approved :: MIT License', # Or choose another license
#         'Operating System :: OS Independent',
#     ],
#     python_requires='>=3.7',
# )
# setup.py
from setuptools import setup, find_packages
import os
setup(
    name='PAP-filemeta',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True, # Include non-Python files specified in MANIFEST.in if you have one
    install_requires=[
        'fastapi==0.111.0',
        'uvicorn[standard]==0.29.0',
        'sqlalchemy==2.0.30',
        'psycopg2-binary==2.9.9',
        'passlib==1.7.4',
        'bcrypt==3.2.0',
        'python-jose[cryptography]==3.3.0',
        'python-multipart==0.0.9', # Ensure this version is compatible with your FastAPI version
        'pydantic==2.7.1',         # Ensure this version is compatible with your FastAPI version
        'click==8.1.7',
    ],
    entry_points={
        'console_scripts': [
            'filemeta=filemeta.cli:cli', # This maps the 'filemeta' command to the cli() function in filemeta/cli.py
        ],
    },
    author='pranavik928',
    author_email='pranavik928@gmail.com', # Replace with your actual email
    description='A CLI and API for managing server file metadata.',
    long_description=open('README.md').read() if os.path.exists('README.md') else '',
    long_description_content_type='text/markdown',
    url='https://github.com/Pranavi598/PROJECT', # Replace with your project's GitHub or other URL
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License', # Assuming MIT License, adjust if different
        'Operating System :: OS Independent',
        'Topic :: System :: Filesystems',
        'Topic :: Utilities',
    ],
    python_requires='>=3.8', # Specify minimum Python version
)


