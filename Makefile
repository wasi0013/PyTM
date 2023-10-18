.PHONY: help clean clean-pyc clean-build list test test-all coverage docs release sdist

help:
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "test-all - run tests on every Python version with tox"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "release - package and upload a release"
	@echo "sdist - package"
	@echo "upgrade-all - upgrades all python packages to the latest version"

clean: clean-build clean-pyc

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

lint:
	flake8 PyTM test

test:
	py.test

test-all:
	tox

coverage:
	coverage run --source PyTM setup.py test
	coverage report -m
	coverage html
	sensible-browser 'htmlcov/index.html'

docs:
	rm -f docs/PyTM.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ PyTM
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	sensible-browser 'docs/_build/html/index.html'

release: clean
	python setup.py sdist
	twine upload --verbose dist/*

sdist: clean
	python setup.py sdist
	ls -l dist

upgrade-all:
	sed -i 's/==/>=/g' requirements.txt    
	python -m pip install -r requirements.txt --upgrade
	python -m pip freeze > requirements.txt
  
