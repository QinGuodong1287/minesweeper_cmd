.PHONY: deploy
deploy:
	@echo "Making minesweeper_cmd.zip ..."
	zip ../minesweeper_cmd.zip *.py lang/ tool/ README.md LICENSE
	@echo
	@echo "Making minesweeper_cmd_tool.zip ..."
	zip ../minesweeper_cmd_tool.zip tool/ README.md LICENSE

clean:
	rm -i ../minesweeper_cmd.zip ../minesweeper_cmd_tool.zip
