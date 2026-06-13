.PHONY: install validate test physics aviation artifacts report dashboard init-db source-status website-data

install:
	python -m pip install -e ".[dev]"

validate:
	python -m battery_frontier.cli validate

test:
	python -m pytest

physics:
	python -m battery_frontier.cli physics-reference

aviation:
	python -m battery_frontier.cli aviation-reference

artifacts:
	python -m battery_frontier.cli dashboard-artifacts

report:
	python -m battery_frontier.cli daily-report

source-status:
	python -m battery_frontier.cli source-status

website-data:
	python -m battery_frontier.cli website-data

dashboard:
	python -m streamlit run dashboard/app.py

init-db:
	python -m battery_frontier.cli init-db
