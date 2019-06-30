setup: clean-venv
	virtualenv -p python3 .venv
	.venv/bin/pip install -r requirements.txt

clean:
	find . -iname __pycache__ | xargs rm -fr
	find . -iname '*.pyc' | xargs rm -f

clean-venv:
	rm -fr .venv

dist-clean: clean clean-venv

update-requirements: setup
	.venv/bin/pip freeze > requirements.txt
