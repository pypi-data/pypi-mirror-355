# Matrix

## `mat`

A matrix.

The elements of a row should be separated by commas, while the rows
themselves should be separated by semicolons. The semicolon syntax merges
preceding arguments separated by commas into an array. You can also use this
special syntax of math function calls to define custom functions that take
2D data.

Content in cells can be aligned with the [`align`]($math.mat.align)
parameter, or content in cells that are in the same row can be aligned with
the `&` symbol.

# Example
```example
$ mat(
  1, 2, ..., 10;
  2, 2, ..., 10;
  dots.v, dots.v, dots.down, dots.v;
  10, 10, ..., 10;
) $
```

## Parameters

### delim 

The delimiter to use.

Can be a single character specifying the left delimiter, in which case
the right delimiter is inferred. Otherwise, can be an array containing a
left and a right delimiter.



### align 

The horizontal alignment that each cell should have.



### augment 

Draws augmentation lines in a matrix.

- `{none}`: No lines are drawn.
- A single number: A vertical augmentation line is drawn
  after the specified column number. Negative numbers start from the end.
- A dictionary: With a dictionary, multiple augmentation lines can be
  drawn both horizontally and vertically. Additionally, the style of the
  lines can be set. The dictionary can contain the following keys:
  - `hline`: The offsets at which horizontal lines should be drawn.
    For example, an offset of `2` would result in a horizontal line
    being drawn after the second row of the matrix. Accepts either an
    integer for a single line, or an array of integers
    for multiple lines. Like for a single number, negative numbers start from the end.
  - `vline`: The offsets at which vertical lines should be drawn.
    For example, an offset of `2` would result in a vertical line being
    drawn after the second column of the matrix. Accepts either an
    integer for a single line, or an array of integers
    for multiple lines. Like for a single number, negative numbers start from the end.
  - `stroke`: How to [stroke]($stroke) the line. If set to `{auto}`,
    takes on a thickness of 0.05em and square line caps.



### gap 

The gap between rows and columns.

This is a shorthand to set `row-gap` and `column-gap` to the same value.



### row-gap 

The gap between rows.



### column-gap 

The gap between columns.



### rows *(required)*

An array of arrays with the rows of the matrix.



## Returns

- content

