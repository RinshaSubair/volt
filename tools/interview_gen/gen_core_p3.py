# tools/interview_gen/gen_core_p3.py
# Electrical Machines & Transformers (iv-core-141 to iv-core-160)

from .common import make_tech_ans

def get_core_p3():
    qs = {}
    data = [
        ("iv-core-141", "Electrical Machines", "Fresher", "BHEL",
         "What are the mandatory conditions for the parallel operation of two 3-phase transformers, and what happens if their percentage impedances mismatch?",
         "Parallel operation allows transformers to share load proportional to their kVA ratings. Mandatory conditions: identical voltage ratio, same polarity, identical phase sequence, and identical phase angle shift (same vector group, e.g., Dyn11 with Dyn11).",
         "If percentage impedances (%Z) are unequal, the load shared by each transformer is inversely proportional to its per-unit impedance: S_A = S_total * (Z_B / (Z_A + Z_B)). The transformer with the smaller %Z will draw a disproportionately large share of the total load and will reach its thermal overload limit first, while the higher %Z unit remains underloaded. Furthermore, if X/R ratios differ, a circulating current flows between secondary windings even at no-load, causing unnecessary I^2*R copper heating.",
         "Most critical condition: Never parallel transformers with different vector group phase shifts (e.g., Dyn11 [30 deg lead] with Dyn1 [30 deg lag])—this creates a phase difference of 60 degrees, driving short-circuit circulating currents that will trip or destroy windings."),

        ("iv-core-142", "Electrical Machines", "Intermediate", "Schneider Electric",
         "Why is a Delta-connected Tertiary Winding added to large Star-Star (Y-Y) power transformers?",
         "A Star-Star transformer without neutral return cannot provide a path for 3rd harmonic magnetizing currents, distorting phase voltages into peaked waveforms and shifting the neutral point.",
         "Third harmonic currents (150 Hz) are in-phase zero-sequence components. In an isolated Y-Y connection, 3rd harmonics cannot flow; as a result, the magnetic flux becomes flat-topped, inducing large 3rd harmonic voltages in each phase that overstress insulation and cause severe telephone communication interference.<br>Adding a closed, unloaded delta tertiary winding provides a low-impedance circulating loop for 3rd harmonic magnetizing currents. This restores sinusoidal core flux, stabilizes the neutral point, and provides a low-impedance zero-sequence path to operate ground-fault relays during unbalanced earth faults.",
         "Tertiary windings can also be rated to supply auxiliary substation loads (fans, pumps, station lighting) or static VAR compensators."),

        ("iv-core-143", "Electrical Machines", "Fresher", "Siemens",
         "Explain the Open-Delta (V-V) transformer connection and calculate its available capacity relative to the original Delta-Delta bank.",
         "If one single-phase transformer in a 3-phase Delta-Delta bank fails or is removed for maintenance, the remaining two transformers can continue delivering 3-phase balanced power in an Open-Delta (V-V) configuration.",
         "In a closed Delta-Delta bank of three identical units each rated S, total capacity is S_total = 3 * S. In the Open-Delta connection, the line current I_line is limited to the single transformer's rated phase current I_ph: Total V-V Capacity = sqrt(3) * V_line * I_line = sqrt(3) * V_ph * I_ph = sqrt(3) * S = 1.732 * S. The ratio of V-V capacity to original 3-phase capacity is: (sqrt(3) * S) / (3 * S) = 1 / sqrt(3) = 57.7%. Furthermore, each remaining transformer operates at a power factor of cos(theta +/- 30 deg), utilizing only 86.6% of its own combined rating (1.732 / 2 = 0.866).",
         "Open-Delta is widely used in rural substations where initial load is small, with provision to install the third unit later as demand grows."),

        ("iv-core-144", "Electrical Machines", "Intermediate", "L&T",
         "Explain Armature Reaction in a DC machine and how Compensating Windings eliminate Cross-Magnetizing distortion.",
         "Armature reaction is the distortion and demagnetization of the main pole magnetic field caused by the magnetic field produced by armature current flowing through rotor conductors.",
         "Armature reaction has two effects:<br>1. Demagnetizing effect: Core saturation weakens the net field flux, causing a slight drop in generated voltage or increase in motor speed.<br>2. Cross-magnetizing effect: Flux shifts toward the trailing pole tip in generators (leading tip in motors), distorting flux density under pole shoes and shifting the Magnetic Neutral Axis (MNA). Under heavy loads, the high peak flux density at pole tips induces excessive voltage between adjacent commutator segments, sparking and causing commutator flashover.<br>Compensating windings embedded in slots in the main pole faces carry armature current in the REVERSE direction, creating an MMF that directly cancels the armature cross-magnetizing MMF across the entire pole arc.",
         "Inter-poles (commutating poles) neutralize armature MMF specifically in the interpolar zone to ensure sparkless commutation; compensating windings neutralize distortion under the main pole faces."),

        ("iv-core-145", "Electrical Machines", "Fresher", "ABB",
         "What are Synchronous Motor V-Curves and Inverted V-Curves, and how does a Synchronous Condenser operate?",
         "V-Curves plot Armature Current (Ia) versus Field Current (If) at constant mechanical shaft load. Inverted V-Curves plot Power Factor (cos phi) versus Field Current (If).",
         "At normal excitation, the motor operates at unity power factor with minimum armature current (bottom of the V-curve).<br>When UNDER-EXCITED (If low), back-EMF is less than terminal voltage; the motor draws lagging reactive power from the grid, behaving like an inductor.<br>When OVER-EXCITED (If high), back-EMF exceeds terminal voltage; the motor draws LEADING reactive power, behaving like a capacitor.<br>A Synchronous Condenser is an over-excited synchronous motor operated at no mechanical shaft load. It supplies adjustable leading reactive power (VARs) to regulate transmission substation voltage and stabilize grid power factor.",
         "Unlike static capacitor banks whose VAR output drops with the square of voltage (V^2), a synchronous condenser provides dynamic reactive support and provides physical rotational inertia (H-constant) to the grid."),

        ("iv-core-146", "Electrical Machines", "Intermediate", "General Electric",
         "What is Hunting in Synchronous Machines and how do Damper (Amortisseur) Windings suppress it?",
         "Hunting is the electromechanical low-frequency oscillation of the rotor magnetic poles about its steady-state synchronous equilibrium position following a sudden load change or electrical fault.",
         "When load increases suddenly, the rotor decelerates momentarily and the torque angle delta increases. When delta reaches the new equilibrium, rotor inertia carries it past the angle (overshoot). The restoring synchronizing torque pulls it back, creating sustained mechanical oscillations governed by the machine's natural frequency.<br>Damper (Amortisseur) windings consist of heavy copper or aluminum bars embedded in the pole shoe faces and short-circuited by end rings. During synchronous steady-state, rotor and stator fields spin at the same speed (zero relative velocity), so zero voltage is induced in damper bars. During hunting oscillations, relative motion occurs, inducing large currents in the damper bars. By Lenz's law, these induced currents produce damping torque that snuffs out the oscillations in both generator and motor modes.",
         "Damper windings also serve a second crucial function: providing starting torque as an induction motor to accelerate synchronous motors up to near-synchronous speed before field excitation is applied."),

        ("iv-core-147", "Electrical Machines", "Advanced", "Alstom",
         "Explain Two-Reaction Theory for Salient-Pole Synchronous Machines and distinguish Direct-axis (Xd) from Quadrature-axis (Xq) reactance.",
         "Cylindrical rotor machines have a uniform air gap, so stator MMF encounters constant magnetic reluctance in all directions. Salient-pole machines have non-uniform air gaps, causing stator reactance to depend strongly on rotor position.",
         "Two-Reaction Theory (Blondel) resolves the armature current into two orthogonal components:<br>1. Direct-axis component (Id): aligned with the physical pole axis where the air gap is minimal, reluctance is lowest, and permeance is highest. Consequently, Direct-axis synchronous reactance Xd is large.<br>2. Quadrature-axis component (Iq): aligned with the inter-polar interpolar space where the air gap is large, reluctance is high, and permeance is lowest. Consequently, Quadrature-axis synchronous reactance Xq is significantly smaller (Xq < Xd, typically Xq approx 0.6 to 0.7 * Xd).<br>Salient-pole machines generate Reluctance Torque proportional to sin(2*delta) * (1/Xq - 1/Xd), allowing them to deliver significant power even with zero field excitation.",
         "Interview tip: Cylindrical rotor machines have Xd = Xq, so reluctance torque is zero. Salient pole machines have Xd > Xq, giving superior synchronizing torque stability at large load angles."),

        ("iv-core-148", "Electrical Machines", "Fresher", "BHEL",
         "What is the difference between Cogging and Crawling in 3-phase Squirrel-Cage Induction Motors?",
         "Both are undesirable parasitic phenomena caused by space harmonics in the air-gap magnetic flux distribution.",
         "1. Crawling: Stator windings produce space harmonics (3rd, 5th, 7th, 11th...). The 7th harmonic field rotates forward at 1/7th synchronous speed (Ns/7), producing a local positive harmonic torque peak. If this harmonic torque combines with high load torque, the motor gets 'stuck' and crawls stably at slightly below Ns/7, drawing heavy currents and overheating.<br>2. Cogging (Magnetic Locking): Occurs at standstill when the number of stator slots (S1) equals or is an exact multiple of rotor slots (S2). When teeth face each other directly, magnetic reluctance is at a sharp minimum. The magnetic attraction locks the rotor in place, and the motor refuses to start regardless of full applied voltage.",
         "Solutions: Skewing rotor slots by one tooth pitch smooths reluctance variation and eliminates cogging; selecting proper slot number combinations (S1 - S2 != 0, +/-1, +/-2) prevents crawling and locking."),

        ("iv-core-149", "Electrical Machines", "Intermediate", "ABB",
         "How do Double Squirrel-Cage and Deep-Bar rotors utilize Skin Effect to achieve high starting torque with low starting current?",
         "A standard squirrel-cage motor with low rotor resistance has low starting torque (T_start propto R2) and huge starting current. High-resistance rotors boost starting torque but suffer terrible full-load efficiency and high slip.",
         "Deep-bar and double-cage rotors solve this trade-off using frequency-dependent skin effect:<br>At standstill (starting), rotor frequency is high (f_rotor = s * f = 1.0 * 50 Hz = 50 Hz). The lower bar (or bottom of deep bar) is surrounded by iron core on three sides, giving it high leakage inductance and high inductive reactance (X_L = 2*pi*f*L). The current is forced by impedance into the outer, high-resistance bar, producing high starting torque with limited starting current.<br>As the motor accelerates to normal operating speed (slip drops to 0.02-0.04), rotor frequency drops to 1-2 Hz. Inductive reactance becomes negligible, and current distributes uniformly into the low-resistance inner bar, providing excellent running efficiency (< 2% slip).",
         "This design achieves Class C and Class D motor characteristics without needing external wound-rotor slip rings or resistors."),

        ("iv-core-150", "Electrical Machines", "Intermediate", "Danfoss",
         "Explain Volts-per-Hertz (V/f) speed control in 3-phase induction motors and why voltage boost is required at very low frequencies.",
         "The air-gap magnetic flux in an AC machine is proportional to stator voltage divided by frequency: Phi propto V / f.",
         "To maintain constant maximum breakdown torque across varying speeds, the airgap flux must remain constant at its rated saturation level. As inverter output frequency f is decreased to slow the motor down, the terminal voltage V must be scaled down in exact linear proportion to prevent core magnetic saturation (which causes huge magnetizing currents, overheating, and tripping).<br>However, at very low frequencies (< 5-10 Hz), the applied voltage V becomes very small and comparable to the stator winding IR resistance drop. The actual internal EMF E = V - I*Rs drops drastically, causing flux Phi = E / f to collapse. To restore full starting torque, a 'voltage boost' (offsetting V slightly above zero at 0 Hz) is added to overcome stator resistance drop.",
         "Above rated base frequency (f > 50 Hz), voltage cannot exceed inverter DC-bus supply rating. The motor enters the Field Weakening (constant power) zone where V stays constant and flux collapses inversely with f."),

        ("iv-core-151", "Electrical Machines", "Intermediate", "Bosch",
         "Compare Brushless DC (BLDC) motors with Permanent Magnet Synchronous Motors (PMSM) in terms of back-EMF, winding distribution, and drive control.",
         "Both are electronically commutated synchronous motors with permanent magnet rotors, but their electromagnetic design and control architectures differ fundamentally.",
         "1. BLDC Motor: Stator has concentrated windings, producing a trapezoidal back-EMF waveform. It is commutated using simple 6-step block commutation ('trapezoidal control') where only two inverter phases conduct at any given instant, monitored by 3 Hall sensors spaced at 120 or 60 degrees. Simple, inexpensive microcontroller hardware is sufficient.<br>2. PMSM: Stator has sinusoidally distributed distributed windings, producing a pure sinusoidal back-EMF waveform. It is driven by continuous 3-phase sinusoidal currents using Field-Oriented Control (FOC) or SVPWM with high-resolution encoders or resolvers. PMSM eliminates the 15-20% torque ripple inherent to 6-step BLDC commutation, providing ultra-quiet, ripple-free motion for EV drivetrains and robotics.",
         "Summary rule of thumb: BLDC = Trapezoidal back-EMF + 6-step rectangular drive; PMSM = Sinusoidal back-EMF + FOC sinusoidal drive."),

        ("iv-core-152", "Electrical Machines", "Advanced", "Tesla",
         "What are Switched Reluctance Motors (SRM), how do they generate torque, and what are their primary industrial challenges?",
         "An SRM has doubly-salient poles on both stator and rotor, with concentrated coils on stator poles and NO windings, NO permanent magnets, and NO slip rings on the rotor.",
         "Torque is generated by the fundamental magnetic principle of minimum reluctance: the unmagnetized laminated silicon-steel rotor always tries to align itself with the excited stator pole pair to minimize magnetic path reluctance. Electromagnetic torque is T = 1/2 * i^2 * (dL / d_theta). Because torque is proportional to the square of current (i^2), torque direction depends solely on the derivative of inductance with rotor position (dL/d_theta), completely independent of current polarity. SRMs use asymmetric half-bridge inverters with fault-tolerant phase independence.<br>Challenges: 1. Extreme acoustic noise and vibration caused by high radial magnetic forces. 2. Severe torque ripple at low speeds. 3. Requires precise rotor angle tracking for optimal phase commutation firing angles.",
         "Why SRMs are hot in EV research: 100% free of rare-earth permanent magnets (NdFeB), highly rugged, capable of ultra-high RPM (> 50,000 RPM), and impervious to inverter shoot-through faults."),

        ("iv-core-153", "Electrical Machines", "Fresher", "Schneider Electric",
         "Explain Hysteresis Loss and Eddy Current Loss in electrical transformer cores and how lamination thickness and silicon steel minimize them.",
         "Core losses (iron losses) occur continuously in transformer cores whenever energized, independent of load current.",
         "1. Hysteresis Loss: Energy lost in continuously flipping magnetic dipoles back and forth against atomic friction over alternating AC cycles. Described by Steinmetz's formula: P_h = eta * B_max^1.6 * f * Volume. Minimized by using cold-rolled grain-oriented (CRGO) silicon steel, which has a narrow hysteresis loop and low coercive force.<br>2. Eddy Current Loss: The alternating core flux induces circulating AC eddy currents in the bulk conductive iron core, dissipating heat according to Joule's law: P_e = k_e * B_max^2 * f^2 * t^2 * Volume, where t is lamination thickness. Minimized by: (a) Slicing the core into thin, insulated sheets (laminations of thickness t = 0.23 mm to 0.35 mm) coated with carlite varnish, which restricts eddy current loops; and (b) Adding 3% to 4.5% Silicon to iron, which boosts electrical resistivity 4-fold without hurting magnetic permeability.",
         "Notice that eddy current loss scales quadratically with lamination thickness (t^2) and frequency (f^2). In modern high-frequency converters, amorphous metal or powdered ferrite is used instead of steel laminations."),

        ("iv-core-154", "Electrical Machines", "Intermediate", "Siemens",
         "What is Sumpner's (Back-to-Back) Test on two identical transformers, and why is it superior to open-circuit and short-circuit tests?",
         "Open-circuit (OC) tests measure iron loss under rated voltage but zero load current; Short-circuit (SC) tests measure copper loss under rated current but low voltage. Neither test operates the transformer under rated thermal temperature conditions.",
         "Sumpner's test connects two identical transformers back-to-back: primaries are in parallel across rated voltage supply V1, while secondaries are connected in phase opposition (series opposition).<br>1. Because secondaries oppose each other, net secondary voltage is zero, and the main supply supplies only no-load iron losses and magnetizing current for both units.<br>2. A separate low-voltage auxiliary AC source injects full rated secondary current into the secondary circuit, supplying full-load copper losses.<br>Both transformers operate simultaneously at full rated voltage AND full rated current, allowing an accurate full-load temperature rise heat-run test to be conducted with power consumption limited to just the internal losses (no multi-megawatt load bank needed).",
         "Efficiency can also be determined under any power factor from Sumpner's test data."),

        ("iv-core-155", "Electrical Machines", "Fresher", "Tata Motors",
         "Why is a DC Series Motor never started on no-load?",
         "In a DC series motor, the field winding is connected in series with the armature, so field current equals armature current: I_field = I_armature = I.",
         "Speed is governed by the motor equation: N propto (V - I*Ra) / Phi. Because magnetic flux Phi is proportional to field current (Phi propto I), speed is inversely proportional to armature current: N propto 1 / I. At no-load, the motor draws only a tiny current to overcome mechanical friction. Flux Phi collapses toward near-zero (remanent magnetism only). As the denominator approaches zero, motor speed accelerates violently toward infinity (runaway condition). Centrifugal forces tear armature conductors out of rotor slots, shatter the commutator, and destroy the motor mechanically.",
         "DC series motors must always be solidly coupled via direct gears or splines to their mechanical loads (e.g., railway traction, cranes, hoists); never use flat belt drives that could slip off."),

        ("iv-core-156", "Electrical Machines", "Intermediate", "Texas Instruments",
         "How does Microstepping improve resolution and eliminate resonance in Stepper Motors?",
         "In full-step mode, a 2-phase hybrid stepper motor energizes phases in full on/off square waves (90 degree electrical steps), typically yielding 200 steps/revolution (1.8 degrees/step).",
         "Full-stepping creates abrupt torque pulses that stimulate mechanical rotor-mass spring resonance, causing audible whine, missed steps, and severe low-speed vibration. Microstepping drives the two stator phase windings with two continuous, 90-degree phase-shifted sinusoidal currents (Ia = I_peak * cos(theta), Ib = I_peak * sin(theta)) synthesized by high-frequency PWM DACs. By dividing each full step into 16, 32, 64, or 256 sub-steps, the stator magnetic vector rotates smoothly and continuously in the air gap.",
         "Microstepping eliminates rotor mechanical hunting and yields positioning down to fractions of an arc-minute, though incremental holding torque decreases to sin(90 deg / N) per microstep."),

        ("iv-core-157", "Electrical Machines", "Fresher", "L&T",
         "Compare Capacitor-Start and Capacitor-Run Single-Phase Induction Motors in terms of starting torque, power factor, and centrifugal switch operation.",
         "Single-phase induction motors have zero starting torque because single-phase AC creates a pulsating field rather than a rotating magnetic field. An auxiliary winding with a phase-shifting capacitor is added to create two out-of-phase currents.",
         "1. Capacitor-Start Motor: Uses a high-capacitance electrolytic capacitor (short-time rated, 100-300 uF) in series with the auxiliary winding to create a ~90 degree phase shift, generating high starting torque (250-350% of full load). Once the motor reaches 75% speed, a mechanical centrifugal switch disconnects the auxiliary circuit.<br>2. Capacitor-Run Motor: Uses a lower-capacitance, oil-filled paper/polypropylene capacitor (continuous-rated, 10-30 uF) permanently connected in series with the auxiliary winding with NO centrifugal switch. It produces moderate starting torque (50-100%) but achieves smooth running, near-unity power factor, low acoustic hum, and high full-load efficiency.",
         "Capacitor-start-and-run (two-value capacitor) motors combine both: large electrolytic capacitor for high starting torque, switched out by centrifugal switch, leaving the small run capacitor active permanently."),

        ("iv-core-158", "Electrical Machines", "Intermediate", "Schneider Electric",
         "What is Hopkinson's Test on DC Shunt Machines and what are its primary advantages?",
         "Hopkinson's Test (regenerative back-to-back test) couples two identical DC shunt machines mechanically and connects them in parallel electrically across the DC busbar.",
         "One machine operates as a motor driving the second machine as a generator. The generator output is fed directly back into the motor's electrical supply terminals. The external DC power supply needs to deliver only the total electrical and mechanical losses of both machines (I_net = I_motor - I_gen). By slightly adjusting the generator field rheostat, both machines can be fully loaded to 100% rated capacity without wasting megawatts of power on a resistive load bank.",
         "Advantage: Accurately tests full-load temperature rise and commutation sparking behavior of large DC machines with minimal utility power consumption."),

        ("iv-core-159", "Electrical Machines", "Advanced", "ABB",
         "Explain Transformer Inrush Current: why does it reach up to 10x rated current, and why is the switching angle critical?",
         "When a transformer is energized, Faraday's Law requires core flux to be the integral of applied voltage: Phi(t) = Integral V_peak * sin(omega*t + alpha) dt + Phi_remanent.",
         "If the circuit breaker closes at the voltage crest (alpha = 90 deg), flux starts from zero and reaches normal peak Phi_max sinusoidally: no transient occurs.<br>However, if closed at zero voltage crossing (alpha = 0), the integral of a sine wave is a negative cosine wave: Phi(t) = -Phi_max * cos(omega*t) + Phi_max. Over the first half cycle (at omega*t = pi), core flux reaches a theoretical peak of 2 * Phi_max (flux doubling). If remanent magnetic flux (+Phi_r) is already present in the core from previous de-energization, total peak flux can reach 2.5 to 2.8 * Phi_max. Because transformer cores are designed to saturate at 1.1-1.2 * Phi_max, the core enters deep saturation; its relative permeability collapses from 10,000 to near unity (air), causing the primary winding to draw a massive magnetizing inrush current limited only by air-core leakage reactance.",
         "Point-on-wave (POW) controlled switching relays close circuit breaker poles at optimal phase voltage crests to completely eliminate inrush transients."),

        ("iv-core-160", "Electrical Machines", "Fresher", "Siemens",
         "What is the difference between Salient-Pole and Cylindrical (Non-Salient) Rotors in Synchronous Alternators?",
         "Cylindrical rotors are long, slender, solid forged steel cylinders with distributed field windings, designed for high-speed operation (1500 to 3000 RPM in 50 Hz grids, driven by steam/gas turbines in thermal plants).",
         "Salient-pole rotors feature protruding poles with concentrated field windings, large diameters, and short axial lengths, designed for low-speed operation (100 to 500 RPM, driven by hydraulic turbines in hydroelectric plants).<br>Hydro turbines require many poles (P = 120f / N = 120*50 / 150 = 40 poles) to generate 50 Hz. At high speeds (3000 RPM), salient projecting poles would experience destructive centrifugal shearing forces, whereas smooth cylindrical rotors exhibit minimal air friction windage losses and withstand high centrifugal hoop stresses.",
         "Key electrical difference: Cylindrical rotor has uniform air gap (Xd = Xq); salient pole has non-uniform air gap (Xd > Xq) and produces reluctance torque."),
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
