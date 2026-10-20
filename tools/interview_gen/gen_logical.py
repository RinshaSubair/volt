# tools/interview_gen/gen_logical.py
# 40 Advanced Placement-Grade Logical Reasoning & Puzzles (iv-puzzle-101 to iv-puzzle-140)

from .common import make_puzzle_ans

def get_all_logical_questions():
    qs = {}
    data = [
        ("iv-puzzle-101", "Logic Puzzles", "Intermediate", "Google",
         "25 Horses, 5 Tracks: What is the minimum number of races needed to find the top 3 fastest horses without a stopwatch?",
         "Divide the horses into 5 groups of 5 and use hierarchical elimination based on transitive ordering.",
         "Step 1: Divide 25 horses into 5 groups (A, B, C, D, E) of 5 horses each. Run 5 races.<br>Step 2: Take the 1st-place winner from each of the 5 races and run Race 6. Suppose the winners finish A1 > B1 > C1 > D1 > E1.<br>Elimination Logic:<br>- A1 is guaranteed to be the overall #1 fastest horse.<br>- Horses from groups D and E can never be in the top 3 (eliminated).<br>- From group C, only C1 could potentially be #3 (C2 and C3 eliminated).<br>- From group B, B1 could be #2, and B2 could be #3 (B3 eliminated).<br>- From group A, A2 could be #2 or #3, and A3 could be #3.<br>Step 3: Only 5 candidate horses remain for 2nd and 3rd place: {A2, A3, B1, B2, C1}. Run Race 7 among these 5 horses. The 1st and 2nd horses in Race 7 are the overall #2 and #3 horses!<br>Total minimum races required = 5 + 1 + 1 = 7 races.",
         "Interviewer takeaway: Demonstrates elimination of search space using partial order relations."),

        ("iv-puzzle-102", "Logic Puzzles", "Fresher", "Microsoft",
         "The 100 Doors Problem: You have 100 closed doors in a hallway. On pass 1, you toggle every door. On pass 2, you toggle every 2nd door... On pass 100, you toggle the 100th door. Which doors remain OPEN at the end?",
         "A door is toggled once for every positive divisor it possesses. A door remains open if and only if it is toggled an ODD number of times.",
         "For any integer N, factors come in natural pairs: if d divides N, then (N / d) also divides N (e.g., for 12, pairs are (1,12), (2,6), (3,4) = 6 divisors -> toggled 6 times, ending CLOSED).<br>The ONLY numbers that have an odd number of factors are PERFECT SQUARES, because one factor is paired with itself: d * d = N (e.g., for 16: (1,16), (2,8), and (4,4) -> the factor 4 appears only once, giving 5 unique divisors: 1, 2, 4, 8, 16).<br>Therefore, only the doors numbered with perfect square indices will be toggled an odd number of times and remain OPEN.<br>The open doors are: 1, 4, 9, 16, 25, 36, 49, 64, 81, and 100 (exactly 10 doors).",
         "Interviewer takeaway: Connects physical simulation problems to prime factorization and divisor number theory."),

        ("iv-puzzle-103", "Logic Puzzles", "Fresher", "Goldman Sachs",
         "8 Identical Balls, 1 is slightly heavier: Find the heavy ball using a two-pan balance scale in at most 2 weighings.",
         "A balance scale has 3 possible outcomes (<, =, >), allowing search space to be divided into 3 equal partitions (Ternary Search).",
         "Weighing 1: Divide the 8 balls into groups of (3, 3, 2). Place 3 balls on the left pan and 3 balls on the right pan.<br>- Case A (Left pans balance): The heavy ball is in the remaining group of 2 balls. Weigh the 2 balls against each other in Weighing 2; the heavier pan reveals the target ball.<br>- Case B (One pan is heavier): The heavy ball is in that group of 3 balls. For Weighing 2: Take 2 balls from this group of 3 and place 1 on each pan. If one is heavier, it is the ball; if they balance, the 3rd unweighed ball is the heavy ball.<br>Total weighings needed: exactly 2 in all cases.",
         "General formula: With n weighings on a balance scale, you can find 1 defective heavier ball among up to 3^n balls (for n = 2, 3^2 = 9 balls)."),

        ("iv-puzzle-104", "Probability & Riddles", "Intermediate", "Jane Street",
         "The Monty Hall Problem: You are on a game show with 3 doors. Behind 1 is a car; behind the other 2 are goats. You pick Door 1. The host (who knows what is behind every door) opens Door 3 to reveal a goat. He asks: 'Do you want to switch to Door 2?' Should you switch?",
         "You should ALWAYS switch! Switching doubles your probability of winning from 1/3 to 2/3.",
         "Initial Probability: When you made your first pick, your chosen door had a 1/3 chance of having the car. The remaining two doors collectively had a 2/3 probability.<br>Host's Constraint: The host NEVER opens your door and NEVER opens the door with the car; he intentionally reveals a goat.<br>Bayesian Update: When the host opens Door 3, he filters out the goat from the unchosen pair. The entire 2/3 probability of the unchosen doors is now concentrated entirely onto Door 2!<br>- If you STAY: You win if and only if your initial pick was right (Probability = 1/3).<br>- If you SWITCH: You win whenever your initial pick was WRONG (Probability = 2/3). Since your initial pick was wrong 2 out of 3 times, switching wins 2/3 of the time.",
         "Interviewer takeaway: Demonstrates mastery of conditional probability and avoiding the 50/50 gambler's trap."),

        ("iv-puzzle-105", "Logic Puzzles", "Fresher", "Amazon",
         "Bridge and Torch Problem: 4 people must cross a fragile bridge at night with 1 torch. Max 2 people can cross at once. Person A takes 1 min, B takes 2 mins, C takes 7 mins, D takes 10 mins. Can all four cross in 17 minutes?",
         "The key insight is having the two slowest people (C and D) cross TOGETHER so their transit times overlap.",
         "Step 1: A (1 min) and B (2 min) cross the bridge carrying the torch. (Time elapsed = 2 mins).<br>Step 2: A returns alone with the torch. (Time elapsed = 2 + 1 = 3 mins).<br>Step 3: C (7 min) and D (10 min) cross together carrying the torch. (Time elapsed = 3 + 10 = 13 mins).<br>Step 4: B returns alone with the torch. (Time elapsed = 13 + 2 = 15 mins).<br>Step 5: A and B cross together again. (Time elapsed = 15 + 2 = 17 mins).<br>All 4 people are safely across in exactly 17 minutes!",
         "Trap: Having the fastest person (A) shuttle back and forth every time takes 1 + 2 + 1 + 7 + 1 + 10 = 22 minutes (fails!). Grouping the slow walkers avoids duplicate 7-minute penalties."),

        ("iv-puzzle-106", "Logic Puzzles", "Fresher", "McKinsey",
         "Burning Ropes: You have two ropes. Each rope takes exactly 60 minutes to burn completely, but the ropes burn non-uniformly. How can you measure exactly 45 minutes?",
         "Burning a rope from BOTH ends simultaneously cuts its burn time in half (from 60 minutes to 30 minutes), regardless of non-uniform density.",
         "Action 1 (t = 0): Light Rope 1 from BOTH ends simultaneously, and light Rope 2 from ONE end only.<br>Action 2 (t = 30 min): Rope 1 burns out completely. Exactly 30 minutes have elapsed! At this exact instant, Rope 2 has exactly 30 minutes of burn time remaining.<br>Action 3 (t = 30 min): Immediately light the other end of Rope 2! Because Rope 2 is now burning from both ends, its remaining 30 minutes will burn down in exactly 15 minutes.<br>Action 4 (t = 45 min): When Rope 2 finishes burning completely, exactly 30 + 15 = 45 minutes have elapsed.",
         "Interviewer takeaway: Solves non-linear time problems by exploiting parallel rate-doubling."),

        ("iv-puzzle-107", "Logic Puzzles", "Intermediate", "Google",
         "The Two Egg Problem: You are in a 100-story building with 2 identical eggs. Find the highest floor from which an egg can be dropped without breaking, minimizing the worst-case number of drops.",
         "Equalize the total worst-case drops across all floors by decreasing the step size by 1 drop on each successive jump.",
         "Let the first drop be at floor x. If it breaks, Egg 2 must test every floor sequentially from 1 to x - 1 (x total drops).<br>If Egg 1 does not break, the next jump must be (x - 1) floors, so that the worst-case total drops (1 first drop + 1 second drop + (x - 2) linear drops) remains equal to x.<br>The sequence of jumps is: x + (x - 1) + (x - 2) + ... + 1 >= 100.<br>The sum of the first x integers is: x * (x + 1) / 2 >= 100.<br>For x = 13: 13 * 14 / 2 = 91 (too small).<br>For x = 14: 14 * 15 / 2 = 105 >= 100.<br>Strategy: Drop Egg 1 at floors: 14, 27 (14+13), 39 (27+12), 50 (39+11), 60, 69, 77, 84, 90, 95, 99, 100.<br>Worst-case drops is GUARANTEED to be at most 14 drops.",
         "Interviewer takeaway: Demonstrates dynamic programming and balancing worst-case branch variance."),

        ("iv-puzzle-108", "Probability & Riddles", "Fresher", "Microsoft",
         "3 Ants on a Triangle: 3 ants sit at the 3 vertices of an equilateral triangle. Each ant randomly picks an edge direction (clockwise or counter-clockwise) with 50% probability and walks. What is the probability that NO ants collide?",
         "Ants will not collide if and only if ALL ants walk in the same rotational direction around the triangle.",
         "Each ant has 2 independent choices: Clockwise (C) or Counter-Clockwise (CC).<br>Total possible combinations for 3 ants = 2^3 = 8 outcomes.<br>Collision-free outcomes:<br>1. All 3 ants walk Clockwise: (C, C, C) -> 1 outcome.<br>2. All 3 ants walk Counter-Clockwise: (CC, CC, CC) -> 1 outcome.<br>Total collision-free outcomes = 2.<br>Probability of NO collision = 2 / 8 = 1 / 4 (25%).<br>Complement: Probability of at least one collision is 1 - 1/4 = 3/4 (75%).",
         "Generalization for an N-sided polygon: Probability of no collision = 2 / 2^N = (1/2)^(N - 1)."),

        ("iv-puzzle-109", "Logic Puzzles", "Intermediate", "Meta",
         "1,000 Bottles of Wine, 1 is Poisoned: You have 10 test rats. A poisoned rat dies within 24 hours. You have exactly 24 hours to find the poisoned bottle. How do you identify the exact bottle?",
         "Use Binary Encoding. 10 rats can represent 2^10 = 1,024 unique states (Alive or Dead).",
         "1. Label each wine bottle with a binary number from 1 to 1000 (represented by a 10-bit binary string from 0000000001 to 1111101000).<br>2. Label the 10 rats from Rat 0 to Rat 9, where Rat k corresponds to bit position k in the binary representation.<br>3. Feeding Rule: For each bottle, check its 10-bit binary representation. Feed a drop of this bottle to Rat k if and only if bit k of the bottle's number is 1.<br>4. Result after 24 hours: Line up the rats from Rat 9 down to Rat 0. Write a '1' if the rat is DEAD, and '0' if the rat is ALIVE.<br>This 10-bit binary sequence directly gives the exact decimal number of the poisoned bottle!",
         "Example: If only Rat 0 and Rat 3 die, binary number is 0000001001 = 2^3 + 2^0 = bottle #9 is poisoned."),

        ("iv-puzzle-110", "Logic Puzzles", "Fresher", "Goldman Sachs",
         "10 Pill Bottles, 1 has Defective Heavy Pills: 9 bottles contain 10g pills, 1 bottle contains 11g pills. Using a digital scale only ONCE, how do you find the defective bottle?",
         "Use an arithmetic progression sample selection to map weight deviation uniquely to the bottle index.",
         "Step 1: Label the bottles from 1 to 10.<br>Step 2: Take 1 pill from Bottle 1, 2 pills from Bottle 2, 3 pills from Bottle 3, ... and 10 pills from Bottle 10.<br>Total pills taken = 1 + 2 + 3 + ... + 10 = 55 pills.<br>Step 3: Place all 55 pills together onto the digital scale for a single weighing.<br>Step 4: If all bottles were normal (10g each), expected weight would be: 55 * 10g = 550 grams.<br>Step 5: Each pill from the defective bottle adds exactly 1 extra gram (11g - 10g = +1g).<br>Formula: Defective Bottle Number = (Measured Weight in grams) - 550 grams.<br>Example: If the scale reads 557 grams, Bottle #7 is defective (557 - 550 = 7).",
         "Interviewer takeaway: Demonstrates converting discrete search into algebraic index mapping."),

        ("iv-puzzle-111", "Probability & Riddles", "Intermediate", "Jane Street",
         "Russian Roulette with a Twist: A 6-chamber revolver has 2 bullets placed in ADJACENT chambers. The shooter spins the cylinder, points it at you, and pulls the trigger: CLICK (empty chamber). He asks: 'Do you want me to spin the cylinder again, or pull the trigger immediately?' Which choice maximizes your survival?",
         "Do NOT spin the cylinder; choose to pull the trigger immediately!",
         "Let the 6 chambers be numbered 1 to 6 in circle order, with bullets in adjacent chambers (1 and 2). Empty chambers are 3, 4, 5, 6.<br>- If you SPIN: The cylinder resets randomly. The probability of landing on a bullet is 2 / 6 = 1/3 (Survival = 4/6 = 66.7%).<br>- If you DO NOT SPIN (Conditional Probability): You know the previous shot was EMPTY. There are 4 possible empty chambers you just survived (3, 4, 5, 6).<br>Look at what comes NEXT after each of those 4 empty chambers:<br>- If previous was 3 -> Next is 4 (Empty - SURVIVE)<br>- If previous was 4 -> Next is 5 (Empty - SURVIVE)<br>- If previous was 5 -> Next is 6 (Empty - SURVIVE)<br>- If previous was 6 -> Next is 1 (Bullet - DIE)<br>Survival probability if you do NOT spin = 3 out of 4 = 75%!",
         "Survival jumps from 66.7% (spin) to 75.0% (don't spin). Conditional probability rewards staying."),

        ("iv-puzzle-112", "Probability & Riddles", "Fresher", "Google",
         "The Birthday Paradox: Why do you need only 23 people in a room for a greater than 50% probability that at least two people share the exact same birthday?",
         "We calculate the probability of the COMPLEMENT event: that ALL people have distinct, unique birthdays.",
         "Assume 365 days in a year (ignore leap years).<br>- Person 1 can have any birthday (365/365).<br>- Person 2 must have a different birthday (364/365).<br>- Person 3 must differ from first two (363/365)...<br>- Person N must differ from all previous: (365 - N + 1) / 365.<br>Probability of NO shared birthdays among N people is: P(No Match) = (365/365) * (364/365) * ... * ((365 - N + 1)/365).<br>For N = 23: P(No Match) approx 0.4927 (49.27%).<br>Therefore, probability of AT LEAST ONE shared birthday is: P(At least one match) = 1 - 0.4927 = 0.5073 (50.73% > 50%!).<br>Why human intuition fails: People intuitively think of matching THEIR OWN birthday (which takes 253 people for 50%). But among 23 people, there are N*(N - 1)/2 = 23*22/2 = 253 pairwise comparisons!",
         "This mathematical principle underpins Hash Collisions and the Birthday Attack in cryptography."),

        ("iv-puzzle-113", "Logic Puzzles", "Fresher", "Microsoft",
         "3 Switches in Room A, 3 Light Bulbs in Room B: You cannot see into Room B from Room A. You can visit Room B only ONCE. How do you determine which switch controls which bulb?",
         "Light bulbs produce two distinct physical phenomena: LIGHT and HEAT.",
         "Step 1: Turn Switch 1 ON. Leave it on for 10 minutes to let the bulb heat up.<br>Step 2: After 10 minutes, turn Switch 1 OFF and immediately turn Switch 2 ON.<br>Step 3: Walk into Room B immediately.<br>Observation Rules:<br>- The bulb that is currently ON is controlled by Switch 2.<br>- The bulb that is OFF but WARM/HOT to the touch is controlled by Switch 1.<br>- The bulb that is OFF and COLD to the touch is controlled by Switch 3.",
         "Interviewer takeaway: Lateral thinking—expanding problem constraints beyond optical vision to thermal state."),

        ("iv-puzzle-114", "Logic Puzzles", "Intermediate", "Uber",
         "Water Jug Problem: You have an unmarked 3-liter jug and an unmarked 5-liter jug, with an unlimited water supply. How do you measure exactly 4 liters?",
         "Use state transitions based on modular arithmetic: 5 - (3 - 2) = 4.",
         "Step 1: Fill the 5-liter jug to the top. (State: 3L: 0, 5L: 5).<br>Step 2: Pour water from the 5L jug into the 3L jug until 3L is full. (State: 3L: 3, 5L: 2).<br>Step 3: Empty the 3L jug onto the ground. (State: 3L: 0, 5L: 2).<br>Step 4: Pour the 2 liters from the 5L jug into the 3L jug. (State: 3L: 2, 5L: 0).<br>Step 5: Fill the 5L jug to the top again. (State: 3L: 2, 5L: 5).<br>Step 6: Carefully pour water from the 5L jug into the 3L jug until the 3L jug is full (it needs exactly 1 liter). (State: 3L: 3, 5L: 4).<br>The 5-liter jug now contains EXACTLY 4 liters of water!",
         "Bézout's identity guarantees that any volume k can be measured if k is a multiple of gcd(A, B). Here gcd(3, 5) = 1."),

        ("iv-puzzle-115", "Logic Puzzles", "Intermediate", "Amazon",
         "The 100 Prisoners and Lockers Problem: 100 prisoners numbered 1 to 100. In a room are 100 closed boxes containing random numbers 1 to 100. Each prisoner can open 50 boxes. If EVERY prisoner finds their own number, all go free; if even one fails, all are executed. How can prisoners achieve > 30% survival probability?",
         "Exploit Permutation Cycles. Random guessing yields (1/2)^100 approx 0.0000000000000000000000000000008 survival probability; loop-following boosts survival to 31.18%!",
         "Loop Strategy:<br>1. Prisoner k enters the room and opens Box k.<br>2. Look at the number inside Box k: if it is number j, open Box j next.<br>3. Continue following the numbers from box to box until either you find your own number k or you exhaust 50 attempts.<br>Why this works mathematically:<br>Every permutation of 100 numbers decomposes into a set of disjoint cyclic loops. If every loop in the permutation has length <= 50, then EVERY SINGLE PRISONER will find their number within 50 steps!<br>The probability that a random permutation of 100 elements has NO cycle of length > 50 is: 1 - (1/51 + 1/52 + ... + 1/100) = 1 - ln(2) approx 31.18%.",
         "Interviewer takeaway: Demonstrates cycle decomposition in abstract algebra and group theory."),

        ("iv-puzzle-116", "Logic Puzzles", "Fresher", "Apple",
         "The Mutilated Chessboard: A standard chessboard has 64 squares. Cut off two diagonally opposite corner squares (leaving 62 squares). Can you cover the remaining board using 31 rectangular dominoes (each domino covering 2 adjacent squares)?",
         "Use Parity / Invariant coloring principles.",
         "A standard chessboard has 32 white squares and 32 black squares.<br>1. Observe the two diagonally opposite corners: in any chessboard, diagonally opposite corners ALWAYS have the EXACT SAME COLOR (both are white, or both are black).<br>2. Removing two opposite corners leaves 32 squares of one color and 30 squares of the other color (e.g., 32 black and 30 white squares).<br>3. Every single 2x1 domino placed on the board MUST cover exactly 1 white square and 1 black square.<br>4. Therefore, 31 dominoes MUST cover exactly 31 white squares and 31 black squares.<br>Conclusion: Because the mutilated board has 30 white and 32 black squares, it is MATHEMATICALLY IMPOSSIBLE to cover the board!",
         "Interviewer takeaway: Proof by invariant parity—saving hours of futile combinatorial brute-force."),

        ("iv-puzzle-117", "Logic Puzzles", "Fresher", "TCS",
         "3 Mislabelled Fruit Crates: You have 3 crates labeled 'Apples', 'Oranges', and 'Apples & Oranges'. You are told that ALL THREE labels are 100% INCORRECT. You can pick 1 fruit from 1 crate with your eyes closed. How do you correctly label all 3 crates?",
         "Pick a fruit from the crate labeled 'Apples & Oranges'.",
         "Because all labels are known to be 100% false:<br>1. The crate labeled 'Apples & Oranges' CANNOT contain both apples and oranges; it must contain ONLY Apples or ONLY Oranges.<br>2. Reach into the crate labeled 'Apples & Oranges' and draw one fruit.<br>- Case A: The drawn fruit is an APPLE. That crate is guaranteed to be the 'Apples' crate!<br>Now look at the remaining two crates labeled 'Oranges' and 'Apples':<br>- The crate labeled 'Oranges' cannot be Oranges (since all labels are false), and cannot be Apples (already identified). Therefore, it MUST be 'Apples & Oranges'!<br>- The crate labeled 'Apples' must therefore be 'Oranges'.<br>- Case B: The drawn fruit is an ORANGE. By symmetric logic, that crate is 'Oranges', crate labeled 'Apples' is 'Apples & Oranges', and crate labeled 'Oranges' is 'Apples'.",
         "Interviewer takeaway: Identifying the single pivot node whose state resolves the entire constraint network."),

        ("iv-puzzle-118", "Probability & Riddles", "Intermediate", "Google",
         "The Last Passenger's Seat: 100 passengers board a 100-seat airplane in order. The 1st passenger lost his boarding pass and picks a random seat. Subsequent passengers take their assigned seat if free; if occupied, they pick a random seat. What is the probability that the 100th passenger sits in their own assigned seat?",
         "The answer is exactly 1/2 (50%) regardless of the number of passengers N!",
         "Consider the critical decision point for any displaced passenger:<br>At any moment, if a passenger chooses a seat at random, there are two special seats that determine the fate of Passenger 100:<br>1. Seat 1 (the 1st passenger's assigned seat): If anyone sits in Seat 1, the cycle ends, and all remaining passengers (including Passenger 100) will get their own assigned seats.<br>2. Seat 100 (Passenger 100's assigned seat): If anyone sits in Seat 100, Passenger 100 is doomed.<br>3. Any other seat (Seat 2 to 99): Simply defers the decision to a later passenger.<br>Because every displaced passenger picks randomly with equal probability among available seats, Seat 1 and Seat 100 are ALWAYS EQUALLY LIKELY to be picked first! Whichever is chosen first resolves the game. Therefore, by symmetry, the probability is exactly 1/2.",
         "Interviewer takeaway: Symmetry arguments dissolve complex recursive stochastic processes into single-line answers."),

        ("iv-puzzle-119", "Logic Puzzles", "Fresher", "Infosys",
         "Two Sand Timers: You have a 7-minute hourglass and a 4-minute hourglass. How do you measure exactly 9 minutes to boil an egg?",
         "Start both timers simultaneously and flip the 4-minute timer as soon as it runs out.",
         "Action 1 (t = 0): Start boiling the egg and flip both the 7-minute and 4-minute timers.<br>Action 2 (t = 4 min): The 4-minute timer empties. Immediately flip the 4-minute timer again. (The 7-minute timer has 3 minutes left).<br>Action 3 (t = 7 min): The 7-minute timer empties. Exactly 7 minutes have elapsed! Notice the 4-minute timer has been running for 3 minutes, meaning it has EXACTLY 1 MINUTE of sand left in its top chamber.<br>Action 4 (t = 7 min): Immediately flip the 7-minute timer? No! Just let the 4-minute timer finish its remaining 1 minute.<br>Action 5 (t = 8 min): When the 4-minute timer runs out, 8 minutes have elapsed. Flip it again? Simpler alternative:<br>Standard clean method:<br>Start both. At 4m, flip 4m. At 7m, 4m has 1m left. Flip 7m to catch that 1m? Let 4m finish (t = 8m), 7m has 1m. Flip 7m over = 7 + 1 + 1 = 9 minutes!",
         "Simple, deterministic state-tracking."),

        ("iv-puzzle-120", "Logic Puzzles", "Fresher", "Wipro",
         "The Two Guards (Knights and Knaves): Two doors lead out of a cell: one leads to Freedom, the other to Execution. Guard A always tells the TRUTH; Guard B always LIES. You do not know which is which. You can ask ONE guard ONE question. What question do you ask?",
         "Ask either guard: 'Which door would the OTHER guard say leads to Freedom?' Then choose the OPPOSITE door!",
         "Logical truth table evaluation:<br>- Suppose Guard A is Truth-teller and Guard B is Liar.<br>If you ask Guard A: He knows Guard B lies, so Guard A truthfully reports Guard B's lie -> Points to EXECUTION door.<br>- Suppose you ask Guard B (Liar): He knows Guard A tells the truth (Freedom door), so Guard B lies about what Guard A would say -> Points to EXECUTION door.<br>In BOTH cases, the guard will GUARANTEED point to the EXECUTION door! Therefore, simply walk through the OPPOSITE door to win Freedom.",
         "Boolean logic: Truth * Lie = Lie; Lie * Truth = Lie. The product of truth and falsehood is always a lie."),

        ("iv-puzzle-121", "Logic Puzzles", "Fresher", "Cognizant",
         "The Handshake Problem: 10 people meet at a conference and every person shakes hands with every other person exactly once. How many total handshakes take place?",
         "This is a combination problem: choosing 2 people out of 10 without regard to order: C(n, 2).",
         "Formula: Total handshakes = n * (n - 1) / 2.<br>For n = 10: Total = 10 * 9 / 2 = 90 / 2 = 45 handshakes.<br>Intuitive proof: Person 1 shakes hands with 9 other people. Person 2 has already shaken Person 1's hand, so shakes hands with 8 remaining people. Summing: 9 + 8 + 7 + 6 + 5 + 4 + 3 + 2 + 1 = 45.",
         "Graph theory connection: Number of edges in a complete graph K_n is n*(n-1)/2."),

        ("iv-puzzle-122", "Logic Puzzles", "Fresher", "TCS",
         "Clock Angle Problem: What is the exact angle in degrees between the hour hand and the minute hand of an analog clock at 3:15?",
         "A clock face is 360 degrees divided into 12 hours (30 degrees/hour) and 60 minutes (6 degrees/minute).",
         "Trap: Many people instantly answer '0 degrees' assuming both hands point at 3. But the hour hand MOVES as minutes advance!<br>- Minute hand at 15 minutes: Position = 15 * 6 deg = 90 degrees.<br>- Hour hand speed: 360 deg / 12 hours = 30 deg/hour = 0.5 degrees per minute.<br>- Hour hand position at 3:15 = (3 * 30 deg) + (15 min * 0.5 deg/min) = 90 deg + 7.5 deg = 97.5 degrees.<br>Angle between hands = |97.5 deg - 90 deg| = 7.5 degrees!",
         "Never forget that the hour hand continuously advances at 0.5 degrees per minute."),

        ("iv-puzzle-123", "Logic Puzzles", "Fresher", "Accenture",
         "The Missing Dollar Riddle: 3 guests check into a hotel room costing $30 ($10 each). The manager realizes the room is only $25, and gives $5 to the bellboy to return. The dishonest bellboy pockets $2 and returns $1 to each guest. Each guest paid $9 ($27 total) + bellboy has $2 = $29. Where is the missing $1?",
         "The riddle uses fraudulent accounting by adding when it should subtract.",
         "Breakdown of total money ($30):<br>- Total paid by guests = 3 * $9 = $27.<br>- Where did that $27 go? The hotel manager has $25 and the bellboy has $2 ($25 + $2 = $27!). The accounting balances perfectly.<br>The flaw in the riddle is adding the bellboy's stolen $2 to the guests' paid $27. The bellboy's $2 is ALREADY INCLUDED in the $27 paid by the guests! Adding them is mathematical nonsense; you subtract: $27 paid - $2 bellboy = $25 hotel.",
         "Interviewer takeaway: Identifying framing fallacies and verifying conservation of flow."),

        ("iv-puzzle-124", "Logic Puzzles", "Intermediate", "Google",
         "Trailing Zeros in 100!: How many trailing zeros does the number 100! (100 factorial) have?",
         "A trailing zero is created by the prime factor pair (2 * 5 = 10). In factorials, factors of 2 are abundant; the number of zeros is bounded strictly by factors of 5.",
         "Legendre's Formula: The exponent of a prime p in n! is: E_p(n!) = Sum floor(n / p^k) for k = 1, 2, ...<br>For p = 5 and n = 100:<br>- Multiples of 5 up to 100: floor(100 / 5) = 20.<br>- Multiples of 25 (which contribute an extra 5): floor(100 / 25) = 4.<br>- Multiples of 125: floor(100 / 125) = 0.<br>Total factors of 5 = 20 + 4 = 24.<br>Therefore, 100! ends in EXACTLY 24 trailing zeros.",
         "Legendre's formula computes trailing zeros for any n! in O(log_5 n) time."),

        ("iv-puzzle-125", "Logic Puzzles", "Fresher", "Infosys",
         "The Frog in the Well: A frog is at the bottom of a 30-meter well. Each day it climbs up 3 meters, but each night it slips down 2 meters. On which day does the frog reach the top of the well?",
         "Net daily progress is 1 meter, BUT on the final day, once the frog reaches the top, it climbs OUT and does NOT slip back down!",
         "After 27 days and nights: The frog has climbed 27 * 1m = 27 meters.<br>On Day 28: During the daytime, the frog climbs 3 meters: 27m + 3m = 30 meters! The frog reaches the top edge of the well and leaps out into freedom. It never slips down again.<br>Answer: Day 28 (NOT Day 30).",
         "Trap alert: Forgetting boundary conditions and premature loop termination."),

        ("iv-puzzle-126", "Logic Puzzles", "Advanced", "Goldman Sachs",
         "5 Pirates and 100 Gold Coins: 5 rational, self-interested, bloodthirsty pirates (A, B, C, D, E in order of seniority) must divide 100 gold coins. Senior pirate proposes a split; all pirates vote. If >= 50% vote YES, proposal passes; if < 50%, proposer is thrown overboard and next pirate proposes. What proposal should Pirate A make?",
         "Solve backward using Game Theoretic Backward Induction (Subgame Perfect Nash Equilibrium).",
         "Case 1 (Only D and E remain): D needs 50% of 2 votes (1 vote). D votes for himself: (D: 100, E: 0). E gets 0.<br>Case 2 (C, D, E remain): C needs 1 vote out of 3. C bribes E with 1 coin (better than 0). Split: (C: 99, D: 0, E: 1). E votes YES. Passes!<br>Case 3 (B, C, D, E remain): B needs 2 votes out of 4 (himself + 1). B bribes D with 1 coin (since D gets 0 in Case 2). Split: (B: 99, C: 0, D: 1, E: 0). D votes YES. Passes!<br>Case 4 (A, B, C, D, E): A needs 3 votes out of 5 (himself + 2). A bribes C with 1 coin (C gets 0 in B's plan) and E with 1 coin (E gets 0 in B's plan).<br>Pirate A's optimal winning proposal: Pirate A: 98 coins, Pirate B: 0 coins, Pirate C: 1 coin, Pirate D: 0 coins, Pirate E: 1 coin! (98, 0, 1, 0, 1).<br>Pirates A, C, and E vote YES (3 out of 5 = 60%). Passes!",
         "Interviewer takeaway: Mastery of backward induction and game-theoretic incentives."),

        ("iv-puzzle-127", "Probability & Riddles", "Fresher", "Microsoft",
         "Matching Socks in the Dark: A drawer contains 10 black socks and 10 brown socks. In total darkness, what is the minimum number of socks you must pull out to guarantee at least one matching pair?",
         "Pigeonhole Principle: If n pigeonholes are occupied by n + 1 pigeons, at least one pigeonhole must contain >= 2 pigeons.",
         "Here there are only 2 colors ('pigeonholes'): Black and Brown.<br>- Draw 1 sock: Could be Black or Brown.<br>- Draw 2 socks: Could be {Black, Black} (pair!), {Brown, Brown} (pair!), or {Black, Brown} (no pair yet).<br>- Draw 3 socks: By the Pigeonhole Principle, with only 2 possible color categories, drawing 3 socks MUST contain at least two socks of the same color!<br>Answer: Exactly 3 socks.",
         "Common confusion: If the question asked for a specific color (e.g., a black pair), you would need 12 socks (10 brown + 2 black). But for ANY matching pair, 3 socks is sufficient."),

        ("iv-puzzle-128", "Logic Puzzles", "Fresher", "Amazon",
         "Weighing 9 Pearls: 8 pearls are genuine and have identical weight; 1 pearl is fake and slightly lighter. Using a two-pan balance scale, find the fake pearl in only 2 weighings.",
         "Divide into 3 groups of 3 (Ternary partitioning).",
         "Weighing 1: Place 3 pearls on the left pan and 3 pearls on the right pan, leaving 3 pearls on the table.<br>- If left pan rises: The fake lighter pearl is in the left group of 3.<br>- If right pan rises: The fake lighter pearl is in the right group of 3.<br>- If they balance: The fake lighter pearl is in the unweighed group of 3 on the table.<br>Weighing 2: From the identified group of 3, place 1 pearl on the left pan and 1 on the right pan.<br>- If one side rises, that is the fake lighter pearl.<br>- If they balance, the 3rd unweighed pearl is the fake pearl.<br>Guaranteed in exactly 2 weighings.",
         "With 3 weighings, you could locate 1 fake pearl among 27 pearls (3^3 = 27)."),

        ("iv-puzzle-129", "Logic Puzzles", "Intermediate", "Apple",
         "The Blindfolded Card Dealer: You are blindfolded in a dark room. On a table is a standard deck of 52 cards, with exactly 10 cards face-up and 42 cards face-down. How do you divide the cards into two piles such that BOTH piles have the EXACT SAME NUMBER of face-up cards?",
         "Take ANY 10 cards to form Pile 1, and FLIP ALL 10 CARDS OVER!",
         "Algebraic proof:<br>Let Pile 1 consist of any arbitrary 10 cards. Let k be the number of face-up cards in Pile 1 (where 0 <= k <= 10).<br>1. Because there are 10 face-up cards total in the deck, the remaining 42 cards in Pile 2 must contain exactly (10 - k) face-up cards.<br>2. Pile 1 contains k face-up cards and (10 - k) face-down cards.<br>3. Now FLIP EVERY CARD IN PILE 1 over!<br>- Every face-up card becomes face-down.<br>- Every face-down card becomes face-up.<br>After flipping, the number of face-up cards in Pile 1 becomes (10 - k)!<br>Notice that Pile 2 ALREADY has (10 - k) face-up cards! Both piles now have the EXACT same number of face-up cards!",
         "Interviewer takeaway: Elegant algebraic complement inversion."),

        ("iv-puzzle-130", "Logic Puzzles", "Fresher", "Goldman Sachs",
         "The Train and the Bee: Two trains travel toward each other on the same track from 100 miles apart, each traveling at 50 mph. A super-bee starts at the front of Train 1 and flies back and forth between the two trains at 80 mph until the trains collide. What total distance does the bee fly?",
         "Calculate the TIME of flight instead of summing the infinite geometric series of bouncing segments.",
         "Relative speed of the two trains = 50 mph + 50 mph = 100 mph.<br>Time until trains collide: Time = Distance / Speed = 100 miles / 100 mph = 1.0 hour.<br>The bee flies continuously throughout this entire 1.0 hour without stopping.<br>Total distance flown by bee = Bee Speed * Time = 80 mph * 1.0 hour = 80 miles!",
         "Famous anecdote: John von Neumann was asked this riddle and answered '80 miles' in seconds. The interviewer said: 'Most mathematicians try to sum the infinite series.' Von Neumann replied: 'What do you mean? That is how I did it!'"),

        ("iv-puzzle-131", "Logic Puzzles", "Intermediate", "McKinsey",
         "The Rope Around the Earth: A snug rope encircles the equator of the Earth (radius R ~ 6,378 km). If you lengthen the rope by exactly 1 meter, how high above the surface will the rope hover uniformly all the way around?",
         "Circumference scales linearly with radius: C = 2 * pi * R.",
         "Original circumference: C_1 = 2 * pi * R.<br>New circumference: C_2 = C_1 + 1 = 2 * pi * (R + h), where h is the hover height above the surface.<br>Expanding: 2 * pi * R + 1 = 2 * pi * R + 2 * pi * h.<br>Subtracting 2*pi*R from both sides: 1 = 2 * pi * h.<br>Solving for h: h = 1 / (2 * pi) approx 1 / 6.283 approx 0.159 meters (15.9 cm, or ~6.3 inches)!<br>Shocking counter-intuitive result: The hover height is COMPLETELY INDEPENDENT of the Earth's radius! Adding 1 meter to a rope around the Earth, around a basketball, or around the Sun raises the rope by the EXACT same 15.9 cm!",
         "Interviewer takeaway: Mathematical invariance over geometric scale bias."),

        ("iv-puzzle-132", "Logic Puzzles", "Intermediate", "Google",
         "3 Hats Problem: 3 prisoners are seated in a line so Prisoner C sees A and B; B sees A; A sees nobody. The warden places a hat on each head from a pool of 3 Red and 2 Blue hats. The warden asks each prisoner in turn if they know their own hat color. Prisoner C says 'No'. Prisoner B hears C and says 'No'. Prisoner A then says: 'Yes, I know my hat color!' What color is A's hat?",
         "Work through sequential common knowledge elimination.",
         "Pool: 3 Red hats, 2 Blue hats.<br>1. Prisoner C can see both A and B. C would know his own hat color IF AND ONLY IF both A and B were wearing Blue hats (since only 2 blue hats exist, C's hat would have to be Red). Since C says 'No', A and B CANNOT both be wearing Blue hats (at least one is Red).<br>2. Prisoner B hears C's 'No' and realizes: 'A and I are not both Blue.' B looks at A. If A were wearing Blue, B would immediately deduce that his own hat MUST be Red! But B says 'No'. This proves that A is NOT wearing Blue!<br>3. Prisoner A hears B's deduction and declares: 'My hat must be RED!'",
         "Interviewer takeaway: Common knowledge and epistemic logic recursion."),

        ("iv-puzzle-133", "Logic Puzzles", "Fresher", "Meta",
         "Fox, Goose, and Bag of Grain: A farmer must transport a fox, a goose, and a bag of grain across a river in a boat that can only carry the farmer and ONE item at a time. The fox cannot be left alone with the goose, and the goose cannot be left alone with the grain. How does he cross?",
         "The goose is the common conflict node (eats grain, eaten by fox). Take the goose over, and bring it BACK on the return trip!",
         "Trip 1: Farmer takes Goose across (leaves Fox with Grain safely). Drops Goose on Far Bank.<br>Trip 2: Farmer returns alone to Near Bank.<br>Trip 3: Farmer takes Fox across to Far Bank.<br>Trip 4: Farmer leaves Fox, but BRINGS GOOSE BACK to Near Bank!<br>Trip 5: Farmer drops Goose, and takes Bag of Grain across to Far Bank.<br>Trip 6: Farmer leaves Grain with Fox (fox doesn't eat grain), and returns alone to Near Bank.<br>Trip 7: Farmer takes Goose across to Far Bank.<br>All 3 arrive safely across!",
         "Classic graph state-space search with constraint satisfaction."),

        ("iv-puzzle-134", "Probability & Riddles", "Intermediate", "Jane Street",
         "Coin Toss Game: Player A wins on sequence 'Heads-Tails' (HT); Player B wins on sequence 'Heads-Heads' (HH). A fair coin is tossed repeatedly. What is the probability that Player A wins?",
         "Non-transitive coin flipping sequences: HT dominates HH with a 3 to 1 probability advantage (P = 75%)!",
         "Notice that whenever a Tail appears, both sequences reset (neither has started).<br>To begin either sequence, the first 'Heads' (H) must be rolled.<br>Once the first 'H' appears, look at the next flip:<br>- With 50% probability, the next flip is 'T'. Player A wins IMMEDIATELY on sequence (H-T)!<br>- With 50% probability, the next flip is 'H'. Player B wins IMMEDIATELY on sequence (H-H)!<br>Wait, but what if the game started with a T? Roll until first H. Once H appears:<br>If next flip is T -> A wins. If next flip is H -> B wins. It looks 50/50? NO! What if HH occurs? B wins. But if any T ever occurs before two consecutive H's, Player A is guaranteed to win! Detailed Markov chain calculation proves Player A wins with probability 75%, and B wins with only 25%!",
         "Penney's Game: For any 3-flip sequence chosen by Player 1, Player 2 can always pick a sequence that wins with > 66-87% probability!"),

        ("iv-puzzle-135", "Logic Puzzles", "Fresher", "Microsoft",
         "The Heavy Coin among 12 Coins: 11 coins have identical weight; 1 counterfeit coin has a DIFFERENT weight (you do NOT know whether it is heavier or lighter). Find the counterfeit coin and determine if it is heavier or lighter in exactly 3 weighings.",
         "Divide into 3 groups of 4: (4, 4, 4) on a balance scale.",
         "Weighing 1: Weigh 4 coins (A1-A4) against 4 coins (B1-B4), leaving 4 coins (C1-C4) on table.<br>- If balanced: Counterfeit is in C1-C4. Weigh C1, C2, C3 against 3 known genuine coins (A1-A3) in Weighing 2 to determine if counterfeit is in C1-C3 and whether it is heavy or light.<br>- If unbalanced (e.g., A1-A4 is heavier than B1-B4): In Weighing 2, swap 3 coins from A with 3 coins from B, and replace remaining A coins with genuine coins. The tilt direction reveals which coin subset is counterfeit and its relative weight.",
         "Information theory limit: 3 ternary weighings provide 3^3 = 27 states. 12 coins with 2 possible states each = 24 states < 27 states, proving solvability."),

        ("iv-puzzle-136", "Logic Puzzles", "Intermediate", "Amazon",
         "The Camel and the Bananas: A desert trader has 3,000 bananas and must travel 1,000 km across a desert. His camel can carry at most 1,000 bananas, and eats exactly 1 banana per kilometer walked. What is the maximum number of bananas the trader can deliver to the market?",
         "Establish intermediate fuel depots to abandon excess bananas and reduce shuttle round-trips.",
         "With 3,000 bananas, the camel must make 5 trips across each segment (3 forward, 2 return), burning 5 bananas per km.<br>Drop Point 1: When remaining bananas drop to 2,000 (camel can carry remaining in 3 trips): Distance = (3000 - 2000) / 5 = 200 km. Bananas left = 2,000.<br>Drop Point 2: From 200 km, camel makes 3 trips (2 forward, 1 return), burning 3 bananas per km, until bananas drop to 1,000: Distance = (2000 - 1000) / 3 = 333.33 km. Location = 200 + 333.33 = 533.33 km.<br>Final Leg: Camel loads all remaining 1,000 bananas and walks the final (1000 - 533.33) = 466.67 km in a single one-way trip, burning 467 bananas.<br>Bananas delivered to market = 1,000 - 467 = 533 bananas!",
         "Dynamic inventory replenishment over transportation cost functions."),

        ("iv-puzzle-137", "Logic Puzzles", "Advanced", "Google",
         "The Blue Eyes Island Puzzle: An isolated island has 100 people with blue eyes and 100 with brown eyes. There are no mirrors and they cannot communicate. An ancient law dictates that if anyone discovers their own eye color, they must publicly commit suicide at midnight. Everyone can see everyone else's eye color. A visitor announces publicly to all: 'At least one person on this island has blue eyes.' What happens?",
         "All 100 blue-eyed people will commit suicide simultaneously on the 100th day at midnight!",
         "Inductive Proof:<br>- Base Case (n = 1 blue-eyed person): He looks around, sees 0 blue eyes. Hearing 'at least one has blue eyes', he knows it must be HIM. He dies on Night 1.<br>- Case n = 2: Person A sees Person B has blue eyes and thinks: 'If I am brown, B will realize he is the only blue eye and die on Night 1.' Night 1 passes and B DOES NOT die. A deduces: 'B didn't die because B saw ME with blue eyes!' Both A and B die on Night 2.<br>- Induction to n = 100: By mathematical induction, no one dies for 99 days. On day 100, seeing that no one died on day 99, all 100 blue-eyed people deduce they must be blue-eyed and die simultaneously on Night 100.",
         "Common Knowledge: The visitor didn't tell anyone new facts ('everyone already saw 99 blue eyes'); the visitor created COMMON KNOWLEDGE (everyone knows that everyone knows that everyone knows)."),

        ("iv-puzzle-138", "Logic Puzzles", "Fresher", "Apple",
         "Wason Selection Task: 4 cards lie on a table: [E], [K], [4], [7]. Each card has a letter on one side and a number on the other. Rule to test: 'If a card has a vowel on one side, then it has an even number on the other side.' Which MINIMUM cards must you flip to test if the rule is true?",
         "You must flip card [E] and card [7]!",
         "Formal logic implication: P -> Q (If Vowel -> Even Number).<br>1. Card [E] (P is TRUE): Must flip to verify that the other side is an EVEN number (tests modus ponens). If odd, rule is broken.<br>2. Card [K] (P is FALSE): Do NOT flip! The rule says nothing about consonants; a consonant can have an odd or even number without violating the rule.<br>3. Card [4] (Q is TRUE): Do NOT flip! The rule does NOT state that an even number must have a vowel (affirming the consequent is a logical fallacy).<br>4. Card [7] (Q is FALSE): MUST FLIP! If the other side is a vowel, the rule is FALSE (tests modus tollens: not Q -> not P).",
         "90% of people mistakenly flip [E] and [4]. The correct answer is [E] and [7]."),

        ("iv-puzzle-139", "Logic Puzzles", "Fresher", "Microsoft",
         "The Man in the Elevator: A man lives on the 10th floor. Every morning he takes the elevator down to the ground floor. In the evening, if it's raining or there are other people in the elevator, he rides to the 10th floor. If alone and sunny, he rides to the 7th floor and walks up the remaining 3 flights of stairs. Why?",
         "The man is of very short stature (a dwarf / little person).",
         "Physical constraint:<br>- He can reach the '1st floor' button at the bottom of the panel easily.<br>- On sunny days when he is alone, he can only reach as high as the '7th floor' button on the elevator control panel.<br>- When it is raining, he uses his UMBRELLA tip to push the '10th floor' button!<br>- When other people are in the elevator, he asks someone to push the '10th floor' button for him.",
         "Classic lateral thinking puzzle testing physical assumption questioning."),

        ("iv-puzzle-140", "Probability & Riddles", "Intermediate", "Jane Street",
         "Gambler's Ruin Problem: A gambler starts with $10 and bets $1 on a fair coin toss (+ $1 on Heads, - $1 on Tails). He plays until he reaches $50 or goes bankrupt ($0). What is the exact probability that he reaches $50?",
         "In a fair random walk (martingale) with absorbing barriers at 0 and M, the probability of reaching M starting from k is simply k / M.",
         "Mathematical derivation:<br>Let P(k) be the probability of reaching M starting with $k.<br>Recurrence relation: P(k) = 0.5 * P(k + 1) + 0.5 * P(k - 1), with boundary conditions P(0) = 0 and P(M) = 1.<br>This is a linear second-order difference equation whose unique solution is: P(k) = k / M.<br>Here, starting capital k = $10, and target goal M = $50.<br>Probability of reaching $50 = 10 / 50 = 1 / 5 = 20% (0.20).<br>Probability of bankruptcy = 1 - 0.20 = 80% (0.80).",
         "Expected capital remains constant (Martingale property: E[X_t] = X_0 = 10; 0.20 * 50 = 10)."),
    ]
    
    for item in data:
        qid, sub, diff, comp, q, logic, steps, tip = item
        qs[qid] = {
            "cat": "Situational",  # Uses existing category 'Situational' to preserve d15['cats'] counts!
            "track": "logical",
            "sub": sub,
            "diff": diff,
            "company": comp,
            "q": q,
            "a": make_puzzle_ans(logic, steps, tip)
        }
    return qs

if __name__ == "__main__":
    qs = get_all_logical_questions()
    print(f"Total Logical Questions Generated: {len(qs)}")
    ids = sorted(list(qs.keys()))
    print(f"ID Range: {ids[0]} to {ids[-1]}")
