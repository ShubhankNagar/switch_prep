from cs_common import build, B, I, A

notes = [
("OS Basics, Processes & Threads", r"""
An **operating system** is system software that manages hardware resources (CPU, memory, disk, devices) and provides services to programs. Core jobs: process management, memory management, file systems, I/O/device management, security and protection.

### Kernel, user mode, system calls
- **Kernel mode** – full hardware access; **user mode** – restricted. A program requests OS services via a **system call** (`read`, `write`, `fork`, `open`), which traps into kernel mode.
- **Kernel types:** *monolithic* (Linux – all services in kernel space, fast), *microkernel* (minimal kernel, services in user space – more robust, slower IPC), *hybrid* (Windows NT, macOS XNU).

### Process
A **process is a program in execution**. It has its own:
- Address space: **text** (code), **data** (globals), **heap** (dynamic allocation), **stack** (function frames).
- **PCB (Process Control Block)**: PID, state, program counter, CPU registers, scheduling info, memory maps, open files.

**Process states:** New → Ready → Running → (Waiting/Blocked on I/O) → Ready … → Terminated.
- Running → Ready: preempted by scheduler (time slice over).
- Running → Waiting: requests I/O.
- Waiting → Ready: I/O complete.

`fork()` creates a child process (copy of parent, using **copy-on-write**); `exec()` replaces its memory with a new program. A **zombie** process has finished but its parent hasn't called `wait()` to read its exit status. An **orphan** is a child whose parent died; it is adopted by `init`/`systemd`.

### Thread
A **thread** is the smallest unit of CPU scheduling — a path of execution within a process. Threads of the same process **share** code, data, heap and open files, but each has its **own stack, registers and program counter**.

| | Process | Thread |
|---|---|---|
| Memory | Separate address space | Shared within process |
| Creation/switch cost | Heavy | Light |
| Communication | IPC (pipes, sockets, shared mem) | Shared variables (needs sync) |
| Fault isolation | Crash doesn't affect others | One thread crash can kill the process |
| Example | Each Chrome tab | Tomcat request-handling threads |

### User-level vs kernel-level threads
- **User threads** – managed by a library; fast to switch but the kernel sees one thread, so a blocking call blocks all.
- **Kernel threads** – managed by the OS; can run in parallel on multiple cores.
- Models: many-to-one, one-to-one (Linux, Java platform threads), many-to-many. **Java virtual threads** (JDK 21) are M:N — many virtual threads mounted on a few carrier OS threads, great for I/O-heavy Spring Boot apps.

### Context switching
Saving the state (PCB/TCB) of the current process/thread and loading another's. Pure overhead: no useful work, flushes caches/TLB (for process switches). Thread switches within the same process are cheaper since the address space stays the same.

### Concurrency vs parallelism
- **Concurrency** – multiple tasks make progress by interleaving (possible on one core).
- **Parallelism** – tasks literally run at the same time on multiple cores.

### Multiprogramming, multitasking, multiprocessing
- Multiprogramming: keep several jobs in memory so the CPU is never idle.
- Multitasking: time-sharing with rapid switching for interactivity.
- Multiprocessing: multiple CPUs/cores.

### Java connection
A JVM is one OS process; each `Thread` (platform) maps to an OS thread. Tomcat's thread pool (default 200) handles HTTP requests — a great bridge example in interviews.
"""),

("CPU Scheduling Algorithms", r"""
The **CPU scheduler** (short-term scheduler) picks which ready process runs next; the **dispatcher** performs the context switch. Long-term scheduler controls admission to memory (degree of multiprogramming); medium-term scheduler swaps processes out/in.

### Criteria
- **CPU utilisation** & **throughput** (jobs/time) – maximise.
- **Turnaround time** = completion − arrival.
- **Waiting time** = turnaround − burst time.
- **Response time** = first run − arrival (important for interactive systems).

**Preemptive** scheduling can take the CPU away from a running process; **non-preemptive** lets it run until it blocks or finishes.

### Algorithms
**1. FCFS (First Come First Served)** – non-preemptive queue. Simple, but suffers the **convoy effect** (short jobs wait behind a long one).

**2. SJF (Shortest Job First)** – pick the smallest burst; **optimal average waiting time** but needs burst prediction (exponential averaging) and can **starve** long jobs. Preemptive version = **SRTF** (Shortest Remaining Time First).

**3. Priority scheduling** – highest priority first (preemptive or not). Problem: **starvation**; solution: **aging** (gradually raise the priority of waiting processes).

**4. Round Robin (RR)** – each process gets a **time quantum** (e.g. 10–100 ms) then goes to the back of the queue. Great response time; quantum too large → FCFS, too small → excessive context switches.

**5. Multilevel Queue** – separate queues (system, interactive, batch) with own algorithms; fixed priority between queues.

**6. Multilevel Feedback Queue (MLFQ)** – processes move between queues based on behaviour: CPU-hogs drop to lower priority; I/O-bound/interactive stay high. Used in real OSes.

**7. Linux CFS / EEVDF** – Linux's Completely Fair Scheduler (now EEVDF since kernel 6.6) tracks "virtual runtime" in a red-black tree and runs the task that has received the least fair share.

### Worked example
Processes (arrival 0): P1=24, P2=3, P3=3 ms.
- FCFS order P1,P2,P3: waiting 0, 24, 27 → **avg 17 ms**.
- SJF order P2,P3,P1: waiting 0, 3, 6 → **avg 3 ms**.
- RR (q=4): P1 0–4, P2 4–7, P3 7–10, P1 10–30. Waiting P1=6, P2=4, P3=7 → **avg 5.67 ms**.

Practice drawing **Gantt charts** — some campus-style rounds ask you to compute average waiting/turnaround time.

### Other terms
- **Starvation** – a process waits indefinitely. Fix: aging.
- **CPU-bound vs I/O-bound** processes – schedulers favour I/O-bound for responsiveness.
- **Real-time scheduling** – Rate Monotonic (static priority by period), Earliest Deadline First (dynamic).
- **Processor affinity** – keep a process on the same core to reuse cache.

### Which algorithm to mention when asked "which is best?"
No single best: batch systems care about throughput (SJF-like), interactive systems care about response (RR/MLFQ), real-time systems care about deadlines (EDF). Modern general-purpose OSes use MLFQ/fair-share variants.
"""),

("Process Synchronization: Race Conditions, Mutex, Semaphore, Monitor", r"""
When threads share data, the final result can depend on the **timing** of their execution — a **race condition**.

```java
// count++ is actually: load count -> add 1 -> store count
// Two threads interleaving can lose an update: both read 5, both write 6.
```

### Critical section problem
A **critical section** is code that accesses shared resources. A solution must satisfy:
1. **Mutual exclusion** – only one process inside at a time.
2. **Progress** – if none is inside, the choice of who enters next can't be postponed indefinitely.
3. **Bounded waiting** – a limit on how many times others can enter before a waiting process gets its turn (no starvation).

Software solution for 2 processes: **Peterson's algorithm** (uses `flag[]` and `turn`). Hardware support: atomic instructions **Test-and-Set**, **Compare-and-Swap (CAS)** — the basis of Java's `AtomicInteger`.

### Mutex (lock)
A binary lock with **ownership**: the thread that locks must unlock.
```java
lock.lock();
try { balance += amount; } finally { lock.unlock(); }
```
**Spinlock** – busy-waits instead of sleeping; good only for very short critical sections on multi-core.

### Semaphore
An integer variable accessed only via atomic `wait()` (P, down) and `signal()` (V, up).
```
wait(S):   while (S <= 0) block; S--;
signal(S): S++; wake a waiting process;
```
- **Binary semaphore** (0/1) – like a mutex but **no ownership** (any thread can signal).
- **Counting semaphore** – controls access to N identical resources (e.g. DB connection pool of 10). Java: `java.util.concurrent.Semaphore`.

### Mutex vs semaphore
| Mutex | Semaphore |
|---|---|
| Locking mechanism | Signalling mechanism |
| Owned by one thread | No owner |
| Value 0/1 | 0..N |
| Protect a critical section | Limit concurrency / signal events between threads |

### Monitor
A high-level construct: an object whose methods are executed with mutual exclusion automatically, plus **condition variables** (`wait`, `signal`). Java's `synchronized` + `wait()/notify()/notifyAll()` implements monitors; every object has an intrinsic lock.

### Classic problems
**1. Producer–Consumer (bounded buffer)** – semaphores `empty = N`, `full = 0`, `mutex = 1`.
```
Producer: wait(empty); wait(mutex); add item; signal(mutex); signal(full);
Consumer: wait(full);  wait(mutex); remove item; signal(mutex); signal(empty);
```
Swapping the order of `wait(empty)` and `wait(mutex)` can deadlock. In Java just use `BlockingQueue`.

**2. Readers–Writers** – many readers may read simultaneously; writers need exclusive access. Variants favour readers (writers may starve) or writers. Java: `ReentrantReadWriteLock`.

**3. Dining Philosophers** – 5 philosophers, 5 chopsticks; naive "pick left then right" deadlocks. Fixes: allow at most 4 at the table, pick both chopsticks atomically, or asymmetric ordering (odd picks left first, even picks right first).

### Other concepts
- **Priority inversion** – a high-priority task waits for a lock held by a low-priority task that is preempted by a medium one. Fix: **priority inheritance** (famous Mars Pathfinder bug).
- **Busy waiting** wastes CPU; blocking primitives put the thread to sleep.
- **Atomicity, visibility and ordering** – in Java also handle visibility with `volatile` and happens-before rules.
"""),

("Deadlocks: Conditions, Prevention, Avoidance (Banker's), Detection", r"""
A **deadlock** is a situation where a set of processes are each waiting for a resource held by another process in the set, so none can proceed.

```
Thread A: lock(X) ... lock(Y)
Thread B: lock(Y) ... lock(X)   → A holds X waits Y, B holds Y waits X
```

### Four necessary (Coffman) conditions — all must hold
1. **Mutual exclusion** – at least one resource is non-shareable.
2. **Hold and wait** – a process holds resources while waiting for others.
3. **No preemption** – resources can't be forcibly taken away.
4. **Circular wait** – a cycle P1→P2→…→Pn→P1 of waiting.

### Resource Allocation Graph (RAG)
Processes (circles) and resources (squares); request edges P→R, assignment edges R→P. If each resource has a single instance, **a cycle ⇔ deadlock**. With multiple instances, a cycle means deadlock is *possible*.

### Handling strategies
**1. Prevention** – break one condition:
- Mutual exclusion: make resources shareable (read-only files) — rarely possible.
- Hold & wait: request all resources at once, or release before requesting more (low utilisation, starvation).
- No preemption: if a request fails, release held resources (works for CPU/memory state, not printers).
- **Circular wait: impose a global ordering on resources and always acquire in increasing order** — the most practical (e.g. always lock accounts by ascending account ID in a money transfer).

**2. Avoidance** – the OS checks each request and grants it only if the system stays in a **safe state**. Requires advance knowledge of maximum needs. → **Banker's algorithm**.

**3. Detection & recovery** – allow deadlocks, periodically detect cycles (wait-for graph), then recover by killing processes or preempting resources with rollback. Databases do this: MySQL InnoDB detects deadlocks and rolls back one transaction ("Deadlock found when trying to get lock").

**4. Ignore (Ostrich algorithm)** – used by most general-purpose OSes (Windows, Linux) since deadlocks are rare and prevention is costly.

### Banker's algorithm
Data: `Available[m]`, `Max[n][m]`, `Allocation[n][m]`, `Need = Max − Allocation`.

**Safety algorithm:** `Work = Available`; find a process with `Need ≤ Work`, pretend it finishes (`Work += Allocation`), mark it done; repeat. If all finish → safe; the order is a **safe sequence**.

**Example** (resources A,B,C; Available = 3 3 2):

| P | Allocation | Max | Need |
|---|---|---|---|
| P0 | 0 1 0 | 7 5 3 | 7 4 3 |
| P1 | 2 0 0 | 3 2 2 | 1 2 2 |
| P2 | 3 0 2 | 9 0 2 | 6 0 0 |
| P3 | 2 1 1 | 2 2 2 | 0 1 1 |
| P4 | 0 0 2 | 4 3 3 | 4 3 1 |

Work=332 → P1 (122≤332) → Work=532 → P3 → 743 → P4 → 745 → P0 → 755 → P2 → 10 5 7. Safe sequence: **P1, P3, P4, P0, P2**.

**Resource-request algorithm:** when Pi requests, check `Request ≤ Need` and `Request ≤ Available`, pretend to allocate, run the safety check; if unsafe, roll back and make Pi wait.

Limitations: needs max demand in advance, fixed number of processes/resources, overhead O(m·n²) — rarely used in real OSes, but a classic interview topic.

### Deadlock vs starvation vs livelock
- **Deadlock** – nobody progresses, all blocked.
- **Starvation** – some process waits indefinitely while others progress.
- **Livelock** – processes keep changing state in response to each other but make no progress (two people stepping aside in a corridor).

### Java tip
Detect with `jstack` thread dumps ("Found one Java-level deadlock"). Avoid with lock ordering, `tryLock(timeout)`, and minimal lock scope.
"""),

("Memory Management: Contiguous Allocation, Paging, Segmentation", r"""
The OS must give each process memory, keep processes isolated, and use RAM efficiently.

### Logical vs physical address
The CPU generates **logical (virtual) addresses**; the **MMU (Memory Management Unit)** translates them to **physical addresses** at runtime. This allows relocation and protection.

### Contiguous allocation
Each process occupies one continuous block.
- **Fixed partitioning** → **internal fragmentation** (unused space inside an allocated partition).
- **Variable partitioning** → **external fragmentation** (enough total free memory but not contiguous).
- Placement strategies: **First fit** (fast), **Best fit** (smallest hole that fits, leaves tiny holes), **Worst fit** (largest hole).
- **Compaction** shuffles processes to merge holes — expensive.

### Paging
Divides **logical memory into fixed-size pages** and **physical memory into frames** of the same size (typically 4 KB). Any page can go in any frame → **no external fragmentation** (only small internal fragmentation in the last page).

Logical address = **page number (p)** + **offset (d)**. The **page table** maps p → frame number f. Physical address = f × pageSize + d.

Example: 32-bit address, 4 KB pages → offset = 12 bits, page number = 20 bits → 2^20 entries per page table.

**Page table entry bits:** frame number, valid/invalid, protection (R/W/X), dirty (modified), referenced (accessed).

### TLB (Translation Lookaside Buffer)
Every memory access would need two accesses (page table + data). The **TLB** is a small, fast associative cache of recent page→frame translations.

**Effective Access Time** = h × (TLB + mem) + (1 − h) × (TLB + 2 × mem)
With TLB = 10 ns, memory = 100 ns, hit ratio 90%: 0.9 × 110 + 0.1 × 210 = **120 ns**.

### Large page tables
- **Multilevel (hierarchical) paging** – page the page table (x86-64 uses 4–5 levels).
- **Hashed page tables** – for sparse address spaces.
- **Inverted page table** – one entry per physical frame (saves memory, slower lookup).
- **Huge pages** (2 MB/1 GB) – fewer TLB misses for large heaps (databases, JVM `-XX:+UseLargePages`).

### Segmentation
Divides memory into **variable-sized logical segments** matching the program's structure: code, data, stack, heap. Address = (segment number, offset); the **segment table** stores base and limit. Offset > limit → segmentation fault (trap).

| Paging | Segmentation |
|---|---|
| Fixed-size pages | Variable-size segments |
| Invisible to programmer | Matches logical program view |
| Internal fragmentation | External fragmentation |
| Page table | Segment table (base, limit) |

**Segmented paging** combines both: segments divided into pages (classic x86 design; modern 64-bit OSes mostly use flat paging).

### Swapping
Moving an entire process between RAM and disk (backing store) to free memory. Modern systems swap pages rather than whole processes.

### Interview analogy
JVM heap regions (Eden, Survivor, Old) are a user-space memory manager on top of the OS's virtual memory — and "OutOfMemoryError: Java heap space" is the JVM's limit, not physical RAM.
"""),

("Virtual Memory, Demand Paging & Page Replacement", r"""
**Virtual memory** lets a process use an address space larger than physical RAM by keeping only the needed pages in memory and the rest on disk. Benefits: run larger programs, more processes in memory, isolation, shared libraries mapped once, copy-on-write `fork()`, memory-mapped files.

### Demand paging
Pages are loaded **only when first accessed** (lazy loading).
1. Process accesses a page whose PTE is marked invalid → **page fault** trap.
2. OS checks the access is legal (else segfault).
3. Finds a free frame (or evicts a victim via page replacement).
4. Reads the page from disk into the frame (process blocked meanwhile).
5. Updates the page table, restarts the instruction.

**Effective access time** = (1 − p) × memory_access + p × page_fault_time. Since a fault costs milliseconds vs ~100 ns for memory, even p = 0.001 slows memory ~40×. Page faults must be very rare.

### Page replacement algorithms
When no frame is free, choose a victim page (if dirty, write it back first).

**Reference string 7 0 1 2 0 3 0 4 2 3 0 3 2, with 3 frames:**

**1. FIFO** – evict the oldest loaded page. Simple, but can evict heavily used pages. Suffers **Belady's anomaly**: more frames can cause *more* faults (e.g. string 1 2 3 4 1 2 5 1 2 3 4 5 gives 9 faults with 3 frames and 10 with 4).

**2. Optimal (OPT/MIN)** – evict the page that won't be used for the longest time in the future. Lowest possible faults, **impossible to implement** (needs the future); used as a benchmark.

**3. LRU (Least Recently Used)** – evict the page unused for the longest time (past approximates future, thanks to locality). Good performance, no Belady's anomaly (it's a *stack algorithm*). Expensive to implement exactly (timestamps or a stack/linked list on every access) — same idea as the LRU cache DSA problem (HashMap + doubly linked list).

**4. LRU approximations** – **Clock / Second-Chance**: frames in a circular list with a reference bit; the hand clears set bits and evicts the first page with bit 0. Enhanced clock also considers the dirty bit.

**5. LFU / MFU** – count-based; rarely used.

Worked FIFO on the string above (3 frames) gives 10 faults; LRU gives 9; OPT gives 7. Practice these on paper.

### Thrashing
When processes don't have enough frames for their **working set**, they page-fault constantly; the CPU sits idle waiting for disk, the OS sees low CPU utilisation and admits even more processes → collapse.

Solutions:
- **Working-set model** – track pages used in the last Δ references; only run processes whose working sets fit.
- **Page-fault frequency (PFF)** control – give more frames if fault rate is high, take away if low.
- Reduce degree of multiprogramming, add RAM.

### Locality of reference
- **Temporal** – recently used data likely used again (loops, counters).
- **Spatial** – nearby data likely used soon (arrays). This is why iterating a 2D array row-by-row is faster than column-by-column in C/Java.

### Frame allocation
Equal vs proportional allocation; **global replacement** (take frames from any process) vs **local** (only from own frames).

### Copy-on-write (COW)
After `fork()`, parent and child share pages marked read-only; a page is copied only when one of them writes to it. Makes `fork()` + `exec()` cheap.

### Memory-mapped files
`mmap` maps a file into the address space; reads/writes become memory accesses and the OS pages data in/out. Used by databases (MongoDB's old engine, LMDB) and Kafka's zero-copy reads.
"""),

("File Systems & Disk Management", r"""
A **file system** organises data on storage devices into files and directories and manages space, metadata and access control.

### File concepts
- **Attributes (metadata):** name, type, size, owner, permissions, timestamps, location.
- **Operations:** create, open, read, write, seek, close, delete, truncate.
- **Access methods:** sequential, direct (random), indexed.
- Linux **permissions**: `rwx` for owner/group/others, e.g. `chmod 754 file` = rwx r-x r--.

### Directory structures
Single-level → two-level → **tree** (hierarchical, most common) → **acyclic graph** (shared files via links). **Hard link** – another directory entry pointing to the same inode (can't cross file systems or link directories). **Soft (symbolic) link** – a special file containing a path; breaks if target is deleted.

### Allocation methods
**1. Contiguous** – each file occupies consecutive blocks. Fast sequential and random access; suffers external fragmentation and growth problems (used in CD-ROMs).

**2. Linked** – each block points to the next. No external fragmentation, easy growth; slow random access, pointer overhead, a broken pointer loses the rest. **FAT (File Allocation Table)** keeps all the next-pointers in a table in memory (FAT32, exFAT on USB drives).

**3. Indexed** – each file has an index block listing all its blocks. Fast random access, no external fragmentation; index overhead. **Unix inode** uses direct pointers (12) + single, double, triple indirect blocks, supporting very large files efficiently.

### Inode
Stores metadata (owner, permissions, size, timestamps, block pointers) — **not the file name**. The directory maps names → inode numbers. `ls -i` shows inode numbers. Running out of inodes means you can't create files even with free space.

### Free-space management
Bit vector (bitmap, one bit per block), linked list of free blocks, grouping, counting (start + run length).

### Journaling
A crash in the middle of an update can corrupt the file system. **Journaling** file systems (ext4, NTFS, XFS) first write intended changes to a log (journal); after a crash they replay or discard incomplete operations. Similar idea to a database's **write-ahead log (WAL)**. Copy-on-write file systems (ZFS, Btrfs) never overwrite in place.

### Common file systems
ext4 (Linux default), XFS, Btrfs, NTFS (Windows), APFS (macOS), FAT32/exFAT (removable media).

### Disk scheduling (HDD)
Seek time dominates on spinning disks; the OS orders requests to reduce head movement.
- **FCFS** – fair but slow.
- **SSTF** (Shortest Seek Time First) – nearest request next; can starve far requests.
- **SCAN (elevator)** – head moves end to end servicing requests.
- **C-SCAN** – services in one direction, then jumps back to the start; more uniform wait.
- **LOOK / C-LOOK** – like SCAN/C-SCAN but only go as far as the last request.

Example: requests 98, 183, 37, 122, 14, 124, 65, 67, head at 53 → FCFS total head movement 640 cylinders; SSTF 236.

SSDs have no seek time, so schedulers are simpler (Linux uses `none`/`mq-deadline` for NVMe); SSDs care about **wear leveling** and **TRIM**.

### RAID (quick)
- RAID 0 – striping (speed, no redundancy).
- RAID 1 – mirroring.
- RAID 5 – striping with distributed parity (tolerates 1 disk failure).
- RAID 10 – mirror + stripe (common for databases).

### Buffering & caching
The OS **page cache** keeps recently used file blocks in RAM; writes are buffered and flushed later (`fsync` forces durability — why databases call it on commit).
"""),

("Inter-Process Communication (IPC) & Misc Topics", r"""
Processes have separate address spaces, so they need OS-provided mechanisms to exchange data. Two fundamental models: **shared memory** and **message passing**.

### IPC mechanisms
| Mechanism | Description | Notes |
|---|---|---|
| **Pipe (anonymous)** | Unidirectional byte stream between related processes (parent–child) | `ls \| grep java` in shell |
| **Named pipe (FIFO)** | Pipe with a filesystem name; unrelated processes can use it | `mkfifo` |
| **Message queue** | Kernel-managed queue of discrete messages | POSIX `mq_open`; message boundaries preserved |
| **Shared memory** | Region mapped into multiple processes' address spaces | **Fastest** (no kernel copy after setup) but needs synchronization (semaphores) |
| **Semaphores** | Synchronization primitive across processes | Often paired with shared memory |
| **Signals** | Asynchronous notifications (`SIGINT`, `SIGTERM`, `SIGKILL`) | `kill -9` can't be caught; Spring Boot handles `SIGTERM` for graceful shutdown |
| **Sockets** | Communication endpoints, local (Unix domain) or over network (TCP/UDP) | Basis of client–server, microservices |
| **Memory-mapped files** | Map same file in multiple processes | |
| **RPC / gRPC** | Call a function in another process/machine | Built on sockets |

**Shared memory vs message passing:** shared memory is faster for large data but needs explicit synchronization and only works on one machine; message passing is simpler, safer and works across machines, but has copying overhead.

### Synchronous vs asynchronous communication
Blocking send/receive vs non-blocking. In distributed systems the same ideas appear as REST (sync) vs Kafka/RabbitMQ (async) — a nice link for a backend developer.

### Other frequently asked OS topics
**Booting process:** power on → BIOS/UEFI firmware runs POST → bootloader (GRUB) loaded from disk → loads kernel into memory → kernel initialises drivers, mounts root FS → starts `init`/`systemd` (PID 1) → services and login.

**Interrupts:** hardware (keyboard, disk, timer) or software (traps, system calls, exceptions) signals that make the CPU pause, save state, run an **interrupt service routine**, and resume. The **timer interrupt** enables preemptive scheduling.

**Polling vs interrupts:** polling repeatedly checks device status (wastes CPU); interrupts notify the CPU when ready. **DMA (Direct Memory Access)** lets devices transfer data to memory without the CPU copying each byte.

**Spooling:** buffering jobs for a slow device (printer queue).

**Cache memory & hierarchy:** registers → L1 → L2 → L3 → RAM → SSD → HDD — faster/smaller/costlier at the top.

**32-bit vs 64-bit OS:** 32-bit can address 4 GB of virtual memory per process; 64-bit can address far more (practically 128 TB+ user space on x86-64).

**Real-time OS (RTOS):** guarantees response within deadlines (hard real-time: airbags; soft: video streaming).

**Virtualization & containers:** a **hypervisor** (Type 1 bare-metal like ESXi/KVM, Type 2 hosted like VirtualBox) runs full VMs each with its own kernel. **Containers** (Docker) share the host kernel and use Linux **namespaces** (isolation of PIDs, network, mounts) and **cgroups** (resource limits) — lighter and faster to start. Expect this question since you deploy Spring Boot apps.

**User vs kernel space, system call example:** `System.out.println` in Java eventually calls the `write()` system call on file descriptor 1 (stdout).

### Sample comparison answer
"Threads in one JVM share the heap, so I synchronise with locks or concurrent collections. Separate microservices are separate processes — even separate machines — so they communicate via REST or Kafka, which are message-passing IPC over sockets."
"""),
]

