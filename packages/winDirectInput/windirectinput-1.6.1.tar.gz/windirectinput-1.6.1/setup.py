from setuptools import setup
from wheel.bdist_wheel import bdist_wheel as _bdist_wheel

# Override the bdist_wheel command to use normalized name for the wheel file
class bdist_wheel(_bdist_wheel):
    def finalize_options(self):
        super().finalize_options()
        # Force the wheel filename to use the normalized name
        self.distribution.metadata.name = self.distribution.metadata.name.lower()

setup(
    cmdclass={'bdist_wheel': bdist_wheel},
    name='winDirectInput',
    version='1.6.1',
    author='AbdulRahim Khan',
    author_email='abdulrahimpds@gmail.com',
    description='A Windows-specific package for simulating keyboard and mouse inputs',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/abdulrahimpds/winDirectInput',
    py_modules=['directinput'],
    install_requires=[
        'opencv-python',
        'numpy',
        'mss',
        'pyscreeze',
        'pillow',
        'pyperclip'
    ],
    classifiers=[
        'Programming Language :: Python :: 3.8',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Microsoft :: Windows',
    ],
    python_requires='>=3.8'
)
