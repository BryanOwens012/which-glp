# Session Context

## User Prompts

### Prompt 1

git pull origin develop

### Prompt 2

On the frontend, the quality of life numbers should be rendered as out of 10, not %. E.,g "38% -> 72%" should be "3.8 -> 7.2". That makes things more consistent with the rating.
Also, the label should be "Average Quality of Life", not "Quality of Life"

### Prompt 3

Would it make more sense to do which of these:
- Average Quality of Life
- Quality of Life
- Quality of Life Improvement

### Prompt 4

Ok, do Quality of Life Improvement

### Prompt 5

git add all, commit, push

### Prompt 6

We have an issue: on the /experiences page, the drug dropdown defaults to what appears to be empty string. And so only 920 load. It should actually default to "All drugs"

### Prompt 7

git add all, commit, push

### Prompt 8

Does the "all" get cached with mv or Redis? Explore

### Prompt 9

Should I make Redis cache the first 5 pages of the "All drugs" and the 5 most popular drugs?

### Prompt 10

How about: if the user's on / or /experiences, it prefetches the first page of the /experiences for all drugs, since that's very likely where the user is going next

### Prompt 11

Yes. First, explore in the codebase if there's anything like this already. If so, pattern-match

### Prompt 12

[Request interrupted by user for tool use]

### Prompt 13

In fact, could we make /compare redirect to /? Instead of the vice versa that it's doing right now? That would look cleaner

### Prompt 14

[Request interrupted by user for tool use]

### Prompt 15

Is there a cleaner way to do this, for separation of concerns?

### Prompt 16

Ok, do that. And all links that point to /compare should redirect to /

