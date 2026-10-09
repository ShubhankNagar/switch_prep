from fr1_common import M, C, T, build

mcqs = [
M("OOP output prediction", '''What does this print?
```java
class A {
    static void show() { System.out.print("A "); }
    void print()       { System.out.print("a "); }
}
class B extends A {
    static void show() { System.out.print("B "); }
    void print()       { System.out.print("b "); }
}
// in main
A obj = new B();
obj.show();
obj.print();
```''', ["B b", "A a", "A b", "B a"], 2,
'''Static methods are hidden, not overridden. They are resolved at compile time from the reference type `A`, so `show()` prints "A". Instance methods use dynamic dispatch on the runtime object `B`, so `print()` prints "b".''',
["Microsoft", "Adobe", "Oracle"]),

M("OOP output prediction", '''What does this print?
```java
class P { int x = 10; int get() { return x; } }
class Q extends P { int x = 20; int get() { return x; } }
// in main
P p = new Q();
System.out.println(p.x + " " + p.get());
```''', ["20 20", "10 10", "10 20", "20 10"], 2,
'''Fields are not polymorphic. `p.x` is resolved from the reference type `P`, giving 10. The method `get()` is overridden, so it runs `Q.get()`, which reads `Q`'s own `x`, giving 20. This is called field hiding, and it is a common interview trap.''',
["Adobe", "SAP"]),

M("OOP output prediction", '''What does `new B();` print?
```java
class A {
    static { System.out.print("1"); }
    { System.out.print("2"); }
    A() { System.out.print("3"); }
}
class B extends A {
    static { System.out.print("4"); }
    { System.out.print("5"); }
    B() { System.out.print("6"); }
}
```''', ["123456", "142356", "412563", "145236"], 1,
'''Class initialization runs first, parent before child: static blocks 1 and then 4. Next, construction: `B()` implicitly calls `super()`, so A's instance initializer (2) and constructor body (3) run, followed by B's instance initializer (5) and constructor body (6). Result: 142356.''',
["Microsoft", "Adobe", "Goldman Sachs"]),

M("Java overloading", '''What does this print?
```java
static void m(Object o) { System.out.println("Object"); }
static void m(String s) { System.out.println("String"); }
// in main
m(null);
```''', ["Object", "String", "Compile error: ambiguous", "NullPointerException"], 1,
'''`null` is compatible with both parameter types, and the compiler picks the most specific overload. `String` is a subclass of `Object`, so `m(String)` wins. If there were also an `m(Integer)` overload, the call would be ambiguous and would not compile.''',
["Microsoft", "Oracle"]),

M("OOP", '''Which statement about Java interfaces (Java 9+) is FALSE?''',
["They can declare static methods", "They can have default methods", "They can have private helper methods",
 "They can declare non-final instance fields"], 3,
'''Any field declared in an interface is implicitly `public static final`, which makes it a constant. Interfaces cannot hold per-instance state. Java 8 added default and static methods, and Java 9 added private methods for sharing code between default methods.''',
["Adobe", "SAP", "Microsoft"]),

M("OOP", '''A class implements two interfaces that BOTH define `default void greet()`. What happens?''',
["The first interface listed wins", "Compile error unless the class overrides greet()",
 "Runtime exception when greet() is called", "The method from the interface declared later wins"], 1,
'''This is the diamond problem with default methods. Java refuses to guess and reports a compile error. The class must override `greet()`, and inside it can choose an implementation explicitly with `InterfaceA.super.greet()`.''',
["Microsoft", "Adobe"]),

M("OOP", '''A superclass has `public void process()`. A subclass overrides it as `protected void process()`. What is the result?''',
["Compiles; the subclass method is just less visible", "Compile error: an override cannot reduce visibility",
 "Runtime IllegalAccessError", "Compiles but becomes overloading instead of overriding"], 1,
'''An overriding method may keep or widen access, but must not narrow it. Otherwise code that holds a superclass reference could not call it, which breaks substitutability. Covariant return types and fewer or narrower checked exceptions are allowed.''',
["Oracle", "Adobe"]),

M("Trees", '''Which traversal of a Binary Search Tree visits the keys in ascending order?''',
["Preorder", "Postorder", "Inorder", "Level order"], 2,
'''Inorder visits the left subtree, then the node, then the right subtree. In a BST, everything on the left is smaller and everything on the right is larger, so inorder produces sorted output. This property is used to validate a BST or find the kth smallest element.''',
["Microsoft", "Amazon", "Adobe"]),

M("Trees", '''What is the maximum number of nodes in a binary tree of height h, where a tree with only a root has height 1?''',
["2^h", "2^h - 1", "2^(h-1)", "h^2"], 1,
'''Level i (counting from 1) can hold at most 2^(i-1) nodes. Summing 1 + 2 + 4 + ... + 2^(h-1) gives 2^h - 1, which is a perfect binary tree. If height is instead counted in edges (root has height 0), the formula becomes 2^(h+1) - 1.''',
["Microsoft", "Oracle"]),

M("Trees", '''Which pair of traversals does NOT, in general, uniquely identify an arbitrary binary tree (with distinct values)?''',
["Inorder + Preorder", "Inorder + Postorder", "Preorder + Postorder", "Inorder + Level order"], 2,
'''Without inorder, you cannot tell whether a lone child is a left child or a right child. For example, preorder 1,2 and postorder 2,1 fit both shapes. Preorder plus postorder is unique only for full binary trees, where every node has 0 or 2 children.''',
["Microsoft", "Adobe"]),

M("Linked lists", '''In Floyd's cycle detection, slow and fast meet inside the cycle. You then move one pointer back to head and advance both by ONE step at a time. Where do they meet?''',
["At the head", "At the node where the cycle begins", "At the middle of the list", "They never meet again"], 1,
'''If the distance from head to the cycle start is a, and from the start to the meeting point is b, the math gives a = k*cycleLength - b. So moving both pointers by a steps brings them together at the cycle's entry node. It needs O(n) time and O(1) space.''',
["Microsoft", "Amazon", "Adobe"]),

M("Linked lists", '''Using `slow = head; fast = head; while (fast != null && fast.next != null) { slow = slow.next; fast = fast.next.next; }` on the list 1->2->3->4->5->6, which node does `slow` end at?''',
["3", "4", "5", "6"], 1,
'''The fast pointer visits 1, 3, 5 and then null, so slow moves three times: 1 to 2 to 3 to 4. For even-length lists, this loop returns the SECOND middle. To get the first middle (3), use `while (fast.next != null && fast.next.next != null)`.''',
["Microsoft", "Adobe"]),

M("Trees", '''Keys 1, 2, 3, ..., n are inserted IN ORDER into a plain (unbalanced) BST. What is the worst-case time complexity of a search?''',
["O(1)", "O(log n)", "O(n)", "O(n log n)"], 2,
'''Each new key becomes the right child of the previous one, so the BST degenerates into a linked list of height n. Self-balancing trees (AVL, red-black, which back `TreeMap`) keep the height at O(log n) by rotating.''',
["Microsoft", "Amazon"]),

M("Trees", '''Which data structure is used for an iterative level-order (BFS) traversal of a binary tree?''',
["Stack", "Queue", "Priority queue", "Hash set"], 1,
'''BFS processes nodes in first-in, first-out order: dequeue a node, then enqueue its children. Reading `queue.size()` at the start of each level lets you group nodes by level, which also solves zigzag traversal, right-side view and level averages. Iterative DFS uses a stack instead.''',
["Microsoft", "Adobe", "Walmart"]),

M("SOLID", '''`Square extends Rectangle` overrides `setWidth()` to also set the height. Code that sets a Rectangle's width to 5 and height to 4 and expects an area of 20 now gets 16. Which principle is violated?''',
["Single Responsibility", "Open/Closed", "Liskov Substitution", "Dependency Inversion"], 2,
'''Liskov Substitution says a subtype must be usable wherever its base type is expected without breaking callers' assumptions. Square changes the behaviour a Rectangle promises. A better model is to make both implement a `Shape` interface instead of using inheritance.''',
["Microsoft", "Atlassian", "Adobe"]),

M("Design patterns", '''In a double-checked locking Singleton, why must the `instance` field be declared `volatile`?''',
["To make the getter synchronized", "To prevent other threads from seeing a partially constructed object through reordering",
 "To make the field final", "To stop the garbage collector from collecting the instance"], 1,
'''`instance = new Singleton()` is three steps: allocate memory, run the constructor, assign the reference. Without `volatile`, those steps can be reordered, so another thread could see a non-null reference before the constructor has finished. `volatile` adds the happens-before guarantee. Alternatives are an enum Singleton or the holder-class idiom.''',
["Adobe", "Paytm", "Goldman Sachs"]),

M("Java access modifiers", '''A member has NO access modifier (package-private). Where is it accessible?''',
["Everywhere", "Only inside its own class", "Within the same package only, including subclasses in that package",
 "Same package plus subclasses in any package"], 2,
'''Default access is package-private. A subclass in a different package cannot see it, and that is the difference from `protected`, which also grants access to subclasses in other packages through inheritance. The order from least to most visible is private, default, protected, public.''',
["Oracle", "SAP"]),

M("OOP", '''Which statement about abstract classes is TRUE?''',
["They cannot have constructors", "They cannot contain concrete methods", "They can have constructors, state and concrete methods, but cannot be instantiated directly",
 "A class can extend multiple abstract classes"], 2,
'''An abstract class can hold fields, constructors (called through `super()` from subclasses), concrete methods and abstract methods. You cannot write `new` on it directly, and Java allows single class inheritance only. Use one when related classes share state or code.''',
["Microsoft", "Oracle", "Adobe"]),

M("Java overriding", '''A parent method is declared `Animal create()`. Can the child override it as `Dog create()`, where Dog extends Animal?''',
["No, the return types must match exactly", "Yes, covariant return types are allowed", "Only if Dog is final", "Only for static methods"], 1,
'''Since Java 5, an overriding method may return a subtype of the original return type. These are called covariant returns. That is why `clone()` overrides commonly return the concrete type. Primitive return types must still match exactly.''',
["Adobe", "Microsoft"]),

M("Aptitude", '''A can finish a job in 10 days and B can finish it in 15 days. Working together, how many days do they take?''',
["5", "6", "7.5", "12.5"], 1,
'''A does 1/10 of the job per day and B does 1/15. Together that is 3/30 + 2/30 = 5/30 = 1/6 per day, so the job takes 6 days. A quick check: in 30 days A would do 3 jobs and B 2 jobs, so 5 jobs take 30 days and one job takes 6.''',
["Adobe", "Oracle", "SAP"]),
]

