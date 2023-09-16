

init:
	pip install -r requirements.txt --extra-index-url https://__token__:$GL_TOKEN@gitlab.com/api/v4/groups/park-smart/-/packages/pypi/simple


test:
	py.test tests

install:
	python setup.py install

main:
	python main.py

.PHONY: init test main
