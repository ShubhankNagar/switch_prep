from lld_common import *

topics = []

topics.append(T(
"snake-and-ladder", "Design Snake and Ladder", 5, "Basic", 35,
"A classic machine-coding warm-up: a configurable Snake and Ladder game with multiple players, pluggable dice and a clean game loop.",
r'''
## Problem
Build a multiplayer Snake and Ladder game. The board has 100 cells, some snakes (head -> tail, going down) and ladders (start -> end, going up). Players take turns rolling a die; the first to reach exactly 100 wins.

## Requirements
**P0**
1. Configurable board size, snakes, ladders and players (input or code).
2. Players move by die value; landing on a snake head moves down to its tail; landing on a ladder bottom moves up to its top.
3. A move beyond 100 is not allowed (player stays).
4. Print every move: `Raj rolled 4 and moved from 12 to 16`.
5. Game ends when a player reaches 100 (or continue until one player is left - P1).

**P1:** multiple dice, rolling 6 grants another turn, three 6s cancel the turn, crocodile/mine special cells.

## Entities
`Board`, `Jump` (generic for snake or ladder), `Player`, `Dice` (interface), `Game`.

## Class diagram
```text
Game
  - board: Board
  - players: Deque<Player>      (round-robin turn order)
  - dice: Dice
  + play(): Player              (returns winner)

Board
  - size: int
  - jumps: Map<Integer, Jump>   (start cell -> jump)
  + finalPosition(pos): int

Jump - start, end, isSnake()  (start > end => snake)
Player - name, position

<<interface>> Dice  + roll(): int
   ^.. RandomDice(count)      ^.. FixedDice (deterministic, for tests/demos)
```

## Patterns used and why
- **Unified `Jump` entity**: snakes and ladders differ only in direction, so one class with a map lookup gives O(1) resolution - simpler than two hierarchies.
- **Strategy** for `Dice`: random dice for play, a fixed sequence for tests; multiple dice or loaded dice are just new implementations.
- **Queue for turns**: `ArrayDeque` poll/offer gives round-robin turn order naturally.
- **Builder/validation** in `Board`: reject a snake and ladder starting on the same cell, jumps out of range, and cycles.

## Java implementation
```java
import java.util.*;

class Jump {
    final int start, end;
    Jump(int start, int end) { this.start = start; this.end = end; }
    boolean isSnake() { return end < start; }
}

class Board {
    private final int size;
    private final Map<Integer, Jump> jumps = new HashMap<>();

    Board(int size) { this.size = size; }

    void addJump(int start, int end) {
        if (start <= 1 || start >= size || end < 1 || end > size || start == end)
            throw new IllegalArgumentException("Invalid jump " + start + "->" + end);
        if (jumps.containsKey(start))
            throw new IllegalArgumentException("Cell " + start + " already has a snake/ladder");
        jumps.put(start, new Jump(start, end));
    }

    int getSize() { return size; }

    /** Follows snakes/ladders (chains allowed) and returns the final cell. */
    int finalPosition(int pos) {
        int guard = 0;
        while (jumps.containsKey(pos)) {
            Jump j = jumps.get(pos);
            System.out.println("   " + (j.isSnake() ? "Bitten by snake" : "Climbed ladder") + " at " + pos + " -> " + j.end);
            pos = j.end;
            if (++guard > jumps.size()) throw new IllegalStateException("Cycle in board configuration");
        }
        return pos;
    }
}

class Player {
    final String name;
    int position = 0;
    Player(String name) { this.name = name; }
}

interface Dice { int roll(); }

class RandomDice implements Dice {
    private final int count;
    private final Random random;
    RandomDice(int count, long seed) { this.count = count; this.random = new Random(seed); }
    public int roll() {
        int sum = 0;
        for (int i = 0; i < count; i++) sum += random.nextInt(6) + 1;
        return sum;
    }
}

class FixedDice implements Dice {          // deterministic dice for tests
    private final int[] values; private int i = 0;
    FixedDice(int... values) { this.values = values; }
    public int roll() { return values[i++ % values.length]; }
}

class Game {
    private final Board board;
    private final Deque<Player> turns;
    private final Dice dice;

    Game(Board board, List<Player> players, Dice dice) {
        if (players.size() < 2) throw new IllegalArgumentException("Need at least 2 players");
        this.board = board; this.turns = new ArrayDeque<>(players); this.dice = dice;
    }

    Player play() {
        int moves = 0;
        while (true) {
            Player p = turns.poll();
            int roll = dice.roll();
            int from = p.position;
            int target = from + roll;
            if (target > board.getSize()) {
                System.out.println(p.name + " rolled " + roll + " but cannot move beyond " + board.getSize());
            } else {
                p.position = board.finalPosition(target);
                System.out.println(p.name + " rolled " + roll + " and moved from " + from + " to " + p.position);
            }
            if (p.position == board.getSize()) {
                System.out.println(p.name + " wins the game in " + (moves + 1) + " moves!");
                return p;
            }
            turns.offer(p);
            if (++moves > 10_000) throw new IllegalStateException("Game too long");
        }
    }
}

public class Main {
    public static void main(String[] args) {
        Board board = new Board(30);
        board.addJump(27, 5);    // snake
        board.addJump(17, 4);    // snake
        board.addJump(3, 22);    // ladder
        board.addJump(11, 26);   // ladder
        try { board.addJump(3, 9); } catch (IllegalArgumentException e) { System.out.println("Config error: " + e.getMessage()); }

        List<Player> players = List.of(new Player("Raj"), new Player("Priya"));
        // FixedDice makes the demo reproducible; swap with new RandomDice(1, seed) for real play
        Game game = new Game(board, players, new FixedDice(3, 5, 4, 6, 2, 6, 6, 1, 4, 3));
        game.play();
    }
}
```

## Walkthrough of key decisions
- `finalPosition` loops so a ladder ending on a snake head is followed, with a guard against misconfigured cycles.
- Overshooting is a no-op move, a common rule clarified at the start.
- The `Game` does not know whether the dice are random - perfect for unit tests that assert exact outcomes.

## Extension questions
1. **Roll 6 = extra turn, three 6s = lose turn:** track consecutive sixes in the loop; do not re-offer the player until the turn ends.
2. **Multiple dice:** `RandomDice(2, seed)` - already supported; or a strategy for min/max/sum of dice.
3. **Continue until one player remains:** remove winners from the queue and collect a ranking list.
4. **Special cells (crocodile sends back 5, mine skips 2 turns):** generalise `Jump` into a `Cell` interface with `apply(Player)` - Strategy/Command per cell.
5. **Thread safety / online multiplayer:** game state per room; one thread per game or actor-style message queue.
''',
["Represent snakes and ladders with one Jump entity in a Map<start, Jump> for O(1) resolution.",
 "Use a Deque for round-robin turns: poll the current player, offer them back after the move.",
 "Dice is a Strategy: RandomDice for play, FixedDice for deterministic tests and demos.",
 "Validate the board: no duplicate starts, jumps within range, guard against cycles.",
 "Clarify rules up front: overshooting 100, extra turn on 6, play until one or all finish.",
 "Keep Game logic free of I/O decisions so it is testable; Main only wires and runs.",
 "Generalise cells into a Cell interface for special squares like mines or crocodiles."],
[("Why model snakes and ladders as the same class?",
  r'''Both are just a mapping from a start cell to an end cell; the only difference is direction (end < start for snakes). One `Jump` class stored in `Map<Integer, Jump>` makes position resolution a single lookup and avoids duplicate code. If snakes and ladders later need different behaviour (e.g., ladders only usable on even rolls), I would introduce a `Cell` interface with `apply()` and separate implementations.'''),
 ("How would you test the game deterministically?",
  r'''Inject a `Dice` implementation. In tests I pass a `FixedDice` returning a predetermined sequence, so I can assert exact positions, snake and ladder hits, and the winner after N turns. The `Board` is built in the test with known jumps. Because `Game` depends on the `Dice` interface (DIP), no mocking framework is needed, and randomness is confined to `RandomDice`, which can take a seed.'''),
 ("How would you implement 'rolling a 6 gives another turn, but three 6s in a row forfeit the turn'?",
  r'''Inside the turn, loop while the roll is 6: count consecutive sixes, accumulate or apply moves, and break when the roll is not 6. If the count reaches three, revert the player to the position at the start of the turn and end the turn. Only after the turn completes is the player offered back into the queue. Keeping this logic in a `TurnPolicy` strategy lets different rule variants coexist.'''),
 ("How do you detect an invalid board configuration?",
  r'''During setup: reject jumps that start on cell 1 or the last cell, endpoints outside the board, a start equal to the end, and two jumps sharing a start cell. A ladder ending on a snake head is allowed but can create cycles (snake 20->10, ladder 10->20), so either detect cycles by following chains from every start with a visited set, or guard at runtime with a maximum chain length, as in my `finalPosition`.''')],
[{"title": "workat.tech - Snake and Ladder Machine Coding", "url": "https://workat.tech/machine-coding/practice/snake-and-ladder-problem-zgtac9lxwntg"}, ALLD]
))

