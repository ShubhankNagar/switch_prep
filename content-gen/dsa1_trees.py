from dsa1_common import P, PAT

TR_INTRO = r'''
**Binary Trees & BSTs** are the most-asked topic at product companies. Nearly every tree problem is either a **DFS (recursion)** or a **BFS (level order with a queue)**.

**How to choose**
- Answer depends on subtrees (height, diameter, balanced, path sums, LCA) -> **post-order DFS**: compute children first, combine at the parent, return something upward.
- Need info passed down from ancestors (max so far, valid range for BST, path so far) -> **pre-order DFS** with extra parameters.
- Anything "per level" (level order, right view, zigzag, width, min depth) -> **BFS**, processing `queue.size()` nodes at a time.
- BST -> exploit ordering: **in-order traversal yields sorted values**; search goes left or right only.

LeetCode's node: `TreeNode { int val; TreeNode left, right; }` (already defined).

**DFS template (return value + global answer)**
```java
int best = 0;
int dfs(TreeNode node) {
    if (node == null) return 0;              // base case
    int left = dfs(node.left);
    int right = dfs(node.right);
    best = Math.max(best, left + right);     // answer that "bends" through node
    return 1 + Math.max(left, right);        // value passed to parent
}
```

**BFS template**
```java
Deque<TreeNode> q = new ArrayDeque<>();
if (root != null) q.offer(root);
while (!q.isEmpty()) {
    int size = q.size();
    for (int i = 0; i < size; i++) {
        TreeNode node = q.poll();
        // process node
        if (node.left != null) q.offer(node.left);
        if (node.right != null) q.offer(node.right);
    }
    // a level is finished here
}
```

**Pitfalls**
- Distinguish what you **return** to the parent vs what you **record** as the global answer (diameter, max path sum).
- Validating a BST by only checking immediate children is wrong - pass down `(min, max)` bounds (use `long` or nullable bounds for `Integer.MIN_VALUE` edge cases).
- Recursion depth on skewed trees can be O(n) - mention iterative alternatives.
- `ArrayDeque` cannot hold `null`; check children before offering.
'''

