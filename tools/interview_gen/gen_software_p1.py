# tools/interview_gen/gen_software_p1.py
# Data Structures, Algorithms & OOP (iv-soft-101 to iv-soft-130)

from .common import make_tech_ans

def get_software_p1():
    qs = {}
    data = [
        ("iv-soft-101", "Data Structures & Algorithms", "Fresher", "Amazon",
         "Explain the internal working of a Hash Table, and compare Separate Chaining with Open Addressing for collision resolution.",
         "A Hash Table provides average O(1) time complexity for insert, search, and delete operations by mapping keys to array bucket indices using a hash function.",
         "1. Hash Function: Computes an integer hash code from the key, then applies modulo array length: index = hash(key) % capacity. A good hash function distributes keys uniformly.<br>2. Collisions occur when two distinct keys map to the same index.<br>- Separate Chaining: Each bucket holds a linked list (or balanced red-black tree, like Java 8+ HashMap when bucket size exceeds 8). Deletions are trivial, and table performance degrades gracefully even if load factor exceeds 1.0, but incurs pointer memory overhead and cache misses.<br>- Open Addressing (Linear/Quadratic Probing, Double Hashing): All entries live directly inside the array. When a collision occurs, the algorithm probes alternative slots until an empty slot is found. Better CPU cache locality and zero pointer overhead, but suffers from primary/secondary clustering and requires load factor strictly < 0.7.",
         "Always mention Load Factor (alpha = n / k). When alpha exceeds a threshold (typically 0.75), rehashing occurs: the array doubles in capacity and all keys are rehashed, an O(n) operation amortized over all insertions."),

        ("iv-soft-102", "Data Structures & Algorithms", "Intermediate", "Google",
         "How does QuickSort work, why is its worst-case O(n^2), and how does Randomized QuickSort or Dual-Pivot QuickSort mitigate this?",
         "QuickSort is a divide-and-conquer sorting algorithm with average-case time complexity of O(n log n) and excellent in-place cache performance.",
         "It chooses a 'pivot' element and partitions the array into two halves: elements less than the pivot on the left, and elements greater on the right, recursively sorting both partitions.<br>Worst-Case O(n^2): Occurs when the partition is maximally unbalanced (e.g., pivot is always the smallest or largest element). If a deterministic pivot (like the first or last element) is chosen on an already sorted or reverse-sorted array, recursion depth reaches n instead of log n.<br>Mitigation:<br>1. Randomized Pivot: Swapping the pivot with a randomly chosen index guarantees O(n log n) expected time on any input.<br>2. Median-of-Three: Choosing the median of {first, middle, last} elements avoids sorted array traps.<br>3. Dual-Pivot QuickSort (Yaroslavskiy, default in Java/V8): Uses two pivots to partition the array into three segments (< P1, P1..P2, > P2), reducing memory writes by ~20% and improving cache efficiency.",
         "QuickSort is NOT stable (relative order of equal keys is not preserved). For stability with O(n log n) worst-case guarantee, MergeSort is preferred."),

        ("iv-soft-103", "Data Structures & Algorithms", "Intermediate", "Microsoft",
         "What is an AVL Tree versus a Red-Black Tree, and why is Red-Black Tree preferred in standard libraries (C++ std::map, Java TreeMap)?",
         "Both are self-balancing binary search trees (BSTs) guaranteeing O(log n) worst-case search, insertion, and deletion.",
         "1. AVL Tree: Strictly balanced. For every node, the height difference between left and right subtrees (Balance Factor) can be at most +/- 1. Because it is strictly balanced, its maximum height is ~1.44 * log2(n). This makes AVL trees faster for lookups/search operations.<br>2. Red-Black Tree: Loosely balanced using color properties (root is black, no two adjacent red nodes, equal black-height from root to leaves). Maximum height can be up to 2 * log2(n). Lookups are slightly slower than AVL, but insertions require at most 2 tree rotations and deletions at most 3 rotations (constant rotational overhead).<br>Why Red-Black dominates standard libraries: Real-world workloads have mixed insertions and deletions; Red-Black trees require significantly fewer rebalancing rotations during mutations, making them faster in dynamic container implementations.",
         "Rule of thumb: AVL is better when the data structure is search-heavy; Red-Black is better when insertions and deletions are frequent."),

        ("iv-soft-104", "Data Structures & Algorithms", "Intermediate", "Meta",
         "How do you detect a cycle in a Linked List, and how do you find the exact node where the cycle begins (Floyd's Cycle Detection)?",
         "Floyd's Cycle-Finding Algorithm (Tortoise and Hare) uses two pointers moving at different speeds to detect cycles in O(n) time and O(1) space.",
         "1. Cycle Detection: Initialize `slow = head` and `fast = head`. Move `slow` by 1 step (`slow = slow->next`) and `fast` by 2 steps (`fast = fast->next->next`). If `fast` or `fast->next` hits NULL, the list has no cycle. If `slow == fast`, a cycle exists.<br>2. Finding Cycle Entry Point: Let distance from head to cycle start be L1, distance from cycle start to meeting point be L2, and cycle length be C. Fast has traveled 2 * (L1 + L2) = L1 + L2 + k*C, which simplifies to L1 = k*C - L2. This proves that the distance from the head to the cycle start is mathematically equal to the distance from the meeting point to the cycle start traveling around the loop!<br>Algorithm: Reset `slow = head` while keeping `fast` at the meeting point. Advance both pointers 1 step at a time: `slow = slow->next; fast = fast->next;`. The exact node where they collide is the cycle entry node!",
         "Be ready to write this clean O(1) space algorithm on a whiteboard; it is a top-10 most frequent FAANG coding question."),

        ("iv-soft-105", "Data Structures & Algorithms", "Fresher", "TCS",
         "What is the difference between Array and LinkedList in terms of memory layout, CPU cache locality, and algorithmic complexity?",
         "Arrays store elements in contiguous memory blocks; Linked Lists store elements in scattered heap nodes connected by pointers.",
         "1. Time Complexity:<br>- Random Access by Index: Array is O(1) because address = base + index * sizeof(type); LinkedList is O(n) because it must traverse pointers sequentially.<br>- Insertion/Deletion at beginning: Array is O(n) (requires shifting all elements); LinkedList is O(1) (updating head pointer).<br>- Insertion/Deletion in middle: Array is O(n) (element shifting); LinkedList is O(1) insertion once the node pointer is known, but O(n) to find the location.<br>2. Hardware Cache Locality: Modern CPUs fetch memory into L1/L2 caches in 64-byte cache lines. Arrays exhibit near-perfect spatial locality, enabling CPU hardware prefetchers to load sequential elements instantly with zero cache misses. LinkedList nodes are scattered randomly across the heap, triggering a CPU cache miss on almost every pointer dereference.",
         "In modern computer architectures, an Array search or traversal is often 5x to 50x faster than a LinkedList due to hardware cache line utilization."),

        ("iv-soft-106", "Data Structures & Algorithms", "Intermediate", "Uber",
         "Explain Dijkstra's Algorithm for Single-Source Shortest Path and why it fails with negative edge weights.",
         "Dijkstra's algorithm finds the shortest path from a source node to all other vertices in a weighted graph with non-negative edge weights.",
         "Implementation: Uses a Min-Heap (Priority Queue) to greedily select the unvisited vertex with the smallest tentative distance, then 'relaxes' its outgoing edges: if dist[u] + weight(u, v) < dist[v], then dist[v] = dist[u] + weight(u, v) and push v into the heap. Time complexity is O((V + E) log V).<br>Why it fails with negative weights: Dijkstra is a greedy algorithm that permanently marks a node as 'visited/finalized' once it is extracted from the priority queue, assuming no future path can ever reduce its cost. If an edge with a negative weight exists later down another path, it could decrease the total path cost to an already-visited vertex. Because Dijkstra never revisits finalized vertices, it produces incorrect results.<br>Solution: Bellman-Ford algorithm handles negative edge weights in O(V * E) time and detects negative-weight cycles.",
         "If the graph is unweighted, Dijkstra is overkill: simple Breadth-First Search (BFS) finds shortest paths in linear O(V + E) time."),

        ("iv-soft-107", "Data Structures & Algorithms", "Advanced", "Google",
         "What is a Trie (Prefix Tree), how is it implemented, and what are its performance advantages for autocomplete and IP routing?",
         "A Trie is a specialized k-ary tree data structure used for storing strings where keys are represented by paths rather than stored in nodes.",
         "Structure: Each node contains an array or hash map of child pointers (e.g., 26 pointers for lowercase English letters) and a boolean flag `isEndOfWord`. Words sharing common prefixes share the same ancestor nodes (e.g., 'car', 'cart', 'card' share nodes 'c' -> 'a' -> 'r').<br>Performance:<br>- Search, Insert, and Prefix Query time complexity is strictly O(L), where L is the length of the string, completely independent of the total number of words N stored in the dataset.<br>- In contrast, a Hash Table has average O(L) search but CANNOT perform prefix searches (like finding all words starting with 'electr-') without scanning all N keys (O(N * L)).<br>Applications: Autocomplete search suggestions, spell-checkers, Longest Prefix Matching in IP routing tables (using Radix/Patricia trie).",
         "Memory optimization: Standard Tries can consume significant memory due to sparse null pointers. Radix Trees (compact tries) compress single-child sequences into a single edge."),

        ("iv-soft-108", "Data Structures & Algorithms", "Intermediate", "Microsoft",
         "What is the difference between Breadth-First Search (BFS) and Depth-First Search (DFS) in graphs, and how are they implemented?",
         "BFS explores neighbor nodes layer-by-layer; DFS explores as deep as possible along each branch before backtracking.",
         "1. BFS: Implemented iteratively using a Queue (FIFO). Traverses nodes in order of their topological distance from the root. Memory complexity is O(Width), which can be O(V) in dense graphs. Standard application: Finding the shortest path on unweighted graphs, peer-to-peer network broadcasting, cycle detection.<br>2. DFS: Implemented using a Stack (LIFO) or recursively using the program call stack. Memory complexity is O(Depth) = O(H). Standard application: Topological Sorting in Directed Acyclic Graphs (DAG), finding strongly connected components (Kosaraju/Tarjan), maze pathfinding, cycle detection in directed graphs.",
         "Both algorithms run in O(V + E) time when using an adjacency list. In both algorithms, a `visited` set or boolean array is mandatory to prevent infinite loops in cyclic graphs."),

        ("iv-soft-109", "Data Structures & Algorithms", "Advanced", "Bloomberg",
         "Explain Dynamic Programming: What are Optimal Substructure and Overlapping Subproblems, and compare Memoization with Tabulation.",
         "Dynamic Programming (DP) is an algorithmic optimization technique that solves complex problems by breaking them down into simpler subproblems and storing subproblem results to avoid redundant calculations.",
         "Mandatory conditions:<br>1. Optimal Substructure: An optimal solution to the overall problem incorporates optimal solutions to its constituent subproblems (e.g., shortest path from A to C via B requires shortest path from A to B and B to C).<br>2. Overlapping Subproblems: The same subproblems are solved repeatedly during naive recursion (e.g., calculating naive Fibonacci f(5) computes f(3) two times, f(2) three times).<br>Approaches:<br>- Memoization (Top-Down): Maintains standard recursive call structure, but checks a cache (hash map or array) before computing. Solves only the subproblems strictly needed, but incurs recursion call-stack overhead.<br>- Tabulation (Bottom-Up): Iterative approach starting from base cases and building solutions iteratively in a table (array). Eliminates call-stack overhead and allows space optimization (e.g., keeping only the last 2 states).",
         "Famous DP problems to master: 0/1 Knapsack, Longest Common Subsequence (LCS), Longest Increasing Subsequence (LIS), Coin Change, Edit Distance."),

        ("iv-soft-110", "Data Structures & Algorithms", "Fresher", "Infosys",
         "What is Big-O, Big-Omega, and Big-Theta notation in asymptotic algorithm analysis?",
         "Asymptotic notations describe the limiting behavior of an algorithm's execution time or memory footprint as input size n approaches infinity.",
         "1. Big-O (O): Asymptotic UPPER bound. Represents the worst-case growth rate: f(n) <= c * g(n) for all n >= n0. It guarantees that the algorithm will NEVER take more time than this boundary.<br>2. Big-Omega (Omega): Asymptotic LOWER bound. Represents the best-case execution floor: f(n) >= c * g(n) for all n >= n0. It guarantees that the algorithm takes at least this much time.<br>3. Big-Theta (Theta): Asymptotic TIGHT bound. Bounds the function from both above and below: c1 * g(n) <= f(n) <= c2 * g(n). It represents the precise growth rate.<br>Common confusion: Colloquially in interviews, engineers say 'Big-O' when they technically mean 'Big-Theta'. For example, MergeSort is Theta(n log n) in all cases (best, average, worst).",
         "Always analyze both TIME complexity and auxiliary SPACE complexity when presenting algorithms in technical interviews."),

        ("iv-soft-111", "Object-Oriented Programming", "Fresher", "TCS",
         "Explain the 4 fundamental pillars of Object-Oriented Programming (OOP) with real-world software engineering examples.",
         "The 4 pillars are Abstraction, Encapsulation, Inheritance, and Polymorphism.",
         "1. Encapsulation: Bundling data (state) and methods (behavior) within a single class, restricting direct external access to internal state via access specifiers (`private`, `protected`). Prevents unauthorized modification and maintains class invariants (e.g., private `balance` modified only via `deposit()` and `withdraw()`).<br>2. Abstraction: Hiding internal implementation complexities and exposing only an intuitive, clean interface to the user (e.g., an `Engine` interface exposes `start()`, hiding spark plugs, fuel injection, and valve timing).<br>3. Inheritance: Mechanism where a child class inherits properties and behaviors from a parent class (`class ElectricCar extends Vehicle`), promoting code reuse and establishing an 'IS-A' relationship.<br>4. Polymorphism: Ability of an object or method to take on multiple forms: Compile-time (Method Overloading) and Runtime (Method Overriding via dynamic dispatch / virtual functions).",
         "A great answer connects these concepts to maintainability: Encapsulation reduces coupling; Abstraction manages complexity; Polymorphism enables extensible architectures."),

        ("iv-soft-112", "Object-Oriented Programming", "Intermediate", "Microsoft",
         "Explain the SOLID principles of Object-Oriented Design with practical code architecture violations and fixes.",
         "SOLID is an acronym for five foundational design principles formulated by Robert C. Martin (Uncle Bob) to create maintainable, flexible software architectures.",
         "1. S - Single Responsibility Principle (SRP): A class should have one, and only one, reason to change (e.g., a `User` class should not handle both business profile logic and database persistence; split persistence into `UserRepository`).<br>2. O - Open/Closed Principle (OCP): Software entities should be open for extension, but closed for modification. Implement new features by adding new classes implementing an interface, not by altering existing tested code.<br>3. L - Liskov Substitution Principle (LSP): Subtypes must be substitutable for their base types without altering program correctness (famous classic violation: `Square` extending `Rectangle`, where setting width changes height unexpectedly).<br>4. I - Interface Segregation Principle (ISP): Clients should not be forced to depend on interfaces they do not use; prefer many small, cohesive interfaces over one bloated 'fat' interface.<br>5. D - Dependency Inversion Principle (DIP): High-level modules should not depend on low-level modules; both should depend on abstractions (interfaces).",
         "Interviewers love asking how Dependency Inversion enables unit testing: by depending on interfaces, mock implementations can easily be injected during testing."),

        ("iv-soft-113", "Object-Oriented Programming", "Fresher", "Wipro",
         "What is the difference between Method Overloading and Method Overriding, and how does the compiler/runtime resolve them?",
         "Method Overloading is static (compile-time) polymorphism; Method Overriding is dynamic (runtime) polymorphism.",
         "1. Method Overloading: Multiple methods in the same class share the exact same name but have different parameter lists (different number, types, or order of arguments). The compiler resolves the target method at compile time based on the static argument types (Static Binding / Early Binding). Return type alone is insufficient to overload.<br>2. Method Overriding: A subclass provides a specific implementation of a method already declared in its superclass, with identical method signature and return type. The method to execute is resolved at RUNTIME based on the actual object instance type in heap memory, using a Virtual Method Table (vtable) and late dynamic dispatch.",
         "In C++, virtual functions (`virtual void draw()`) must be explicitly declared to enable overriding; in Java, all non-static, non-final methods are virtual by default."),

        ("iv-soft-114", "Object-Oriented Programming", "Intermediate", "Amazon",
         "Explain the Singleton Design Pattern: How do you implement a Thread-Safe Singleton with Double-Checked Locking in Java/C++?",
         "The Singleton pattern ensures that a class has only one instance and provides a global point of access to it (e.g., Database connection pool, Logger, Hardware configuration manager).",
         "Implementation details:<br>1. Private constructor to prevent external instantiation via `new`.<br>2. Private static instance variable.<br>3. Public static method `getInstance()` that returns the instance.<br>Thread-Safe Double-Checked Locking:<br>```java\npublic class Singleton {\n  private static volatile Singleton instance;\n  private Singleton() {}\n  public static Singleton getInstance() {\n    if (instance == null) { // 1st Check (no lock)\n      synchronized (Singleton.class) {\n        if (instance == null) { // 2nd Check (with lock)\n          instance = new Singleton();\n        }\n      }\n    }\n    return instance;\n  }\n}\n```<br>Why `volatile` is mandatory: Prevents instruction reordering by the compiler/CPU. Without volatile, the memory allocation and assignment (`instance = pointer`) could be reordered before the constructor runs, allowing a second thread to read a partially-initialized object!",
         "In modern Java, Bill Pugh's Initialization-on-demand holder idiom or `enum` Singleton is preferred because classloader guarantees thread safety without synchronization overhead."),

        ("iv-soft-115", "Object-Oriented Programming", "Intermediate", "Google",
         "Why is 'Composition over Inheritance' a fundamental object-oriented design maxim?",
         "Inheritance creates a tight, compile-time 'IS-A' coupling between base and child classes; Composition creates a flexible, runtime 'HAS-A' relationship by holding references to other objects.",
         "Problems with Inheritance:<br>1. Fragile Base Class Problem: Changes to parent class internal implementation can break child subclasses unexpectedly.<br>2. White-box reuse: Subclasses often have visibility into parent internals, violating encapsulation.<br>3. Static binding: Class relationships are fixed at compile-time and cannot be altered dynamically during runtime.<br>4. Single inheritance limitation: In languages like Java or C#, a class can inherit from only one parent.<br>Advantages of Composition:<br>1. Black-box reuse: Objects interact strictly through well-defined public interfaces; internal implementations remain encapsulated.<br>2. Dynamic runtime behavior: A class can swap its behavior on-the-fly simply by changing its composed strategy object (Strategy Pattern).",
         "Use inheritance only when true polymorphic substitutability (Liskov Substitution Principle) is required; use composition for code reuse."),

        ("iv-soft-116", "Object-Oriented Programming", "Intermediate", "Meta",
         "Explain the Observer Design Pattern and how it powers modern reactive architectures (Event Listeners, Pub/Sub).",
         "The Observer pattern defines a one-to-many dependency between objects so that when one object (Subject/Observable) changes state, all its dependents (Observers) are notified and updated automatically.",
         "Components:<br>1. Subject: Maintains a collection of observer interfaces, with methods `registerObserver()`, `removeObserver()`, and `notifyObservers()`.<br>2. Observer Interface: Declares the `update()` callback contract.<br>3. Concrete Observers: Implement the interface and react to state broadcasts.<br>Advantages: Loose coupling—the subject knows nothing about concrete observer implementations, only that they implement the update interface.<br>Observer vs Pub/Sub: In the classic Observer pattern, the Subject knows its registered observers directly. In modern distributed Publish/Subscribe (Kafka, RabbitMQ, Redis), an independent Event Broker decouples publishers and subscribers completely in time and space.",
         "Beware of memory leaks in garbage-collected languages (the 'Lapsed Listener' problem): Observers must be explicitly unregistered, or held using WeakReferences."),

        ("iv-soft-117", "Object-Oriented Programming", "Fresher", "Oracle",
         "What is an Abstract Class versus an Interface in modern Java/C++?",
         "Both provide abstraction by defining contracts that subclasses or implementing classes must fulfill.",
         "1. Abstract Class: An incomplete class that can have state (instance member variables with constructors) as well as concrete method implementations alongside abstract methods. A class can extend only ONE abstract class (single inheritance). Represents an 'IS-A' relationship (e.g., `Dog` is an `Animal`).<br>2. Interface: A pure contract defining behavior ('CAN-DO' capability, e.g., `Comparable`, `Serializable`). Historically contained only method signatures; modern Java 8+ allows default and static methods. A class can implement multiple interfaces (multiple inheritance of type). Does NOT have instance fields or constructors.",
         "Guideline: Use an abstract class when classes share common code and internal state; use an interface when defining a common behavioral capability across unrelated classes."),

        ("iv-soft-118", "Object-Oriented Programming", "Intermediate", "Adobe",
         "Explain the Factory Method and Abstract Factory design patterns and their architectural distinction.",
         "Both are creational design patterns that decouple object creation from client code.",
         "1. Factory Method: Defines an interface/method for creating a single object, but lets subclasses decide which concrete class to instantiate (`createButton()`). It uses inheritance and relies on a polymorphic method in a subclass.<br>2. Abstract Factory: Provides an interface for creating FAMILIES of related or dependent objects without specifying their concrete classes (`GUIFactory` creates `createButton()` AND `createCheckbox()`). It uses object composition: a client is given a concrete factory instance (e.g., `MacFactory` or `WindowsFactory`) that guarantees all created UI widgets match the same visual theme.",
         "Rule of thumb: Factory Method creates ONE product; Abstract Factory creates a FAMILY of related products."),

        ("iv-soft-119", "Object-Oriented Programming", "Intermediate", "Salesforce",
         "What is the Strategy Design Pattern and how does it eliminate complex nested if-else / switch-case statements?",
         "The Strategy pattern defines a family of algorithms, encapsulates each one inside a separate class, and makes them interchangeable at runtime.",
         "Structure:<br>1. Strategy Interface: Declares common algorithm execution method (e.g., `PaymentStrategy` with `pay(amount)`).<br>2. Concrete Strategies: `CreditCardPayment`, `PayPalPayment`, `UPIPayment`.<br>3. Context Class: `ShoppingCart` holds a reference to a `PaymentStrategy` object and delegates payment execution to it.<br>Benefit: Eliminates ugly, error-prone `switch(paymentType)` statements. Adding a new payment method (e.g., `CryptoPayment`) requires simply creating a new class implementing the interface without modifying a single line of existing code in `ShoppingCart` (fully adhering to the Open/Closed Principle).",
         "Strategy is one of the most practical and widely implemented patterns in enterprise production software."),

        ("iv-soft-120", "Object-Oriented Programming", "Intermediate", "Uber",
         "Explain the Decorator Design Pattern and how it achieves dynamic runtime extension over static subclassing.",
         "The Decorator pattern attaches additional responsibilities to an object dynamically at runtime without modifying the underlying class or using subclass explosion.",
         "Mechanism: A Decorator class implements the same interface as the target component and wraps a reference to a component instance. In its own methods, it calls the wrapped component's method and adds its own custom behavior before or after.<br>Example: In Java I/O: `new BufferedReader(new InputStreamReader(new FileInputStream(\"file.txt\")))`. Here, `BufferedReader` decorates `InputStreamReader`, which decorates `FileInputStream`.<br>Subclassing vs Decorator: If a Coffee shop has 4 coffee bases and 5 optional condiments (Milk, Sugar, Whip, Caramel, Soy), subclassing would require creating 4 * 2^5 = 128 distinct classes! Decorators allow wrapping any arbitrary combination of condiments at runtime with only 9 classes.",
         "Remember: Decorator maintains the exact same interface as the wrapped object, unlike Adapter which alters the interface."),

        ("iv-soft-121", "Data Structures & Algorithms", "Intermediate", "Goldman Sachs",
         "Explain the Heap data structure: How does a Binary Heap maintain the Heap Property, and what is the time complexity of Heapify?",
         "A Binary Heap is a complete binary tree that satisfies the Heap Property: in a Max-Heap, every parent node is >= its children; in a Min-Heap, every parent node is <= its children.",
         "Memory Layout: Stored compactly in an array with zero pointer overhead. For node at index `i`: Left child = `2*i + 1`, Right child = `2*i + 2`, Parent = `(i - 1) / 2`.<br>Operations:<br>- Insertion: Insert at end of array, then 'bubble up' (sift-up) in O(log n) time.<br>- Extract Min/Max: Replace root with last element, then 'sift-down' (heapify) in O(log n) time.<br>- Build Heap (Heapify): Building a heap from an arbitrary array of n elements takes O(n) linear time, NOT O(n log n).<br>Why Build Heap is O(n): Nodes near the leaves are numerous (n/2 nodes) but only sift down 0 or 1 levels. Higher nodes have greater sift-down height but are exponentially fewer. Summing (n / 2^(h+1)) * O(h) converges to a geometric series bounded by O(n).",
         "Priority Queues in all major languages (C++ `std::priority_queue`, Java `PriorityQueue`, Python `heapq`) are implemented using binary heaps."),

        ("iv-soft-122", "Data Structures & Algorithms", "Advanced", "Google",
         "What is an LRU (Least Recently Used) Cache and how is it implemented with O(1) get and O(1) put operations?",
         "An LRU cache evicts the least recently accessed item when it reaches its maximum capacity limit.",
         "To achieve O(1) time complexity for BOTH `get()` and `put()`: We combine a Hash Map with a Doubly Linked List.<br>1. Hash Map: Maps keys to Doubly Linked List node pointers, giving O(1) direct access to any node.<br>2. Doubly Linked List: Maintains item access recency ordering. The most recently used item is placed at the Head; the least recently used item sits at the Tail.<br>- `get(key)`: Lookup node in map (O(1)). If found, detach the node from its current position and move it to the Head (O(1)). Return value.<br>- `put(key, value)`: If key exists, update value and move node to Head. If key is new: if cache is full, remove the Tail node from both list and map (eviction, O(1)). Insert new node at Head and add to map (O(1)).",
         "Using dummy Head and dummy Tail sentinel nodes in the doubly linked list eliminates boundary edge cases when inserting/deleting at ends."),

        ("iv-soft-123", "Data Structures & Algorithms", "Fresher", "Cognizant",
         "Explain Binary Search: What are its preconditions, time complexity, and how do you avoid integer overflow when calculating midpoint?",
         "Binary Search searches for a target value within a sorted array by repeatedly halving the search interval in O(log n) time.",
         "Precondition: The data collection MUST be sorted in monotonic order with O(1) random index access.<br>Algorithm: Maintain pointers `low` and `high`. Compute midpoint `mid`. If `arr[mid] == target`, return `mid`. If `arr[mid] < target`, search right half (`low = mid + 1`). If `arr[mid] > target`, search left half (`high = mid - 1`).<br>Integer Overflow Bug: The traditional formula `mid = (low + high) / 2` contains a famous integer overflow bug! If `low + high` exceeds the maximum 32-bit signed integer value (2,147,483,647), the sum overflows into a negative number, causing array out-of-bounds crashes.<br>The safe formula: `mid = low + (high - low) / 2` or using bitwise right-shift `mid = (low + high) >>> 1`.",
         "This integer overflow bug existed undetected in Java's `Arrays.binarySearch()` standard library for over 9 years until identified by Joshua Bloch in 2006."),

        ("iv-soft-124", "Data Structures & Algorithms", "Intermediate", "Apple",
         "How do you implement a Stack using two Queues, and what are the time complexity trade-offs?",
         "A Stack is LIFO (Last In First Out); a Queue is FIFO (First In First Out). A stack can be simulated using two queues (Q1 and Q2).",
         "Two implementation approaches:<br>1. Costly Push, O(1) Pop:<br>- `push(x)`: Enqueue x into Q2. While Q1 is not empty, dequeue from Q1 and enqueue into Q2. Swap names of Q1 and Q2. Now the newest element is always at the front of Q1! Time: O(n).<br>- `pop()`: Dequeue from Q1. Time: O(1).<br>2. O(1) Push, Costly Pop:<br>- `push(x)`: Enqueue directly into Q1. Time: O(1).<br>- `pop()`: Dequeue (n - 1) elements from Q1 and enqueue into Q2. The remaining element in Q1 is the newest item; dequeue and return it. Swap Q1 and Q2. Time: O(n).",
         "A single queue can also implement a stack by enqueuing an item and rotating the previous n elements behind it: `for (int i=0; i<size; i++) q.push(q.pop());`."),

        ("iv-soft-125", "Data Structures & Algorithms", "Intermediate", "Amazon",
         "Explain Topological Sort in a Directed Acyclic Graph (DAG) using Kahn's Algorithm (BFS) and DFS.",
         "Topological Sort is a linear ordering of vertices in a directed graph such that for every directed edge u -> v, vertex u comes before vertex v.",
         "Crucial property: Topological sort is possible if and only if the graph has NO directed cycles (must be a DAG).<br>1. Kahn's Algorithm (BFS): Calculate in-degree (number of incoming edges) for all vertices. Enqueue all vertices with in-degree == 0. While queue is not empty: dequeue vertex u, append to topological order list, and for each outgoing edge u -> v, decrement in-degree of v. If in-degree of v becomes 0, enqueue v. If the resulting sorted list contains fewer than V vertices, a cycle exists!<br>2. DFS Approach: Run standard DFS traversal. When all descendants of vertex u have been fully explored (post-visit), push u onto a Stack. When DFS terminates, popping all elements from the stack yields the valid topological order.",
         "Applications: Build dependency resolution (e.g., Make, Maven, Gradle compiling files in dependency order), course prerequisite scheduling, task scheduling pipelines."),

        ("iv-soft-126", "Object-Oriented Programming", "Fresher", "Accenture",
         "What is the difference between Shallow Copy and Deep Copy of an object?",
         "Both create copies of an existing object, but differ in how referenced nested objects are handled.",
         "1. Shallow Copy: Copies all primitive field values, but for reference fields (pointers, nested objects, arrays), it copies only the memory address/pointer. Consequently, both the original and copied objects point to the EXACT same nested object in heap memory. Modifying a nested property on the copy inadvertently mutates the original object.<br>2. Deep Copy: Recursively clones the parent object AND allocates completely new memory allocations for all nested child objects and arrays. The copy is 100% independent; mutating the copy has zero effect on the original object.",
         "In Java, `Object.clone()` by default performs a shallow copy. Deep copying is achieved via custom copy constructors, clone methods, or serialization libraries."),

        ("iv-soft-127", "Object-Oriented Programming", "Intermediate", "Cisco",
         "Explain the Adapter Design Pattern and compare Object Adapter with Class Adapter.",
         "The Adapter pattern acts as a bridge between two incompatible interfaces, allowing classes to work together that otherwise could not.",
         "Real-world analogy: An electrical travel adapter plug allowing a European 2-pin round plug to connect to an American 3-pin flat wall socket.<br>Variants:<br>1. Object Adapter (preferred): Uses composition. The Adapter class implements the Target interface and holds an internal reference to the Adaptee instance. When target methods are called, the adapter translates arguments and invokes the corresponding method on the adaptee.<br>2. Class Adapter: Uses multiple inheritance. The Adapter inherits from BOTH the Target interface and the Adaptee implementation class. Only possible in languages supporting multiple inheritance like C++.",
         "Adapter is used extensively when integrating legacy third-party libraries into modern codebases without rewriting legacy code."),

        ("iv-soft-128", "Data Structures & Algorithms", "Advanced", "Netflix",
         "What is a Disjoint Set Union (DSU / Union-Find) data structure and how do Path Compression and Union by Rank achieve near O(1) operations?",
         "DSU maintains a collection of non-overlapping sets and supports two primary operations: `find(x)` (which set does x belong to?) and `union(x, y)` (merge two sets).",
         "Optimizations:<br>1. Union by Rank/Size: Always attach the smaller tree under the root of the taller tree. This prevents the tree from degenerating into a tall linked list, guaranteeing tree height remains O(log n).<br>2. Path Compression: During the `find(x)` operation, make every visited node point directly to the root: `parent[x] = find(parent[x])`. This flattens the tree structure permanently.<br>Combined Complexity: When using both Union by Rank and Path Compression, the amortized time per operation is O(alpha(n)), where alpha(n) is the Inverse Ackermann function. For any conceivable input in the universe (n <= 10^80 atoms), alpha(n) < 5, making operations effectively constant O(1) in practice.",
         "DSU is the cornerstone of Kruskal's Minimum Spanning Tree algorithm and dynamic graph connectivity queries."),

        ("iv-soft-129", "Data Structures & Algorithms", "Intermediate", "LinkedIn",
         "Explain the Sliding Window technique in array/string problems and distinguish Fixed-Size from Dynamic-Size windows.",
         "The Sliding Window technique avoids nested O(n^2) brute-force loops by maintaining a contiguous subsegment (window) that slides across the array in single-pass O(n) time.",
         "1. Fixed-Size Window (e.g., maximum sum subarray of size k): Compute sum of the first k elements. As the window shifts one position right, add the new incoming element `arr[i]` and subtract the outgoing element `arr[i - k]` in O(1) time. Time complexity: O(n).<br>2. Dynamic-Size Window (e.g., longest substring without repeating characters, minimum window substring): Maintain two pointers `left` and `right`. Expand `right` to include elements until a condition is violated; then advance `left` to shrink the window until the constraint is satisfied again.<br>Both pointers advance monotonically from 0 to n; each element is added and removed at most once, guaranteeing strictly O(n) linear time.",
         "Whenever an interview question asks for 'longest/shortest continuous subarray or substring satisfying condition X', immediately think Sliding Window."),

        ("iv-soft-130", "Object-Oriented Programming", "Fresher", "IBM",
         "Explain the role of Virtual Functions and the Virtual Table (vtable / vptr) in C++ dynamic polymorphism.",
         "In C++, declaring a member function `virtual` tells the compiler to defer method binding from compile-time to runtime (Late Dynamic Binding).",
         "Internal Mechanics:<br>1. vtable (Virtual Method Table): The compiler constructs a static lookup table of function pointers for each class containing virtual functions. Each entry points to the most-derived implementation of the virtual functions.<br>2. vptr (Virtual Pointer): The compiler silently injects a hidden pointer (`vptr`) into every object instance of that class, pointing to that class's vtable.<br>At runtime, when `base_ptr->draw()` is executed: The CPU dereferences `base_ptr->vptr` to locate the actual object's vtable, indexes the `draw()` entry, and jumps to the derived method's address. This introduces a slight overhead (one pointer indirection), but enables true runtime polymorphism.",
         "Rule of thumb: Always declare base class destructors as virtual (`virtual ~Base();`) to prevent memory leaks when deleting derived objects via base pointers."),
    ]
    
    for item in data:
        qid, sub, diff, comp, q, c, t, tip = item
        qs[qid] = {
            "cat": "Technical",
            "track": "software",
            "sub": sub,
            "diff": diff,
            "company": comp,
            "q": q,
            "a": make_tech_ans(c, t, tip)
        }
    return qs
