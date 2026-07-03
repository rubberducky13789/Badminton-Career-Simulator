# Badminton Career Simulator

A text-based badminton career game available in two editions:

- **Website:** Open `index.html` in a browser.
- **Terminal:** Run `python3 badminton_career_simulator.py`.

Build your player's overall rating, enter full tournament draws against international opponents, earn prize money, improve your skills, climb to world number one, and win the Season-Ending Championship.

The website uses plain HTML, CSS, and JavaScript. The terminal edition uses only Python's standard library.

## How to play

- Each turn represents one week. Choose technical training, fitness training, rest, a tournament, or player development.
- The opening flow presents the rules first, then asks for the player's name, starting age, gender, and nationality.
- Each created player receives a generated profile portrait and randomized origin story.
- The persistent profile card tracks identity details, current and highest ranking, OVR, win-loss record, titles, and career achievements.
- Age- and gender-aware origin archetypes create a unique opening story, with new storyline chapters generated from results, injuries, ranking changes, rivalries, comebacks, and achievements.
- The realistic OVR model uses fractional growth, training consistency, tournament performance, age, health, confidence, and form. AI opponents follow the same improvement and decline rules.
- Created-player portraits use a clean white background. Opponent portraits accept only verified BWF-hosted photos and otherwise show a clearly labelled non-AI fallback linked to the official BWF directory.
- The opponent system uses confirmed BWF member IDs and BWF-hosted headshots. Every opponent tracks age, gender, nationality, OVR, ranking, independent training, injuries, retirement, and AI-versus-AI rivalries.
- Skill changes use realistic ranges: training +0.1–0.5, good tournament runs +0.5–2, major wins +1–3, injuries −1–5, losing streaks −0.5–2, and post-peak seasonal decline −0.1–1. Higher ratings receive stronger improvement resistance.
- The career log uses a responsive timeline grid with icons, season/week dates, entry counts, progressive loading, and filters for matches, training, injuries, rankings, news, and rivalries.
- Permanent skill, fitness, and confidence combine into an NBA 2K-style overall rating. Stamina affects match form instead of changing overall.
- Spend money in Player Development to permanently improve ratings.
- Players ranked outside the world top 100 must qualify for tournaments.
- Tournament draws continue through the Round of 64, Round of 32, Round of 16, quarter-finals, semi-finals, and final.
- Training and matches consume stamina. Low stamina and overtraining increase injury risk.
- Reach world rank #1 and win the Season-Ending Championship to win.
- Financial ruin, a career-ending injury, or reaching age 35 without completing the objective ends the career.