tr = [
P("maximum-depth-of-binary-tree", "Maximum Depth of Binary Tree", "Easy", "Amazon, Microsoft, LinkedIn, Apple, Adobe",
"Return the number of nodes on the longest path from the root down to a leaf. Example: [3,9,20,null,null,15,7] -> 3.",
r'''
Recursive definition: depth(null) = 0; depth(node) = 1 + max(depth(left), depth(right)). That's a post-order DFS in one line.

Iterative alternative: BFS and count levels. Both O(n) time; DFS uses O(h) stack, BFS uses O(width) queue.
''',
r'''
class Solution {
    public int maxDepth(TreeNode root) {
        if (root == null) return 0;
        return 1 + Math.max(maxDepth(root.left), maxDepth(root.right));
    }
}
''', "O(n)", "O(h)"),

P("invert-binary-tree", "Invert Binary Tree", "Easy", "Google, Amazon, Microsoft, Adobe",
"Mirror a binary tree by swapping every node's left and right children, and return the root. Example: [4,2,7,1,3,6,9] -> [4,7,2,9,6,3,1].",
r'''
At each node swap the two children, then invert both subtrees (order doesn't matter - pre-order or post-order both work). Base case: null returns null.

Iterative version: BFS, swapping children of every polled node. O(n) time.
''',
r'''
class Solution {
    public TreeNode invertTree(TreeNode root) {
        if (root == null) return null;
        TreeNode left = invertTree(root.left);
        root.left = invertTree(root.right);
        root.right = left;
        return root;
    }
}
''', "O(n)", "O(h)"),

P("same-tree", "Same Tree", "Easy", "Amazon, Microsoft, Bloomberg",
"Check whether two binary trees are structurally identical with equal values at every node. Example: [1,2,3] and [1,2,3] -> true; [1,2] and [1,null,2] -> false.",
r'''
Compare recursively: both null -> true; exactly one null or values differ -> false; otherwise both left subtrees and both right subtrees must match. O(n) time.

This helper is reused in Subtree of Another Tree.
''',
r'''
class Solution {
    public boolean isSameTree(TreeNode p, TreeNode q) {
        if (p == null && q == null) return true;
        if (p == null || q == null || p.val != q.val) return false;
        return isSameTree(p.left, q.left) && isSameTree(p.right, q.right);
    }
}
''', "O(n)", "O(h)"),

P("subtree-of-another-tree", "Subtree of Another Tree", "Easy", "Amazon, Microsoft, Facebook, Google",
"Return true if subRoot appears inside root as a subtree: some node of root together with all its descendants is identical to subRoot.",
r'''
For every node in `root`, check `isSame(node, subRoot)`. Recurse: answer is `isSame(root, subRoot) || isSubtree(root.left, subRoot) || isSubtree(root.right, subRoot)`. Worst case O(n·m).

**Optimal follow-up:** serialize both trees (with null markers and delimiters) and do a substring search with KMP - O(n + m).
''',
r'''
class Solution {
    public boolean isSubtree(TreeNode root, TreeNode subRoot) {
        if (root == null) return false;
        if (isSame(root, subRoot)) return true;
        return isSubtree(root.left, subRoot) || isSubtree(root.right, subRoot);
    }

    private boolean isSame(TreeNode a, TreeNode b) {
        if (a == null && b == null) return true;
        if (a == null || b == null || a.val != b.val) return false;
        return isSame(a.left, b.left) && isSame(a.right, b.right);
    }
}
''', "O(n * m)", "O(h)"),

P("diameter-of-binary-tree", "Diameter of Binary Tree", "Easy", "Facebook, Amazon, Google, Microsoft, Flipkart",
"Return the number of edges on the longest path between any two nodes of a binary tree (the path need not pass through the root). Example: [1,2,3,4,5] -> 3 (4-2-1-3).",
r'''
The longest path through a node = height(left) + height(right) (in edges). Compute heights with post-order DFS and, at each node, update a global `best` with `left + right`. Return `1 + max(left, right)` upward.

**Classic trap:** the answer isn't necessarily through the root, which is why we check every node. O(n) instead of the naive O(n²) (recomputing heights).
''',
r'''
class Solution {
    private int best = 0;

    public int diameterOfBinaryTree(TreeNode root) {
        height(root);
        return best;
    }

    private int height(TreeNode node) {
        if (node == null) return 0;
        int l = height(node.left), r = height(node.right);
        best = Math.max(best, l + r);
        return 1 + Math.max(l, r);
    }
}
''', "O(n)", "O(h)", True),

P("balanced-binary-tree", "Balanced Binary Tree", "Easy", "Amazon, Google, Microsoft, Bloomberg",
"A tree is height-balanced if at every node the left and right subtree heights differ by at most 1. Determine whether the given tree is balanced.",
r'''
**Naive:** at every node compute both heights separately - O(n²) on skewed trees.

**Optimal:** one post-order pass returning the height, or **-1** as a sentinel meaning "already unbalanced". If either child returns -1 or the heights differ by more than 1, return -1 immediately. The tree is balanced iff the root doesn't return -1. O(n).
''',
r'''
class Solution {
    public boolean isBalanced(TreeNode root) {
        return check(root) != -1;
    }

    private int check(TreeNode node) {
        if (node == null) return 0;
        int l = check(node.left);
        if (l == -1) return -1;
        int r = check(node.right);
        if (r == -1 || Math.abs(l - r) > 1) return -1;
        return 1 + Math.max(l, r);
    }
}
''', "O(n)", "O(h)"),

P("binary-tree-level-order-traversal", "Binary Tree Level Order Traversal", "Medium", "Amazon, Microsoft, Facebook, LinkedIn, Flipkart, Oracle",
"Return the node values level by level, left to right, as a list of lists. Example: [3,9,20,null,null,15,7] -> [[3],[9,20],[15,7]].",
r'''
Standard BFS with a queue. The trick for grouping by level: at the start of each iteration, record `size = queue.size()` - exactly the nodes of the current level - and poll that many, adding their children for the next level.

DFS alternative: pass `depth` and append to `result.get(depth)`. Both O(n).
''',
r'''
class Solution {
    public List<List<Integer>> levelOrder(TreeNode root) {
        List<List<Integer>> res = new ArrayList<>();
        if (root == null) return res;
        Deque<TreeNode> q = new ArrayDeque<>();
        q.offer(root);
        while (!q.isEmpty()) {
            int size = q.size();
            List<Integer> level = new ArrayList<>(size);
            for (int i = 0; i < size; i++) {
                TreeNode node = q.poll();
                level.add(node.val);
                if (node.left != null) q.offer(node.left);
                if (node.right != null) q.offer(node.right);
            }
            res.add(level);
        }
        return res;
    }
}
''', "O(n)", "O(n)", True),

P("binary-tree-right-side-view", "Binary Tree Right Side View", "Medium", "Facebook, Amazon, Microsoft, Bloomberg, Flipkart",
"Imagine standing to the right of the tree: return the values you can see from top to bottom (the rightmost node of each level). Example: [1,2,3,null,5,null,4] -> [1,3,4].",
r'''
**BFS:** level order, and take the **last** node of each level.

**DFS (elegant):** visit right child before left, passing depth. The first time you reach a new depth (`depth == result.size()`), that node is the rightmost of that level. O(n).

The left view is the same with left-first traversal.
''',
r'''
class Solution {
    public List<Integer> rightSideView(TreeNode root) {
        List<Integer> res = new ArrayList<>();
        dfs(root, 0, res);
        return res;
    }

    private void dfs(TreeNode node, int depth, List<Integer> res) {
        if (node == null) return;
        if (depth == res.size()) res.add(node.val);
        dfs(node.right, depth + 1, res);
        dfs(node.left, depth + 1, res);
    }
}
''', "O(n)", "O(h)", True),

P("binary-tree-zigzag-level-order-traversal", "Binary Tree Zigzag Level Order Traversal", "Medium", "Amazon, Microsoft, Facebook, Bloomberg, Walmart",
"Return level-order values but alternate direction each level: left-to-right, then right-to-left, and so on. Example: [3,9,20,null,null,15,7] -> [[3],[20,9],[15,7]].",
r'''
Do normal BFS, but build each level in a `LinkedList`: on left-to-right levels `addLast`, on right-to-left levels `addFirst`. Flip a boolean after each level. Children are still enqueued left then right, so the queue order is unchanged. O(n).
''',
r'''
class Solution {
    public List<List<Integer>> zigzagLevelOrder(TreeNode root) {
        List<List<Integer>> res = new ArrayList<>();
        if (root == null) return res;
        Deque<TreeNode> q = new ArrayDeque<>();
        q.offer(root);
        boolean leftToRight = true;
        while (!q.isEmpty()) {
            int size = q.size();
            LinkedList<Integer> level = new LinkedList<>();
            for (int i = 0; i < size; i++) {
                TreeNode node = q.poll();
                if (leftToRight) level.addLast(node.val);
                else level.addFirst(node.val);
                if (node.left != null) q.offer(node.left);
                if (node.right != null) q.offer(node.right);
            }
            res.add(level);
            leftToRight = !leftToRight;
        }
        return res;
    }
}
''', "O(n)", "O(n)"),

P("lowest-common-ancestor-of-a-binary-search-tree", "Lowest Common Ancestor of a Binary Search Tree", "Medium", "Amazon, Facebook, Microsoft, LinkedIn, Twitter",
"In a BST, find the lowest node that has both given nodes p and q as descendants (a node counts as its own descendant). Example: root [6,2,8,0,4,7,9], p = 2, q = 8 -> 6.",
r'''
Use the BST ordering. Starting from the root:
- If both `p` and `q` are smaller than the node, the LCA is in the left subtree.
- If both are larger, go right.
- Otherwise they split here (or one equals the node) - this node is the LCA.

Iterative, O(h) time, O(1) space.
''',
r'''
class Solution {
    public TreeNode lowestCommonAncestor(TreeNode root, TreeNode p, TreeNode q) {
        TreeNode node = root;
        while (node != null) {
            if (p.val < node.val && q.val < node.val) node = node.left;
            else if (p.val > node.val && q.val > node.val) node = node.right;
            else return node;
        }
        return null;
    }
}
''', "O(h)", "O(1)"),

P("lowest-common-ancestor-of-a-binary-tree", "Lowest Common Ancestor of a Binary Tree", "Medium", "Facebook, Amazon, Microsoft, Google, Flipkart, Atlassian, Uber",
"In a general binary tree (no ordering), return the lowest node that has both p and q as descendants (a node may be its own descendant). Both nodes exist in the tree.",
r'''
Post-order DFS returning "the p or q (or LCA) found in this subtree":
- If node is null, p, or q -> return node.
- Recurse left and right.
- If **both** sides return non-null, p and q are in different subtrees -> current node is the LCA.
- Otherwise return whichever side is non-null.

O(n) time, O(h) space. Know this one cold - it's among the most asked tree questions.
''',
r'''
class Solution {
    public TreeNode lowestCommonAncestor(TreeNode root, TreeNode p, TreeNode q) {
        if (root == null || root == p || root == q) return root;
        TreeNode left = lowestCommonAncestor(root.left, p, q);
        TreeNode right = lowestCommonAncestor(root.right, p, q);
        if (left != null && right != null) return root;
        return left != null ? left : right;
    }
}
''', "O(n)", "O(h)", True),

P("validate-binary-search-tree", "Validate Binary Search Tree", "Medium", "Amazon, Microsoft, Facebook, Bloomberg, Adobe, Oracle",
"Check whether a binary tree is a valid BST: every node's left subtree has only smaller values, its right subtree only larger values, and both subtrees are BSTs. Example: [5,1,4,null,null,3,6] -> false.",
r'''
**Wrong approach:** only comparing each node with its direct children - a deep node can violate an ancestor's constraint.

**Correct:** pass down an allowed open range `(low, high)`. Going left tightens `high = node.val`; going right tightens `low = node.val`. Use `long` bounds so nodes with `Integer.MIN_VALUE`/`MAX_VALUE` work.

**Alternative:** in-order traversal must be strictly increasing - track the previous value. Both O(n).
''',
r'''
class Solution {
    public boolean isValidBST(TreeNode root) {
        return valid(root, Long.MIN_VALUE, Long.MAX_VALUE);
    }

    private boolean valid(TreeNode node, long low, long high) {
        if (node == null) return true;
        if (node.val <= low || node.val >= high) return false;
        return valid(node.left, low, node.val) && valid(node.right, node.val, high);
    }
}
''', "O(n)", "O(h)", True),

P("kth-smallest-element-in-a-bst", "Kth Smallest Element in a BST", "Medium", "Amazon, Facebook, Google, Uber, Oracle",
"Return the k-th smallest value (1-indexed) in a binary search tree. Example: root [3,1,4,null,2], k = 1 -> 1.",
r'''
In-order traversal of a BST visits values in sorted order, so the k-th visited node is the answer. Do it **iteratively** with an explicit stack so you can stop as soon as you've popped k nodes - O(h + k) time instead of traversing everything.

**Follow-up (frequent inserts/deletes):** augment each node with its subtree size, then descend in O(h).
''',
r'''
class Solution {
    public int kthSmallest(TreeNode root, int k) {
        Deque<TreeNode> st = new ArrayDeque<>();
        TreeNode cur = root;
        while (cur != null || !st.isEmpty()) {
            while (cur != null) {
                st.push(cur);
                cur = cur.left;
            }
            cur = st.pop();
            if (--k == 0) return cur.val;
            cur = cur.right;
        }
        return -1;
    }
}
''', "O(h + k)", "O(h)"),

P("construct-binary-tree-from-preorder-and-inorder-traversal", "Construct Binary Tree from Preorder and Inorder Traversal", "Medium", "Amazon, Microsoft, Google, Facebook, Bloomberg",
"Given the preorder and inorder traversals of a tree with unique values, rebuild the tree and return its root. Example: preorder [3,9,20,15,7], inorder [9,3,15,20,7] -> [3,9,20,null,null,15,7].",
r'''
Preorder's first element is the root. Find it in inorder: everything left of it is the left subtree, everything right is the right subtree. Recurse.

**Optimization:** a HashMap from value -> inorder index makes the lookup O(1), and a global pointer into preorder avoids slicing arrays. Build left before right (preorder order). O(n) total.
''',
r'''
class Solution {
    private int preIdx = 0;
    private final Map<Integer, Integer> inPos = new HashMap<>();

    public TreeNode buildTree(int[] preorder, int[] inorder) {
        for (int i = 0; i < inorder.length; i++) inPos.put(inorder[i], i);
        return build(preorder, 0, inorder.length - 1);
    }

    private TreeNode build(int[] preorder, int lo, int hi) {
        if (lo > hi) return null;
        int rootVal = preorder[preIdx++];
        TreeNode root = new TreeNode(rootVal);
        int mid = inPos.get(rootVal);
        root.left = build(preorder, lo, mid - 1);
        root.right = build(preorder, mid + 1, hi);
        return root;
    }
}
''', "O(n)", "O(n)", True),

P("binary-tree-maximum-path-sum", "Binary Tree Maximum Path Sum", "Hard", "Facebook, Amazon, Google, Microsoft, Uber, Flipkart",
"A path is any sequence of connected nodes, each used once, not necessarily through the root. Return the largest possible sum of node values on a non-empty path. Example: [-10,9,20,null,null,15,7] -> 42 (15+20+7).",
r'''
Same shape as Diameter. Define `gain(node)` = best sum of a downward path **starting** at node (what the parent can extend). Ignore negative child gains: `l = max(0, gain(left))`, `r = max(0, gain(right))`.
- The best path that **bends** at this node is `node.val + l + r` - update the global max.
- Return `node.val + max(l, r)` to the parent (a path can only continue down one side).

Initialize the global max with `Integer.MIN_VALUE` for all-negative trees. O(n).
''',
r'''
class Solution {
    private int best = Integer.MIN_VALUE;

    public int maxPathSum(TreeNode root) {
        gain(root);
        return best;
    }

    private int gain(TreeNode node) {
        if (node == null) return 0;
        int l = Math.max(0, gain(node.left));
        int r = Math.max(0, gain(node.right));
        best = Math.max(best, node.val + l + r);
        return node.val + Math.max(l, r);
    }
}
''', "O(n)", "O(h)", True),

P("serialize-and-deserialize-binary-tree", "Serialize and Deserialize Binary Tree", "Hard", "Amazon, Facebook, Microsoft, Google, LinkedIn, Uber",
"Design methods to convert a binary tree into a string and rebuild the identical tree from that string. Any format is allowed as long as it round-trips.",
r'''
**Pre-order with null markers:** write each value followed by a comma, and `#` for null children. Because nulls are explicit, pre-order alone uniquely identifies the tree.

To deserialize, split on commas into a queue and rebuild recursively: poll a token; `#` -> null; otherwise create the node and build its left then right subtree. Both O(n).

BFS (level-order) serialization is an equally valid alternative.
''',
r'''
public class Codec {
    public String serialize(TreeNode root) {
        StringBuilder sb = new StringBuilder();
        write(root, sb);
        return sb.toString();
    }

    private void write(TreeNode node, StringBuilder sb) {
        if (node == null) {
            sb.append("#,");
            return;
        }
        sb.append(node.val).append(',');
        write(node.left, sb);
        write(node.right, sb);
    }

    public TreeNode deserialize(String data) {
        Deque<String> tokens = new ArrayDeque<>(Arrays.asList(data.split(",")));
        return read(tokens);
    }

    private TreeNode read(Deque<String> tokens) {
        String t = tokens.poll();
        if (t.equals("#")) return null;
        TreeNode node = new TreeNode(Integer.parseInt(t));
        node.left = read(tokens);
        node.right = read(tokens);
        return node;
    }
}
''', "O(n)", "O(n)", True),

P("count-good-nodes-in-binary-tree", "Count Good Nodes in Binary Tree", "Medium", "Microsoft, Amazon, Salesforce",
"A node is good if no node on the path from the root to it has a greater value. Count the good nodes. Example: [3,1,4,3,null,1,5] -> 4.",
r'''
Pre-order DFS carrying `maxSoFar` - the largest value seen on the path from the root. A node is good if `node.val >= maxSoFar`. Recurse into children with `max(maxSoFar, node.val)`.

This is the template for "information flows down from ancestors". O(n).
''',
r'''
class Solution {
    public int goodNodes(TreeNode root) {
        return dfs(root, Integer.MIN_VALUE);
    }

    private int dfs(TreeNode node, int maxSoFar) {
        if (node == null) return 0;
        int good = node.val >= maxSoFar ? 1 : 0;
        int nextMax = Math.max(maxSoFar, node.val);
        return good + dfs(node.left, nextMax) + dfs(node.right, nextMax);
    }
}
''', "O(n)", "O(h)"),

P("binary-tree-inorder-traversal", "Binary Tree Inorder Traversal", "Easy", "Microsoft, Amazon, Google, Adobe",
"Return the in-order (left, node, right) sequence of node values. Example: [1,null,2,3] -> [1,3,2]. Interviewers usually ask for the iterative version.",
r'''
Recursive is trivial. **Iterative:** push nodes while going as far left as possible; pop one, record it, then move to its right child and repeat. This simulates the call stack.

Know pre-order (push right then left) and post-order (reverse of a modified pre-order) iteratively too. **Morris traversal** gives O(1) space by temporarily threading right pointers - a good bonus mention.
''',
r'''
class Solution {
    public List<Integer> inorderTraversal(TreeNode root) {
        List<Integer> res = new ArrayList<>();
        Deque<TreeNode> st = new ArrayDeque<>();
        TreeNode cur = root;
        while (cur != null || !st.isEmpty()) {
            while (cur != null) {
                st.push(cur);
                cur = cur.left;
            }
            cur = st.pop();
            res.add(cur.val);
            cur = cur.right;
        }
        return res;
    }
}
''', "O(n)", "O(h)"),

P("maximum-width-of-binary-tree", "Maximum Width of Binary Tree", "Medium", "Amazon, Google, Microsoft, Flipkart",
"The width of a level is the distance between its leftmost and rightmost non-null nodes, counting the null positions between them as in a complete tree. Return the maximum width. Example: [1,3,2,5,3,null,9] -> 4.",
r'''
Number nodes like a heap: root `0`, left child `2i`, right child `2i + 1`. Width of a level = `lastIndex - firstIndex + 1`.

BFS level by level. Indices double every level and would overflow on deep, sparse trees, so **normalize**: subtract the level's first index from every index before computing children. O(n).
''',
r'''
class Solution {
    public int widthOfBinaryTree(TreeNode root) {
        if (root == null) return 0;
        Deque<TreeNode> nodes = new ArrayDeque<>();
        Deque<Integer> idx = new ArrayDeque<>();
        nodes.offer(root);
        idx.offer(0);
        int best = 0;
        while (!nodes.isEmpty()) {
            int size = nodes.size();
            int first = idx.peekFirst();
            int last = 0;
            for (int i = 0; i < size; i++) {
                TreeNode node = nodes.poll();
                int id = idx.poll() - first;   // normalized index
                last = id;
                if (node.left != null) { nodes.offer(node.left); idx.offer(2 * id); }
                if (node.right != null) { nodes.offer(node.right); idx.offer(2 * id + 1); }
            }
            best = Math.max(best, last + 1);
        }
        return best;
    }
}
''', "O(n)", "O(n)"),

P("all-nodes-distance-k-in-binary-tree", "All Nodes Distance K in Binary Tree", "Medium", "Amazon, Facebook, Google, Microsoft, Flipkart",
"Return the values of all nodes exactly k edges away from a given target node, in any order. Example: root [3,5,1,6,2,0,8,null,null,7,4], target 5, k = 2 -> [7,4,1].",
r'''
A tree only has child pointers, but distance can go **upward** too. So:
1. DFS once to record each node's **parent** in a HashMap - the tree is now an undirected graph.
2. BFS from `target` over neighbours (left, right, parent) with a visited set, stopping after k levels. The nodes in the queue are the answer.

O(n) time and space. This "convert tree to graph" trick also solves "Burn a tree" problems.
''',
r'''
class Solution {
    public List<Integer> distanceK(TreeNode root, TreeNode target, int k) {
        Map<TreeNode, TreeNode> parent = new HashMap<>();
        fillParents(root, null, parent);

        Deque<TreeNode> q = new ArrayDeque<>();
        Set<TreeNode> seen = new HashSet<>();
        q.offer(target);
        seen.add(target);
        for (int dist = 0; dist < k && !q.isEmpty(); dist++) {
            int size = q.size();
            for (int i = 0; i < size; i++) {
                TreeNode node = q.poll();
                for (TreeNode nb : new TreeNode[]{node.left, node.right, parent.get(node)}) {
                    if (nb != null && seen.add(nb)) q.offer(nb);
                }
            }
        }
        List<Integer> res = new ArrayList<>();
        for (TreeNode node : q) res.add(node.val);
        return res;
    }

    private void fillParents(TreeNode node, TreeNode par, Map<TreeNode, TreeNode> parent) {
        if (node == null) return;
        parent.put(node, par);
        fillParents(node.left, node, parent);
        fillParents(node.right, node, parent);
    }
}
''', "O(n)", "O(n)"),

P("flatten-binary-tree-to-linked-list", "Flatten Binary Tree to Linked List", "Medium", "Microsoft, Facebook, Amazon, Adobe",
"Flatten a binary tree in place into a right-skewed \"linked list\" following pre-order, where each node's left child is null. Example: [1,2,5,3,4,null,6] -> 1->2->3->4->5->6.",
r'''
**Recursive:** flatten subtrees, then splice. **Reverse post-order** (right, left, node) with a `prev` pointer is also neat.

**O(1) space (Morris-like):** at each node with a left child, find the rightmost node of the left subtree (its pre-order predecessor of the right subtree), attach the current right subtree there, move the left subtree to the right, and null out left. Then step right. Each edge is walked a constant number of times: O(n).
''',
r'''
class Solution {
    public void flatten(TreeNode root) {
        TreeNode cur = root;
        while (cur != null) {
            if (cur.left != null) {
                TreeNode pred = cur.left;
                while (pred.right != null) pred = pred.right;
                pred.right = cur.right;
                cur.right = cur.left;
                cur.left = null;
            }
            cur = cur.right;
        }
    }
}
''', "O(n)", "O(1)"),
]

