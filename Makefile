PYTHON ?= python
PAPER_PYTHON ?= .venv-paper/Scripts/python.exe
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
paper:
	$(PAPER_PYTHON) paper/build.py --final
	$(PAPER_PYTHON) scripts/audit_numbers.py
slides:
	$(PAPER_PYTHON) slides/build_slides.py --final
package:
	$(PYTHON) scripts/package.py
reproduce:
	@echo Expected runtime on the reference laptop (i5-8265U, 4 threads, AC power): about 8 hours for the 36-run main grid.
	$(PYTHON) scripts/data_pipeline.py
	$(PYTHON) scripts/prepare_development.py
	$(PYTHON) scripts/download_model.py
	$(PYTHON) scripts/run_experiments.py --phase main
	$(PYTHON) scripts/run_analysis.py
