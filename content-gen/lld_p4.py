from lld_common import *

topics = []

topics.append(T(
"chess-game", "Design a Chess Game", 13, "Advanced", 40,
"A lighter but complete chess design: board, polymorphic pieces with move rules, turn management, capture and check detection, with notes on castling and en passant.",
r'''
## Problem
Design a two-player chess game. Interviewers want a clean model - each piece knows its movement, the board validates paths, the game manages turns and end conditions - not every rule. Clarify scope: castling, en passant and promotion are extensions.

## Requirements
**P0**
1. 8x8 board with the standard initial position.
2. Players alternate (White first); a move is `from -> to` (e.g., `e2 -> e4`).
3. Each piece type validates its own movement; sliding pieces cannot jump (except the knight).
4. Cannot capture your own piece; cannot make a move that leaves your king in check.
5. Detect check; detect checkmate/stalemate as a stretch.

**P1:** castling, en passant, pawn promotion, move history/undo, PGN notation, timers.

## Entities
`Color`, `Position`, `Piece` (abstract) with `King`, `Queen`, `Rook`, `Bishop`, `Knight`, `Pawn`; `Board`, `Move`, `Player`, `Game`, `GameStatus`.

## Class diagram
```text
<<abstract>> Piece
  - color: Color
  + canMove(board, from, to): boolean     (piece-specific geometry + path check)
  + symbol(): char
   ^-- King  ^-- Queen  ^-- Rook  ^-- Bishop  ^-- Knight  ^-- Pawn

Position (record)  - row, col     + parse("e2")
Board   - grid: Piece[8][8]
        + get(pos), move(from,to), isPathClear(from,to), findKing(color), isAttacked(pos, byColor)
Move    - from, to, piece, captured
Game    - board, current: Color, status, history: Deque<Move>
        + makeMove("e2","e4"): validates turn, piece rules, self-check; switches turn
```

## Patterns used and why
- **Polymorphism / Strategy-per-piece**: `canMove` is overridden per piece, eliminating a `switch(pieceType)`. Queen reuses rook and bishop logic via shared helpers.
- **Factory** for the initial setup (`Board.standard()`).
- **Command** objects (`Move`) in a history stack enable undo and replay.

## Java implementation
```java
import java.util.*;

enum Color { WHITE, BLACK; Color opposite() { return this == WHITE ? BLACK : WHITE; } }
enum GameStatus { ACTIVE, CHECK, CHECKMATE, STALEMATE }

record Position(int row, int col) {      // row 0 = rank 1 (white side)
    static Position parse(String s) {
        if (s.length() != 2) throw new IllegalArgumentException("Bad square " + s);
        int c = s.charAt(0) - 'a', r = s.charAt(1) - '1';
        if (r < 0 || r > 7 || c < 0 || c > 7) throw new IllegalArgumentException("Bad square " + s);
        return new Position(r, c);
    }
    public String toString() { return "" + (char) ('a' + col) + (row + 1); }
}

abstract class Piece {
    final Color color;
    Piece(Color color) { this.color = color; }
    abstract boolean canMove(Board b, Position from, Position to);
    abstract char letter();
    char symbol() { return color == Color.WHITE ? Character.toUpperCase(letter()) : letter(); }

    protected static boolean straight(Board b, Position f, Position t) {
        return (f.row() == t.row() || f.col() == t.col()) && b.isPathClear(f, t);
    }
    protected static boolean diagonal(Board b, Position f, Position t) {
        return Math.abs(f.row() - t.row()) == Math.abs(f.col() - t.col()) && b.isPathClear(f, t);
    }
}

class King extends Piece {
    King(Color c) { super(c); }
    boolean canMove(Board b, Position f, Position t) {
        return Math.max(Math.abs(f.row() - t.row()), Math.abs(f.col() - t.col())) == 1;
    }
    char letter() { return 'k'; }
}
class Queen extends Piece {
    Queen(Color c) { super(c); }
    boolean canMove(Board b, Position f, Position t) { return straight(b, f, t) || diagonal(b, f, t); }
    char letter() { return 'q'; }
}
class Rook extends Piece {
    Rook(Color c) { super(c); }
    boolean canMove(Board b, Position f, Position t) { return straight(b, f, t); }
    char letter() { return 'r'; }
}
class Bishop extends Piece {
    Bishop(Color c) { super(c); }
    boolean canMove(Board b, Position f, Position t) { return diagonal(b, f, t); }
    char letter() { return 'b'; }
}
class Knight extends Piece {
    Knight(Color c) { super(c); }
    boolean canMove(Board b, Position f, Position t) {
        int dr = Math.abs(f.row() - t.row()), dc = Math.abs(f.col() - t.col());
        return dr * dc == 2;                     // (1,2) or (2,1); jumps over pieces
    }
    char letter() { return 'n'; }
}
class Pawn extends Piece {
    Pawn(Color c) { super(c); }
    boolean canMove(Board b, Position f, Position t) {
        int dir = color == Color.WHITE ? 1 : -1, startRow = color == Color.WHITE ? 1 : 6;
        int dr = t.row() - f.row(), dc = Math.abs(t.col() - f.col());
        Piece target = b.get(t);
        if (dc == 0 && target == null) {
            if (dr == dir) return true;
            return f.row() == startRow && dr == 2 * dir && b.get(new Position(f.row() + dir, f.col())) == null;
        }
        return dc == 1 && dr == dir && target != null;   // diagonal capture
    }
    char letter() { return 'p'; }
}
```

```java
class Board {
    private final Piece[][] grid = new Piece[8][8];

    static Board standard() {
        Board b = new Board();
        Color[] colors = {Color.WHITE, Color.BLACK};
        for (Color c : colors) {
            int back = c == Color.WHITE ? 0 : 7, pawns = c == Color.WHITE ? 1 : 6;
            Piece[] row = {new Rook(c), new Knight(c), new Bishop(c), new Queen(c), new King(c), new Bishop(c), new Knight(c), new Rook(c)};
            for (int col = 0; col < 8; col++) { b.grid[back][col] = row[col]; b.grid[pawns][col] = new Pawn(c); }
        }
        return b;
    }

    Piece get(Position p) { return grid[p.row()][p.col()]; }
    void set(Position p, Piece piece) { grid[p.row()][p.col()] = piece; }

    boolean isPathClear(Position f, Position t) {
        int dr = Integer.signum(t.row() - f.row()), dc = Integer.signum(t.col() - f.col());
        int r = f.row() + dr, c = f.col() + dc;
        while (r != t.row() || c != t.col()) {
            if (grid[r][c] != null) return false;
            r += dr; c += dc;
        }
        return true;
    }

    Position findKing(Color color) {
        for (int r = 0; r < 8; r++) for (int c = 0; c < 8; c++)
            if (grid[r][c] instanceof King && grid[r][c].color == color) return new Position(r, c);
        throw new IllegalStateException("King missing");
    }

    boolean isAttacked(Position target, Color by) {
        for (int r = 0; r < 8; r++) for (int c = 0; c < 8; c++) {
            Piece p = grid[r][c];
            if (p != null && p.color == by && p.canMove(this, new Position(r, c), target)) return true;
        }
        return false;
    }

    void print() {
        for (int r = 7; r >= 0; r--) {
            StringBuilder sb = new StringBuilder((r + 1) + " ");
            for (int c = 0; c < 8; c++) sb.append(grid[r][c] == null ? '.' : grid[r][c].symbol()).append(' ');
            System.out.println(sb);
        }
        System.out.println("  a b c d e f g h");
    }
}

record Move(Position from, Position to, Piece piece, Piece captured) { }

class InvalidMoveException extends RuntimeException { InvalidMoveException(String m) { super(m); } }

class Game {
    private final Board board = Board.standard();
    private Color turn = Color.WHITE;
    private GameStatus status = GameStatus.ACTIVE;
    private final Deque<Move> history = new ArrayDeque<>();

    GameStatus move(String fromSq, String toSq) {
        if (status == GameStatus.CHECKMATE || status == GameStatus.STALEMATE) throw new InvalidMoveException("Game over");
        Position from = Position.parse(fromSq), to = Position.parse(toSq);
        Piece piece = board.get(from);
        if (piece == null) throw new InvalidMoveException("No piece at " + from);
        if (piece.color != turn) throw new InvalidMoveException("It is " + turn + "'s turn");
        if (!isLegal(from, to)) throw new InvalidMoveException("Illegal move " + from + "->" + to);
        Piece captured = board.get(to);
        board.set(to, piece); board.set(from, null);
        history.push(new Move(from, to, piece, captured));
        turn = turn.opposite();
        boolean inCheck = board.isAttacked(board.findKing(turn), turn.opposite());
        boolean hasMove = hasAnyLegalMove(turn);
        status = !hasMove ? (inCheck ? GameStatus.CHECKMATE : GameStatus.STALEMATE) : (inCheck ? GameStatus.CHECK : GameStatus.ACTIVE);
        return status;
    }

    /** Geometry + own-piece check + does not leave own king in check (simulate and undo). */
    private boolean isLegal(Position from, Position to) {
        if (from.equals(to)) return false;
        Piece piece = board.get(from), target = board.get(to);
        if (target != null && target.color == piece.color) return false;
        if (!piece.canMove(board, from, to)) return false;
        board.set(to, piece); board.set(from, null);
        boolean selfCheck = board.isAttacked(board.findKing(piece.color), piece.color.opposite());
        board.set(from, piece); board.set(to, target);
        return !selfCheck;
    }

    private boolean hasAnyLegalMove(Color color) {
        for (int r = 0; r < 8; r++) for (int c = 0; c < 8; c++) {
            Position f = new Position(r, c);
            Piece p = board.get(f);
            if (p == null || p.color != color) continue;
            for (int r2 = 0; r2 < 8; r2++) for (int c2 = 0; c2 < 8; c2++)
                if (isLegal(f, new Position(r2, c2))) return true;
        }
        return false;
    }

    Board board() { return board; }
}

public class Main {
    public static void main(String[] args) {
        Game g = new Game();
        String[][] foolsMate = {{"f2", "f3"}, {"e7", "e5"}, {"g2", "g4"}, {"d8", "h4"}};
        try { g.move("e7", "e5"); } catch (InvalidMoveException e) { System.out.println("Error: " + e.getMessage()); }
        try { g.move("a1", "a3"); } catch (InvalidMoveException e) { System.out.println("Error: " + e.getMessage()); }
        for (String[] m : foolsMate) System.out.println(m[0] + "->" + m[1] + " : " + g.move(m[0], m[1]));
        g.board().print();
    }
}
```

The demo plays "Fool's Mate", the fastest checkmate.

## Extension questions
1. **Castling:** `hasMoved` flags; clear path; king never passes through attacked squares.
2. **En passant:** uses the last move from `history`.
3. **Promotion:** replace the pawn via a `PieceFactory`.
4. **Online play:** one `Game` per match id, server-side validation, Observer pushes moves to clients.
''',
["Each piece subclass overrides canMove with its geometry; shared helpers handle straight and diagonal sliding.",
 "The board validates path clearance for sliding pieces; knights skip the path check.",
 "Game validation pipeline: piece exists, correct turn, not capturing own piece, geometry, no self-check.",
 "Self-check is detected by simulating the move, testing if the king is attacked, then reverting.",
 "Checkmate = in check with no legal moves; stalemate = not in check with no legal moves.",
 "Moves are Command-like records in a history stack for undo, en passant and notation.",
 "Scope clearly: castling, en passant and promotion are typical extensions, not P0."],
[("How do you avoid a giant switch on piece type?",
  r'''Make `Piece` abstract with an abstract `canMove(board, from, to)` and let each subclass implement its geometry - runtime polymorphism. Shared helpers in the base class (`straight`, `diagonal`) avoid duplication, so `Queen` is just `straight || diagonal`. The game calls `piece.canMove(...)` without knowing the type. Adding a fairy piece (say, an Archbishop combining bishop and knight) means one new class, satisfying the Open/Closed Principle.'''),
 ("How do you detect that a move leaves the king in check?",
  r'''Temporarily apply the move on the board, find the mover's king, and check whether any opponent piece can move to that square (`isAttacked`), then restore the original pieces. If the king is attacked, the move is illegal. This handles pinned pieces and moving the king into check uniformly. For efficiency, engines compute attack maps incrementally, but simulate-and-revert is the clear and correct approach for an interview.'''),
 ("How would you implement castling?",
  r'''Track whether the king and each rook have moved (a `hasMoved` flag updated on every move, restored on undo). Castling is legal when neither has moved, the squares between them are empty, the king is not currently in check, and the squares the king passes through and lands on are not attacked. The move relocates both king and rook, so it is best modelled as a special `Move` subtype (`CastleMove`) whose execute and undo handle both pieces.'''),
 ("How would you support undo in chess?",
  r'''Store each executed move as an object containing from, to, the moving piece, the captured piece, and any special-state changes (castling rights, en passant square, promotion piece, hasMoved flags). Push it onto a history stack. Undo pops the last move and restores everything it recorded, then switches the turn back. This is the Command pattern; the same history also generates PGN notation and supports replay.''')],
[ALLD, {"title": "awesome-low-level-design - Chess Game", "url": "https://github.com/ashishps1/awesome-low-level-design/blob/main/problems/chess-game.md"},
 {"title": "FIDE Laws of Chess", "url": "https://handbook.fide.com/chapter/E012023"}]
))