TRIE_INTRO = r'''
A **Trie** (prefix tree) stores strings character by character: each node has up to 26 children (for lowercase letters) and a flag marking the end of a word. Inserting or searching a word of length L costs O(L), independent of how many words are stored, and all words sharing a prefix share a path.

**How to recognize it**
- "Starts with / prefix", autocomplete, search suggestions.
- Searching **many words at once** in a grid or text (Word Search II) - a trie lets one DFS prune all words simultaneously.
- Wildcard matching with `.`.
- **Bitwise tries** (each node has children 0/1) for maximum XOR problems.

**Template**
```java
class TrieNode {
    TrieNode[] next = new TrieNode[26];
    boolean isEnd;          // or String word; for Word Search II
}

void insert(TrieNode root, String word) {
    TrieNode node = root;
    for (char c : word.toCharArray()) {
        int i = c - 'a';
        if (node.next[i] == null) node.next[i] = new TrieNode();
        node = node.next[i];
    }
    node.isEnd = true;
}

TrieNode walk(TrieNode root, String s) {   // returns node for prefix s or null
    TrieNode node = root;
    for (char c : s.toCharArray()) {
        node = node.next[c - 'a'];
        if (node == null) return null;
    }
    return node;
}
```
`search(word)` = `walk` != null && `isEnd`; `startsWith(prefix)` = `walk` != null.

**Pitfalls**
- Forgetting the end-of-word flag (then "app" is "found" after inserting only "apple").
- Memory: an array of 26 per node is fast but heavy; use a `HashMap<Character, TrieNode>` for large alphabets.
- In grid DFS, mark cells visited and restore them on backtrack; remove found words (null out `word`) to avoid duplicates.
'''

