from setuptools import setup, find_packages

setup(
    name='CTkFileDialog',
    version='0.1.3',
    include_package_data=True,
    author='FlickGMD',
    author_email='salvadorfabiansulcacuba@gmail.com',
    description='Un elegante diálogo de archivos para CustomTkinter',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=[
        'customtkinter>=5.0.0',
        'Pillow',
        'opencv-python',
        'CTkMessagebox',
        'CTkToolTip'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: User Interfaces',
    ],
    python_requires='>=3.7',
)