coding = [
C("Lowest Common Ancestor of a Binary Tree", "Medium", ["Microsoft", "Amazon", "Adobe", "Flipkart"],
'''You are given the root of a binary tree (NOT necessarily a BST) and two nodes `p` and `q` that both exist in it. Return their lowest common ancestor, which is the deepest node that has both `p` and `q` as descendants. A node counts as a descendant of itself.

**Example**
```
Tree: [3,5,1,6,2,0,8,null,null,7,4]
p = 5, q = 1  ->  3
p = 5, q = 4  ->  5   (5 is an ancestor of 4)
```
**Constraints**
- 2 <= number of nodes <= 10^5
- All values are unique; p != q; both are in the tree''',
["Ask each subtree: 'did you find p or q?' and pass the answer up.",
 "If the left and right subtrees each report a non-null node, the current node is the LCA."],
r'''
/* class TreeNode { int val; TreeNode left, right; TreeNode(int v) { val = v; } } */
class Solution {
    public TreeNode lowestCommonAncestor(TreeNode root, TreeNode p, TreeNode q) {
        if (root == null || root == p || root == q) return root;
        TreeNode left = lowestCommonAncestor(root.left, p, q);
        TreeNode right = lowestCommonAncestor(root.right, p, q);
        if (left != null && right != null) return root;   // p and q split here
        return left != null ? left : right;
    }
}
''',
'''This is a post-order recursion. Each call returns `p` or `q` if it finds one in its subtree, the LCA if both were found below, or null. If the current node is `p` or `q`, we return it right away. Its subtree may contain the other node, but then the current node is already the LCA. When both the left and right recursive calls return non-null, `p` and `q` lie on different sides, so this node is where their paths split. Otherwise we pass up whichever side is non-null. A common follow-up: if p or q might not be in the tree, track whether each was actually found. For a BST, you can just walk down by comparing values.''',
"O(n)", "O(h) recursion stack", "https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/"),

C("Copy List with Random Pointer", "Medium", ["Microsoft", "Amazon", "Adobe", "Goldman Sachs"],
'''Each node of a linked list has a `next` pointer and a `random` pointer that may point to any node in the list or be null. Build a deep copy: brand-new nodes whose `next` and `random` pointers form the same structure, without pointing back into the original list.

**Example**
```
Input:  [[7,null],[13,0],[11,4],[10,2],[1,0]]   // [val, randomIndex]
Output: [[7,null],[13,0],[11,4],[10,2],[1,0]]
```
**Constraints**
- 0 <= n <= 1000
- -10^4 <= Node.val <= 10^4''',
["A HashMap from original node to copy makes it easy in O(n) space.",
 "For O(1) extra space, weave each copy right after its original: A -> A' -> B -> B'."],
r'''
/* class Node { int val; Node next, random; Node(int v) { val = v; } } */
class Solution {
    public Node copyRandomList(Node head) {
        if (head == null) return null;
        // 1. Interleave copies: A -> A' -> B -> B'
        for (Node cur = head; cur != null; cur = cur.next.next) {
            Node copy = new Node(cur.val);
            copy.next = cur.next;
            cur.next = copy;
        }
        // 2. Set random pointers of copies
        for (Node cur = head; cur != null; cur = cur.next.next) {
            if (cur.random != null) cur.next.random = cur.random.next;
        }
        // 3. Detach the two lists
        Node dummy = new Node(0), tail = dummy;
        for (Node cur = head; cur != null; cur = cur.next) {
            tail.next = cur.next;
            tail = tail.next;
            cur.next = cur.next.next;   // restore original
        }
        return dummy.next;
    }
}
''',
'''The simple approach uses a `HashMap<Node, Node>` from each original to its copy, in two passes. Interviewers at Microsoft and Amazon often ask you to remove the map. The interleaving trick puts each copy directly after its original, so "the copy of X" is just `X.next`. That lets you set the copy's random pointer with `cur.next.random = cur.random.next`. The last pass splits the merged list into the copy and the restored original. Restoring the original matters because callers do not expect their input to be changed. Draw the three passes on the whiteboard before you code.''',
"O(n)", "O(1) extra (excluding the output list)", "https://leetcode.com/problems/copy-list-with-random-pointer/"),

C("Reverse Nodes in k-Group", "Hard", ["Microsoft", "Adobe", "Amazon", "Paytm"],
'''Given the head of a linked list, reverse the nodes `k` at a time and return the new head. If the number of nodes left at the end is less than `k`, leave them as they are. Rearrange the nodes themselves; changing only their values is not allowed.

**Example**
```
Input:  1->2->3->4->5, k = 2   Output: 2->1->4->3->5
Input:  1->2->3->4->5, k = 3   Output: 3->2->1->4->5
```
**Constraints**
- 1 <= k <= n <= 5000
- O(1) extra memory is the expected follow-up''',
["Use a dummy node, and keep `groupPrev` pointing at the node just before the current group.",
 "First check that k nodes exist ahead; then reverse exactly k nodes and reconnect both ends."],
r'''
/* class ListNode { int val; ListNode next; ListNode(int v) { val = v; } } */
class Solution {
    public ListNode reverseKGroup(ListNode head, int k) {
        ListNode dummy = new ListNode(0);
        dummy.next = head;
        ListNode groupPrev = dummy;
        while (true) {
            ListNode kth = groupPrev;
            for (int i = 0; i < k && kth != null; i++) kth = kth.next;
            if (kth == null) break;                 // fewer than k nodes left
            ListNode groupNext = kth.next;
            // reverse the group
            ListNode prev = groupNext, cur = groupPrev.next;
            while (cur != groupNext) {
                ListNode nxt = cur.next;
                cur.next = prev;
                prev = cur;
                cur = nxt;
            }
            ListNode oldFirst = groupPrev.next;     // becomes the group's tail
            groupPrev.next = kth;
            groupPrev = oldFirst;
        }
        return dummy.next;
    }
}
''',
'''For each group, find its kth node. If there are fewer than k nodes left, stop and leave them unchanged. Then reverse the group with the standard three-pointer loop. The trick is to start `prev` at `groupNext` rather than null, so the group's new tail already points to the rest of the list once the loop ends. Finally, attach `groupPrev` to the new head (`kth`) and move `groupPrev` to the old first node, which is now the tail. The dummy node removes the special case for the first group. Each node is visited a constant number of times.''',
"O(n)", "O(1)", "https://leetcode.com/problems/reverse-nodes-in-k-group/"),

C("Serialize and Deserialize Binary Tree", "Hard", ["Microsoft", "Amazon", "Uber", "Google"],
'''Design two functions. `serialize(root)` turns a binary tree into a single String, and `deserialize(data)` rebuilds exactly the same tree from that String. You may choose any format, as long as the round trip preserves the structure.

**Example**
```
Input tree: [1,2,3,null,null,4,5]
serialize   -> "1,2,#,#,3,4,#,#,5,#,#"   (one possible format)
deserialize -> the same tree
```
**Constraints**
- 0 <= nodes <= 10^4
- -1000 <= Node.val <= 1000''',
["Preorder traversal with an explicit marker for null children uniquely describes the tree.",
 "When deserializing, consume tokens in the same preorder using a shared iterator or queue."],
r'''
import java.util.*;

/* class TreeNode { int val; TreeNode left, right; TreeNode(int v) { val = v; } } */
public class Codec {
    public String serialize(TreeNode root) {
        StringBuilder sb = new StringBuilder();
        write(root, sb);
        return sb.toString();
    }
    private void write(TreeNode n, StringBuilder sb) {
        if (n == null) { sb.append("#,"); return; }
        sb.append(n.val).append(',');
        write(n.left, sb);
        write(n.right, sb);
    }

    public TreeNode deserialize(String data) {
        Deque<String> tokens = new ArrayDeque<>(Arrays.asList(data.split(",")));
        return read(tokens);
    }
    private TreeNode read(Deque<String> tokens) {
        String t = tokens.poll();
        if (t == null || t.equals("#")) return null;
        TreeNode n = new TreeNode(Integer.parseInt(t));
        n.left = read(tokens);
        n.right = read(tokens);
        return n;
    }
}
''',
'''Preorder alone is ambiguous, but preorder with null markers (`#`) is not, because every subtree's boundaries are explicit. Serialization writes the node value, then the left subtree, then the right subtree. Deserialization reads tokens in the same order from a shared queue: a `#` returns null, anything else creates a node and recursively builds its left and right children. Use `StringBuilder` to avoid O(n^2) string concatenation. Follow-ups you might get: a BFS-based format like LeetCode's, a more compact encoding for a BST (preorder plus value bounds, no null markers), and an iterative version to avoid stack overflow on very deep, skewed trees.''',
"O(n) for both operations", "O(n)", "https://leetcode.com/problems/serialize-and-deserialize-binary-tree/"),
]