tries = [
P("implement-trie-prefix-tree", "Implement Trie (Prefix Tree)", "Medium", "Amazon, Microsoft, Google, Uber, Twitter, Flipkart",
"Implement a Trie class with insert(word), search(word) (exact word present?) and startsWith(prefix) (any word with this prefix?). Example: insert(\"apple\"); search(\"app\") -> false; startsWith(\"app\") -> true.",
r'''
Each node holds `children[26]` and an `isEnd` flag. `insert` walks/creates nodes for each character and marks the last one. Both `search` and `startsWith` walk the path with a shared helper; `search` additionally requires `isEnd`. Every operation is O(L) for a word of length L.
''',
r'''
class Trie {
    private static class Node {
        Node[] next = new Node[26];
        boolean isEnd;
    }

    private final Node root = new Node();

    public Trie() { }

    public void insert(String word) {
        Node node = root;
        for (char c : word.toCharArray()) {
            int i = c - 'a';
            if (node.next[i] == null) node.next[i] = new Node();
            node = node.next[i];
        }
        node.isEnd = true;
    }

    public boolean search(String word) {
        Node node = walk(word);
        return node != null && node.isEnd;
    }

    public boolean startsWith(String prefix) {
        return walk(prefix) != null;
    }

    private Node walk(String s) {
        Node node = root;
        for (char c : s.toCharArray()) {
            node = node.next[c - 'a'];
            if (node == null) return null;
        }
        return node;
    }
}
''', "O(L) per op", "O(total chars)", True),

P("design-add-and-search-words-data-structure", "Design Add and Search Words Data Structure", "Medium", "Facebook, Amazon, Google, Microsoft",
"Design a WordDictionary with addWord(word) and search(word), where the search pattern may contain '.' matching any single letter. Example: add \"bad\", \"dad\"; search(\".ad\") -> true; search(\"b..\") -> true.",
r'''
Store words in a trie. Search with DFS over the pattern index:
- Normal letter: follow that single child.
- `.`: try **every** non-null child; succeed if any branch matches.
- At the end of the pattern, return `isEnd`.

Adding is O(L). Search is O(L) without dots and up to O(26^d · L) with d dots in the worst case - fine for the constraints (at most a few dots).
''',
r'''
class WordDictionary {
    private static class Node {
        Node[] next = new Node[26];
        boolean isEnd;
    }

    private final Node root = new Node();

    public WordDictionary() { }

    public void addWord(String word) {
        Node node = root;
        for (char c : word.toCharArray()) {
            int i = c - 'a';
            if (node.next[i] == null) node.next[i] = new Node();
            node = node.next[i];
        }
        node.isEnd = true;
    }

    public boolean search(String word) {
        return dfs(word, 0, root);
    }

    private boolean dfs(String word, int pos, Node node) {
        if (node == null) return false;
        if (pos == word.length()) return node.isEnd;
        char c = word.charAt(pos);
        if (c == '.') {
            for (Node child : node.next) {
                if (child != null && dfs(word, pos + 1, child)) return true;
            }
            return false;
        }
        return dfs(word, pos + 1, node.next[c - 'a']);
    }
}
''', "O(L) add, O(26^d * L) search", "O(total chars)"),

P("word-search-ii", "Word Search II", "Hard", "Amazon, Microsoft, Google, Uber, Airbnb, Atlassian",
"Given a letter grid and a list of words, return all words that can be formed by paths of horizontally/vertically adjacent cells, using each cell at most once per word. Example: a 4x4 board with words [\"oath\",\"pea\",\"eat\",\"rain\"] -> [\"eat\",\"oath\"].",
r'''
**Naive:** run Word Search I for every word - too slow for many words.

**Trie + backtracking:** insert all words into a trie (store the full word at its end node). DFS from every cell, moving down the trie alongside the grid path; if the current letter has no child, prune immediately. When a node holds a word, record it and set `node.word = null` to avoid duplicates. Mark cells with `#` while on the path and restore afterward.

**Extra pruning:** remove leaf trie nodes after their word is found, so exhausted branches are skipped.
''',
r'''
class Solution {
    private static class Node {
        Node[] next = new Node[26];
        String word;
    }

    public List<String> findWords(char[][] board, String[] words) {
        Node root = new Node();
        for (String w : words) {
            Node node = root;
            for (char c : w.toCharArray()) {
                int i = c - 'a';
                if (node.next[i] == null) node.next[i] = new Node();
                node = node.next[i];
            }
            node.word = w;
        }
        List<String> res = new ArrayList<>();
        for (int r = 0; r < board.length; r++) {
            for (int c = 0; c < board[0].length; c++) {
                dfs(board, r, c, root, res);
            }
        }
        return res;
    }

    private void dfs(char[][] board, int r, int c, Node parent, List<String> res) {
        if (r < 0 || c < 0 || r >= board.length || c >= board[0].length) return;
        char ch = board[r][c];
        if (ch == '#') return;
        Node node = parent.next[ch - 'a'];
        if (node == null) return;
        if (node.word != null) {
            res.add(node.word);
            node.word = null;           // avoid duplicates
        }
        board[r][c] = '#';
        dfs(board, r + 1, c, node, res);
        dfs(board, r - 1, c, node, res);
        dfs(board, r, c + 1, node, res);
        dfs(board, r, c - 1, node, res);
        board[r][c] = ch;
    }
}
''', "O(m * n * 4^L)", "O(total chars)", True),

P("maximum-xor-of-two-numbers-in-an-array", "Maximum XOR of Two Numbers in an Array", "Medium", "Google, Amazon, Adobe, Microsoft",
"Return the maximum value of nums[i] XOR nums[j] over all pairs. Example: [3,10,5,25,2,8] -> 28 (5 XOR 25).",
r'''
**Brute force:** all pairs, O(n²).

**Binary trie:** insert each number bit by bit from bit 30 down to 0 (each node has children 0 and 1). To maximize XOR with `x`, walk the trie greedily: at each bit prefer the **opposite** bit (which makes that XOR bit 1); if absent, take the same bit. Higher bits dominate lower ones, so greedy is optimal. O(31·n).
''',
r'''
class Solution {
    private static class Node {
        Node[] child = new Node[2];
    }

    public int findMaximumXOR(int[] nums) {
        Node root = new Node();
        for (int x : nums) {
            Node node = root;
            for (int b = 30; b >= 0; b--) {
                int bit = (x >> b) & 1;
                if (node.child[bit] == null) node.child[bit] = new Node();
                node = node.child[bit];
            }
        }
        int best = 0;
        for (int x : nums) {
            Node node = root;
            int cur = 0;
            for (int b = 30; b >= 0; b--) {
                int bit = (x >> b) & 1;
                if (node.child[1 - bit] != null) {
                    cur |= (1 << b);
                    node = node.child[1 - bit];
                } else {
                    node = node.child[bit];
                }
            }
            best = Math.max(best, cur);
        }
        return best;
    }
}
''', "O(31 * n)", "O(31 * n)"),
]

