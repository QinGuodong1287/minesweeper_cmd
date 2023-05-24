.PHONY: deploy
deploy:
	@echo "Making minesweeper_cmd.zip ..."
	zip ../minesweeper_cmd.zip *.py lang/ tool/ README.md LICENSE Makefile

clean:
	rm -r ../minesweeper_cmd.zip