theory = [
T("Explain the SOLID principles with an example from a Spring Boot project.",
'''**S – Single Responsibility:** a class has one reason to change. `OrderController` handles HTTP, `OrderService` holds business rules, and `OrderRepository` handles persistence. **O – Open/Closed:** add behaviour without editing existing code. A new payment mode is a new `PaymentStrategy` bean, not another `if-else` branch. **L – Liskov Substitution:** any `PaymentStrategy` implementation can replace another without surprising callers. **I – Interface Segregation:** prefer small interfaces such as `Readable` and `Exportable` over one large interface that forces empty implementations. **D – Dependency Inversion:** depend on abstractions. Services take interfaces through constructor injection, and Spring wires in the concrete beans, which also makes mocking easy in unit tests. Close with a concrete refactor you did, such as replacing a switch on payment type with strategy beans held in a `Map<String, PaymentStrategy>`.''',
["Microsoft", "Adobe", "Walmart", "Atlassian"]),

T("Abstract class vs interface: when do you choose which, given that Java 8+ interfaces can have default methods?",
'''An **interface** defines a capability or contract: no instance state, multiple inheritance of type, and default, static and private methods for shared behaviour. Use one when unrelated classes need the same role (`Comparable`, `PaymentGateway`) or when you want easy mocking and multiple implementations. An **abstract class** can hold instance fields, constructors, protected members and a partly implemented algorithm, as in the Template Method pattern, but a class can extend only one. Use it when closely related classes share state and code, for example `AbstractNotificationSender` with common retry and logging logic plus an abstract `doSend()`. Rule of thumb: start with an interface, and add an abstract base class implementing it only if implementations duplicate state or logic. Default methods were added mainly to evolve APIs without breaking existing implementers, not to replace abstract classes.''',
["Adobe", "Oracle", "Microsoft", "SAP"]),

T("Overloading vs overriding: how does Java decide which method to call?",
'''**Overloading** means the same method name with different parameter lists in the same class or hierarchy. The compiler picks the method at compile time from the static types of the arguments, preferring an exact match, then widening, then boxing, then varargs. The return type alone cannot distinguish overloads. **Overriding** means a subclass provides a new implementation with the same signature. The call is resolved at runtime through dynamic dispatch on the actual object type (the JVM uses a vtable). Overriding rules: you cannot reduce visibility, you may use a covariant return type, you cannot throw broader checked exceptions, and `static`, `private` and `final` methods are not overridden (static ones are hidden). Annotate overrides with `@Override` so the compiler catches signature mistakes.''',
["Microsoft", "SAP", "Oracle"]),

T("Composition vs inheritance: why is 'favour composition over inheritance' good advice?",
'''Inheritance is an "is-a" relationship that is fixed at compile time. Subclasses depend on parent implementation details (the fragile base class problem), and Java allows only one parent. Composition is a "has-a" relationship: a class holds references to collaborators and delegates work to them. You can swap behaviour at runtime, test with mocks, and combine several capabilities. Example: rather than `LoggingArrayList extends ArrayList` (which double-counts, because `addAll` calls `add` internally), wrap a `List` and delegate. In Spring, services are composed of injected repositories, clients and strategies. That is composition. Inheritance is still right for true subtype relationships with a stable base, such as a framework base class or a sealed hierarchy of domain types.''',
["Microsoft", "Atlassian", "Adobe"]),

T("How do you implement a thread-safe Singleton? How can a Singleton be broken?",
'''Options: (1) an eager `private static final` instance, which is simple and thread-safe; (2) the holder idiom, a `private static class Holder { static final S INSTANCE = new S(); }`, which is lazy and thread-safe through class-loading guarantees; (3) double-checked locking with a `volatile` field; (4) an `enum` with a single constant, which Joshua Bloch recommends. A Singleton can be broken by **reflection**, by calling the private constructor via `setAccessible(true)` (guard: throw in the constructor if the instance already exists); by **serialization**, because deserializing creates a new object (guard: implement `readResolve()` returning the instance); by **cloning** (guard: override `clone()` to throw); and by **multiple classloaders**. The enum approach handles reflection and serialization automatically. In Spring, beans are singletons per container by default, which is why you rarely write this pattern by hand.''',
["Adobe", "Paytm", "Goldman Sachs", "Microsoft"]),

T("Which design patterns have you used in your project? Explain one in detail.",
'''Pick 2-3 that you can actually defend. **Strategy:** for multiple discount or payment types, an interface `DiscountStrategy` with Spring beans `FlatDiscount` and `PercentDiscount`, chosen at runtime from a map injected by Spring. This removed a growing switch statement and follows Open/Closed. **Builder:** Lombok `@Builder` for DTOs with many optional fields, which keeps construction readable and immutable. **Factory:** creating the right `ReportExporter` (PDF, CSV, Excel) from a request parameter. **Observer:** Spring `ApplicationEventPublisher` to send email after an order is saved, without coupling the order service to the mailer. Also recognise the patterns the framework uses: proxy (AOP, `@Transactional`), template method (`JdbcTemplate`), and singleton (bean scope). Explain the problem, the pattern, and the trade-off it introduced.''',
["Microsoft", "Swiggy", "Adobe", "Walmart"]),
]

DAY = build(2, "Microsoft & Adobe", "Tree and linked-list problems that Microsoft and Adobe interviewers favour, plus OOP, inheritance and design-principle MCQs.", mcqs, coding, theory)