topics.append(T(
"hotel-booking", "Design a Hotel Booking System", 14, "Intermediate", 45,
"Design a hotel reservation system with room types, date-range availability, overlap-safe booking, pricing strategies and cancellation.",
r'''
## Problem
Design the core of a hotel management / booking system (like OYO, MakeMyTrip's hotel module): search available rooms for a date range, book, check in/out, cancel, and price stays.

## Requirements
**P0**
1. Hotel has rooms of types `SINGLE`, `DOUBLE`, `SUITE`, each with a base nightly price.
2. Search available rooms by type for `[checkIn, checkOut)` dates.
3. Book a room for a guest; **no overlapping bookings** for the same room, even under concurrent requests.
4. Cancel a booking (refund based on policy); check-in / check-out status changes.
5. Price = nights x nightly rate, with weekend surcharge.

**P1:** multiple hotels/cities, coupons, room service charges on the invoice, housekeeping status, overbooking policy.

## Entities
`Room`, `RoomType`, `Guest`, `Booking` (`BookingStatus`), `DateRange`, `PricingStrategy`, `CancellationPolicy`, `BookingService`, `Hotel`.

## Class diagram
```text
Hotel 1 *-- * Room(number, type)
Booking - id, room, guest, range: DateRange, amount, status
DateRange (record) - start, end (end exclusive)  + overlaps(other), nights()

BookingService
  - bookingsByRoom: Map<roomNumber, TreeMap<LocalDate, Booking>>   (sorted by check-in)
  - pricing: PricingStrategy
  - cancellation: CancellationPolicy
  + search(type, range): List<Room>
  + book(guest, roomNo, range): Booking
  + cancel(bookingId, today): refund
  + checkIn(id), checkOut(id)

<<interface>> PricingStrategy    ^.. WeekendSurchargePricing
<<interface>> CancellationPolicy ^.. TieredCancellation
```

## Overlap check - the core algorithm
Two half-open ranges `[s1, e1)` and `[s2, e2)` overlap iff `s1 < e2 && s2 < e1`. Using half-open ranges means a guest checking out on the 12th and another checking in on the 12th do **not** conflict.

Per room, keep bookings in a `TreeMap<checkIn, Booking>`. To test a new range, only two neighbours matter: the booking with the greatest check-in before the new check-out (`lowerEntry(newEnd)`); if it ends after the new start, there is a conflict. That is **O(log n)** instead of scanning all bookings.

## Patterns used and why
- **Strategy** for pricing and cancellation (seasonal, weekend, member discounts; flexible vs non-refundable).
- **State-like lifecycle** for `Booking`: `CONFIRMED -> CHECKED_IN -> CHECKED_OUT`, or `CONFIRMED -> CANCELLED`; illegal transitions throw.
- **Value object** `DateRange` (immutable record) encapsulates overlap logic.
- **Per-room locking** (`synchronized` on the room's map) so bookings of different rooms proceed in parallel.

## Java implementation
```java
import java.time.*;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.*;

enum RoomType {
    SINGLE(2000), DOUBLE(3500), SUITE(8000);
    final long nightly;
    RoomType(long n) { nightly = n; }
}
enum BookingStatus { CONFIRMED, CHECKED_IN, CHECKED_OUT, CANCELLED }

record DateRange(LocalDate start, LocalDate end) {
    DateRange {
        if (!end.isAfter(start)) throw new IllegalArgumentException("Check-out must be after check-in");
    }
    boolean overlaps(DateRange o) { return start.isBefore(o.end) && o.start.isBefore(end); }
    long nights() { return ChronoUnit.DAYS.between(start, end); }
}

record Room(String number, RoomType type) { }
record Guest(String id, String name) { }

class Booking {
    final String id; final Room room; final Guest guest; final DateRange range; final long amount;
    BookingStatus status = BookingStatus.CONFIRMED;
    Booking(String id, Room room, Guest guest, DateRange range, long amount) {
        this.id = id; this.room = room; this.guest = guest; this.range = range; this.amount = amount;
    }
    void transition(BookingStatus from, BookingStatus to) {
        if (status != from) throw new IllegalStateException("Booking " + id + " is " + status + ", cannot move to " + to);
        status = to;
    }
}

interface PricingStrategy { long price(RoomType type, DateRange range); }

class WeekendSurchargePricing implements PricingStrategy {
    private final double surcharge;
    WeekendSurchargePricing(double surcharge) { this.surcharge = surcharge; }
    public long price(RoomType type, DateRange r) {
        long total = 0;
        for (LocalDate d = r.start(); d.isBefore(r.end()); d = d.plusDays(1)) {
            boolean weekend = d.getDayOfWeek() == DayOfWeek.FRIDAY || d.getDayOfWeek() == DayOfWeek.SATURDAY;
            total += Math.round(type.nightly * (weekend ? 1 + surcharge : 1));
        }
        return total;
    }
}

interface CancellationPolicy { long refund(Booking b, LocalDate today); }

class TieredCancellation implements CancellationPolicy {
    public long refund(Booking b, LocalDate today) {
        long daysBefore = ChronoUnit.DAYS.between(today, b.range.start());
        if (daysBefore >= 7) return b.amount;          // full refund
        if (daysBefore >= 2) return b.amount / 2;      // 50%
        return 0;                                      // no refund
    }
}

class RoomUnavailableException extends RuntimeException { RoomUnavailableException(String m) { super(m); } }
```

```java
class BookingService {
    private final Map<String, Room> rooms = new LinkedHashMap<>();
    private final Map<String, TreeMap<LocalDate, Booking>> byRoom = new ConcurrentHashMap<>();
    private final Map<String, Booking> bookings = new ConcurrentHashMap<>();
    private final PricingStrategy pricing; private final CancellationPolicy cancellation;
    private final AtomicIdGen ids = new AtomicIdGen();

    BookingService(PricingStrategy p, CancellationPolicy c) { pricing = p; cancellation = c; }

    void addRoom(Room r) { rooms.put(r.number(), r); byRoom.put(r.number(), new TreeMap<>()); }

    private boolean isFree(TreeMap<LocalDate, Booking> map, DateRange range) {
        // Only the booking with the latest check-in before our check-out can overlap
        // (cancelled bookings are removed from the map, the loop is just defensive)
        Map.Entry<LocalDate, Booking> e = map.lowerEntry(range.end());
        while (e != null && e.getValue().status == BookingStatus.CANCELLED) e = map.lowerEntry(e.getKey());
        return e == null || !e.getValue().range.overlaps(range);
    }

    List<Room> search(RoomType type, DateRange range) {
        return rooms.values().stream()
            .filter(r -> r.type() == type)
            .filter(r -> { TreeMap<LocalDate, Booking> m = byRoom.get(r.number()); synchronized (m) { return isFree(m, range); } })
            .collect(Collectors.toList());
    }

    Booking book(Guest guest, String roomNo, DateRange range) {
        Room room = rooms.get(roomNo);
        if (room == null) throw new IllegalArgumentException("No room " + roomNo);
        TreeMap<LocalDate, Booking> map = byRoom.get(roomNo);
        synchronized (map) {                               // per-room lock
            if (!isFree(map, range)) throw new RoomUnavailableException("Room " + roomNo + " not free for " + range);
            Booking b = new Booking(ids.next(), room, guest, range, pricing.price(room.type(), range));
            map.put(range.start(), b);
            bookings.put(b.id, b);
            return b;
        }
    }

    long cancel(String bookingId, LocalDate today) {
        Booking b = get(bookingId);
        synchronized (byRoom.get(b.room.number())) {
            b.transition(BookingStatus.CONFIRMED, BookingStatus.CANCELLED);
            byRoom.get(b.room.number()).remove(b.range.start());
        }
        return cancellation.refund(b, today);
    }

    void checkIn(String id) { get(id).transition(BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN); }
    void checkOut(String id) { get(id).transition(BookingStatus.CHECKED_IN, BookingStatus.CHECKED_OUT); }

    private Booking get(String id) {
        Booking b = bookings.get(id);
        if (b == null) throw new IllegalArgumentException("No booking " + id);
        return b;
    }
}

class AtomicIdGen {
    private final java.util.concurrent.atomic.AtomicLong seq = new java.util.concurrent.atomic.AtomicLong();
    String next() { return "BK" + seq.incrementAndGet(); }
}

public class Main {
    public static void main(String[] args) throws Exception {
        BookingService svc = new BookingService(new WeekendSurchargePricing(0.25), new TieredCancellation());
        svc.addRoom(new Room("101", RoomType.DOUBLE));
        svc.addRoom(new Room("102", RoomType.DOUBLE));
        svc.addRoom(new Room("201", RoomType.SUITE));
        Guest raj = new Guest("g1", "Raj"), meera = new Guest("g2", "Meera");

        DateRange r1 = new DateRange(LocalDate.of(2026, 12, 10), LocalDate.of(2026, 12, 13)); // Thu-Sun
        Booking b1 = svc.book(raj, "101", r1);
        System.out.println(b1.id + " room 101 " + r1.nights() + " nights = Rs " + b1.amount);

        DateRange r2 = new DateRange(LocalDate.of(2026, 12, 12), LocalDate.of(2026, 12, 14));
        System.out.println("Free DOUBLE rooms for 12-14 Dec: " + svc.search(RoomType.DOUBLE, r2).stream().map(Room::number).toList());
        DateRange r3 = new DateRange(LocalDate.of(2026, 12, 13), LocalDate.of(2026, 12, 15));
        System.out.println("Back-to-back booking on 101: " + svc.book(meera, "101", r3).id);

        // Concurrent race for room 102
        ExecutorService pool = Executors.newFixedThreadPool(4);
        List<Callable<String>> tasks = new ArrayList<>();
        for (int i = 0; i < 4; i++) {
            final int n = i;
            tasks.add(() -> {
                try { return "guest" + n + " got " + svc.book(new Guest("x" + n, "G" + n), "102", r2).id; }
                catch (RoomUnavailableException e) { return "guest" + n + " rejected"; }
            });
        }
        long winners = pool.invokeAll(tasks).stream().map(f -> { try { return f.get(); } catch (Exception e) { return ""; } })
            .peek(System.out::println).filter(s -> s.contains("got")).count();
        pool.shutdown();
        System.out.println("Winners for room 102: " + winners);

        System.out.println("Refund on cancel 5 days before: Rs " + svc.cancel(b1.id, LocalDate.of(2026, 12, 5)));
        System.out.println("Room 101 free again for 10-12 Dec: " + svc.search(RoomType.DOUBLE, new DateRange(LocalDate.of(2026, 12, 10), LocalDate.of(2026, 12, 12))).stream().map(Room::number).toList());
        try { svc.checkIn(b1.id); } catch (IllegalStateException e) { System.out.println("Error: " + e.getMessage()); }
    }
}
```

## Extension questions
1. **Book "any DOUBLE room" instead of a specific one:** iterate free rooms and attempt `book` until one succeeds (another thread may win first).
2. **Inventory-count model:** large OTAs track counts per room type per date (`Map<date, available>`) rather than individual rooms; a booking decrements each night atomically and the hotel assigns room numbers at check-in.
3. **Distributed:** DB table `room_night(room_id, date)` with a unique constraint, or optimistic locking on per-date inventory rows.
4. **Invoice with extras:** `Invoice` aggregating room charges and services (Decorator or line items), taxes via strategy.
5. **Holds during payment:** temporary hold with expiry, similar to BookMyShow seat locks.
''',
["Use half-open date ranges [checkIn, checkOut); ranges overlap iff s1 < e2 and s2 < e1.",
 "Keep bookings per room in a TreeMap keyed by check-in for O(log n) overlap checks via lowerEntry.",
 "Lock per room so bookings for different rooms proceed concurrently without double booking.",
 "Pricing and cancellation refunds are Strategies; weekend surcharges computed per night.",
 "Booking lifecycle transitions are guarded: CONFIRMED -> CHECKED_IN -> CHECKED_OUT or CANCELLED.",
 "DateRange as an immutable record encapsulates validation and overlap logic.",
 "At scale, OTAs track per-date inventory counts per room type and enforce uniqueness in the database."],
[("How do you check if a room is available for a date range efficiently?",
  r'''Represent stays as half-open intervals. Store each room's bookings in a `TreeMap` keyed by check-in date. Because bookings of one room never overlap each other, the only booking that can conflict with a new range is the one with the greatest check-in strictly before the new check-out (`lowerEntry(newEnd)`); if its check-out is after the new check-in, there is a conflict. That is O(log n) per room instead of a linear scan.'''),
 ("How do you prevent two guests from booking the same room for overlapping dates at the same time?",
  r'''Make check-and-insert atomic per room. In memory I synchronize on that room's booking map, so concurrent requests for the same room serialize while different rooms proceed in parallel. In a database, model per-night rows (`room_id, date`) with a unique constraint so the second insert fails, or use per-date inventory counts with optimistic locking (`UPDATE ... SET available = available - 1 WHERE available > 0 AND version = ?`).'''),
 ("Why use half-open date intervals?",
  r'''A hotel stay naturally occupies nights from check-in up to, but not including, the check-out date. With `[start, end)`, one guest checking out on the 12th and another checking in on the 12th do not overlap, which is the correct business behaviour. Night counts become `end - start` without off-by-one errors, and the overlap condition `s1 < e2 && s2 < e1` stays simple.'''),
 ("How would you support different cancellation policies per rate plan?",
  r'''Model `CancellationPolicy` as a strategy with `refund(booking, today)`: fully refundable until 7 days before, 50% until 2 days, non-refundable, and so on. Attach the chosen policy to each booking at booking time (its rate plan) so later policy changes do not affect existing reservations. The cancellation flow simply calls `booking.policy().refund(...)`, and new policies are just new classes.''')],
[ALLD, {"title": "awesome-low-level-design - Hotel Management System", "url": "https://github.com/ashishps1/awesome-low-level-design/blob/main/problems/hotel-management-system.md"},
 {"title": "Java SE Docs - TreeMap (NavigableMap)", "url": "https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/TreeMap.html"}]
))