topics.append(T(
"tic-tac-toe", "Design Tic-Tac-Toe (N x N)", 6, "Basic", 30,
"An N x N Tic-Tac-Toe with pluggable players and O(1) win detection using row, column and diagonal counters.",
r'''
## Problem
Design Tic-Tac-Toe for two players on an N x N board. Players alternate placing their symbol; the first to fill a full row, column or diagonal wins; a full board with no winner is a draw.

## Requirements
**P0**
1. Configurable board size N (default 3) and two players with symbols X and O.
2. Validate moves: inside the board, cell empty, correct player's turn.
3. Detect win or draw after each move.
4. Print the board after each move.

**P1:** human vs computer (AI strategy), undo last move, more than two players, K-in-a-row variant (Gomoku).

## Entities
`Symbol` (X, O), `Player`, `Board`, `Move`, `GameStatus`, `WinChecker`, `Game`.

## Class diagram
```text
Game
  - board: Board
  - players: Player[2], current index
  - status: GameStatus (IN_PROGRESS, X_WON, O_WON, DRAW)
  - history: Deque<Move>
  + makeMove(row, col): GameStatus
  + undo()

Board  - n, grid: Symbol[][]
       - rowCount[], colCount[], diag, antiDiag   (+1 for X, -1 for O)
       + place(move): boolean (returns true if move wins)

Player - name, symbol, strategy: MoveStrategy
<<interface>> MoveStrategy  + nextMove(Board): int[]
   ^.. ScriptedMoves   ^.. FirstFreeCellAI
```

## Patterns used and why
- **O(1) win detection:** instead of scanning the whole board after every move (O(N^2)), keep counters: add +1 for X and -1 for O to the row, column and, when applicable, diagonals. If any counter's absolute value hits N, that player wins. This is a classic interviewer follow-up (also LeetCode 348).
- **Strategy** for move selection: human input, scripted moves for tests, or AI (random, minimax).
- **Command-like `Move`** objects in a history stack make undo trivial: reverse the counters.

## Java implementation
```java
import java.util.*;

enum Symbol {
    X(1), O(-1);
    final int weight;
    Symbol(int w) { weight = w; }
}

enum GameStatus { IN_PROGRESS, X_WON, O_WON, DRAW }

record Move(int row, int col, Symbol symbol) { }

class InvalidMoveException extends RuntimeException {
    InvalidMoveException(String m) { super(m); }
}

class Board {
    private final int n;
    private final Symbol[][] grid;
    private final int[] rows, cols;
    private int diag, antiDiag, filled;

    Board(int n) {
        this.n = n; grid = new Symbol[n][n]; rows = new int[n]; cols = new int[n];
    }
    int size() { return n; }
    boolean isEmpty(int r, int c) { return grid[r][c] == null; }
    boolean isFull() { return filled == n * n; }

    /** Places the move and returns true if it wins. O(1). */
    boolean place(Move m) {
        int r = m.row(), c = m.col();
        if (r < 0 || r >= n || c < 0 || c >= n) throw new InvalidMoveException("Out of board: " + r + "," + c);
        if (grid[r][c] != null) throw new InvalidMoveException("Cell occupied: " + r + "," + c);
        grid[r][c] = m.symbol();
        filled++;
        return update(r, c, m.symbol().weight);
    }

    void remove(Move m) {               // used by undo
        grid[m.row()][m.col()] = null;
        filled--;
        update(m.row(), m.col(), -m.symbol().weight);
    }

    private boolean update(int r, int c, int w) {
        rows[r] += w; cols[c] += w;
        if (r == c) diag += w;
        if (r + c == n - 1) antiDiag += w;
        return Math.abs(rows[r]) == n || Math.abs(cols[c]) == n || Math.abs(diag) == n || Math.abs(antiDiag) == n;
    }

    void print() {
        for (Symbol[] row : grid) {
            StringBuilder sb = new StringBuilder();
            for (Symbol s : row) sb.append(s == null ? "-" : s.name()).append(' ');
            System.out.println("  " + sb.toString().trim());
        }
    }
}

interface MoveStrategy { int[] nextMove(Board b); }

class ScriptedMoves implements MoveStrategy {
    private final Deque<int[]> moves;
    ScriptedMoves(int[]... ms) { moves = new ArrayDeque<>(Arrays.asList(ms)); }
    public int[] nextMove(Board b) { return moves.poll(); }
}

class FirstFreeCellAI implements MoveStrategy {
    public int[] nextMove(Board b) {
        for (int r = 0; r < b.size(); r++)
            for (int c = 0; c < b.size(); c++)
                if (b.isEmpty(r, c)) return new int[]{r, c};
        throw new IllegalStateException("No free cell");
    }
}

class Player {
    final String name; final Symbol symbol; final MoveStrategy strategy;
    Player(String name, Symbol symbol, MoveStrategy strategy) { this.name = name; this.symbol = symbol; this.strategy = strategy; }
}
```

```java
class Game {
    private final Board board;
    private final Player[] players;
    private int current = 0;
    private GameStatus status = GameStatus.IN_PROGRESS;
    private final Deque<Move> history = new ArrayDeque<>();

    Game(int n, Player p1, Player p2) {
        if (p1.symbol == p2.symbol) throw new IllegalArgumentException("Players need different symbols");
        board = new Board(n); players = new Player[]{p1, p2};
    }

    GameStatus makeMove(int r, int c) {
        if (status != GameStatus.IN_PROGRESS) throw new InvalidMoveException("Game over: " + status);
        Player p = players[current];
        Move m = new Move(r, c, p.symbol);
        boolean won = board.place(m);           // throws on invalid move, turn not consumed
        history.push(m);
        if (won) status = p.symbol == Symbol.X ? GameStatus.X_WON : GameStatus.O_WON;
        else if (board.isFull()) status = GameStatus.DRAW;
        else current = 1 - current;
        return status;
    }

    void undo() {
        if (history.isEmpty()) return;
        board.remove(history.pop());
        if (status == GameStatus.IN_PROGRESS) current = 1 - current;
        status = GameStatus.IN_PROGRESS;
    }

    GameStatus playAuto() {
        while (status == GameStatus.IN_PROGRESS) {
            Player p = players[current];
            int[] mv = p.strategy.nextMove(board);
            try {
                makeMove(mv[0], mv[1]);
                System.out.println(p.name + " (" + p.symbol + ") -> " + mv[0] + "," + mv[1]);
                board.print();
            } catch (InvalidMoveException e) {
                System.out.println(p.name + ": " + e.getMessage() + ", try again");
            }
        }
        return status;
    }
}

public class Main {
    public static void main(String[] args) {
        Player raj = new Player("Raj", Symbol.X, new ScriptedMoves(new int[]{1, 1}, new int[]{0, 0}, new int[]{0, 2}, new int[]{2, 0}));
        Player bot = new Player("Bot", Symbol.O, new FirstFreeCellAI());
        Game g = new Game(3, raj, bot);
        System.out.println("Result: " + g.playAuto());

        Game g2 = new Game(3, raj, bot);
        g2.makeMove(0, 0); g2.makeMove(1, 1);
        g2.undo();
        System.out.println("After undo, O can play 1,1 again -> " + g2.makeMove(0, 1));
    }
}
```

In the first game the bot grabs `0,0`; Raj's scripted attempt at `0,0` is rejected without losing his turn, then he completes the anti-diagonal `0,2 - 1,1 - 2,0`.

## Extension questions
1. **Unbeatable AI:** minimax with alpha-beta pruning on 3x3 (search space is tiny).
2. **K-in-a-row on large boards (Gomoku):** counters no longer suffice; after each move, count consecutive symbols in 4 directions from the last cell - O(K).
3. **More players:** symbols array, current = (current + 1) % k, counters per player (or the directional check).
4. **Online multiplayer:** game rooms keyed by id in a `ConcurrentHashMap`, moves validated server-side, synchronized per game.
''',
["Keep row, column, diagonal and anti-diagonal counters (+1 for X, -1 for O) for O(1) win detection.",
 "A move wins when any affected counter's absolute value equals N; a full board without a win is a draw.",
 "Validate moves (bounds, occupied, game over) with exceptions that do not consume the player's turn.",
 "MoveStrategy lets human, scripted and AI players share the same Game loop.",
 "Move records in a history stack make undo straightforward by reversing counters.",
 "For K-in-a-row variants, check consecutive cells in four directions from the last move instead.",
 "Minimax with alpha-beta pruning is the standard answer for an unbeatable 3x3 AI."],
[("How do you check for a winner efficiently?",
  r'''Instead of scanning rows, columns and diagonals after each move (O(N^2) or O(N)), I keep integer arrays `rows[n]`, `cols[n]` and two ints for the diagonals. A move adds +1 for X or -1 for O to its row and column, and to a diagonal if `r == c` or `r + c == n - 1`. If any updated counter reaches +n or -n, that player has filled the line. Each move is O(1), and the counters can be reversed for undo.'''),
 ("How would you add a computer player?",
  r'''Introduce `MoveStrategy` with `nextMove(Board)`. A human strategy reads from input, a simple AI picks a random or first free cell, and a strong AI uses minimax: recursively simulate all moves, scoring wins +1, losses -1 and draws 0, maximising for itself and minimising for the opponent, with alpha-beta pruning. The `Game` loop is unchanged because it only calls `player.strategy.nextMove()`.'''),
 ("How do you support undo?",
  r'''Every successful move is pushed onto a stack as an immutable `Move(row, col, symbol)` - essentially the Command pattern. Undo pops it, clears the cell, decrements the filled count and subtracts the symbol's weight from the same counters, then restores the turn and resets status to in-progress. Redo would use a second stack that is cleared on any new move.'''),
 ("What changes for a 15x15 board where 5 in a row wins?",
  r'''Line counters only work when the whole row must be filled. For K-in-a-row, after placing at (r, c) I check the four directions (horizontal, vertical, two diagonals): count consecutive same symbols forward and backward from the cell; if the total is at least K, the player wins. That is O(K) per move. The board, players and move strategies remain the same; only the win-checking component changes, so I would put it behind a `WinChecker` interface.''')],
[{"title": "LeetCode 348 - Design Tic-Tac-Toe", "url": "https://leetcode.com/problems/design-tic-tac-toe/"}, ALLD]
))

