MAKEFLAGS += --silent
ui_folder="./src/views"

all: ui_recompile run

run:
	python3 ./main.py

ui_recompile:
	pyside6-uic $(ui_folder)/layouts/main_window.ui -o $(ui_folder)/ui_main_window.py
	pyside6-uic $(ui_folder)/layouts/stop_layout.ui -o $(ui_folder)/ui_stop_layout.py
	pyside6-uic $(ui_folder)/layouts/lines_layout.ui -o $(ui_folder)/ui_lines_layout.py
	pyside6-uic $(ui_folder)/layouts/navigation_layout.ui -o $(ui_folder)/ui_navigation_layout.py
	echo "ui compilation complete"

executable:
	pyinstaller app.spec -y

run_executable_linux:
	"./dist/app/Pa jak podjade"