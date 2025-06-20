# TODO list

This is a document, each of the subheaders is a particular issue or new feature
that needs to be addressed in this codebase. Issues that we've finished go into
"Finished Issues". Issues that are yet to be addressed are in "Unfinished Issues".

## Unfinished Issues

## Finished Issues

### Getting the Python update script to reorder posts after they go from future to past

For our workshop posts (under `content/workshops`), there are two pieces of frontmatter that matter for this issue:

1. `temporalstatus`: This determines whether a workshop has already passed or is
   yet to happen.
2. `listindex`: This determines what order the workshop shows up when listed on
   our homepage and under "Past Workshops" on our `workshops` page.

We manually use `listindex` instead of just ordering by `workshopdate` because
we often wlll use natural language dates for workshops we haven't nailed down
yet (e.g. "Q4 2025"), which can have non-obvious rules for ordering, so we
instead want to manually list them.

In theory the `listindex` should always be incremented by `1` when we make a new
post. This ensures that no two posts have the same `listindex`. In practice this
is quite annoying to do and keep track of given how many posts we have. So
instead it's easier to just set `listindex` to whatever it needs to be to make
the homepage look nice (i.e. the list of workshops with `temporalstatus:
future`) and then clean up afterwards.

This is aided by the fact that by the time a workshop goes from `temporalstatus:
future` to `temporalstatus: past`, it should already have a concrete date
associated with it. 

We currently have a script that looks at `workshopdate`s of posts every night
and then changes the `temporalstatus` from `future` to `past` if that date is
already in the past.

**We want that script to also change the `listindex` so that all posts with
`temporalstatus: past` have monotonically increasing `listindex`es relative to
`workshopdate` each off set by 1**

For example, let's say that on the homepage we have three workshops: A, B, and
C, where A has a `listindex` of `1`, B has a listindex of `5`, and C has a
`listindex` of `6`. This lets A be at the top, followed by B, and then C (with
some sloppiness where whoever was making the workshop posts just assigned
whatever numbers to `listindex` were necessary to make things work).

Because these workshops are on the homepage, all of them
have `temporalstatus: future`. Then we have 10 workshops with
`temporalstatus: past` that run from `listindex: 1` to `listindex: 10`.

Then our workshop A is finished and our overnight Python script comes along and
changes `A`'s `temporalstatus` from `future` to `past`. We'd also like that same
script to change `A`'s `listindex` from `1` to `11`. Then when the same happens
for B's `temporalstatus` we'd like to change `B`'s `listindex` from `5` to `12`.
So and on and so forth.

If the update script would simultaneously change multiple posts'
`temporalstatus`, we want it to change the `listindex`es in order of time, so
that e.g. if `A` and `B` were both changed from `temporalstatus: future` to
`temporalstatus: past` at the same time, but `A` had an earlier `workshopdate`
than `B`, `A` should get a `listindex` of `11` and `B` should get a `listindex`
of `12`.

---

**COMPLETED**

- Enhanced the `scripts/updater.py` script to implement the requested functionality. The script now:
- Parses all workshop markdown files to extract frontmatter data
- Identifies workshops that need status updates (future workshops with past dates)  
- Finds the current maximum listindex among past workshops
- Updates workshops in chronological order, assigning sequential listindex values starting from max+1
- Includes comprehensive logging for debugging and monitoring
- Handles complex date formats with times and timezones