topics.append(T(
"vending-machine", "Design a Vending Machine", 7, "Intermediate", 45,
"The canonical State-pattern problem: a vending machine that accepts coins and notes, dispenses products, returns change and handles cancellations.",
r'''
## Problem
Design a vending machine with product slots. A user selects a product, inserts money, receives the product and change, or cancels to get a refund. An admin restocks products and cash.

## Requirements
**P0**
1. Inventory of products by code (e.g., `A1 -> Coke, Rs 40, qty 5`).
2. Accept coins/notes: 1, 2, 5, 10, 20, 50, 100.
3. Flow: select product -> insert money (possibly several times) -> dispense product + change when enough is paid.
4. Cancel at any point before dispensing returns all inserted money.
5. Handle out-of-stock and "cannot make change" scenarios.

**P1:** admin mode for restock, card/UPI payment, multiple selections in one session, reporting.

## Entities
`Product`, `Inventory`, `Denomination` (enum), `CashInventory`, `VendingMachine` (context), `State` interface with `IdleState`, `ProductSelectedState`, `PaymentState`, `DispenseState` (internal).

## Class diagram
```text
VendingMachine (context)
  - state: VendingState
  - inventory: Inventory
  - cash: CashInventory
  - selected: Product, inserted: List<Denomination>
  + selectProduct(code), insert(denomination), cancel()

<<interface>> VendingState
  + selectProduct(vm, code)
  + insert(vm, d)
  + cancel(vm)
   ^.. IdleState  ^.. ProductSelectedState (waiting for money)

Inventory      - products: Map<code, Product>, stock: Map<code, Integer>
CashInventory  - counts: EnumMap<Denomination, Integer>
               + makeChange(amount): Optional<List<Denomination>>  (greedy, largest first)
```

State transitions:

```text
IDLE --select(valid,in stock)--> HAS_SELECTION --insert--> HAS_SELECTION (paid < price)
HAS_SELECTION --insert(paid >= price, change ok)--> dispense --> IDLE
HAS_SELECTION --insert(paid >= price, no change)--> refund --> IDLE
HAS_SELECTION --cancel--> refund --> IDLE
```

## Patterns used and why
- **State**: the same button means different things in different states (inserting money while idle is rejected). State classes remove nested `if (state == ...)` from every method and make adding states (e.g., `MaintenanceState`) local.
- **Singleton (optional)** for the machine in a single-device context.
- **Greedy change-making** with denomination counts; works for canonical coin systems like INR. Mention DP if denominations are non-canonical.
- **Enum with value** for denominations - type-safe money input.

## Java implementation
```java
import java.util.*;

enum Denomination {
    ONE(1), TWO(2), FIVE(5), TEN(10), TWENTY(20), FIFTY(50), HUNDRED(100);
    final int value;
    Denomination(int v) { value = v; }
}

class Product {
    final String code, name; final int price;
    Product(String code, String name, int price) { this.code = code; this.name = name; this.price = price; }
}

class Inventory {
    private final Map<String, Product> products = new HashMap<>();
    private final Map<String, Integer> stock = new HashMap<>();
    void add(Product p, int qty) { products.put(p.code, p); stock.merge(p.code, qty, Integer::sum); }
    Product get(String code) { return products.get(code); }
    boolean inStock(String code) { return stock.getOrDefault(code, 0) > 0; }
    void decrement(String code) { stock.merge(code, -1, Integer::sum); }
}

class CashInventory {
    private final EnumMap<Denomination, Integer> counts = new EnumMap<>(Denomination.class);
    CashInventory() { for (Denomination d : Denomination.values()) counts.put(d, 0); }
    void add(Denomination d, int n) { counts.merge(d, n, Integer::sum); }
    void addAll(List<Denomination> ds) { ds.forEach(d -> add(d, 1)); }

    /** Greedy change making using available counts; empty if not possible. Does not mutate on failure. */
    Optional<List<Denomination>> makeChange(int amount) {
        List<Denomination> result = new ArrayList<>();
        EnumMap<Denomination, Integer> temp = new EnumMap<>(counts);
        Denomination[] desc = Denomination.values();
        for (int i = desc.length - 1; i >= 0 && amount > 0; i--) {
            Denomination d = desc[i];
            while (amount >= d.value && temp.get(d) > 0) {
                amount -= d.value; temp.merge(d, -1, Integer::sum); result.add(d);
            }
        }
        if (amount != 0) return Optional.empty();
        counts.clear(); counts.putAll(temp);
        return Optional.of(result);
    }
}

interface VendingState {
    void selectProduct(VendingMachine vm, String code);
    void insert(VendingMachine vm, Denomination d);
    void cancel(VendingMachine vm);
}

class IdleState implements VendingState {
    public void selectProduct(VendingMachine vm, String code) {
        Product p = vm.inventory().get(code);
        if (p == null) { System.out.println("Invalid code " + code); return; }
        if (!vm.inventory().inStock(code)) { System.out.println(p.name + " is out of stock"); return; }
        vm.setSelected(p);
        System.out.println("Selected " + p.name + " (Rs " + p.price + "). Insert money.");
        vm.setState(new HasSelectionState());
    }
    public void insert(VendingMachine vm, Denomination d) {
        System.out.println("Select a product first. Returning Rs " + d.value);
    }
    public void cancel(VendingMachine vm) { System.out.println("Nothing to cancel"); }
}

class HasSelectionState implements VendingState {
    public void selectProduct(VendingMachine vm, String code) {
        System.out.println("Product already selected; cancel to change");
    }
    public void insert(VendingMachine vm, Denomination d) {
        vm.addInserted(d);
        int paid = vm.insertedTotal(), price = vm.selected().price;
        System.out.println("Inserted Rs " + d.value + ", total Rs " + paid);
        if (paid < price) return;
        vm.cash().addAll(vm.inserted());               // money goes in first so it can be used for change
        Optional<List<Denomination>> change = vm.cash().makeChange(paid - price);
        if (change.isEmpty()) {
            System.out.println("Cannot make change. Refunding.");
            vm.cash().makeChange(paid);                // give back the same value
            vm.reset();
            return;
        }
        vm.inventory().decrement(vm.selected().code);
        System.out.println("Dispensed " + vm.selected().name + ", change: " + change.get());
        vm.reset();
    }
    public void cancel(VendingMachine vm) {
        System.out.println("Cancelled. Refunding " + vm.inserted());
        vm.reset();
    }
}
```

```java
class VendingMachine {
    private VendingState state = new IdleState();
    private final Inventory inventory = new Inventory();
    private final CashInventory cash = new CashInventory();
    private Product selected;
    private final List<Denomination> inserted = new ArrayList<>();

    // public API delegates to current state
    public synchronized void selectProduct(String code) { state.selectProduct(this, code); }
    public synchronized void insert(Denomination d) { state.insert(this, d); }
    public synchronized void cancel() { state.cancel(this); }

    // admin
    public void restock(Product p, int qty) { inventory.add(p, qty); }
    public void loadCash(Denomination d, int n) { cash.add(d, n); }

    // used by states
    void setState(VendingState s) { state = s; }
    Inventory inventory() { return inventory; }
    CashInventory cash() { return cash; }
    Product selected() { return selected; }
    void setSelected(Product p) { selected = p; }
    void addInserted(Denomination d) { inserted.add(d); }
    List<Denomination> inserted() { return new ArrayList<>(inserted); }
    int insertedTotal() { return inserted.stream().mapToInt(d -> d.value).sum(); }
    void reset() { selected = null; inserted.clear(); state = new IdleState(); }
}

public class Main {
    public static void main(String[] args) {
        VendingMachine vm = new VendingMachine();
        vm.restock(new Product("A1", "Coke", 40), 2);
        vm.restock(new Product("B1", "Chips", 25), 0);
        vm.loadCash(Denomination.TEN, 1);
        vm.loadCash(Denomination.FIVE, 1);

        vm.insert(Denomination.TEN);                  // rejected in idle
        vm.selectProduct("B1");                       // out of stock
        vm.selectProduct("A1");
        vm.insert(Denomination.TWENTY);
        vm.insert(Denomination.FIFTY);                // pays 70, change 30
        vm.selectProduct("A1");
        vm.insert(Denomination.TEN);
        vm.cancel();                                  // refund
        vm.selectProduct("A1");
        vm.insert(Denomination.HUNDRED);              // change 60 not possible -> refund
    }
}
```

## Extension questions
1. **Maintenance/admin state:** `MaintenanceState` rejects customer actions and allows restock - add one class.
2. **Card/UPI payments:** `PaymentMethod` strategy; coins become one implementation.
3. **Non-canonical denominations:** greedy can fail (e.g., coins 1, 3, 4 for 6); use DP bounded by available counts.
4. **Concurrency:** physical machines have one user, but a networked fleet needs per-machine locking (public methods are synchronized here).
5. **Timeouts:** auto-cancel a session after 60s of inactivity using a scheduled task.
''',
["Vending machine is the textbook State pattern: each state handles select, insert and cancel differently.",
 "The context (VendingMachine) delegates every public call to its current state object.",
 "States trigger transitions themselves (Idle -> HasSelection -> Idle after dispense or refund).",
 "Make change greedily from available denomination counts; never mutate cash on a failed attempt.",
 "Refund when change cannot be made and on cancel; handle out-of-stock before accepting money.",
 "Denominations as an enum with value make money input type-safe.",
 "New behaviour like maintenance mode or card payment is added as new classes, not new if-branches."],
[("Why use the State pattern for a vending machine?",
  r'''The machine's response to each action depends on its current state: inserting money while idle should be rejected, selecting a product while one is already selected should be refused, and so on. Without State, every method has a `switch` on a status enum, and adding a state means editing all of them. With State, each state class encapsulates its rules and transitions, so the context just delegates. Adding `MaintenanceState` touches one new class and a transition point.'''),
 ("How do you calculate change, and when does greedy fail?",
  r'''Greedily take the largest denomination not exceeding the remaining amount while that denomination is available, working on a copy of the cash counts and committing only if the exact amount is reached. For canonical systems like INR (1, 2, 5, 10, 20, 50, 100) greedy gives an optimal answer when coins are unlimited. It can fail with limited counts or non-canonical sets: with coins {1, 3, 4}, greedy pays 6 as 4+1+1 instead of 3+3. Then use a bounded-knapsack DP.'''),
 ("What happens if the machine cannot return change?",
  r'''Detect it before dispensing. After the user pays at least the price, add the inserted money to the cash box, then try to compute change on a temporary copy. If it fails, refund the inserted value and return to idle without dispensing - the transaction is atomic. A better UX is to check change availability up front and show "exact change only" when cash reserves are low.'''),
 ("How would you add an admin restock flow securely?",
  r'''Separate the admin interface from the customer interface (Interface Segregation): `AdminOperations` with `restock`, `collectCash`, `setPrice`, reachable only after authentication with a PIN. Entering admin mode transitions the machine to `MaintenanceState`, in which customer actions are rejected, and exiting returns it to `IdleState`. All admin operations are logged for audit.''')],
[{"title": "Refactoring.Guru - State", "url": "https://refactoring.guru/design-patterns/state"}, ALLD,
 {"title": "awesome-low-level-design - Vending Machine", "url": "https://github.com/ashishps1/awesome-low-level-design/blob/main/problems/vending-machine.md"}]
))

