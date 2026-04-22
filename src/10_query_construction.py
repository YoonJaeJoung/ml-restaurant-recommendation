def ask(question, options):
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

occasion = ask("What's the occasion?", [
  "Date night",
  "Family dinner",
  "Lunch with coworkers",
  "Catching up with friends",
  "Solo meal",
  "Celebration"
])

vibe = ask("What vibe are you looking for?", [
  "Cozy and intimate",
  "Lively and fun",
  "Quiet and relaxed",
  "Upscale and fancy",
  "Casual and laid-back",
  "Outdoor seating"
])

cuisine = ask("Any cuisine preference?", [
  "Italian",
  "Japanese / Sushi",
  "Chinese",
  "Mexican",
  "Indian",
  "Seafood",
  "American",
  "Mediterranean",
  "No preference"
])

priority = ask("Any other priorities?", [
  "Great cocktails",
  "Good for groups",
  "Late night",
  "Quick and easy",
  "Vegetarian friendly",
  "Good brunch",
  "None"
])

# Build query
parts = []
if cuisine != "No preference":
  parts.append(cuisine)
parts.append(vibe)
parts.append(occasion)
if priority != "None":
  parts.append(priority)

query = " ".join(parts)
print(f"\n:white_check_mark: Your query: \"{query}\"")