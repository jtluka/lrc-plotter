# Lrc Plotter

This is a simple tool that graphs CPU utilization and flow throughput of LNST
recipe runs based on provided lrc file.

To show the cpu utilization:
```
poetry run lrc-plotter --view cpu /tmp/lnst-run-data-0.lrc
```

To show the flow throughput:
```
poetry run lrc-plotter --view flow /tmp/lnst-run-data-0.lrc
```
