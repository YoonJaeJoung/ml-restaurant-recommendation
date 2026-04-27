"""
10_query_construction.py — interactive CLI that mirrors the website's
"Need inspiration?" panel.

Asks the user 4 questions (cuisine, vibe, occasion, priority) and composes a
natural-language query. The priority list is *dynamic*: it depends on the
visit time, the same way `app/frontend/src/components/InspireBuilder.jsx` and
`app/backend/query_builder.py` do. Priority is also multi-select — pick any
combination, or "None" to skip.

Order of the resulting query: cuisine → vibe → occasion → priority(s).
"""
from datetime import datetime


# ── Time-of-day → priority options (mirrors PRIORITY_BY_TIME in the frontend) ─
PRIORITY_BY_TIME = {
    "breakfast": ["Good coffee", "Quick and easy", "Vegetarian friendly",
                  "Good brunch", "Quiet and relaxed", "None"],
    "lunch":     ["Quick and easy", "Good for groups", "Vegetarian friendly",
                  "Outdoor seating", "None"],
    "dinner":    ["Great cocktails", "Good for groups", "Late night",
                  "Vegetarian friendly", "Upscale and fancy", "None"],
    "anytime":   ["Great cocktails", "Good for groups", "Late night",
                  "Quick and easy", "Vegetarian friendly", "Good brunch", "None"],
}


def get_time_slot(visit: datetime | None, any_time: bool) -> str:
    if any_time or visit is None:
        return "anytime"
    h = visit.hour
    if 6  <= h < 11: return "breakfast"
    if 11 <= h < 16: return "lunch"
    if 16 <= h < 23: return "dinner"
    return "anytime"


def ask_single(question, options):
    """Ask one question, return one selected option."""
    print(f"\n{question}")
    for i, option in enumerate(options, 1):
        print(f" {i}. {option}")
    while True:
        try:
            choice = int(input("Enter number: "))
            if 1 <= choice <= len(options):
                return options[choice - 1]
            print("Invalid choice, try again.")
        except ValueError:
            print("Please enter a number.")


def ask_multi(question, options):
    """
    Ask one question, return a list of selected options (multi-select).
    Accepts comma- or space-separated numbers, e.g. "1,3" or "1 3".
    Picking 'None' (or nothing) yields []. Picking 'None' alongside
    other options ignores 'None'.
    """
    print(f"\n{question} (pick any — comma- or space-separated, e.g. 1,3)")
    for i, option in enumerate(options, 1):
        print(f" {i}. {option}")
    while True:
        raw = input("Enter number(s): ").strip()
        if not raw:
            return []
        tokens = [t for t in raw.replace(",", " ").split() if t]
        try:
            picks = [int(t) for t in tokens]
        except ValueError:
            print("Please enter numbers only.")
            continue
        if any(p < 1 or p > len(options) for p in picks):
            print("Invalid choice, try again.")
            continue
        # de-duplicate while preserving order
        seen, chosen = set(), []
        for p in picks:
            opt = options[p - 1]
            if opt not in seen:
                seen.add(opt); chosen.append(opt)
        # 'None' alongside real picks is meaningless — drop it.
        real = [c for c in chosen if c != "None"]
        if real:
            return real
        return [] if "None" in chosen else chosen


def ask_visit_time() -> tuple[datetime | None, bool]:
    """Ask whether the user wants any-time, otherwise an HH:MM."""
    print("\nWhen are you planning to visit?")
    print(" 1. Any time")
    print(" 2. Specific time (HH:MM, 24h)")
    while True:
        try:
            choice = int(input("Enter number: "))
            if choice == 1:
                return None, True
            if choice == 2:
                raw = input("Enter time (HH:MM): ").strip()
                try:
                    hh, mm = (int(x) for x in raw.split(":"))
                    return datetime.now().replace(hour=hh, minute=mm,
                                                  second=0, microsecond=0), False
                except Exception:
                    print("Bad format — use HH:MM (e.g. 19:30).")
                    continue
            print("Invalid choice, try again.")
        except ValueError:
            print("Please enter a number.")


def main():
    visit, any_time = ask_visit_time()
    time_slot = get_time_slot(visit, any_time)

    occasion = ask_single("What's the occasion?", [
        "Date night",
        "Family dinner",
        "Lunch with coworkers",
        "Catching up with friends",
        "Solo meal",
        "Celebration",
    ])

    vibe = ask_single("What vibe are you looking for?", [
        "Cozy and intimate",
        "Lively and fun",
        "Quiet and relaxed",
        "Upscale and fancy",
        "Casual and laid-back",
        "Outdoor seating",
    ])

    cuisine = ask_single("Any cuisine preference?", [
        "Italian",
        "Japanese / Sushi",
        "Chinese",
        "Mexican",
        "Indian",
        "Seafood",
        "American",
        "Mediterranean",
        "No preference",
    ])

    priorities = ask_multi(
        f"Any other priorities? (time slot: {time_slot})",
        PRIORITY_BY_TIME[time_slot],
    )

    # Build query: cuisine → vibe → occasion → priority(s)
    parts = []
    if cuisine != "No preference":
        parts.append(cuisine)
    parts.append(vibe)
    parts.append(occasion)
    real_priorities = [p for p in priorities if p != "None"]
    if real_priorities:
        parts.append(" ".join(real_priorities))

    query = " ".join(parts)
    print(f'\n✅ Your query: "{query}"')


if __name__ == "__main__":
    main()