HEAP_INTRO = r'''
A **Heap / Priority Queue** gives O(log n) insert and O(log n) removal of the smallest (or largest) element, with O(1) peek. In Java: `PriorityQueue<Integer>` is a **min-heap** by default; for a max-heap use `new PriorityQueue<>(Collections.reverseOrder())` or a comparator.

**How to recognize it**
- "K largest / K smallest / K closest / K most frequent" -> keep a heap of size **k**.
- "Running median" or "balance two halves" -> **two heaps** (max-heap for the lower half, min-heap for the upper).
- Repeatedly take the best available item (scheduling, merging k sorted lists, greedy simulation like Last Stone Weight / Reorganize String).
- Dijkstra and other "process cheapest next" graph algorithms.

**Top-K template - k largest using a min-heap of size k**
```java
PriorityQueue<Integer> pq = new PriorityQueue<>();   // min-heap
for (int x : nums) {
    pq.offer(x);
    if (pq.size() > k) pq.poll();   // drop the smallest; k largest remain
}
// pq.peek() is the k-th largest
```
Why a *min*-heap for the *largest*? The root is the weakest of the current top-k, so it's the one to evict. Cost: O(n log k), better than sorting when k is small.

**Comparators**
```java
// by frequency descending, then by key ascending
PriorityQueue<int[]> pq = new PriorityQueue<>(
    (a, b) -> a[1] != b[1] ? Integer.compare(b[1], a[1]) : Integer.compare(a[0], b[0]));
```

**Pitfalls**
- `(a, b) -> a - b` can overflow for large/negative values - prefer `Integer.compare`.
- Iterating a `PriorityQueue` does **not** give sorted order; only `poll()` does.
- `remove(Object)` is O(n); use lazy deletion if you need to remove arbitrary elements often.
- Mention **Quickselect** (average O(n)) as an alternative for a single k-th element.
'''

