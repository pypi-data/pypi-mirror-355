# Quarto

![Test](https://github.com/patapelada/quarto-lib/actions/workflows/test.yml/badge.svg)
![Release](https://github.com/patapelada/quarto-lib/actions/workflows/publish.yml/badge.svg)

## Objective

To create a line of four pieces (horizontal, vertical, or diagonal) that share at least one common characteristic:

- Color: light or dark
- Shape: round or square
- Height: tall or short
- Top: solid or hollow

The twist: you choose the piece your opponent must place on the board.

## Game Setup

- Board: 4x4 grid (16 positions)
- Pieces: 16 unique combinations of 4 binary characteristics (2⁴ = 16)

## Gameplay Sequence

1. Player A chooses a piece (from the 16 available) and gives it to Player B.
2. Player B places the piece on any empty square, then selects a new piece (from the remaining 15) and gives it to Player A.
3. Continue until someone forms a winning line or all squares are filled (draw).

## Strategic Depth

Because you give your opponent their piece:

- You try to avoid giving them a winning move
- And you try to force them into giving you a winning opportunity

## Game Complexity

Each turn involves two key decisions:

1. Placement: Choose 1 of up to 16 (later fewer) empty squares.
2. Piece selection: Choose 1 of the remaining unplaced pieces for the opponent.

### Game Tree Size

Turn 1: 16 choices (piece to give)  
Turn 3: 15 placements × 14 piece choices  
Turn 2: 16 placements × 15 piece choices  
...  
Final Turn: Placement of the last piece

While not all paths are valid due to early wins, the maximum number of game states is large:

- 16! piece placements × 16! orderings ≈ 2×10³⁶ possible games (theoretical upper bound)
