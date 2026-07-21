# BanglaMuscle 90 — GitHub Pages Upload Package

This is the complete single-file version of BanglaMuscle.

## Included

### 90-Day Challenge
- Automatically starts at Day 1 on first launch
- Calendar-based Day 1 through Day 90 tracking
- Three phases:
  - Days 1–30: Foundation
  - Days 31–60: Build
  - Days 61–90: Transform
- Challenge progress bar and completion date
- XP, levels, missions, badges, streaks and recovery tokens

### XP
- Core workout: 100 XP
- Optional workout: 70 XP
- Recovery workout: 50 XP
- Protein target: 40 XP
- Post-workout protein: 25 XP
- Hydration: 15 XP
- Pre-workout fuel: 10 XP
- Daily gym/rest check-in: 10 XP

### Challenge protection
Rest days count when the recovery mission is completed. Recovery tokens can protect recent missed days without deleting workout history.

### Existing systems retained
- Week 1 · Day 1 through Day 6 roadmap
- Optional Day 4, Day 5 and Day 6 unlocking
- Exercise demonstrations and beginner form cues
- Adaptive weekly machine-weight progression
- Day 1 machine baselines
- Daily and weekly lifting volume
- 3–6 day training selection
- Protein and calorie targets
- Daily gym question
- Pre-workout, water, post-workout and rest reminder waterfall
- LocalStorage persistence
- JSON export

## Deployment

1. Extract the ZIP.
2. Open the GitHub repository.
3. Replace the repository-root `index.html`.
4. Commit the change to `main`.
5. In Settings → Pages:
   - Source: Deploy from a branch
   - Branch: main
   - Folder: / (root)

## Important static-site limitation

The application works fully in the browser and saves data locally. Scheduled browser reminders are reliable while the page is open. Guaranteed push notifications when the browser is completely closed require a PWA push service, backend or native application.