topics.append(T(
"library-management", "Design a Library Management System", 8, "Intermediate", 40,
"Model books vs physical copies, members, borrowing rules, fines and reservations with a clean service layer and pluggable fine policies.",
r'''
## Problem
A library has many books, each with several physical copies. Members search the catalogue, borrow and return copies, pay fines for late returns, and reserve books that are currently unavailable.

## Requirements
**P0**
1. Add books (ISBN, title, author) and copies (barcode) to the catalogue.
2. Search by title or author.
3. Members borrow up to 5 copies, each for 14 days.
4. Return a copy; compute a fine for late returns (Rs 10/day).
5. Reserve a book when no copy is available; when a copy returns, it is held for the first reserver.

**P1:** notifications (due soon, reservation ready), different member types (student/faculty) with different limits, renewals, librarian roles.

## Entities
`Book` (metadata), `BookCopy` (physical item, status), `Member`, `Loan`, `Reservation`, `FinePolicy`, `NotificationService`, `LibraryService`, `Catalog`.

**Key insight:** distinguish a **Book** (title-level info, one per ISBN) from a **BookCopy** (physical copy with barcode). Mixing the two is the most common mistake in this problem.

## Class diagram
```text
Book       - isbn, title, author
BookCopy   - barcode, book: Book, status (AVAILABLE, BORROWED, RESERVED)
Member     - id, name, type: MemberType (maxBooks, loanDays)
Loan       - copy, member, issueDate, dueDate, returnDate

Catalog
  - books: Map<isbn, Book>
  - copies: Map<isbn, List<BookCopy>>
  + searchByTitle(q), searchByAuthor(q), availableCopy(isbn)

LibraryService
  - catalog, members, activeLoans: Map<barcode, Loan>
  - reservations: Map<isbn, Queue<Member>>
  - finePolicy: FinePolicy, notifier: Notifier
  + borrow(memberId, isbn, date): Loan
  + returnCopy(barcode, date): long fine
  + reserve(memberId, isbn)

<<interface>> FinePolicy  + fine(loan, returnDate)   ^.. PerDayFine
<<interface>> Notifier    + notify(member, msg)      ^.. ConsoleNotifier
```

## Patterns used and why
- **Strategy** for `FinePolicy` (per-day, capped, waived for faculty).
- **Observer-style notifier** to inform reservers when a copy is held for them.
- **Enum with data** for member types (limits and loan days) - adding a type is one line.
- **Repository-like `Catalog`** separates search/storage from business rules.
- `LocalDate` passed explicitly to methods makes time-based logic testable (no hidden `now()`).

## Java implementation
```java
import java.time.*;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.stream.*;

enum CopyStatus { AVAILABLE, BORROWED, ON_HOLD }

enum MemberType {
    STUDENT(5, 14), FACULTY(10, 30);
    final int maxBooks, loanDays;
    MemberType(int max, int days) { maxBooks = max; loanDays = days; }
}

class Book {
    final String isbn, title, author;
    Book(String isbn, String title, String author) { this.isbn = isbn; this.title = title; this.author = author; }
}

class BookCopy {
    final String barcode; final Book book;
    CopyStatus status = CopyStatus.AVAILABLE;
    String heldFor;                                   // member id when ON_HOLD
    BookCopy(String barcode, Book book) { this.barcode = barcode; this.book = book; }
}

class Member {
    final String id, name; final MemberType type;
    int activeLoans = 0;
    Member(String id, String name, MemberType type) { this.id = id; this.name = name; this.type = type; }
}

class Loan {
    final BookCopy copy; final Member member; final LocalDate issueDate, dueDate;
    Loan(BookCopy c, Member m, LocalDate issue) {
        copy = c; member = m; issueDate = issue; dueDate = issue.plusDays(m.type.loanDays);
    }
}

class LibraryException extends RuntimeException { LibraryException(String m) { super(m); } }

interface FinePolicy { long fine(Loan loan, LocalDate returnDate); }

class PerDayFine implements FinePolicy {
    private final long perDay, cap;
    PerDayFine(long perDay, long cap) { this.perDay = perDay; this.cap = cap; }
    public long fine(Loan loan, LocalDate returned) {
        long late = ChronoUnit.DAYS.between(loan.dueDate, returned);
        return late <= 0 ? 0 : Math.min(cap, late * perDay);
    }
}

interface Notifier { void notify(Member m, String msg); }
class ConsoleNotifier implements Notifier {
    public void notify(Member m, String msg) { System.out.println("  [notify " + m.name + "] " + msg); }
}

class Catalog {
    private final Map<String, Book> books = new HashMap<>();
    private final Map<String, List<BookCopy>> copies = new HashMap<>();
    private final Map<String, BookCopy> byBarcode = new HashMap<>();

    void addBook(Book b) { books.putIfAbsent(b.isbn, b); }
    void addCopy(String isbn, String barcode) {
        Book b = books.get(isbn);
        if (b == null) throw new LibraryException("Unknown ISBN " + isbn);
        BookCopy c = new BookCopy(barcode, b);
        copies.computeIfAbsent(isbn, k -> new ArrayList<>()).add(c);
        byBarcode.put(barcode, c);
    }
    List<Book> searchByTitle(String q) {
        return books.values().stream().filter(b -> b.title.toLowerCase().contains(q.toLowerCase())).collect(Collectors.toList());
    }
    List<Book> searchByAuthor(String q) {
        return books.values().stream().filter(b -> b.author.toLowerCase().contains(q.toLowerCase())).collect(Collectors.toList());
    }
    Optional<BookCopy> copyFor(String isbn, String memberId) {
        List<BookCopy> list = copies.getOrDefault(isbn, List.of());
        Optional<BookCopy> held = list.stream()
            .filter(c -> c.status == CopyStatus.ON_HOLD && memberId.equals(c.heldFor)).findFirst();
        return held.isPresent() ? held : list.stream().filter(c -> c.status == CopyStatus.AVAILABLE).findFirst();
    }
    BookCopy byBarcode(String barcode) { return byBarcode.get(barcode); }
}
```

```java
class LibraryService {
    private final Catalog catalog;
    private final Map<String, Member> members = new HashMap<>();
    private final Map<String, Loan> activeLoans = new HashMap<>();          // barcode -> loan
    private final Map<String, Deque<Member>> reservations = new HashMap<>(); // isbn -> queue
    private final FinePolicy finePolicy;
    private final Notifier notifier;

    LibraryService(Catalog c, FinePolicy f, Notifier n) { catalog = c; finePolicy = f; notifier = n; }

    void addMember(Member m) { members.put(m.id, m); }

    private Member member(String id) {
        Member m = members.get(id);
        if (m == null) throw new LibraryException("Unknown member " + id);
        return m;
    }

    synchronized Loan borrow(String memberId, String isbn, LocalDate date) {
        Member m = member(memberId);
        if (m.activeLoans >= m.type.maxBooks) throw new LibraryException(m.name + " reached limit of " + m.type.maxBooks);
        BookCopy copy = catalog.copyFor(isbn, memberId)
            .orElseThrow(() -> new LibraryException("No copy available for " + isbn + "; please reserve"));
        copy.status = CopyStatus.BORROWED; copy.heldFor = null;
        Deque<Member> q = reservations.get(isbn);
        if (q != null) q.remove(m);
        m.activeLoans++;
        Loan loan = new Loan(copy, m, date);
        activeLoans.put(copy.barcode, loan);
        return loan;
    }

    synchronized long returnCopy(String barcode, LocalDate date) {
        Loan loan = activeLoans.remove(barcode);
        if (loan == null) throw new LibraryException("Copy " + barcode + " is not on loan");
        loan.member.activeLoans--;
        long fine = finePolicy.fine(loan, date);
        BookCopy copy = loan.copy;
        Deque<Member> q = reservations.get(copy.book.isbn);
        if (q != null && !q.isEmpty()) {
            Member next = q.poll();
            copy.status = CopyStatus.ON_HOLD; copy.heldFor = next.id;
            notifier.notify(next, "'" + copy.book.title + "' is ready for pickup");
        } else {
            copy.status = CopyStatus.AVAILABLE;
        }
        return fine;
    }

    synchronized void reserve(String memberId, String isbn) {
        Member m = member(memberId);
        Deque<Member> q = reservations.computeIfAbsent(isbn, k -> new ArrayDeque<>());
        if (q.contains(m)) throw new LibraryException("Already reserved");
        q.offer(m);
        System.out.println(m.name + " reserved " + isbn + " (position " + q.size() + ")");
    }
}

public class Main {
    public static void main(String[] args) {
        Catalog catalog = new Catalog();
        catalog.addBook(new Book("111", "Clean Code", "Robert Martin"));
        catalog.addBook(new Book("222", "Effective Java", "Joshua Bloch"));
        catalog.addCopy("111", "CC-1");
        catalog.addCopy("222", "EJ-1");
        catalog.addCopy("222", "EJ-2");

        LibraryService lib = new LibraryService(catalog, new PerDayFine(10, 500), new ConsoleNotifier());
        lib.addMember(new Member("m1", "Raj", MemberType.STUDENT));
        lib.addMember(new Member("m2", "Anita", MemberType.FACULTY));

        System.out.println("Search 'java': " + catalog.searchByTitle("java").stream().map(b -> b.title).toList());
        LocalDate d0 = LocalDate.of(2026, 1, 1);
        Loan l1 = lib.borrow("m1", "111", d0);
        System.out.println("Raj borrowed " + l1.copy.barcode + ", due " + l1.dueDate);
        try { lib.borrow("m2", "111", d0); } catch (LibraryException e) { System.out.println("Error: " + e.getMessage()); }
        lib.reserve("m2", "111");
        long fine = lib.returnCopy("CC-1", d0.plusDays(20));     // 6 days late
        System.out.println("Raj returned late, fine Rs " + fine);
        try { lib.borrow("m1", "111", d0.plusDays(20)); } catch (LibraryException e) { System.out.println("Error: " + e.getMessage()); }
        Loan l2 = lib.borrow("m2", "111", d0.plusDays(21));
        System.out.println("Anita borrowed held copy " + l2.copy.barcode + ", due " + l2.dueDate);
    }
}
```

## Extension questions
1. **Renewals:** allowed if no one has reserved the book; `Loan.dueDate` becomes mutable or a new loan is created.
2. **Hold expiry:** if the reserver does not pick up in 3 days, pass the copy to the next in queue (scheduled job).
3. **Different fine policies per member type:** `Map<MemberType, FinePolicy>` or a composite policy.
4. **Search at scale:** inverted index `Map<token, Set<isbn>>` for title/author keywords.
5. **Concurrency:** two members borrowing the last copy - the `synchronized` service methods serialise this; finer-grained locking per ISBN for throughput.
''',
["Separate Book (ISBN-level metadata) from BookCopy (physical item with barcode and status).",
 "Member types as an enum carrying borrowing limits and loan duration.",
 "Loans map barcode to member and due date; returns compute fines via a FinePolicy strategy.",
 "Reservations are a FIFO queue per ISBN; a returned copy goes ON_HOLD for the next reserver.",
 "Pass dates into methods instead of calling now() inside, so time-based rules are testable.",
 "Notifier interface decouples notifications (email/SMS/console) from library logic.",
 "Synchronize borrow/return/reserve or lock per ISBN to avoid two members taking the last copy."],
[("Why separate Book and BookCopy?",
  r'''A `Book` is the title-level entity (ISBN, title, author) shared by all physical copies; a `BookCopy` is a physical item with its own barcode, status, location and loan history. Search works on books, while borrowing, returns, holds and fines work on copies. Merging them either duplicates metadata per copy or makes it impossible to track which physical copy a member has. The same pattern appears elsewhere: product vs inventory item, movie vs show seat.'''),
 ("How do reservations work when a copy is returned?",
  r'''Each ISBN has a FIFO queue of members who reserved it. On return, if the queue is non-empty, the copy is marked `ON_HOLD` with `heldFor` set to the first member, who is notified. When searching for a copy to lend, a held copy is given only to that member. A scheduled job expires holds not picked up within N days and moves the copy to the next reserver or back to available.'''),
 ("How would you support different fine rules?",
  r'''Define `FinePolicy` with `fine(Loan, LocalDate)`. Implementations: per-day with a cap, a grace period, zero fine for faculty, or higher rates for reference books. The service receives the policy through its constructor, or picks one from a `Map<MemberType, FinePolicy>`. Adding a rule never changes the return logic - that is the Strategy pattern applied to satisfy the Open/Closed Principle.'''),
 ("How would you make time-dependent logic testable?",
  r'''Avoid calling `LocalDate.now()` deep inside business methods. Either pass the date as a parameter, as in my `borrow` and `returnCopy` methods, or inject a `java.time.Clock` and use `LocalDate.now(clock)`. Tests use `Clock.fixed(...)` or explicit dates to simulate late returns and hold expiry deterministically, with no sleeping or mocking of static methods.''')],
[ALLD, {"title": "awesome-low-level-design - Library Management System", "url": "https://github.com/ashishps1/awesome-low-level-design/blob/main/problems/library-management-system.md"},
 {"title": "Java SE Docs - java.time.Clock", "url": "https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/time/Clock.html"}]
))

save("p2", "problems", topics)
