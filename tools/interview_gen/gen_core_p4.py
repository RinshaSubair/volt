# tools/interview_gen/gen_core_p4.py
# Circuits, Controls & Embedded Systems (iv-core-161 to iv-core-180)

from .common import make_tech_ans

def get_core_p4():
    qs = {}
    data = [
        ("iv-core-161", "Circuits & Networks", "Fresher", "Texas Instruments",
         "State the Maximum Power Transfer Theorem for AC circuits when load impedance is complex (Z_load = R_L + j*X_L).",
         "Maximum active real power is transferred from an AC source to a load when the load impedance is the complex conjugate of the source Thevenin impedance: Z_load = Z_th* = R_th - j*X_th.",
         "Load reactance X_L cancels source reactance X_th (X_L + X_th = 0), establishing total circuit resonance where net circuit reactance is zero. The remaining total resistance is 2 * R_th, so circuit current is I = V_th / (2 * R_th). Real power transferred to the load is P_max = I^2 * R_L = (V_th / (2 * R_th))^2 * R_th = V_th^2 / (4 * R_th).<br>Note on efficiency: At maximum power transfer, exactly half the total power is dissipated internally inside the source resistance, yielding an efficiency of exactly 50%.",
         "Important distinction: In power transmission systems, we operate at maximum efficiency (> 95%), NOT maximum power transfer. Maximum power transfer is prized in telecommunications, RF front-ends, and sensor instrumentation where signal power is milliwatts."),

        ("iv-core-162", "Circuits & Networks", "Intermediate", "Analog Devices",
         "What is Quality Factor (Q) in series and parallel RLC resonant circuits, and how does it relate to 3dB bandwidth?",
         "Quality factor Q is a dimensionless figure of merit that quantifies energy storage versus energy dissipation: Q = 2*pi * (Peak Energy Stored / Energy Dissipated per cycle).",
         "1. Series RLC: At resonance (omega_0 = 1 / sqrt(L*C)), impedance is at a minimum (Z = R). Quality factor is Q = (omega_0 * L) / R = 1 / (omega_0 * C * R) = (1/R) * sqrt(L/C). The voltages across L and C are amplified to Q times the input source voltage (V_L = V_C = Q * V_source), known as voltage magnification.<br>2. Parallel RLC: At resonance, impedance is at a maximum (Z = R_p). Q = R_p / (omega_0 * L) = omega_0 * C * R_p = R_p * sqrt(C/L), producing current magnification (I_L = I_C = Q * I_source).<br>Bandwidth relationship: Bandwidth BW = f_2 - f_1 = f_0 / Q. High Q means sharp selectivity and narrow bandwidth.",
         "Series RLC has Q inversely proportional to R, whereas Parallel RLC has Q directly proportional to R."),

        ("iv-core-163", "Circuits & Networks", "Intermediate", "Qualcomm",
         "Explain Two-Port Network ABCD parameters and state the conditions for a network to be Reciprocal and Symmetric.",
         "Transmission (ABCD) parameters relate the input voltage and current (sending end) to output voltage and current (receiving end): V1 = A*V2 - B*I2; I1 = C*V2 - D*I2 (using the standard convention where I2 leaves port 2).",
         "Physical meanings: A = V1/V2 (open-circuit reverse voltage ratio, dimensionless); B = -V1/I2 (short-circuit transfer impedance, ohms); C = I1/V2 (open-circuit transfer admittance, siemens); D = -I1/I2 (short-circuit reverse current ratio, dimensionless).<br>1. Condition for Reciprocity (network obeys Lorentz reciprocity theorem, passive linear bilateral components): A*D - B*C = 1.<br>2. Condition for Symmetry (network looks identical when viewed from port 1 or port 2): A = D.",
         "ABCD parameters are particularly powerful because the combined parameters of cascaded two-port networks are obtained by simple matrix multiplication: [T_total] = [T_1] * [T_2]."),

        ("iv-core-164", "Circuits & Networks", "Fresher", "Schneider Electric",
         "Explain Tellegen's Theorem and why it holds true for non-linear, time-varying, and active circuits.",
         "Tellegen's theorem states that for any lumped electrical network of b branches conforming to Kirchhoff's Laws (KCL and KVL), the algebraic sum of the instantaneous branch powers is identically zero: Sum (v_k(t) * i_k(t)) = 0 for k = 1 to b.",
         "The extraordinary power of Tellegen's theorem is that it relies solely on the network's topological graph structure (incidence matrix) and does NOT depend on the physical nature of the branch components. It holds true whether components are linear or non-linear, passive or active, time-invariant or time-varying, bilateral or unilateral. It is the network graph theory expression of the law of conservation of energy.",
         "Tellegen's theorem is fundamental in sensitivity analysis, proving Reciprocity theorems, and formulating power flow algorithms."),

        ("iv-core-165", "Circuits & Networks", "Intermediate", "Texas Instruments",
         "What is the physical meaning of Initial and Final Value Theorems in Laplace s-domain circuit analysis?",
         "The Initial Value Theorem calculates the system state immediately after switching (t = 0+): lim (t -> 0+) f(t) = lim (s -> infinity) [s * F(s)]. The Final Value Theorem calculates the steady-state value as t -> infinity: lim (t -> infinity) f(t) = lim (s -> 0) [s * F(s)].",
         "Physical intuition: As s -> infinity, s represents infinite frequency (ultra-fast transients occurring instantaneously at t = 0+), where inductors act as open circuits (sL -> infinity) and capacitors act as short circuits (1/sC -> 0). As s -> 0, s represents DC steady-state, where inductors act as short circuits (sL -> 0) and capacitors act as open circuits (1/sC -> infinity).<br>Fatal constraint: Final Value Theorem is valid if and only if all poles of [s * F(s)] lie strictly in the open left half of the s-plane. If the system has poles on the j*omega axis (undamped oscillation like sin(t)) or in the right half plane, FVT produces completely false mathematical nonsense.",
         "Trap alert: Never apply Final Value Theorem to an LC oscillator or an unstable system!"),

        ("iv-core-166", "Control Systems", "Intermediate", "Bosch",
         "Explain the Kalman Rank Condition for Controllability and Observability in state-space control systems.",
         "A linear time-invariant system is described by dx/dt = A*x + B*u; y = C*x + D*u, where x is an n-dimensional state vector.",
         "1. Controllability: The system is completely state controllable if and only if an unconstrained control input u(t) can transfer any initial state x(0) to any desired target state x(t1) in finite time t1. Kalman's Controllability Matrix is Q_c = [ B | A*B | A^2*B | ... | A^(n-1)*B ]. The system is controllable iff Rank(Q_c) = n (full row rank).<br>2. Observability: The system is completely observable iff observing the output y(t) over a finite time interval allows unique determination of initial state x(0). Kalman's Observability Matrix is Q_o = [ C; C*A; C*A^2; ...; C*A^(n-1) ]. The system is observable iff Rank(Q_o) = n (full column rank).",
         "If a system is uncontrollable or unobservable, pole-zero cancellations occur in the transfer function, hiding internal unstable modes (such as hidden resonance) from the output."),

        ("iv-core-167", "Control Systems", "Advanced", "Honeywell",
         "State the Nyquist Stability Criterion and explain how it evaluates closed-loop stability from the open-loop frequency response.",
         "The Nyquist criterion evaluates the stability of a closed-loop system 1 + G(s)H(s) = 0 based on Cauchy's Principle of the Argument mapped along the Nyquist contour enclosing the right half of the s-plane (RHP).",
         "Formula: N = Z - P, or Z = N + P.<br>- P is the number of open-loop poles of G(s)H(s) in the unstable right half plane (RHP).<br>- N is the number of clockwise encirclements of the critical point (-1 + j0) made by the Nyquist plot G(jw)H(jw) as omega travels from -infinity to +infinity.<br>- Z is the number of closed-loop poles in the unstable RHP.<br>For a stable closed-loop system, we must have Z = 0, which requires: N = -P (meaning the Nyquist plot must encircle the critical point (-1 + j0) exactly P times in the COUNTER-CLOCKWISE direction). If the open-loop system is already stable (P = 0), then N must equal 0 (zero encirclements of -1 + j0).",
         "Interviewer trap: Always check open-loop poles first! If open-loop has 1 RHP pole, 0 encirclements means the closed-loop system is UNSTABLE (Z = 0 + 1 = 1)."),

        ("iv-core-168", "Control Systems", "Intermediate", "Schneider Electric",
         "Define Gain Margin (GM) and Phase Margin (PM) on a Bode Plot and explain their physical relationship to damping ratio.",
         "Gain Margin and Phase Margin measure how close a feedback system is to the verge of instability (the critical point -1 + j0).",
         "1. Phase Crossover Frequency (omega_pc): The frequency where the open-loop phase lag reaches exactly -180 degrees. Gain Margin is GM = -20*log10 |G(j*omega_pc)| (in dB). It indicates how much the loop gain can be increased before the system goes unstable.<br>2. Gain Crossover Frequency (omega_gc): The frequency where open-loop magnitude is unity (0 dB). Phase Margin is PM = 180 deg + angle(G(j*omega_gc)). It indicates how much additional phase lag the system can tolerate before becoming unstable.<br>Rule of thumb: In second-order dominant systems, Phase Margin relates directly to the damping ratio: zeta approx PM (in degrees) / 100. A Phase Margin of 45 to 60 degrees corresponds to zeta approx 0.45 to 0.707, providing fast transient response with < 10-15% overshoot.",
         "A system can have positive GM and positive PM and still be close to instability if the open-loop locus skirts very close to (-1 + j0) at intermediate frequencies."),

        ("iv-core-169", "Control Systems", "Fresher", "Siemens",
         "Explain Phase-Lead and Phase-Lag compensators and when each should be used in control system design.",
         "Both are cascaded passive RC or active op-amp networks with transfer function D(s) = (s + z) / (s + p).",
         "1. Phase-Lead Compensator (zero is closer to origin than pole: |z| < |p|): Injects positive phase lead near gain crossover frequency, shifting the root locus to the left. It increases phase margin, widens closed-loop bandwidth, speeds up transient rise time, and reduces settling time and overshoot. Use when system is too slow or underdamped.<br>2. Phase-Lag Compensator (pole is closer to origin than zero: |p| < |z|): Provides high DC gain at low frequencies to eliminate steady-state error, while attenuating high-frequency gain without significantly reducing phase margin at crossover. Use when steady-state tracking error is unacceptable but transient speed is already satisfactory.<br>3. Lead-Lag combines both benefits: lead speeds up response while lag boosts low-frequency gain.",
         "Lead compensator acts like an approximate PD controller; Lag compensator acts like an approximate PI controller."),

        ("iv-core-170", "Control Systems", "Intermediate", "Rockwell Automation",
         "What is Integrator Windup in PID controllers and how do Anti-Windup algorithms prevent overshoot?",
         "Integrator Windup occurs in physical control systems when an actuator saturates at its mechanical or electrical limit (e.g., a control valve is 100% wide open, or a motor drive hits maximum current limit).",
         "While the actuator is fully saturated, the system output cannot reach the setpoint, leaving a sustained positive error e(t) > 0. The integral term continues integrating this persistent error over time, growing to an enormous value ('winding up'). When the controlled variable finally reaches setpoint, the actuator cannot close because the huge accumulated integral value must first discharge ('unwind'). This causes massive overshoot, long recovery delays, and potential physical damage.<br>Anti-Windup solutions: 1. Clamping (Conditional Integration): Halts integration whenever the actuator command reaches saturation limits. 2. Back-Calculation: Feeds back the difference between saturated actuator command and unsaturated controller output (u - v) through a tracking gain (1/Tt) to dynamically discharge the integrator.",
         "Always implement anti-windup in any embedded motor drive, thermal controller, or valve positioner."),

        ("iv-core-171", "Embedded & Microcontrollers", "Fresher", "Texas Instruments",
         "Why is the 'volatile' keyword mandatory for hardware peripheral registers and variables shared between an ISR and main loop in C?",
         "The 'volatile' keyword tells the C compiler optimizer that the variable's value can change at any moment outside the control of the currently executing code thread.",
         "Modern optimizing compilers (e.g., GCC -O2 or -O3) aggressively cache frequently accessed memory variables inside CPU core registers. If a variable is checked in a while loop (e.g., `while(!flag_ready)`), the compiler reads the variable once into register R1 and generates an infinite loop that repeatedly checks R1. If `flag_ready` is modified asynchronously by a hardware timer interrupt service routine (ISR) or DMA hardware, the main thread never sees the change because it is reading cached R1, locking the system in an infinite loop.<br>Declaring `volatile uint8_t flag_ready;` forces the compiler to emit a fresh LDR (load register) memory bus read instruction on EVERY single access, guaranteeing visibility.",
         "Rule of thumb: Use volatile for: 1. Hardware memory-mapped I/O registers. 2. Global variables shared with ISRs. 3. Variables shared across threads in an RTOS without mutexes."),

        ("iv-core-172", "Embedded & Microcontrollers", "Intermediate", "Qualcomm",
         "What is Interrupt Latency, what factors contribute to it, and what are the golden rules of writing an ISR?",
         "Interrupt Latency is the time interval elapsed between the physical assertion of a hardware interrupt signal and the execution of the first instruction in the corresponding Interrupt Service Routine (ISR).",
         "Key contributors to latency:<br>1. CPU executing non-interruptible instructions or atomic critical sections with interrupts disabled.<br>2. Completion of the current instruction cycle.<br>3. Hardware context saving (pushing program counter PC, status register PSR, and scratch registers onto the stack; ARM Cortex-M hardware stacking takes ~12 clock cycles).<br>4. Interrupt controller vector fetch (e.g., NVIC).<br>Golden rules of writing an ISR:<br>- Keep it ultra-short and fast (< a few microseconds).<br>- NEVER call blocking functions (e.g., `delay()`, `printf()`, or waiting on a UART transmission flag).<br>- NEVER perform dynamic memory allocation (`malloc()` or `free()`).<br>- NEVER acquire a blocking mutex or semaphore that can sleep the thread.<br>- Architecture pattern: Set a flag or push data to a lockless ring buffer and defer heavy processing to an RTOS worker task.",
         "Cortex-M's 'tail-chaining' feature bypasses pop/push stacking when one interrupt immediately follows another, cutting latency down to 6 clock cycles."),

        ("iv-core-173", "Embedded & Microcontrollers", "Intermediate", "NXP",
         "Compare I2C and SPI serial communication protocols in terms of bus topology, wire count, throughput, and error handling.",
         "I2C (Inter-Integrated Circuit) is a 2-wire, synchronous, multi-master/multi-slave serial bus. SPI (Serial Peripheral Interface) is a 4-wire, synchronous, full-duplex, master-slave interface.",
         "1. I2C uses only 2 wires (SDA and SCL) configured as open-drain with external pull-up resistors. It supports multi-master arbitration and 7-bit/10-bit software device addressing, but throughput is modest (Standard: 100 kHz, Fast: 400 kHz, Fast-Plus: 1 MHz) and pull-up RC rise-time limits bus capacitance to 400 pF.<br>2. SPI uses 4 wires (MOSI, MISO, SCK, and dedicated CS/SS per slave) with push-pull CMOS outputs. It is full-duplex, has zero software address overhead, and runs at very high speeds (10 MHz to 50+ MHz). However, each additional slave requires an extra GPIO pin for Chip Select, consuming board routing space.",
         "Choose I2C when pin count and board routing space are tight; choose SPI for high-bandwidth streaming like SD cards, flash memory, and TFT displays."),

        ("iv-core-174", "Embedded & Microcontrollers", "Intermediate", "Bosch",
         "What is Priority Inversion in Real-Time Operating Systems (RTOS), and how does Priority Inheritance prevent it?",
         "Priority Inversion is a catastrophic bug where a low-priority task indirectly prevents a high-priority task from running, violating real-time determinism.",
         "Scenario: Low-priority Task L acquires a shared mutex M. High-priority Task H wakes up and requests mutex M; because M is held by L, Task H is blocked. Next, Medium-priority Task M (which does not need mutex M) wakes up. Because Task M has higher priority than L, the RTOS preempts Task L. As a result, Task L cannot finish to release mutex M, and High-priority Task H is indefinitely starved by Medium-priority Task M!<br>Famous real-world example: The Mars Pathfinder spacecraft in 1997 suffered repetitive system watchdog resets on Mars due to this exact bug.<br>Solution: Priority Inheritance Protocol (PIP). When Task H blocks on mutex M held by Task L, the RTOS temporarily elevates the priority of Task L to match Task H. Task L runs without preemption by Task M, quickly finishes its critical section, releases mutex M, drops back to low priority, and Task H immediately runs.",
         "Modern RTOSs (FreeRTOS, Zephyr) have built-in priority inheritance mutex options (`xSemaphoreCreateMutex()`)."),

        ("iv-core-175", "Embedded & Microcontrollers", "Intermediate", "STMicroelectronics",
         "How does Direct Memory Access (DMA) with Double Buffering (Ping-Pong) prevent data overrun in high-speed ADC sampling?",
         "Without DMA, the CPU must service an interrupt for every single ADC sample (e.g., at 1 MSPS, the CPU would be interrupted 1,000,000 times a second, consuming 100% of processing power).",
         "A DMA controller transfers data directly from peripheral registers to SRAM over the internal bus matrix without CPU intervention. In Double Buffering (Ping-Pong buffering), DMA is configured with two identical memory buffers: Buffer A and Buffer B.<br>While the DMA hardware fills Buffer A with fresh incoming ADC samples, the CPU core is concurrently processing the previously filled Buffer B (running FFTs or filtering). When Buffer A is full, the DMA controller triggers a Half-Transfer or Transfer-Complete interrupt and automatically switches to filling Buffer B without losing a single clock cycle. The CPU then switches to processing Buffer A. This completely decouples data acquisition from data processing and eliminates data overruns.",
         "On ARM Cortex-M processors, configuring Circular DMA mode makes this ping-pong loop run forever in hardware."),

        ("iv-core-176", "Embedded & Microcontrollers", "Fresher", "Microchip",
         "What is the difference between a Standard Watchdog Timer (WDT) and a Windowed Watchdog Timer (WWT)?",
         "A Watchdog Timer is an autonomous hardware timer clocked from an independent internal RC oscillator that resets the microcontroller if the software fails to refresh ('kick' or 'feed') it within a timeout period.",
         "1. Standard Watchdog: The software must kick the watchdog before it underflows (e.g., within 50 ms). If software hangs in an infinite loop, the watchdog expires and resets the MCU. However, if a corrupted program gets stuck in an erroneous loop that happens to contain the watchdog kick instruction, the watchdog will be continually refreshed and will NEVER detect the system failure.<br>2. Windowed Watchdog (WWT): Enforces both a maximum deadline AND a minimum threshold window (e.g., refresh must occur between 30 ms and 50 ms). If the software kicks the watchdog TOO LATE (> 50 ms) OR TOO EARLY (< 30 ms), a system reset is instantly triggered. This catches runaway code that executes erratically fast due to clock oscillator failures or corrupt jump instructions.",
         "In safety-critical automotive systems (ISO 26262 ASIL-D), windowed watchdogs are legally mandated."),

        ("iv-core-177", "Embedded & Microcontrollers", "Intermediate", "Texas Instruments",
         "Explain Clock Stretching in I2C and how Open-Drain outputs facilitate Multi-Master Bus Arbitration.",
         "I2C lines (SDA and SCL) are open-drain, pulled up by external resistors. A device can only pull the line LOW to GND; it can never actively drive it HIGH.",
         "1. Clock Stretching: In I2C, the master generates the SCL clock. If a slow slave device (e.g., an EEPROM executing an internal write) cannot keep up with master speed, it holds SCL LOW after receiving a byte. Because the line is open-drain (wired-AND logic), the clock stays at 0V. The master senses this and halts its internal clock generator until the slave releases SCL to float HIGH, allowing graceful flow control without buffer overflows.<br>2. Multi-Master Arbitration: Two masters can start transmitting simultaneously. Both monitor the SDA line while transmitting. If Master 1 tries to send a '1' (letting SDA float high) but Master 2 sends a '0' (pulling SDA low), Master 1 detects that the actual bus state does not match its output. Master 1 immediately realizes it has lost arbitration, shuts off its SDA driver without generating an error, and drops into slave receiver mode.",
         "Wired-AND open-drain architecture guarantees that bus collisions never cause electrical short circuits between power rails."),

        ("iv-core-178", "Embedded & Microcontrollers", "Fresher", "ARM",
         "Explain Memory-Mapped I/O (MMIO) versus Port-Mapped I/O (PMIO) in processor architectures.",
         "Both are techniques for the CPU to communicate with peripheral hardware devices (timers, UARTs, GPIOs).",
         "1. Memory-Mapped I/O (MMIO): Hardware peripheral registers share the exact same address space as system RAM. Reading or writing a peripheral register uses standard load/store assembly instructions (`LDR` and `STR` on ARM, `MOV` on x86). Writing to address `0x40021000` toggles a GPIO pin, exactly like writing to a variable in RAM. Advantage: Clean, uniform instruction set, no special assembly instructions needed. Disadvantage: Consumes portion of memory address space.<br>2. Port-Mapped I/O (PMIO): Hardware peripherals have a completely separate, dedicated I/O address space (e.g., 64KB I/O ports in x86). Accessing peripherals requires special CPU instructions (`IN` and `OUT`).<br>All modern ARM (Cortex-M, Cortex-A) and RISC-V microcontrollers exclusively use Memory-Mapped I/O.",
         "In C, MMIO registers are defined as pointer dereferences to fixed hardware addresses cast to volatile pointers: `#define GPIOA_ODR (*((volatile uint32_t*)0x48000014))`."),

        ("iv-core-179", "Embedded & Microcontrollers", "Advanced", "Bosch",
         "What is CAN Bus Bit-Stuffing and how does CAN 2.0B handle error detection and fault confinement (Error Active, Passive, Bus-Off)?",
         "CAN (Controller Area Network) is a two-wire differential robust automotive serial bus. Bit-stuffing inserts a complementary bit after 5 consecutive identical bits to guarantee edge transitions for receiver clock resynchronization.",
         "Error handling: CAN checks every message using 5 mechanisms: Bit Monitoring, 15-bit CRC, Frame Format check, Ack delimiter check, and Bit-stuffing check.<br>Fault Confinement: Every CAN node maintains two internal error counters: Transmit Error Counter (TEC) and Receive Error Counter (REC).<br>1. Error Active (TEC < 128, REC < 128): Node operates normally and broadcasts active error flags (6 dominant bits) upon detecting an error.<br>2. Error Passive (TEC >= 128 or REC >= 128): Node suspects its own transceiver is faulty. It can transmit, but broadcasts passive error flags (6 recessive bits) so it doesn't corrupt the bus for other nodes.<br>3. Bus-Off (TEC > 255): Node is completely disconnected from the CAN bus electronically by the controller, preventing a malfunctioning ECU from dragging down the entire vehicle's network.",
         "CAN FD (Flexible Data-Rate) extends classic CAN by allowing up to 64 data bytes per frame (vs 8 bytes) and switching to 2-8 Mbps during the data payload phase."),

        ("iv-core-180", "Embedded & Microcontrollers", "Intermediate", "Texas Instruments",
         "Explain Successive Approximation Register (SAR) ADC versus Delta-Sigma (Delta-Sigma) ADC architectures and their application trade-offs.",
         "SAR ADCs and Delta-Sigma ADCs are the two most prevalent ADC architectures in modern embedded electronics.",
         "1. SAR ADC: Uses a binary search algorithm (like a balance scale) with an internal DAC and comparator to resolve one bit per clock cycle. For an N-bit conversion, it takes N clock cycles. Fast conversion speeds (100 kSPS to 10 MSPS), low latency (instant single-cycle response), and low power. Ideal for control loops, motor phase current sensing, and multiplexed data acquisition.<br>2. Delta-Sigma ADC: Uses oversampling (running at 64x to 512x the signal frequency), 1-bit or multi-bit delta-sigma modulation, and high-order digital decimation filtering to push quantization noise out of the audio/measurement band (noise shaping). Achieves ultra-high resolution (16 to 32 bits) with exceptional linearity and built-in anti-aliasing. However, digital decimation introduces group delay/latency and sample rates are slower (< 100 kSPS).",
         "Use SAR ADCs when you need low latency in real-time control; use Delta-Sigma for high-precision weigh scales, temperature measurements (thermocouples), and audio."),
    ]
    
    for item in data:
        qid, sub, diff, comp, q, c, t, tip = item
        qs[qid] = {
            "cat": "Technical",
            "track": "core",
            "sub": sub,
            "diff": diff,
            "company": comp,
            "q": q,
            "a": make_tech_ans(c, t, tip)
        }
    return qs
