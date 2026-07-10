#!/bin/bash
# read_pulse.sh — Read the pulse history of the container
# Usage: read_pulse.sh [--db <path>]

DB=""

while [ $# -gt 0 ]; do
    case "$1" in
        --db) DB="$2"; shift 2 ;;
        *) DB="$1"; shift ;;
    esac
done

# Auto-detect database path
if [ -z "$DB" ]; then
    CANDIDATES=("matsya.db" "test-project.db")
    for c in "${CANDIDATES[@]}"; do
        if [ -f "$c" ]; then
            DB="$c"
            break
        fi
    done
fi

# Also check .sm-config.json
if [ -z "$DB" ] && [ -f ".sm-config.json" ]; then
    DB=$(python3 -c "import json; print(json.load(open('.sm-config.json')).get('db_path', ''))" 2>/dev/null)
fi

if [ -z "$DB" ] || [ ! -f "$DB" ]; then
    echo '{"error": "Database not found. Provide --db <path> or run from a project directory."}'
    exit 1
fi

DB_PATH=$(realpath "$DB" 2>/dev/null || echo "$DB")

sqlite3 -json "$DB" "
SELECT
  (SELECT COUNT(*) FROM sprints) AS sprint_count,
  (SELECT json_object('number', number, 'status', status, 'started_at', started_at)
   FROM sprints ORDER BY id DESC LIMIT 1) AS active_sprint,
  (SELECT completed_at FROM phase_runs ORDER BY id DESC LIMIT 1) AS last_pulse_at,
  (SELECT COUNT(*) FROM phase_runs) AS phase_count,
  (SELECT COUNT(*) FROM dispatch_log) AS dispatch_count
" 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
if isinstance(data, list):
    data = data[0]
now = __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
ts_str = data.get('last_pulse_at', '')
if ts_str:
    try:
        ts = __import__('datetime').datetime.strptime(ts_str.replace('Z', '+0000'), '%Y-%m-%dT%H:%M:%f%z')
        silence = int((now - ts).total_seconds())
        mins, secs = divmod(abs(silence), 60)
        hours, mins = divmod(mins, 60)
        if hours > 0:
            data['silence_human'] = f'{hours}h {mins}m'
        else:
            data['silence_human'] = f'{mins}m {secs}s'
        data['silence_seconds'] = silence
    except (ValueError, AttributeError):
        data['silence_human'] = 'unknown'
        data['silence_seconds'] = 0
else:
    data['silence_human'] = 'no pulses recorded'
    data['silence_seconds'] = 0
data['db_path'] = '$DB_PATH'
data['last_pulse'] = data.pop('last_pulse_at', None)
print(json.dumps(data, indent=2))
" 2>/dev/null || echo '{"error": "Failed to read pulse from database"}'
