.PHONY: convert-latex book

BOOK_TITLE = introml_book

latex/%.tex: content/%.md pandoc-filters.sh content/metadata.yaml
	@echo "Converting to LaTeX $* >>> $@"
	@pandoc -f markdown+smart+fenced_divs-auto_identifiers+backtick_code_blocks --preserve-tabs --section-divs --biblatex -F pandoc-filters.sh -o $@ $< content/metadata.yaml

lectures := $(patsubst content/%.md,%,$(wildcard content/lec*.md))
book-targets := $(foreach l,$(lectures),latex/$(l).tex)

convert-latex: $(book-targets)

latex/$(BOOK_TITLE).pdf: convert-latex
	@echo "Running LaTeX $*>>>"
	cd latex && pdflatex $(BOOK_TITLE).tex && biber $(BOOK_TITLE) && pdflatex $(BOOK_TITLE).tex && pdflatex $(BOOK_TITLE).tex

book: convert-latex latex/$(BOOK_TITLE).pdf

clean:
	rm -f latex/lec_*.tex
	rm -f latex/lec_*.aux