qa = [
("What is the difference between a process and a thread?", r"""
A **process** is an independent program in execution with its own address space (code, data, heap, stack) and resources tracked in a PCB. A **thread** is a unit of execution inside a process; threads of the same process **share** code, data, heap and open files but each has its own **stack, program counter and registers**.

| Process | Thread |
|---|---|
| Heavyweight creation and context switch | Lightweight |
| Isolated – one crash doesn't affect others | A crashing thread can bring down the whole process |
| Communicate via IPC | Communicate via shared memory (needs synchronization) |

Example: each Chrome tab runs as a separate process for isolation, while a Spring Boot app is one JVM process using many threads (Tomcat's pool) to serve requests concurrently.
""", B, ["process", "thread"], True),

("Explain the process states and the Process Control Block (PCB).", r"""
States:
- **New** – being created.
- **Ready** – in memory, waiting for CPU.
- **Running** – executing on a CPU.
- **Waiting/Blocked** – waiting for I/O or an event.
- **Terminated** – finished.

Transitions: Ready → Running (dispatch), Running → Ready (preempted / quantum expired), Running → Waiting (I/O request), Waiting → Ready (I/O done), Running → Terminated (exit). Some OSes add **suspended** states when a process is swapped to disk.

The **PCB** is the kernel data structure representing a process: PID, state, program counter, CPU registers, scheduling info (priority, queue pointers), memory-management info (page table base), accounting info, list of open files and I/O status. During a context switch the OS saves the current PCB and loads the next one.
""", B, ["process"], True),

("What is a context switch? Why is it considered overhead?", r"""
A **context switch** is the CPU switching from one process/thread to another: the kernel saves the running task's state (registers, PC, stack pointer) into its PCB/TCB and restores another task's state.

It is triggered by timer interrupts (time quantum over), blocking I/O, system calls, or higher-priority tasks becoming ready.

It's overhead because **no useful work** is done during it, and indirect costs are larger: CPU caches and the **TLB** may be flushed (for process switches, since the address space changes), causing cache misses afterwards. Thread switches within the same process are cheaper because memory mappings stay the same.

That's why too many threads (e.g. thousands of platform threads) hurt throughput — and why Java virtual threads and async I/O exist.
""", I, ["context-switch"], True),

("What are zombie and orphan processes?", r"""
- **Zombie (defunct) process** – a child that has **terminated**, but its parent hasn't yet called `wait()`/`waitpid()` to read its exit status. Its PCB/entry remains in the process table (shown as `Z` in `ps`). A few are harmless; many can exhaust PIDs. Fix: parent should `wait()` or handle `SIGCHLD`; killing the parent makes `init` reap them.
- **Orphan process** – a child whose **parent terminated** while it's still running. It is adopted by `init`/`systemd` (PID 1), which reaps it when it ends. Daemons are intentionally orphaned.

Key difference: a zombie is dead but not cleaned up; an orphan is alive but parentless.
""", B, ["process"], False),

("What is the difference between multiprogramming, multitasking, multithreading and multiprocessing?", r"""
- **Multiprogramming** – multiple programs are kept in memory; when one waits for I/O the CPU switches to another, so the CPU is never idle. Goal: maximise CPU utilisation.
- **Multitasking (time-sharing)** – the CPU switches rapidly between tasks with time slices so users feel they run simultaneously. Goal: responsiveness. Preemptive multitasking uses timer interrupts.
- **Multithreading** – a single process has multiple threads executing concurrently (e.g. UI thread + background download thread).
- **Multiprocessing** – a system has **multiple CPUs/cores** executing processes truly in parallel (SMP).

Concurrency (interleaving) is possible on one core; parallelism needs multiple cores.
""", B, ["basics"], False),

("Explain FCFS, SJF, Round Robin and Priority scheduling with pros and cons.", r"""
- **FCFS** – run in arrival order, non-preemptive. Simple, but the **convoy effect**: short jobs wait behind long ones → high average waiting time.
- **SJF / SRTF** – run the shortest burst (SRTF is the preemptive version). **Optimal average waiting time**, but burst times must be predicted and long jobs can **starve**.
- **Round Robin** – each process gets a fixed **time quantum**, then goes to the back of the ready queue. Fair with good response time; performance depends on quantum (too large → FCFS, too small → context-switch overhead).
- **Priority** – highest priority first (preemptive or not). Flexible, but low-priority jobs can starve → solved by **aging**.

Example (P1=24, P2=3, P3=3 ms, all arriving at 0): FCFS avg wait = 17 ms; SJF = 3 ms; RR (q=4) ≈ 5.67 ms. Real OSes use multilevel feedback queues or fair schedulers.
""", I, ["scheduling"], True),

("What is starvation and how does aging solve it?", r"""
**Starvation** (indefinite blocking) happens when a process waits indefinitely because other processes are always preferred — e.g. a low-priority job in priority scheduling, or a long job in SJF when short jobs keep arriving.

**Aging** gradually increases the priority of processes the longer they wait. Example: priorities range 0 (high) to 127 (low); every 15 minutes a waiting process's priority number decreases by 1. Eventually even the lowest-priority process becomes the highest and gets the CPU.

Difference from deadlock: in starvation the system keeps making progress (other processes run) but one process is neglected; in deadlock no process in the set progresses. Starvation can also occur with unfair locks (Java `ReentrantLock(true)` makes it fair at a throughput cost).
""", B, ["scheduling", "starvation"], False),

("What is a Multilevel Feedback Queue scheduler?", r"""
MLFQ uses **several ready queues with different priorities** (and often different time quanta), and **moves processes between queues based on observed behaviour**:
- New processes start in the highest-priority queue (short quantum).
- If a process uses its full quantum (CPU-bound), it's **demoted** to a lower queue with a longer quantum.
- If a process gives up the CPU early (I/O-bound/interactive), it stays high.
- To prevent starvation, processes waiting too long in low queues are **promoted** (aging / periodic priority boost).

Benefits: approximates SJF without knowing burst times, gives interactive tasks good response time, and still lets batch jobs progress. It's the basis for schedulers in Windows, older Linux/BSD, and macOS. Parameters (number of queues, quanta, boost interval) need tuning.
""", I, ["scheduling"], False),

("What is a race condition and a critical section?", r"""
A **race condition** occurs when multiple threads access shared data concurrently and at least one modifies it, so the result depends on the unpredictable interleaving.

```java
class Counter { int count; void inc() { count++; } } // read-modify-write, not atomic
// two threads calling inc() 1000 times each may end with < 2000
```
A **critical section** is the code segment that accesses the shared resource. A correct solution needs **mutual exclusion**, **progress** and **bounded waiting**.

Fixes in Java: `synchronized`, `ReentrantLock`, `AtomicInteger.incrementAndGet()` (uses CAS), or avoiding shared mutable state (immutability, thread confinement). In databases, the equivalent problem is solved with transactions and row locks (e.g. `SELECT ... FOR UPDATE` when decrementing stock).
""", B, ["synchronization"], True),

("What is the difference between a mutex and a semaphore?", r"""
- **Mutex** – a lock providing mutual exclusion with **ownership**: only the thread that acquired it can release it. Value conceptually 0/1. Used to protect a critical section. Often supports recursion (reentrant) and priority inheritance.
- **Semaphore** – an integer counter manipulated by atomic `wait()` (decrement, block if 0) and `signal()` (increment, wake a waiter). **No ownership** – any thread can signal.
  - *Binary semaphore* (0/1) – similar to a mutex but usable for signalling between threads.
  - *Counting semaphore* – limits concurrent access to N identical resources.

```java
Semaphore pool = new Semaphore(10);   // max 10 concurrent DB calls
pool.acquire(); try { callDb(); } finally { pool.release(); }
```
Summary: mutex = locking mechanism; semaphore = signalling/counting mechanism.
""", I, ["synchronization", "mutex", "semaphore"], True),

("What is a monitor? How does Java implement it?", r"""
A **monitor** is a high-level synchronization construct that bundles shared data with the procedures that operate on it, guaranteeing that **only one thread executes inside the monitor at a time**, plus **condition variables** for waiting until some condition holds.

Java implements monitors on every object:
- `synchronized` methods/blocks acquire the object's intrinsic lock (mutual exclusion).
- `wait()` releases the lock and suspends the thread; `notify()`/`notifyAll()` wake waiting threads (condition signalling).

```java
synchronized void put(T item) throws InterruptedException {
  while (queue.size() == capacity) wait();   // always loop: spurious wakeups
  queue.add(item);
  notifyAll();
}
```
`ReentrantLock` with multiple `Condition` objects is the explicit, more flexible version. Monitors are less error-prone than raw semaphores because locking/unlocking is automatic.
""", I, ["synchronization", "monitor", "java"], False),

("Explain the Producer-Consumer problem and its solution using semaphores.", r"""
A producer adds items to a fixed-size buffer and a consumer removes them. Constraints: producer must wait when buffer is full, consumer must wait when empty, and buffer access must be mutually exclusive.

Semaphores: `mutex = 1`, `empty = N` (free slots), `full = 0` (filled slots).
```
Producer:                     Consumer:
  wait(empty)                   wait(full)
  wait(mutex)                   wait(mutex)
  buffer.add(item)              item = buffer.remove()
  signal(mutex)                 signal(mutex)
  signal(full)                  signal(empty)
```
Order matters: if the producer did `wait(mutex)` before `wait(empty)` on a full buffer, it would sleep holding the mutex and the consumer could never enter → **deadlock**.

In Java, use `ArrayBlockingQueue` (`put()` blocks when full, `take()` blocks when empty). Kafka topics are the distributed version of this pattern.
""", I, ["synchronization", "classic-problems"], True),

("Explain the Readers-Writers and Dining Philosophers problems.", r"""
**Readers–Writers:** many threads read shared data, some write. Multiple readers may read simultaneously, but a writer needs exclusive access.
- *First variant* (reader preference): writers may starve.
- *Second variant* (writer preference): readers may starve.
Solution uses a `readCount` protected by a mutex and a `rw` semaphore that the first reader acquires and the last reader releases. Java: `ReentrantReadWriteLock`, `StampedLock`.

**Dining Philosophers:** 5 philosophers around a table with 5 chopsticks; each needs both neighbours' chopsticks to eat. If all pick up their left chopstick simultaneously → **deadlock** (circular wait).
Solutions:
1. Allow at most 4 philosophers to sit at once (semaphore of 4).
2. Pick up both chopsticks atomically (only if both are free).
3. **Resource ordering** – odd philosophers pick left first, even pick right first (breaks the cycle).
It illustrates deadlock and starvation in resource sharing.
""", I, ["synchronization", "classic-problems", "deadlock"], False),

("What is a deadlock? State the four necessary conditions.", r"""
A **deadlock** is a state where a set of processes are blocked forever, each holding a resource and waiting for a resource held by another process in the set.

All four **Coffman conditions** must hold simultaneously:
1. **Mutual exclusion** – a resource can be held by only one process at a time.
2. **Hold and wait** – a process holds at least one resource while waiting for others.
3. **No preemption** – resources can't be forcibly taken; they're released voluntarily.
4. **Circular wait** – a closed chain of processes, each waiting for a resource held by the next.

Example: Thread A locks `account1` then waits for `account2`; thread B locks `account2` then waits for `account1`. Breaking any one condition prevents deadlock — most practically, circular wait via a global lock ordering.
""", B, ["deadlock"], True),

("What are the methods for handling deadlocks?", r"""
1. **Prevention** – design the system so one of the four conditions can never hold:
   - Hold & wait: request all resources upfront.
   - No preemption: release held resources if a request fails.
   - Circular wait: **order resources and acquire them in increasing order** (most practical).
2. **Avoidance** – the OS grants a request only if the system remains in a **safe state**; requires knowing maximum demands in advance. Example: **Banker's algorithm**.
3. **Detection and recovery** – let deadlocks happen, detect cycles in a wait-for graph periodically, then recover by aborting processes or preempting resources (with rollback). Databases like MySQL InnoDB do this.
4. **Ignore it (Ostrich algorithm)** – assume deadlocks are rare; used by Windows/Linux for general resources, leaving it to applications.

Trade-off: prevention/avoidance reduce resource utilisation; detection has runtime overhead.
""", I, ["deadlock"], True),

("Explain the Banker's algorithm with an example.", r"""
The Banker's algorithm (Dijkstra) is a **deadlock avoidance** algorithm. Each process declares its maximum needs; before granting a request the OS simulates the allocation and checks if the system is still in a **safe state** — i.e. there exists an order in which all processes can finish.

Data: `Available`, `Max`, `Allocation`, `Need = Max − Allocation`.

**Safety check:** `Work = Available`; repeatedly find an unfinished process with `Need ≤ Work`, assume it finishes and releases its allocation (`Work += Allocation`). If all processes finish → safe.

Example: Available = (3,3,2). Needs: P0(7,4,3), P1(1,2,2), P2(6,0,0), P3(0,1,1), P4(4,3,1); allocations P0(0,1,0), P1(2,0,0), P2(3,0,2), P3(2,1,1), P4(0,0,2).
P1 → Work (5,3,2) → P3 → (7,4,3) → P4 → (7,4,5) → P0 → (7,5,5) → P2 → (10,5,7). Safe sequence **<P1, P3, P4, P0, P2>**.

Limitation: needs max demands in advance and has O(m·n²) overhead, so real OSes rarely use it.
""", A, ["deadlock", "bankers"], True),

("What is the difference between deadlock, livelock and starvation?", r"""
- **Deadlock** – processes are **blocked**, each waiting for another; no progress and no CPU usage by them. Example: two threads each holding one lock and waiting for the other's.
- **Livelock** – processes are **active** (not blocked) and keep changing state in response to each other, but no real progress is made. Example: two threads that both back off and retry acquiring locks in perfect sync; two people repeatedly stepping aside in a corridor. Fix: randomised backoff.
- **Starvation** – some process is perpetually denied resources while others proceed (e.g. low priority in priority scheduling, writers in reader-preference locks). Fix: aging, fair locks.

Deadlock implies starvation of the involved processes, but starvation doesn't imply deadlock.
""", I, ["deadlock", "starvation"], False),

("What is paging? How is a logical address translated to a physical address?", r"""
**Paging** divides a process's logical address space into fixed-size **pages** and physical memory into same-size **frames**. Pages can be placed in any free frame, eliminating external fragmentation.

A logical address is split into **page number (p)** and **offset (d)**. The **page table** (base pointed to by a register, e.g. CR3 on x86) maps page p to frame f. Physical address = `f × page_size + d`.

Example: page size 4 KB (offset 12 bits). Logical address 8200 → p = 8200 / 4096 = 2, d = 8. If page 2 maps to frame 5 → physical = 5 × 4096 + 8 = **20488**.

To avoid a memory access for every translation, the **TLB** caches recent translations. Large address spaces use multilevel page tables. Downsides: small internal fragmentation in the last page and page-table memory overhead.
""", I, ["memory", "paging"], True),

("What is the TLB? Calculate effective memory access time.", r"""
The **Translation Lookaside Buffer** is a small, fast, associative hardware cache in the MMU that stores recent page-number → frame-number translations. On a **TLB hit**, translation needs no page-table memory access; on a **miss**, the page table is walked and the TLB updated.

**EAT = h × (t_TLB + t_mem) + (1 − h) × (t_TLB + 2 × t_mem)**

Example: TLB lookup 20 ns, memory 100 ns, hit ratio 80%:
EAT = 0.8 × 120 + 0.2 × 220 = 96 + 44 = **140 ns** (vs 200 ns without TLB).
With a 98% hit ratio: 0.98 × 120 + 0.02 × 220 = **122 ns**.

TLB entries may carry an **ASID** (address-space ID) so they needn't be flushed on every context switch. Huge pages reduce TLB misses for large-memory apps like databases and JVMs.
""", I, ["memory", "tlb"], False),

("What is the difference between paging and segmentation?", r"""
| Paging | Segmentation |
|---|---|
| Memory divided into **fixed-size** pages/frames | Divided into **variable-size** logical segments (code, stack, heap, data) |
| Transparent to the programmer | Reflects the programmer's logical view |
| **Internal fragmentation** (last page) | **External fragmentation** |
| Address = (page no, offset) via page table | Address = (segment no, offset) via segment table with **base & limit** |
| Easy allocation (any free frame) | Harder allocation (find a big enough hole) |
| Sharing/protection at page granularity | Natural sharing/protection per segment (e.g. read-only code) |

**Segmented paging** combines them: each segment is divided into pages, giving logical organisation without external fragmentation. Modern 64-bit OSes mostly use flat paging with segmentation effectively disabled.
""", I, ["memory", "paging", "segmentation"], True),

("What is internal vs external fragmentation?", r"""
- **Internal fragmentation** – wasted space **inside** an allocated block because the block is bigger than requested. Example: fixed 4 KB pages; a process needing 9 KB gets 3 pages (12 KB), wasting 3 KB in the last page. Also with fixed partitions.
- **External fragmentation** – enough **total** free memory exists, but it's split into non-contiguous holes, so a large request can't be satisfied. Occurs in variable partitioning and segmentation.

Remedies:
- External: **compaction** (move processes to merge holes), paging (non-contiguous allocation), buddy system.
- Internal: smaller block/page sizes (trade-off: bigger page tables), slab allocation for kernel objects.

Analogy: a Java heap with lots of free but scattered space triggers compacting GC phases for the same reason.
""", B, ["memory", "fragmentation"], True),

("What is virtual memory and what are its advantages?", r"""
**Virtual memory** is a technique that gives each process the illusion of a large, private, contiguous address space, while physically only part of it is in RAM and the rest is on disk (swap). The MMU translates virtual to physical addresses; missing pages are brought in on demand (**demand paging**).

Advantages:
1. Programs can be **larger than physical memory**.
2. More processes fit in memory → higher multiprogramming and CPU utilisation.
3. **Isolation and protection** – a process can't access another's memory.
4. Efficient **sharing** – shared libraries and code mapped once into many processes.
5. **Copy-on-write** makes `fork()` cheap; memory-mapped files simplify I/O.
6. Simplifies programming – no manual overlays.

Cost: page faults are very expensive (disk access), and too little RAM leads to **thrashing**.
""", B, ["memory", "virtual-memory"], True),

("What is a page fault? What steps does the OS take to handle it?", r"""
A **page fault** is a trap raised by the MMU when a process accesses a page that is **not currently in physical memory** (PTE marked invalid/not-present).

Steps:
1. CPU traps to the kernel; the OS saves the process state.
2. OS checks whether the reference is valid (within address space, permission OK). If invalid → terminate (segmentation fault).
3. Find a free frame; if none, run a **page replacement** algorithm to choose a victim (write it to disk if dirty).
4. Schedule a disk read of the needed page into the frame; the process is blocked meanwhile (CPU runs others).
5. When I/O completes, update the page table (valid bit, frame number).
6. Restart the instruction that caused the fault.

**Minor (soft) fault**: page is in memory (e.g. page cache) but not mapped; **major (hard) fault**: requires disk I/O.
""", I, ["memory", "page-fault"], True),

("Compare FIFO, LRU and Optimal page replacement. What is Belady's anomaly?", r"""
- **FIFO** – evict the page loaded earliest. Simple (a queue), but may evict frequently used pages.
- **Optimal (OPT)** – evict the page whose next use is farthest in the future. Minimum possible faults; not implementable (needs future knowledge) — used as a benchmark.
- **LRU** – evict the page not used for the longest time. Approximates OPT using locality; implemented with counters/stack or approximated with the **Clock (second-chance)** algorithm using reference bits.

Example: string 7 0 1 2 0 3 0 4 2 3 0 3 2 with 3 frames → FIFO 10 faults, LRU 9, OPT 7.

**Belady's anomaly**: with FIFO, increasing the number of frames can **increase** page faults. String 1 2 3 4 1 2 5 1 2 3 4 5 → 9 faults with 3 frames, 10 with 4. LRU and OPT are *stack algorithms* and never show this anomaly.
""", I, ["memory", "page-replacement"], True),

("What is thrashing? How can it be prevented?", r"""
**Thrashing** happens when a process (or the system) spends more time **paging** (swapping pages in and out) than executing. It occurs when processes don't have enough frames to hold their **working set** (the pages actively used), so nearly every access faults.

Vicious cycle: CPU utilisation drops because processes wait on disk → the scheduler thinks the CPU is underused and admits more processes → even fewer frames each → more faults.

Prevention:
1. **Working-set model** – allocate frames to cover each process's working set; suspend processes if total demand exceeds memory.
2. **Page-Fault Frequency (PFF)** – set upper/lower bounds on fault rate; add frames when too high, remove when too low.
3. **Reduce the degree of multiprogramming** (swap out processes).
4. Use **local replacement** so one process can't steal frames from others.
5. Add more RAM.
""", I, ["memory", "thrashing"], True),

("What is demand paging and copy-on-write?", r"""
**Demand paging**: pages are loaded into memory only when they are first referenced, not when the process starts. A reference to a non-resident page causes a page fault and the OS loads it (lazy loading). Benefits: faster startup, less memory used, more processes in memory. A **pure demand paging** process starts with zero pages in memory.

**Copy-on-write (COW)**: after `fork()`, parent and child initially **share the same physical pages**, marked read-only. When either tries to write to a page, a fault occurs and the OS copies just that page for the writer. Since `fork()` is usually followed by `exec()`, most pages are never copied, making process creation fast.

Both techniques rely on the page table's valid and protection bits and the page-fault mechanism.
""", I, ["memory", "virtual-memory"], False),

("What are the file allocation methods? What is an inode?", r"""
1. **Contiguous** – a file occupies consecutive blocks; directory stores start and length. Fast sequential/random access, but external fragmentation and difficulty growing files.
2. **Linked** – each block stores a pointer to the next. No external fragmentation, easy growth; slow random access and fragile pointers. **FAT** stores the chain in a table for faster traversal.
3. **Indexed** – an index block holds pointers to all data blocks. Fast random access; overhead of index blocks.

An **inode** (Unix/Linux) is the indexed structure holding a file's **metadata** — type, permissions, owner, size, timestamps, link count — and **block pointers**: typically 12 direct, one single-indirect, one double-indirect and one triple-indirect pointer, supporting small files efficiently and very large files too. The file **name is not in the inode**; directories map names to inode numbers, which is why hard links work.
""", I, ["file-systems"], False),

("What is the difference between a hard link and a soft link?", r"""
- **Hard link** – an additional directory entry pointing to the **same inode**. All hard links are equal; the data is deleted only when the link count reaches 0. Can't span file systems and normally can't link directories. Moving/renaming the original doesn't break it.
- **Soft (symbolic) link** – a separate small file (own inode) that stores the **path** to the target. Can cross file systems and point to directories, but becomes a **dangling link** if the target is deleted or moved.

```bash
ln original.txt hard.txt       # hard link (same inode, ls -i shows same number)
ln -s original.txt soft.txt    # symlink (ls -l shows soft.txt -> original.txt)
```
Example use: symlinks for switching versions (`/opt/java/current -> jdk-21`).
""", B, ["file-systems"], False),

("Explain disk scheduling algorithms: FCFS, SSTF, SCAN, C-SCAN, LOOK.", r"""
Goal: minimise disk head movement (seek time) on HDDs.

Example: requests 98, 183, 37, 122, 14, 124, 65, 67; head at 53; cylinders 0–199.
- **FCFS** – service in arrival order. Fair, no starvation, but long seeks: **640** cylinders.
- **SSTF** – serve the closest request next: 65, 67, 37, 14, 98, 122, 124, 183 → **236**. Efficient but may starve distant requests.
- **SCAN (elevator)** – move toward one end serving requests, then reverse. Uniform-ish, no starvation.
- **C-SCAN** – serve only while moving in one direction; jump back to the start without serving. More uniform wait times.
- **LOOK / C-LOOK** – like SCAN/C-SCAN but reverse/jump at the last request instead of the disk end; less wasted movement.

SSDs have no moving head, so these matter less; Linux uses simple `none`/`mq-deadline` schedulers for NVMe.
""", I, ["disk-scheduling"], False),

("What are the different IPC mechanisms?", r"""
Inter-Process Communication lets processes with separate address spaces exchange data:

1. **Pipes** – unidirectional byte stream between related processes (`ps aux | grep java`).
2. **Named pipes (FIFOs)** – pipes with a filesystem name, usable by unrelated processes.
3. **Message queues** – kernel-managed queues of discrete messages.
4. **Shared memory** – a memory region mapped into several processes; **fastest** since no kernel copy per message, but needs synchronization (semaphores/mutexes).
5. **Semaphores** – synchronise access across processes.
6. **Signals** – asynchronous notifications (`SIGTERM`, `SIGKILL`, `SIGINT`).
7. **Sockets** – bidirectional communication locally (Unix domain) or across a network (TCP/UDP); basis of client-server systems.
8. **Memory-mapped files** and **RPC/gRPC**.

Two models: **shared memory** (fast, same machine, needs sync) vs **message passing** (simpler, works across machines, copying overhead).
""", B, ["ipc"], True),

("What is a system call? Give examples.", r"""
A **system call** is the programmatic interface through which a user-mode program requests a service from the kernel (hardware access, process control, file I/O). It works via a special trap/syscall instruction that switches the CPU to **kernel mode**, runs the kernel handler, then returns to user mode.

Categories and Linux examples:
- **Process control:** `fork()`, `exec()`, `exit()`, `wait()`, `kill()`
- **File management:** `open()`, `read()`, `write()`, `close()`, `lseek()`
- **Device management:** `ioctl()`, `read()/write()` on device files
- **Information:** `getpid()`, `time()`
- **Communication:** `pipe()`, `socket()`, `send()`, `recv()`, `mmap()`, `shmget()`

Programs usually call them indirectly via libraries (glibc, JVM). For example, Java's `FileOutputStream.write()` ends up invoking the `write()` syscall. You can trace them with `strace`.
""", B, ["basics", "system-calls"], False),

("What is the difference between user-level threads and kernel-level threads?", r"""
- **User-level threads** – managed entirely by a user-space library; the kernel is unaware and sees only the process. Fast creation and switching (no kernel mode switch), portable. But a **blocking system call blocks the whole process**, and they can't run in parallel on multiple cores (many-to-one model).
- **Kernel-level threads** – created and scheduled by the OS. Can run truly in parallel on multiple cores; a blocking call blocks only that thread. Slower to create/switch (kernel involvement).

Mapping models: **many-to-one**, **one-to-one** (Linux pthreads, Java platform threads), **many-to-many** (Go goroutines, **Java 21 virtual threads** – many virtual threads multiplexed on a small pool of carrier kernel threads, unmounted during blocking I/O). This is why virtual threads let a Spring Boot app handle tens of thousands of concurrent blocking requests.
""", I, ["thread"], False),

("What is the difference between a process and a program? What does fork() return?", r"""
A **program** is a passive entity — an executable file on disk. A **process** is an active entity — the program loaded into memory and executing, with a PC, stack, heap, and OS resources. One program can have many processes (opening two terminal windows).

`fork()` creates a child process that's a near-identical copy of the parent. It returns **twice**:
- In the **child**: returns `0`.
- In the **parent**: returns the **child's PID** (> 0).
- On failure: returns `-1` in the parent.

```c
int main() { fork(); fork(); printf("hi\n"); }   // prints "hi" 4 times (2^n processes)
```
Common question: n consecutive `fork()` calls create **2^n − 1** child processes (2^n total). `exec()` then replaces the child's image with a new program.
""", I, ["process", "fork"], False),

("What are containers and how are they different from virtual machines?", r"""
- **Virtual Machine** – a hypervisor (Type 1 like KVM/ESXi or Type 2 like VirtualBox) emulates hardware; each VM runs a **full guest OS with its own kernel**. Strong isolation, but heavy (GBs, boots in minutes).
- **Container** – an isolated process (or group) that **shares the host kernel**. Isolation via Linux **namespaces** (PID, network, mount, user, IPC, UTS) and resource limits via **cgroups**; packaged filesystem via layered images (Docker/OCI). Lightweight (MBs), starts in seconds.

| VM | Container |
|---|---|
| Own kernel | Shared host kernel |
| Stronger isolation | Weaker isolation (kernel exploits affect all) |
| Heavier | Lightweight, dense packing |

In practice, Spring Boot microservices are packaged as Docker containers and orchestrated by Kubernetes, which often runs on cloud VMs.
""", I, ["virtualization", "containers"], True),

("What is an interrupt? Difference between interrupt and polling? What is DMA?", r"""
An **interrupt** is a signal to the CPU that an event needs attention. The CPU finishes the current instruction, saves state, jumps to an **Interrupt Service Routine (ISR)** via the interrupt vector table, then resumes.
- **Hardware interrupts**: keyboard, NIC packet arrival, disk I/O completion, timer (drives preemptive scheduling).
- **Software interrupts/traps**: system calls, exceptions (divide by zero, page fault).

**Polling**: the CPU repeatedly checks a device's status register — wasteful when events are rare, but can be efficient for very high-rate devices (some high-speed NIC drivers switch to polling under load).

**DMA (Direct Memory Access)**: a DMA controller transfers blocks of data between a device and memory **without CPU involvement** per byte; the CPU is interrupted only when the transfer completes. Frees the CPU for other work during large I/O.
""", I, ["interrupts", "io"], False),
]

sources = [
("Operating System Concepts (Silberschatz, Galvin, Gagne) - publisher page", "https://www.os-book.com/"),
("Operating Systems: Three Easy Pieces (free online book)", "https://pages.cs.wisc.edu/~remzi/OSTEP/"),
("GeeksforGeeks - Operating System Interview Questions", "https://www.geeksforgeeks.org/operating-systems-interview-questions/"),
("GeeksforGeeks - Banker's Algorithm", "https://www.geeksforgeeks.org/bankers-algorithm-in-operating-system-2/"),
("InterviewBit - OS Interview Questions", "https://www.interviewbit.com/operating-system-interview-questions/"),
("Linux kernel docs - EEVDF scheduler", "https://docs.kernel.org/scheduler/sched-eevdf.html"),
("OpenJDK JEP 444 - Virtual Threads", "https://openjdk.org/jeps/444"),
]

build("os", "os", "Operating Systems", 7, "🖥️",
      "Processes, threads, scheduling, synchronization, deadlocks, memory management, virtual memory, file systems and IPC for interviews.",
      notes, qa, sources)
