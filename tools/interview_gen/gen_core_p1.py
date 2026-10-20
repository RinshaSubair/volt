# tools/interview_gen/gen_core.py
# Generates 100 Placement-Grade Core Engineering Interview Questions (iv-core-101 to iv-core-200)

import json
from .common import make_tech_ans

def get_core_questions():
    qs = {}
    
    # 1. POWER ELECTRONICS & DRIVES (Questions 101 to 120)
    pe_data = [
        ("iv-core-101", "Power Electronics & Drives", "Intermediate", "Texas Instruments",
         "Why is a bootstrap circuit commonly used in high-side N-channel MOSFET gate drivers, and what happens at 100% duty cycle?",
         "An N-channel MOSFET requires its gate voltage to be 10-15V higher than its SOURCE (Vgs > Vth). Because the high-side source floats between 0V and Vbus, a floating supply is required.",
         "A bootstrap diode charges an external bootstrap capacitor to Vcc when the low-side switch is ON and the phase node is at ground. When the high-side turns ON, the capacitor floats up with the phase node, delivering gate charge via the driver. At 100% duty cycle, the low-side never turns on, preventing capacitor recharge; the bootstrap capacitor discharges through leakage current, causing Vgs to drop below undervoltage lockout (UVLO) and shutting the switch off.",
         "Always mention the 100% duty cycle limitation. In continuous ON applications, designers use a charge pump or an isolated DC-DC converter instead of simple bootstrap diodes."),
        
        ("iv-core-102", "Power Electronics & Drives", "Advanced", "Infineon",
         "Compare Silicon (Si), Silicon Carbide (SiC), and Gallium Nitride (GaN) power semiconductors in terms of bandgap, electron mobility, and switching frequency limits.",
         "Wide bandgap (WBG) semiconductors like SiC (3.2 eV) and GaN (3.4 eV) have a breakdown electric field ~10x higher than Silicon (1.1 eV), allowing much thinner drift regions for the same voltage rating, dramatically cutting Rds(on) and parasitic capacitance.",
         "SiC is dominant in high-voltage, high-power regimes (650V-1700V+), such as EV traction inverters and solar central inverters, because of its superior thermal conductivity (4.9 W/m-K vs 1.5 for Si). GaN features high electron mobility in its 2D electron gas (2DEG) channel, enabling multi-megahertz switching with near-zero reverse recovery charge (Qrr), making it ideal for compact 65W-240W chargers, telecom power supplies, and LiDAR.",
         "Highlight reverse recovery losses: GaN has no intrinsic body diode so Qrr is practically zero, whereas Si MOSFETs suffer severe reverse recovery energy loss in hard-switched half bridges."),

        ("iv-core-103", "Power Electronics & Drives", "Intermediate", "Schneider Electric",
         "Why does a flyback converter require an air gap in its magnetic core, whereas an ideal forward converter transformer does not?",
         "A flyback 'transformer' is actually a coupled inductor that stores energy during the switch ON-time and releases it during the OFF-time. An ideal forward converter transformer transfers energy instantaneously and stores zero net energy.",
         "Without an air gap, the high magnetic permeability of ferrite cores leads to rapid saturation under unidirectional DC bias: B = (mu * N * I) / lm. Introducing a physical air gap sharply increases the magnetic reluctance (R = lg / (mu_0 * A)), lowering effective permeability so the core can store large magnetic energy (W = 1/2 * B^2 / mu_0 * Volume_gap) without the flux density exceeding Bsat (~0.35-0.4 Tesla).",
         "Mention that 90%+ of the magnetic energy in a flyback transformer is stored inside the microscopic physical air gap, not the ferrite core material itself."),

        ("iv-core-104", "Power Electronics & Drives", "Intermediate", "Bosch",
         "Explain Field-Oriented Control (FOC) in brushless PM motors and why the Clarke and Park transformations are indispensable.",
         "FOC decouples stator current into two orthogonal components: flux-producing current (Id) along the rotor d-axis and torque-producing current (Iq) along the rotor q-axis, allowing AC motors to be controlled like separately excited DC motors.",
         "1. Clarke Transform converts balanced 3-phase stationary currents (Ia, Ib, Ic) into a 2-phase stationary orthogonal frame (I_alpha, I_beta).<br>2. Park Transform projects the stationary (alpha, beta) vectors onto a rotating coordinate frame synchronized with rotor electrical angle theta: Id = I_alpha*cos(theta) + I_beta*sin(theta); Iq = -I_alpha*sin(theta) + I_beta*cos(theta). By regulating Id = 0 (for non-salient PMSM), maximum torque per ampere (MTPA) is achieved with Iq proportional to mechanical load.",
         "Point out that rotor position theta must be known with high precision via an absolute optical encoder, resolver, or back-EMF sliding mode observer in sensorless FOC."),

        ("iv-core-105", "Power Electronics & Drives", "Fresher", "L&T",
         "What is the difference between continuous conduction mode (CCM) and discontinuous conduction mode (DCM) in a Buck converter, and what are their trade-offs?",
         "In CCM, inductor current never falls to zero during a switching period. In DCM, the inductor current discharges completely to zero and dwells there before the next clock cycle begins.",
         "CCM features lower peak inductor currents, lower output voltage ripple, and a transfer function Vout = D * Vin independent of load. However, the inductor must be larger and the right-half-plane (RHP) zero in boost/buck-boost complicates compensation. DCM requires a much smaller inductor and eliminates diode reverse recovery loss, but causes high RMS currents and load-dependent output voltage.",
         "Interview trap: In a buck converter under DCM, the voltage conversion ratio is NOT simply D; it depends directly on switching frequency, inductance, and output load resistance R."),

        ("iv-core-106", "Power Electronics & Drives", "Advanced", "ABB",
         "Why is Space Vector PWM (SVPWM) preferred over Sinusoidal PWM (SPWM) in 3-phase voltage source inverters (VSI)?",
         "SVPWM optimizes DC bus voltage utilization by 15.47% (2/sqrt(3) factor) compared to basic SPWM, while reducing output harmonic distortion and switching losses.",
         "SPWM produces a maximum fundamental peak line-to-line voltage of 0.866 * Vdc without overmodulation. SVPWM intrinsically injects optimal zero-sequence 3rd harmonic components by distributing zero vectors (V0 and V7) across each switching sector. This flattens the crest of the modulation waveform, allowing modulation index up to 1.0 (fundamental peak = Vdc / sqrt(3) = 0.577 Vdc phase peak, or line-to-line peak of Vdc).",
         "Mention that SVPWM also reduces switching losses by ensuring that only one inverter leg switches state at each sub-interval transition."),

        ("iv-core-107", "Power Electronics & Drives", "Intermediate", "Delta Electronics",
         "How does an RC snubber circuit suppress transient voltage spikes across a switching MOSFET?",
         "When a MOSFET turns OFF rapidly, the high di/dt across unavoidable parasitic circuit loop inductance (L_par) generates an inductive voltage surge: V = L_par * (di/dt), which can exceed MOSFET breakdown voltage V(BR)DSS.",
         "An RC snubber placed across the Drain and Source provides an alternate low-impedance capacitive path for current during turn-off, clamping di/dt and transferring the inductive energy 1/2*L*I^2 into capacitor C_snubber. The series resistor R_snubber dampens high-frequency parasitic LC ringing (Q = R / (2*omega*L)) to prevent repetitive voltage overstress.",
         "Snubber dissipation P_snub = C_snub * V^2 * f_sw increases with switching frequency. In high-efficiency designs, active clamp or resonant soft-switching (ZVS/ZCS) is preferred over dissipative passive snubbers."),

        ("iv-core-108", "Power Electronics & Drives", "Intermediate", "Siemens",
         "Explain the working of an Active Front End (AFE) regenerative converter and how it achieves near-unity power factor.",
         "An AFE replaces the conventional passive diode bridge rectifier on a VFD with an IGBT/SiC-based active PWM converter, enabling bidirectional power flow and clean sinusoidal grid currents.",
         "By switching the active bridge using VOC (Voltage Oriented Control) or DPC (Direct Power Control) against a line reactor (L), the AFE can synthesize a voltage vector whose phase and magnitude relative to the grid voltage control active (P) and reactive (Q) power independently. When the motor decelerates, regenerated mechanical energy is fed back into the 3-phase AC grid instead of being burned in a braking resistor.",
         "AFEs keep total harmonic current distortion (THDi) under 5%, easily meeting IEEE 519 standards without requiring passive multi-pulse phase-shifting transformers."),

        ("iv-core-109", "Power Electronics & Drives", "Fresher", "Schneider Electric",
         "What is dv/dt induced false turn-on (Miller effect) in half-bridge converters, and how is it prevented?",
         "When the complementary switch turns ON rapidly, the phase node experiences a steep voltage rise (+dv/dt). This charges the Miller capacitance (Cgd) of the low-side switch, injecting a displacement current into its gate.",
         "Displacement current I = Cgd * (dv/dt) flows through the internal gate resistance and external pull-down resistor to ground. If the resulting voltage drop V_gate = I * R_gate exceeds the MOSFET's threshold voltage Vth (especially at high temperature where Vth drops), both upper and lower switches conduct simultaneously, causing a catastrophic DC-bus short-circuit shoot-through.",
         "Solutions: 1. Negative gate bias (-2V to -5V during OFF state). 2. Dedicated active Miller clamp pin on the gate driver IC. 3. Selecting devices with low Cgd/Cgs ratio."),

        ("iv-core-110", "Power Electronics & Drives", "Advanced", "Tesla",
         "What is the difference between Trailing-Edge and Leading-Edge Modulation in multiphase DC-DC buck regulators?",
         "Trailing-edge modulation turns switches ON on a fixed clock edge and turns them OFF when the error ramp crosses the threshold. Leading-edge modulation turns switches OFF on a clock edge and turns them ON when the ramp crosses.",
         "In modern high-performance microprocessors (CPUs/GPUs), load current steps from 10A to 200A occur in nanoseconds. In trailing-edge modulation, if a sudden load transient occurs right after turn-off, the converter must wait until the next clock cycle to respond, leading to large output voltage droop. Leading-edge or constant on-time (COT) architectures turn on the high-side switch instantaneously upon detecting output voltage drop, yielding superior transient response.",
         "Interleaving multiple phases by 360/N degrees also multiplies the effective output ripple frequency by N and cancels input ripple currents, reducing required bulk ceramic capacitor count."),

        ("iv-core-111", "Power Electronics & Drives", "Fresher", "ABB",
         "Why does an induction motor draw 5 to 7 times its rated current during Direct-On-Line (DOL) starting?",
         "At standstill (speed = 0), the rotor slip is s = 1.0. The motor equivalent circuit resembles a short-circuited transformer secondary with zero counter-electromotive force (back-EMF).",
         "The rotor impedance at s = 1 is very low, dominated primarily by leakage reactances (X1 + X2'). Because no back-EMF opposes the applied stator voltage, the initial current is bounded solely by the small winding resistances and leakage reactances: I_start = V_phase / sqrt((R1 + R2')^2 + (X1 + X2')^2). As the rotor accelerates, slip drops toward 0.02-0.05, raising the effective rotor resistance R2'/s, which limits the current to normal full-load values.",
         "DOL starting causes severe grid voltage sags and intense thermal/mechanical stress on stator coils. Star-Delta, auto-transformer, soft-starters, or VFDs are mandatory for motors > 5-10 kW."),

        ("iv-core-112", "Power Electronics & Drives", "Intermediate", "Tata Motors",
         "How does Flux Weakening allow a Permanent Magnet Synchronous Motor (PMSM) to operate above its rated base speed?",
         "At base speed, the motor's generated back-EMF (E = omega * psi_m) reaches the maximum AC voltage the inverter can supply from the available DC bus.",
         "To spin faster without exceeding inverter voltage limits (V_max = Vdc / sqrt(3)), the net airgap magnetic flux must be reduced. In PMSMs where permanent magnets produce fixed flux, an intentional negative d-axis demagnetizing stator current (-Id) is commanded into the stator. This counteracts the permanent magnet flux: Net Flux = psi_m - Ld * |Id|. The motor enters the constant-power region, trading torque for higher rotational speed up to mechanical limits.",
         "Crucial trade-off: Excessive -Id risks permanent thermal demagnetization of NdFeB magnets, and inverter efficiency drops due to higher circulating currents."),

        ("iv-core-113", "Power Electronics & Drives", "Intermediate", "Danfoss",
         "Why are Common-Mode Chokes and dV/dt filters necessary between a VFD and an AC induction motor when using long motor cables?",
         "VFDs switch at fast rise times (tr < 50-100 ns). Over long motor cables (> 20 meters), high-frequency transmission line reflections occur because cable surge impedance (~75-100 ohms) mismatches motor input impedance (several kilo-ohms).",
         "The reflected traveling wave doubles the peak voltage at motor terminals (up to 2-2.5x Vdc), causing dielectric puncture of the inter-turn stator insulation. Furthermore, high dV/dt couples capacitively across the stator-rotor airgap, creating bearing currents (EDM currents) that pit and gall motor ball bearings. dV/dt filters and common-mode chokes slow down the edge rise time and attenuate high-frequency circulating ground currents.",
         "Mention insulated bearings (ceramic or hybrid) on the non-drive end as a standard mechanical defense against inverter-induced bearing fluting."),

        ("iv-core-114", "Power Electronics & Drives", "Intermediate", "Texas Instruments",
         "Explain Synchronous Rectification in low-voltage buck converters and calculate efficiency gain over a Schottky diode.",
         "Synchronous rectification replaces the passive freewheeling diode with a low-resistance N-channel power MOSFET that is driven synchronously during the inductor freewheeling phase.",
         "Consider a 12V to 1.2V buck converter delivering 20A. With a Schottky diode having forward drop Vf = 0.5V, conduction power loss during the (1 - D) = 90% duty cycle is P_diode = 0.9 * 20A * 0.5V = 9.0 Watts. With a synchronous MOSFET of Rds(on) = 3 mOhm, conduction loss is P_sync = 0.9 * (20A)^2 * 0.003 Ohm = 1.08 Watts. The power saved is ~7.92 Watts, lifting efficiency from ~72% to ~93% on the 24W output rail.",
         "Dead-time management is vital: both switches must never be ON together (shoot-through), but excessive dead-time lets the parasitic body diode conduct, wasting power through Qrr."),

        ("iv-core-115", "Power Electronics & Drives", "Advanced", "Eaton",
         "What is the Right Half Plane (RHP) zero in Boost and Buck-Boost converters, and why does it constrain loop bandwidth?",
         "An RHP zero in the small-signal control-to-output transfer function provides a 20 dB/decade gain boost like a normal zero, but introduces a 90-degree phase LAG instead of phase lead.",
         "Physically, when the duty cycle D increases to raise output voltage, the switch ON-time lengthens, momentarily DECREASING the time the inductor connects to the output capacitor. Before the inductor current has time to ramp up, output voltage initially DROPS. This non-minimum-phase response forces designers to cap control loop crossover frequency well below the RHP zero frequency: f_cross < (1/3 to 1/5) * f_RHP, where f_RHP = (R_load * (1 - D)^2) / (2 * pi * L).",
         "A buck converter does not have an RHP zero because its inductor is connected continuously to the output node regardless of switch state."),

        ("iv-core-116", "Power Electronics & Drives", "Fresher", "Siemens",
         "Why does a 3-phase induction motor run at slightly less than synchronous speed, and what happens if it runs at exact synchronous speed?",
         "An induction motor relies fundamentally on electromagnetic induction (Faraday's Law). Voltage and current can only be induced in the rotor conductors if there is relative motion between the rotating stator magnetic field (RMF) and the physical rotor.",
         "If the rotor were to spin at synchronous speed (Ns = 120f / P), the relative velocity between rotor conductors and the RMF would become zero. Consequently, zero flux is cut, zero rotor EMF is induced, zero rotor current flows, and electromagnetic torque collapses to zero. Friction and windage immediately decelerate the rotor until sufficient slip (s = (Ns - N)/Ns) is established to produce balancing torque.",
         "If an external prime mover forces the rotor above synchronous speed (N > Ns), slip becomes negative and the machine operates as an induction generator, delivering electrical power back to the grid."),

        ("iv-core-117", "Power Electronics & Drives", "Intermediate", "Schneider Electric",
         "Explain the operation of a Phase-Locked Loop (PLL) in grid-tied solar inverters under unbalanced grid conditions.",
         "A grid-tied inverter must inject AC current perfectly in-phase with the fundamental positive-sequence grid voltage vector to maintain unity power factor.",
         "In a conventional synchronous reference frame PLL (SRF-PLL), grid voltages are transformed via Clarke and Park transforms into the rotating dq frame. The loop filters the q-axis voltage to zero to track grid phase angle theta. Under grid faults or unbalanced loads, negative-sequence voltages appear as double-frequency (2*omega = 100 Hz) ripples in the dq frame, causing phase error oscillations. Advanced inverters use Decoupled Double Synchronous Reference Frame PLL (DDSRF-PLL) or Dual Second-Order Generalized Integrator (DSOGI-PLL) to isolate and track the positive-sequence component.",
         "Failing to filter negative-sequence components causes the inverter to inject harmonic currents and potentially trip on false islanding protection."),

        ("iv-core-118", "Power Electronics & Drives", "Advanced", "Alstom",
         "What is the difference between Vector Control (FOC) and Direct Torque Control (DTC) in high-power electric drives?",
         "FOC controls torque and flux through coordinate transformations and current-loop PI controllers driving a PWM modulator. DTC controls torque and stator flux magnitude directly using hysteresis comparators and an optimal switching lookup table without current loops or PWM modulators.",
         "DTC computes stator flux and electromagnetic torque estimates directly from measured stator voltages and currents. Two hysteresis controllers evaluate torque and flux errors, and a switching table selects the optimal inverter voltage vector every few microseconds. DTC provides ultra-fast torque response (< 2 ms) and eliminates coordinate transformations, but causes variable switching frequency and higher torque/flux ripple compared to FOC.",
         "Modern FOC with SVPWM is preferred when audible noise, switching frequency consistency, and low-speed torque smoothness are critical; DTC is prized in heavy traction and marine drives."),

        ("iv-core-119", "Power Electronics & Drives", "Intermediate", "Texas Instruments",
         "Why does a Current-Mode controlled DC-DC converter require Slope Compensation above 50% duty cycle?",
         "Peak current-mode control uses inductor peak current to terminate the PWM pulse. When duty cycle D exceeds 0.5 in continuous conduction mode, the control loop becomes inherently unstable due to subharmonic oscillation.",
         "A small disturbance Delta_I in inductor current propagates from cycle to cycle with an error factor equal to -m2 / m1 (where m1 is the rising slope and m2 is the falling slope). For D > 0.5, m2 > m1, meaning the disturbance grows exponentially in amplitude at half the switching frequency (f_sw / 2). Adding an artificial negative ramp (slope compensation slope m_comp >= 0.5 * m2) to the current sense signal stabilizes the loop by ensuring the net error attenuation factor remains strictly less than unity.",
         "Interview tip: Adding slope compensation equal to 100% of the inductor down-slope (m_comp = m2) eliminates deadbeat perturbation in exactly one clock cycle."),

        ("iv-core-120", "Power Electronics & Drives", "Fresher", "L&T",
         "Explain why an IGBT is preferred over a Power MOSFET in high-voltage (> 600V) high-power applications.",
         "A Power MOSFET's on-state resistance Rds(on) scales with breakdown voltage to the power of ~2.5 (Rds(on) propto V_B^2.5) because the drift region must be made thick and lightly doped to sustain high voltage, causing massive conduction losses.",
         "An IGBT (Insulated Gate Bipolar Transistor) combines a MOS gate input with a bipolar junction transistor (BJT) output. In the on-state, minority carriers (holes) are injected from the p+ substrate into the lightly doped n- drift region. This 'conductivity modulation' floods the drift region with charge carriers, collapsing its effective resistance by orders of magnitude and giving the IGBT a low, forward-diode-like saturation voltage drop (Vce(sat) ~ 1.5V - 2.5V) regardless of high current.",
         "Trade-off: Minority carriers must recombine when the IGBT turns off, producing a 'current tail' that causes turn-off switching losses and limits switching frequencies to < 20-50 kHz."),
    ]
    
    for item in pe_data:
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
