import setuptools
with open('README.md', 'r', encoding='utf-8') as fh:
	long_description = fh.read()

setuptools.setup(
	name='capcha',
	version='3.3',
	author='BornTheHell',
	author_email='',
	description='',
	long_description=long_description,
	long_description_content_type='text/markdown',
	packages=['capcha'],
	include_package_data=True,
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
	],
	python_requires='>=3.13',
)