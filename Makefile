PYTHON ?= python
.PHONY: setup data check benchmark smoke tune main ablations analysis paper slides reproduce package
setup:
	$(PYTHON) -m pip install -r requirements.lock
data:
	$(PYTHON) scripts/data_pipeline.py
	$(PYTHON) scripts/prepare_development.py
check:
	$(PYTHON) -m unittest discover -s tests -v
benchmark:
	$(PYTHON) scripts/benchmark_cpu.py
	$(PYTHON) scripts/project_compute.py
smoke:
	$(PYTHON) scripts/smoke.py
tune:
	$(PYTHON) scripts/run_experiments.py --phase tune
main:
	$(PYTHON) scripts/run_experiments.py --phase main
ablations:
	$(PYTHON) scripts/run_experiments.py --phase ablation
analysis:
	$(PYTHON) scripts/run_analysis.py
paper slides reproduce package:
	@echo Target $@ is not yet implemented or validated. See docs/LOG.md.
	@exit 1
