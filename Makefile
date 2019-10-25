# These targets are not files
.PHONY: test lint

lint:
	flake8 --exclude=migrations,migrations-pre17 --ignore=W291,W504,E501,F401,F403 moderation tests

test:
	python runtests.py --failfast
