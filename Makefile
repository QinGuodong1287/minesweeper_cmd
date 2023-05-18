.PHONY: deploy
deploy:
	@echo "Making minesweeper_cmd.zip ..."
	zip ../minesweeper_cmd.zip -xl ./*.py ./lang ./tool ./README.md ./LICENSE
	@echo "Making minesweeper_cmd_tool.zip ..."
	zip ../minesweeper_cmd_tool.zip -xl ./tool ./README.md ./LICENSE
