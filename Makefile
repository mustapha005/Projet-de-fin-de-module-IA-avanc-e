PYTHON ?= python
.PHONY: setup data check smoke tune main ablations analysis paper slides reproduce package
setup:
	$(PYTHON) -m pip install -r requirements.lock
data:
	$(PYTHON) scripts/data_pipeline.py
check:
	$(PYTHON) -m unittest discover -s tests -v
smoke tune main ablations analysis paper slides reproduce package:
	@echo Target $@ is not yet implemented or validated. See docs/LOG.md.
	@exit 1