heap = [
P("kth-largest-element-in-a-stream", "Kth Largest Element in a Stream", "Easy", "Amazon, Facebook, Microsoft, Adobe",
"Design a class initialized with k and an array; each add(val) call inserts a number into the stream and returns the current k-th largest element. Example: k = 3, nums [4,5,8,2]; add(3) -> 4, add(5) -> 5.",
r'''
Keep a **min-heap of size k** holding the k largest values seen so far. Its root is the k-th largest. On `add`, offer the value and poll if the size exceeds k. Each add is O(log k), much better than re-sorting.
''',
r'''
class KthLargest {
    private final int k;
    private final PriorityQueue<Integer> pq = new PriorityQueue<>();

    public KthLargest(int k, int[] nums) {
        this.k = k;
        for (int x : nums) add(x);
    }

    public int add(int val) {
        pq.offer(val);
        if (pq.size() > k) pq.poll();
        return pq.peek();
    }
}
''', "O(log k) per add", "O(k)"),

P("last-stone-weight", "Last Stone Weight", "Easy", "Amazon, Google, Microsoft",
"Repeatedly smash the two heaviest stones: equal weights destroy both; otherwise the lighter is destroyed and the heavier loses that much weight. Return the last stone's weight or 0. Example: [2,7,4,1,8,1] -> 1.",
r'''
A direct simulation needs the two largest elements each round - exactly what a **max-heap** provides. Poll two, push the difference if non-zero, repeat while more than one stone remains. O(n log n).
''',
r'''
class Solution {
    public int lastStoneWeight(int[] stones) {
        PriorityQueue<Integer> pq = new PriorityQueue<>(Collections.reverseOrder());
        for (int s : stones) pq.offer(s);
        while (pq.size() > 1) {
            int y = pq.poll(), x = pq.poll();
            if (y != x) pq.offer(y - x);
        }
        return pq.isEmpty() ? 0 : pq.peek();
    }
}
''', "O(n log n)", "O(n)"),

P("k-closest-points-to-origin", "K Closest Points to Origin", "Medium", "Amazon, Facebook, Google, Uber, Swiggy, Zomato",
"Return any k points closest to the origin (0,0) by Euclidean distance. Example: points [[3,3],[5,-1],[-2,4]], k = 2 -> [[3,3],[-2,4]].",
r'''
Compare squared distances `x*x + y*y` (no `sqrt` needed). Keep a **max-heap of size k** ordered by distance: push each point and evict the farthest when size exceeds k. What's left are the k closest. O(n log k).

Alternatives: sort all points O(n log n), or Quickselect average O(n).
''',
r'''
class Solution {
    public int[][] kClosest(int[][] points, int k) {
        PriorityQueue<int[]> pq = new PriorityQueue<>(
            (a, b) -> Integer.compare(b[0] * b[0] + b[1] * b[1], a[0] * a[0] + a[1] * a[1]));
        for (int[] p : points) {
            pq.offer(p);
            if (pq.size() > k) pq.poll();
        }
        int[][] res = new int[k][];
        for (int i = 0; i < k; i++) res[i] = pq.poll();
        return res;
    }
}
''', "O(n log k)", "O(k)", True),

P("kth-largest-element-in-an-array", "Kth Largest Element in an Array", "Medium", "Facebook, Amazon, Microsoft, Google, Flipkart, Walmart, Goldman Sachs",
"Return the k-th largest element of an unsorted array (by sorted position, so duplicates count). Can you avoid fully sorting? Example: [3,2,1,5,6,4], k = 2 -> 5.",
r'''
**Sort:** O(n log n). **Min-heap of size k:** O(n log k) - the root ends as the answer. This is the expected baseline.

**Quickselect:** partition around a random pivot like quicksort, but recurse only into the side containing index `n - k`. Average O(n), worst O(n²). Mention it as the follow-up; the heap is safer to code under pressure.
''',
r'''
class Solution {
    public int findKthLargest(int[] nums, int k) {
        PriorityQueue<Integer> pq = new PriorityQueue<>();
        for (int x : nums) {
            pq.offer(x);
            if (pq.size() > k) pq.poll();
        }
        return pq.peek();
    }
}
''', "O(n log k)", "O(k)", True),

P("task-scheduler", "Task Scheduler", "Medium", "Facebook, Amazon, Microsoft, Uber, Atlassian",
"Tasks are letters; each takes one unit of time and the same task needs at least n units of gap between runs (CPU may idle). Return the minimum total time. Example: [A,A,A,B,B,B], n = 2 -> 8 (A B idle A B idle A B).",
r'''
**Heap simulation:** repeatedly run the most frequent available tasks in cycles of `n + 1` slots - works but verbose.

**Math (optimal):** let `maxFreq` be the highest count and `maxCount` the number of tasks with that count. The most frequent task forms `maxFreq - 1` full blocks of size `n + 1`, plus a final partial block of size `maxCount`. Answer = `max(tasks.length, (maxFreq - 1) * (n + 1) + maxCount)` - the `max` covers the case where there are enough tasks to fill all idle slots. O(n).
''',
r'''
class Solution {
    public int leastInterval(char[] tasks, int n) {
        int[] count = new int[26];
        for (char t : tasks) count[t - 'A']++;
        int maxFreq = 0, maxCount = 0;
        for (int c : count) {
            if (c > maxFreq) {
                maxFreq = c;
                maxCount = 1;
            } else if (c == maxFreq) {
                maxCount++;
            }
        }
        return Math.max(tasks.length, (maxFreq - 1) * (n + 1) + maxCount);
    }
}
''', "O(n)", "O(1)"),

P("find-median-from-data-stream", "Find Median from Data Stream", "Hard", "Amazon, Google, Microsoft, Facebook, Uber, Flipkart, Goldman Sachs",
"Design a MedianFinder with addNum(num) and findMedian() returning the median of all numbers added so far. Example: add 1, add 2 -> 1.5; add 3 -> 2.0.",
r'''
**Two heaps:** a **max-heap `low`** for the smaller half and a **min-heap `high`** for the larger half. Keep `low.size()` equal to `high.size()` or one larger.

`addNum`: push into `low`, then move `low`'s max into `high` (keeps ordering), then if `high` became bigger, move its min back to `low`. Median = `low.peek()` if sizes differ, else the average of both tops. O(log n) add, O(1) median.

Follow-up (values in 0..100): use a counting array.
''',
r'''
class MedianFinder {
    private final PriorityQueue<Integer> low = new PriorityQueue<>(Collections.reverseOrder());
    private final PriorityQueue<Integer> high = new PriorityQueue<>();

    public MedianFinder() { }

    public void addNum(int num) {
        low.offer(num);
        high.offer(low.poll());
        if (high.size() > low.size()) low.offer(high.poll());
    }

    public double findMedian() {
        if (low.size() > high.size()) return low.peek();
        return (low.peek() + (double) high.peek()) / 2.0;
    }
}
''', "O(log n) add, O(1) median", "O(n)", True),

P("top-k-frequent-words", "Top K Frequent Words", "Medium", "Amazon, Bloomberg, Uber, Yelp, Microsoft",
"Return the k most frequent words, sorted by frequency descending; ties are broken alphabetically. Example: [\"i\",\"love\",\"leetcode\",\"i\",\"love\",\"coding\"], k = 2 -> [\"i\",\"love\"].",
r'''
Count with a HashMap. Then keep a **min-heap of size k** whose comparator ranks the "worst" word at the top: lower frequency first, and for equal frequency the alphabetically **larger** word first (it's the one to evict). After processing, poll everything and reverse to get best-first order. O(n log k).

Simpler alternative: sort all unique words with the comparator - O(n log n).
''',
r'''
class Solution {
    public List<String> topKFrequent(String[] words, int k) {
        Map<String, Integer> freq = new HashMap<>();
        for (String w : words) freq.merge(w, 1, Integer::sum);

        PriorityQueue<String> pq = new PriorityQueue<>((a, b) -> {
            int fa = freq.get(a), fb = freq.get(b);
            if (fa != fb) return Integer.compare(fa, fb); // lower freq = worse
            return b.compareTo(a);                        // later alphabetically = worse
        });
        for (String w : freq.keySet()) {
            pq.offer(w);
            if (pq.size() > k) pq.poll();
        }
        LinkedList<String> res = new LinkedList<>();
        while (!pq.isEmpty()) res.addFirst(pq.poll());
        return res;
    }
}
''', "O(n log k)", "O(n)"),

P("reorganize-string", "Reorganize String", "Medium", "Amazon, Google, Facebook, Uber, Microsoft",
"Rearrange the characters of a string so that no two adjacent characters are equal; return any valid arrangement or \"\" if impossible. Example: \"aab\" -> \"aba\"; \"aaab\" -> \"\".",
r'''
If any character appears more than `(n + 1) / 2` times, it's impossible.

**Greedy with a max-heap by count:** repeatedly take the two most frequent characters, append both (they differ, so no conflict), decrement their counts, and push them back if still positive. If one character remains at the end, append it (its count must be 1). Always placing the most frequent remaining characters prevents getting stuck. O(n log 26) = O(n).
''',
r'''
class Solution {
    public String reorganizeString(String s) {
        int[] count = new int[26];
        for (char c : s.toCharArray()) count[c - 'a']++;
        PriorityQueue<int[]> pq = new PriorityQueue<>((a, b) -> Integer.compare(b[1], a[1]));
        for (int i = 0; i < 26; i++) {
            if (count[i] > (s.length() + 1) / 2) return "";
            if (count[i] > 0) pq.offer(new int[]{i, count[i]});
        }
        StringBuilder sb = new StringBuilder();
        while (pq.size() >= 2) {
            int[] a = pq.poll(), b = pq.poll();
            sb.append((char) ('a' + a[0])).append((char) ('a' + b[0]));
            if (--a[1] > 0) pq.offer(a);
            if (--b[1] > 0) pq.offer(b);
        }
        if (!pq.isEmpty()) sb.append((char) ('a' + pq.poll()[0]));
        return sb.toString();
    }
}
''', "O(n)", "O(1)"),
]

TR = PAT("trees", "Binary Trees & BST", 7, TR_INTRO, tr)
TRIE = PAT("tries", "Tries", 8, TRIE_INTRO, tries)
HEAP = PAT("heap", "Heap / Priority Queue", 9, HEAP_INTRO, heap)
