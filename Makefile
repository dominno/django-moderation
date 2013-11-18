# These targets are not files
.PHONY: test lint

lint:
	pep8 --exclude=migrations --ignore=W291 moderation tests

test:
	python runtests.py --failfast
