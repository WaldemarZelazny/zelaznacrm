# Skill: Ship — Commit, push i dokumentacja

## Cel
Bezpiecznie zacommituj i wypchnij zmiany zgodnie ze standardami projektu.

## Procedura

### 1. Przed commitem
```bash
git status
git diff --stat
pytest --tb=no -q 2>&1 | tail -3
```

### 2. Formatowanie i linting
```bash
black apps/
isort apps/
flake8 apps/
```

### 3. Commit (Conventional Commits)
```bash
git add <konkretne pliki>
git commit -m "typ(moduł): krótki opis co i dlaczego"
```

Typy: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`
Przykłady:
- `feat(leads): add kanban board view`
- `fix(companies): correct NIP validation`
- `docs: update README with setup instructions`

### 4. Push
```bash
git push origin main
```

### 5. Weryfikacja
```bash
git log --oneline -3
```

## Zasady
- Jeden commit = jedna logiczna zmiana
- Nigdy `git add .` bez sprawdzenia `git status` — może zacommitować `.env`
- Zawsze uruchom testy przed pushem
- Pre-commit hooks mogą zmodyfikować pliki — wtedy `git add` ponownie i commit
