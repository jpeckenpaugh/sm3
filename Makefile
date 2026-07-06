.PHONY: all run setup clean

all: setup run

setup:
	chmod +x git_commit.sh wait-and-touch.sh scripts/*.sh
	mkdir -p signals output

run:
	python3 state_machine.py

clean:
	rm -rf signals output backlog.txt vasuki.signal
