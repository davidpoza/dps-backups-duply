all: help

help:
	@echo "make [target]"
	@echo ""
	@echo "setup     -- Setups the environments and initial dev databases."
	@echo

setup:
	virtualenv -p python3 .env
	.env/bin/pip install -r requirements.txt

