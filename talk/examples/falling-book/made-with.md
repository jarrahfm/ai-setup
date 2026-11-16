# How this page was made

`index.html` in this folder is one chapter page, "Why do things fall together?", for 12 to 14 year olds. An AI agent
built it from a written request, then opened it in a browser at a laptop width and a phone width, looked at the
pictures, and checked every number against the sources listed at the bottom of the page.

## The request a teacher could give an AI agent

> Make one web page, in a single file that opens by double-click and uses nothing from the internet: a short
> textbook chapter for 12 to 14 year olds called "Why do things fall together?". Use three or four short sections.
> Every picture must be one the reader can run: (1) a hammer and a feather dropped from 1.6 m, with one button for
> Earth and one for the Moon; (2) a graph of height against time that draws itself while a ball falls on Earth and
> on the Moon, so both lines are on the same graph; (3) one slider that changes gravity and shows the fall time from
> 1.6 m, worked out from t = √(2h ÷ g); (4) one "check yourself" question that explains why each answer is right or
> wrong. Put the key words in bold, each with a one-sentence plain definition: gravity, acceleration, air resistance,
> vacuum. Use only these sources, and quote the sentence you rely on for each fact in a list at the end: NASA, "The
> Apollo 15 Hammer-Feather Drop"; NASA, "Compare Earth and the Moon"; OpenStax College Physics 2e, section 2.7. If a
> fact is not in a source, leave it out. Short sentences, plain words. It must work on a phone, with the keyboard, and
> with "reduce motion" switched on.

What made the result good was not a clever request but the follow-up: open the page, try every button, and ask for
one change at a time ("the clock shows a number for the feather that nobody measured: stop the clock when the
hammer lands").

## What a person must still check

1. **Every number against its source, by hand.** Open each page in the source list and find the sentence. The
   AI can copy a number wrongly or invent a source. On this page: 1.6 m, 1.32 kg, 0.03 kg, 1971, 9.80665 m/s² and
   1.624 m/s².
2. **The times against the formula.** With a calculator: √(2 × 1.6 ÷ 9.80665) = 0.571 s on Earth and
   √(2 × 1.6 ÷ 1.624) = 1.404 s on the Moon. The page shows 0.57 s and 1.40 s.
3. **When sources disagree.** NASA gives 1.624 m/s² for the Moon; OpenStax uses 1.67 m/s². Both are reasonable;
   the page uses NASA's and says so. With 1.67 the Moon time would be 1.38 s. Decide which one your class uses.
4. **What the picture makes up.** The feather's drifting path through air on Earth is drawn to show the idea, not
   measured. The page says so, and shows no number for it. Look for any number the page shows that came from a
   drawing choice, not from a source.
5. **The physics, not only the numbers.** Does the graph start flat? (It should: a dropped object starts still.)
   Do the hammer and the feather land together on the Moon? Does four times the gravity give half the time?
6. **That it works for your students.** Try it on a phone, with only the keyboard, and ask one colleague or student
   to use it without help.

## Choices made while building it

- Figure 2 drops two balls instead of a hammer and a feather, because its lines ignore air resistance; on the Moon
  the feather's line would be the same line as the hammer's.
- The clock in Figure 1 stops when the hammer lands, so the page never shows a time for the drawn feather.
- Gravity values come from NASA; the fall-time rule comes from OpenStax equation 2.76 with a starting speed of zero.
- The definitions of gravity and vacuum come from two more NASA pages (Space Place, "What Is Gravity?"; NASA Glenn,
  "Altitude Wind Tunnel – How the Facility Worked"), and acceleration from the OpenStax Chapter 2 glossary. All six
  pages were opened on 15 November 2026.
- The page is in English only. An Arabic version would need its own check of every definition.
