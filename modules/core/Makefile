start:
	. venv/bin/activate
	python runserver.py

clean:
	@echo Removing binary files...
	rm -f `find core -name '*.pyc'`
	rm -f `find core -name '*.pyo'`
	@echo Removing docs...
	make -C doc clean

doc-html:
	make -C doc html
