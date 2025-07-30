import setuptools
with open('README.md', 'r', encoding='utf-8') as fh:
	long_description = fh.read()

setuptools.setup(
	name='tkinter-gui',
	version='1.3.5',
	author='danon',
	author_email='',
	description='Create multilingual interfaces for your tkinter applications.',
	long_description=long_description,
	long_description_content_type='text/markdown',
	packages=['gui_'],
	include_package_data=True,
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
	],
	python_requires='>=3.9',
)