topics.append(T(
"pub-sub-message-queue", "Design a Pub-Sub Message Queue", 15, "Advanced", 50,
"Build a Kafka-inspired in-memory message queue with topics, multiple subscribers, per-subscriber offsets, async consumer workers and replay.",
r'''
## Problem
Design an in-memory publish-subscribe message queue (a common Flipkart/PhonePe machine-coding question). Publishers send messages to named topics; subscribers register on topics and consume messages independently and concurrently, each at its own pace.

## Requirements
**P0**
1. Create topics; publish messages to a topic.
2. Multiple subscribers per topic; every subscriber receives every message of the topic (fan-out).
3. Subscribers consume in parallel and in order; a slow subscriber must not block others or the publisher.
4. Each subscriber tracks its own **offset**; it can be reset to replay messages.
5. Thread-safe.

**P1:** consumer groups (each message to one member of a group), retries/dead-letter queue, message TTL/retention, partitions, back-pressure.

## Entities
`Message`, `Topic` (append-only list of messages), `Subscriber` (interface with `consume`), `TopicSubscriber` (subscriber + offset), `SubscriberWorker` (thread per subscription), `TopicHandler`, `Broker` (facade API).

## Class diagram
```text
Broker (facade)
  - topics: ConcurrentHashMap<name, Topic>
  - handlers: ConcurrentHashMap<name, TopicHandler>
  + createTopic(name), subscribe(topic, subscriber), publish(topic, msg), resetOffset(topic, sub, offset)

Topic          - name, messages: CopyOnWriteArrayList<Message>  (append-only log)
TopicSubscriber- subscriber, offset: AtomicInteger
TopicHandler   - topic, workers: Map<subscriberId, SubscriberWorker>
               + publish(): wakes all workers
SubscriberWorker implements Runnable
  loop: while offset < topic.size -> consume(messages[offset]), offset++
        else wait() until notified

<<interface>> Subscriber  + id(), consume(Message)
```

## Design choices (Kafka-like)
- Messages are **appended to the topic log and never removed** on consumption; each subscriber has its own offset. This gives fan-out, replay, and independent speeds for free.
- Each subscription has a **dedicated worker thread** that sleeps (`wait`) when caught up and is woken (`notify`) on publish. In production you would use a thread pool and push to per-subscriber queues; the offset model stays.
- `publish` is O(1) and never blocks on consumers.

## Patterns used and why
- **Observer / Publish-Subscribe**: topics notify registered subscribers; publishers and subscribers are fully decoupled.
- **Facade**: `Broker` provides a tiny API over topics, handlers and workers.
- **Producer-consumer** with guarded wait/notify per subscriber worker.
- **Strategy (extension)**: retry policy, delivery semantics (at-most-once vs at-least-once).

## Java implementation
```java
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

record Message(String id, String payload, long timestamp) { }

interface Subscriber {
    String id();
    void consume(Message m) throws Exception;
}

class Topic {
    private final String name;
    private final List<Message> messages = new CopyOnWriteArrayList<>();
    Topic(String name) { this.name = name; }
    String name() { return name; }
    void append(Message m) { messages.add(m); }
    int size() { return messages.size(); }
    Message get(int i) { return messages.get(i); }
}

class TopicSubscriber {
    final Subscriber subscriber;
    final AtomicInteger offset = new AtomicInteger(0);
    TopicSubscriber(Subscriber s) { subscriber = s; }
}

class SubscriberWorker implements Runnable {
    private final Topic topic;
    private final TopicSubscriber ts;
    private volatile boolean running = true;

    SubscriberWorker(Topic topic, TopicSubscriber ts) { this.topic = topic; this.ts = ts; }

    public void run() {
        try {
            while (running) {
                Message m; int idx;
                synchronized (ts) {
                    while (running && ts.offset.get() >= topic.size()) ts.wait();   // guarded wait
                    if (!running) break;
                    idx = ts.offset.get();
                    m = topic.get(idx);
                }
                try {
                    ts.subscriber.consume(m);
                } catch (Exception e) {
                    System.out.println("  " + ts.subscriber.id() + " failed on " + m.id() + ": " + e.getMessage() + " (skipping)");
                }
                ts.offset.compareAndSet(idx, idx + 1);     // no-op if offset was reset meanwhile
            }
        } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }

    void wake() { synchronized (ts) { ts.notify(); } }
    void stop() { running = false; wake(); }
}

class TopicHandler {
    private final Topic topic;
    private final Map<String, SubscriberWorker> workers = new ConcurrentHashMap<>();
    private final Map<String, TopicSubscriber> subs = new ConcurrentHashMap<>();
    TopicHandler(Topic topic) { this.topic = topic; }

    void addSubscriber(Subscriber s) {
        TopicSubscriber ts = new TopicSubscriber(s);
        SubscriberWorker w = new SubscriberWorker(topic, ts);
        if (subs.putIfAbsent(s.id(), ts) != null) throw new IllegalArgumentException("Already subscribed: " + s.id());
        workers.put(s.id(), w);
        Thread t = new Thread(w, "worker-" + topic.name() + "-" + s.id());
        t.setDaemon(true);
        t.start();
    }

    void publish() { workers.values().forEach(SubscriberWorker::wake); }

    void resetOffset(String subId, int offset) {
        TopicSubscriber ts = subs.get(subId);
        synchronized (ts) { ts.offset.set(offset); }
        workers.get(subId).wake();
    }

    void shutdown() { workers.values().forEach(SubscriberWorker::stop); }
}
```

```java
class Broker {
    private final Map<String, Topic> topics = new ConcurrentHashMap<>();
    private final Map<String, TopicHandler> handlers = new ConcurrentHashMap<>();
    private final AtomicLong ids = new AtomicLong();

    void createTopic(String name) {
        Topic t = new Topic(name);
        if (topics.putIfAbsent(name, t) != null) throw new IllegalArgumentException("Topic exists: " + name);
        handlers.put(name, new TopicHandler(t));
    }

    void subscribe(String topic, Subscriber s) { handler(topic).addSubscriber(s); }

    String publish(String topic, String payload) {
        Topic t = topics.get(topic);
        if (t == null) throw new IllegalArgumentException("No topic " + topic);
        Message m = new Message("M" + ids.incrementAndGet(), payload, System.currentTimeMillis());
        t.append(m);
        handler(topic).publish();
        return m.id();
    }

    void resetOffset(String topic, String subId, int offset) { handler(topic).resetOffset(subId, offset); }
    void shutdown() { handlers.values().forEach(TopicHandler::shutdown); }

    private TopicHandler handler(String topic) {
        TopicHandler h = handlers.get(topic);
        if (h == null) throw new IllegalArgumentException("No topic " + topic);
        return h;
    }
}

class PrintingSubscriber implements Subscriber {
    private final String id; private final long delayMs;
    final List<String> received = Collections.synchronizedList(new ArrayList<>());
    PrintingSubscriber(String id, long delayMs) { this.id = id; this.delayMs = delayMs; }
    public String id() { return id; }
    public void consume(Message m) throws Exception {
        Thread.sleep(delayMs);                         // simulate work; slow consumer
        if (m.payload().contains("bad")) throw new IllegalArgumentException("cannot parse");
        received.add(m.payload());
    }
}

public class Main {
    public static void main(String[] args) throws Exception {
        Broker broker = new Broker();
        broker.createTopic("orders");
        PrintingSubscriber fast = new PrintingSubscriber("analytics", 5);
        PrintingSubscriber slow = new PrintingSubscriber("email", 40);
        broker.subscribe("orders", fast);
        broker.subscribe("orders", slow);

        long t0 = System.currentTimeMillis();
        for (int i = 1; i <= 4; i++) broker.publish("orders", "order-" + i);
        broker.publish("orders", "bad-order");
        System.out.println("Publisher finished in " + (System.currentTimeMillis() - t0) + " ms (not blocked by slow consumer)");

        Thread.sleep(400);
        System.out.println("analytics got " + fast.received);
        System.out.println("email got     " + slow.received);

        broker.resetOffset("orders", "analytics", 2);   // replay from offset 2
        Thread.sleep(200);
        System.out.println("analytics after replay " + fast.received);
        try { broker.publish("payments", "x"); } catch (IllegalArgumentException e) { System.out.println("Error: " + e.getMessage()); }
        broker.shutdown();
    }
}
```

## Extension questions
1. **Consumer groups:** subscribers in the same group share one offset (or partitions are assigned to members), so each message goes to one member - competing consumers.
2. **At-least-once delivery and retries:** advance the offset only after successful `consume`; retry with backoff N times, then publish to a dead-letter topic.
3. **Retention:** drop messages older than T or beyond N per topic; offsets become absolute (store base offset).
4. **Partitions for scale:** a topic split into partitions by key hash preserves per-key ordering while allowing parallel consumers.
5. **Thread pool instead of thread per subscriber:** each publish schedules a drain task per subscriber on an executor; an `AtomicBoolean` "draining" flag per subscriber keeps ordering.
6. **Back-pressure:** bounded topics where publish blocks or fails when consumers lag too far.
''',
["Store messages in an append-only topic log; subscribers keep independent offsets (Kafka model).",
 "Fan-out is free: every subscriber reads the same log at its own pace, and offsets enable replay.",
 "Each subscription has a worker that waits when caught up and is notified on publish (guarded wait in a loop).",
 "Publishing is O(1) and never blocks on slow consumers.",
 "Broker is a Facade over topics, handlers and workers; Observer/Pub-Sub decouples producers and consumers.",
 "Failure handling: retry with backoff, then dead-letter topic; commit the offset after successful processing for at-least-once.",
 "Consumer groups and partitions are the standard scaling extensions."],
[("Why use offsets instead of deleting messages after delivery?",
  r'''With an append-only log and per-subscriber offsets, each subscriber progresses independently: a slow email service does not delay analytics, and neither blocks the publisher. Messages are written once regardless of subscriber count (no per-subscriber copies). Replay becomes trivial - reset the offset - which is invaluable for recovering from bugs or onboarding a new consumer. Retention policies then delete old messages by time or size rather than on consumption. This is exactly Kafka's design.'''),
 ("How do you guarantee ordering and at-least-once delivery?",
  r'''Ordering per subscriber comes from a single worker processing messages sequentially by offset. For at-least-once, the offset is committed only after `consume` succeeds; if the consumer crashes mid-processing, it restarts from the last committed offset and may see a message twice, so consumers must be idempotent (dedupe by message id). At-most-once commits before processing. Exactly-once needs idempotent consumers plus transactional offset commits.'''),
 ("How would you implement consumer groups?",
  r'''A consumer group is a set of subscribers that share the work: each message goes to only one member. Either keep one shared offset per group and let members atomically claim the next offset (`getAndIncrement`), which loses strict ordering, or split the topic into partitions and assign each partition to exactly one member, which preserves per-partition order. Rebalancing reassigns partitions when members join or leave.'''),
 ("What happens if a subscriber keeps failing on a message?",
  r'''It must not block the subscriber forever (a poison message). Retry a bounded number of times with exponential backoff; if it still fails, publish the message plus error details to a dead-letter topic and advance the offset. Operators can inspect the dead-letter topic and replay messages after a fix. My demo simply logs and skips; a `RetryPolicy` strategy would make this configurable per subscriber.''')],
[{"title": "workat.tech - Design a Pub-Sub / Message Queue (machine coding)", "url": "https://workat.tech/machine-coding/practice"},
 {"title": "Apache Kafka - Introduction (topics, partitions, offsets)", "url": "https://kafka.apache.org/intro"}, JDOC]
))

save("p4", "problems", topics)
