.DEFAULT_GOAL := all


.PHONY: format
format:
	prettier --html-whitespace-sensitivity ignore --write .

out/blog: templates/blog/* $(shell find content/posts)
	mkdir -p out/blog
	cd .pelican && pelican content
	touch out/blog # mark as done


out/pages/%.html: content/pages/%.md templates/pages.html
	yasha -o $@  --file $< --extensions templates/ext.py templates/pages.html

out/help/%.html: content/help/%.md templates/ext.py templates/help.html
	yasha -o $@ --file $< --extensions templates/ext.py templates/help.html


HELP_MD_FILES := $(wildcard content/help/*.md)
HELP_HTML_FILES := $(patsubst content/help/%.md,out/help/%.html,$(HELP_MD_FILES))

PAGES_MD_FILES := $(wildcard content/pages/*.md)
PAGES_HTML_FILES := $(patsubst content/pages/%.md,out/pages/%.html,$(PAGES_MD_FILES))

all: out/pages out/help out/blog  $(HELP_HTML_FILES) $(PAGES_HTML_FILES)


.PHONY: clean
clean:
	rm -rf out

out/pages:
	mkdir -p out/pages

out/help:
	mkdir -p out/help
