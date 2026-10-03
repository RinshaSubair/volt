# Volt — EEE Master Platform

Volt is a comprehensive, browser-based Electrical & Electronics Engineering (EEE) learning and mastery platform. It features interactive single-page application modules, KaTeX-rendered mathematical rigor, circuit & system visualizations, practice MCQs, and complete syllabus alignment from semester 3 to semester 8 alongside quantitative aptitude preparation.

## Core Features
- **Comprehensive Curriculum**: 623 interactive engineering lessons covering core and elective EEE domains.
- **Mathematical Precision**: KaTeX-powered equation rendering with display-mode formulas and worked numerical examples.
- **Interactive Visualizations**: Embedded SVG diagrams, circuit schematics, and system architectures.
- **Assessment & Practice**: Integrated multiple-choice question banks with step-by-step solutions.
- **Single-File Architecture**: Self-contained client application in `eee-platform.html` requiring zero complex setup.

## Getting Started
To run the platform locally:
1. Clone the repository:
   ```bash
   git clone https://github.com/RinshaSubair/volt.git
   ```
2. Open `eee-platform.html` in any modern web browser (Edge, Chrome, Firefox).

## Project Structure
```
Volt/
├── eee-platform.html                 # Main application entry point
├── programming_questions_bank.js     # Question bank script loaded by eee-platform.html
├── syllabus_topics.json              # Topic definitions and syllabus mapping
├── favicon.ico                       # Platform favicon
├── volt_tests.py                     # Main test and validation suite
├── VOLT_MASTER_SPEC.md               # Product architecture & continuation specifications
├── README.md                         # Platform documentation
├── .gitignore                        # Git ignore rules
│
├── docs/                             # Documentation & curriculum PDFs (local only, git-ignored)
│   ├── STATUS.md                     # Development status and history
│   ├── TODO.md                       # Task tracker
│   ├── RELEASE_BASELINE.md           # Platform release baseline notes
│   ├── EQUATION_VISUAL_FORENSIC_AUDIT.md # Formula and visual audit logs
│   ├── QUANT APT.pdf                 # Quantitative Aptitude syllabus reference
│   └── Syllabus EEE 2023 S3-S8.pdf   # KTU EEE Syllabus reference
│
├── data/                             # Lesson data, topic mappings, and audit results
│   ├── all_623_lessons.json          # Lesson dataset
│   ├── all_623_visuals_data.json     # Visual assets and diagram data
│   ├── category_c_mapped_369.json    # Category mapping dataset
│   ├── exact_audit_623.json          # Verification audit results
│   └── ...                           # Forensic audit and topic metadata
│
├── tools/                            # Development, audit, repair, and test scripts
│   ├── audit_visuals.py              # Visual inspection utilities
│   ├── eliminate_all_katex_errors.py # Math formula sanitization tools
│   ├── verify_backslash_fix.py       # Syntax and LaTeX verification tools
│   └── ...                           # Maintenance and diagnostic helpers
│
└── backups/                          # Archive directory (git-ignored)
    ├── *.zip                         # Snapshot archives
    ├── *.bak*                        # File backups
    ├── logs/                         # Historical test outputs and audit logs
    └── temp/                         # Temporary scratch and test build artifacts
```
