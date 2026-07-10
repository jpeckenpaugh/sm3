# Kurma → Saraswati: Seed Root Default

**Signal from the shell.** A structural gap inherited from Sprint 05, exposed by Sprint 07 testing.

---

## The Issue

`cli.py` line 1447 sets `--seed-root` default to `"."`:

```python
p_init.add_argument("--seed-root", default=".", ...)
```

This means `sm init` and `sm seed` look for `profiles/`, `components/`, and `profile-components/` in the **current working directory** — not where the package or its seed data actually lives.

## The Old Behavior

In the legacy `sm.py` (line 40–41), seed data was resolved relative to the script itself:

```python
SM_DIR = os.path.dirname(os.path.abspath(__file__))
```

This meant you could run `sm seed` from any directory and it would find the seed files. The `seed.py` module's `seed_database()` function already accepts a `seed_root` parameter; the issue is purely what default value is passed to it.

## When It Breaks

Any workflow where the user is not in the project root:

- `pip install -e ~/sm/. && cd test-projects/test-3/ && sm init test-3.db`
- Running `sm seed` from a cron job or automation outside the project directory
- A child container operating on its own database from an arbitrary location

The Sprint 07 test suite never caught this because every test runs from `/root/sm/`, where `"."` resolves correctly.

## What Is Needed

The default `seed_root` in both the `init` and `seed` argument parsers should resolve relative to the **package installation path**, not the CWD. Something like:

```python
_PKG_SEED_ROOT = os.path.dirname(os.path.abspath(__file__))  # or importlib.resources
```

...then used as the default for `--seed-root`.

This is not Sprint 07's scope. It is an inherited gap from Sprint 05's packaging migration that was only surfaced now.

---

*Witnessed by Kurma. Passed to Saraswati for the next sprint's consideration.*
