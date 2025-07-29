# Spacing (V)

## `v`

Inserts vertical spacing into a flow of blocks.

The spacing can be absolute, relative, or fractional. In the last case,
the remaining space on the page is distributed among all fractional spacings
according to their relative fractions.

# Example
```example
#grid(
  rows: 3cm,
  columns: 6,
  gutter: 1fr,
  [A #parbreak() B],
  [A #v(0pt) B],
  [A #v(10pt) B],
  [A #v(0pt, weak: true) B],
  [A #v(40%, weak: true) B],
  [A #v(1fr) B],
)
```

## Parameters

### amount *(required)*

How much spacing to insert.

### weak 

If `{true}`, the spacing collapses at the start or end of a flow.
Moreover, from multiple adjacent weak spacings all but the largest one
collapse. Weak spacings will always collapse adjacent paragraph spacing,
even if the paragraph spacing is larger.



## Returns

- content

