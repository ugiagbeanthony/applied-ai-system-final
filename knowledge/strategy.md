# Guessing strategy notes

## binary search
Always guess the midpoint of the range that is still possible. Each guess then cuts the remaining numbers in half, so a range of 1 to 100 is solved in at most 7 guesses.

## first guess
Open with the middle of the full range. For 1 to 100 start near 50, for 1 to 20 start near 10, for 1 to 50 start near 25.

## too high
When a guess is too high, the secret is lower. Throw away that guess and everything above it, then guess the midpoint of what is left below it.

## too low
When a guess is too low, the secret is higher. Throw away that guess and everything below it, then guess the midpoint of what is left above it.

## narrow range
When only a few numbers remain, stop splitting and just try them in order. Do not repeat a number you already tried, because it is already ruled out.

## running low on attempts
With one or two attempts left, pick the number that splits the remaining range most evenly, and avoid risky jumps to the edges of the range.

## do not repeat
Never guess a number outside the range that earlier hints allow. It wastes an attempt because earlier answers already ruled it out.
