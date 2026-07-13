# Badminton Career Simulator

A text-based badminton career game available in two editions:

- **Website with permanent saves:** Run `python3 server.py`, then open `http://127.0.0.1:8765`.
- **Website without the server:** Opening `index.html` directly still works and falls back to browser-local storage.
- **Terminal:** Run `python3 badminton_career_simulator.py`.

Build your player's overall rating, enter full tournament draws against international opponents, earn prize money, improve your skills, climb to world number one, and win the Season-Ending Championship.

The website uses plain HTML, CSS, and JavaScript. The terminal edition uses only Python's standard library.

Career progress is stored in `data.json`. The local server validates every save and writes it atomically through a temporary file, preventing partial JSON overwrites. A missing or malformed save is safely replaced with the default structure.

Official opponent metadata is stored separately in `bwf-players.json`. While `server.py` is running, it checks the configured BWF World Ranking and HSBC Race to Finals pages once per hour. A failed update keeps the last valid cache instead of replacing it.

## How to play

- Each turn represents one week. Choose technical training, fitness training, rest, a tournament, or player development.
- The opening flow presents the rules first, then asks for the player's name, a blank user-selected starting age from 14–35, gender, and nationality.
- Players build a live-preview character (hair, eyes, mouth, racket, colours), upload and confirm a photo, or capture and confirm a webcam photo. No AI profile pictures are generated.
- A persistent Settings panel controls sound preferences, reduced motion, career-log density, match presentation, and tournament-entry confirmations.
- The persistent profile card tracks identity details, current and highest ranking, OVR, win-loss record, titles, and career achievements.
- Age- and gender-aware origin archetypes create a unique opening story, with new storyline chapters generated from results, injuries, ranking changes, rivalries, comebacks, and achievements.
- A responsive six-sided radar chart displays Technique, Speed & Footwork, Power, Defense, Physicality, and Mentality for the player and every match opponent.
- The OVR formula weights those attributes consistently (24/18/17/16/15/10), with small temporary form and injury modifiers. AI opponents use exactly the same model.
- Created-player portraits use a clean background. Match opponents are limited to verified BWF member IDs, use BWF-hosted headshots, and provide a minimal `Profile` link to the player's actual BWF page.
- The opponent system uses confirmed BWF member IDs and BWF-hosted headshots. Every opponent tracks age, gender, nationality, OVR, ranking, independent training, injuries, retirement, and AI-versus-AI rivalries.
- Attribute changes use realistic ranges: training +0.1–0.5, tournament development distributed across relevant skills, injuries primarily reducing Physicality and Speed, losing streaks affecting Mentality, and post-peak decline targeting athletic attributes.
- The career log uses a responsive timeline grid with icons, season/week dates, entry counts, progressive loading, and filters for matches, training, injuries, rankings, news, and rivalries.
- Current match stamina remains separate from the permanent Physicality rating, so fatigue affects match form without falsely rewriting the career attribute after every rally.
- Spend money in Player Development to permanently improve ratings.
- Players ranked outside the world top 100 must qualify for tournaments.
- Easy, Medium, Hard, and Elite tournaments have visible OVR, title, skill, and ranking requirements. Locked events cannot be entered.
- Tournament draws use difficulty-appropriate opponents, grow tougher by round, and remember recent opponents to prevent repetitive draws.
- Draw pools enforce strict OVR bands: Local 58–69, National 58–76, International 70–89, and Major/Elite 82–100, so world-class BWF stars cannot appear in the lowest tournaments.
- Tournament draws continue through the Round of 64, Round of 32, Round of 16, quarter-finals, semi-finals, and final.
- Training and matches consume stamina. Low stamina and overtraining increase injury risk.
- Reach world rank #1 and win the Season-Ending Championship to win.
- Financial ruin, a career-ending injury, or reaching age 35 without completing the objective ends the career.
