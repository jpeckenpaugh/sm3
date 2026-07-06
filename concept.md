Create a simple python state machine with a SQLite DB that can cycle the following states:

variable $num==1

COMMIT => Git commit
BACKLOG => Populate a `backlog` folder wth all necessary features ft001.md, ft002.md, ft003.md, etc.
VERIFY => Git status to Confirm Outputs. If Outputs don't exist, roll back to last Git commit
COMMIT => Git commit
BRIEF => For each `backlog/ft*.md` file, append a technical brief to the footer of the file
VERIFY
COMMIT
PLAN => Move one or more `backlog/ft*.md` to `sprint/{$num}/` and add plan.md to that folder describing the sprint plan to buid it
VERIFY
COMMIT
ARCHITECT => Create file `sprint/{$num}/spec.md` based on files in `sprint/{$num}/`
VERIFY
COMMIT
ENGINEER => Create outputs to `src/*` baed on `sprint/{$num}/*`
VERIFY
COMMIT
TEST => Create `sprint/{$num}/test/*` to test code in `src/*` against `sprint/{$num}/*` and generate `sprint/{$num}/report.md`
VERIFY
COMMIT
DEVOPS => Use `sprint/{$num}/*` - generate/update `requirements.txt`, debug `src/*` if needed, create `install.sh` and `start.sh` and `sprint/{$num}/recommendation.md`
VERIFY
COMMIT
PM => Look at all outputs of `sprint/{$num}/*` - resolve any blockers. Any new requirements can go into `backlog` as new features. If `backlog` is empty, create/update file `README.md`
VERIFY
COMMIT
GATE => If `backlog/` folder is empty, move to SHIP, otherwise increment [ $num = $num + 1 ]  and move to PLAN
SHIP


OpenCode Agent Profiles by STATE:
doc-agent.md for [ BACKLOG, BRIEF, PLAN, ARCHITECT ]
code-agent.md for [ ENGINEER, TEST, DEVOPS, PM ]

Needed tools:
./git_commit.sh
