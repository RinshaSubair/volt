# tools/update_interview_portal.py
# Injects the 1,038 interview questions and modernized pageInterview UI into index.html and eee-platform.html

import json
import re

def update_portal():
    print("Loading data/all_interview_questions.json...")
    with open("data/all_interview_questions.json", "r", encoding="utf-8") as f:
        master_iv = json.load(f)
    print(f"Total master questions: {len(master_iv)}")

    print("Reading index.html...")
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Replace const INTERVIEW = { ... };
    print("Formatting master INTERVIEW JS object...")
    iv_lines = ["/* ---------- INTERVIEW BANK ---------- */", "const INTERVIEW = {"]
    for qid, q in master_iv.items():
        q_json = json.dumps(q, ensure_ascii=False)
        iv_lines.append(f'"{qid}": {q_json},')
    iv_lines.append("};")
    new_interview_js = "\n".join(iv_lines)

    # Locate bounds of const INTERVIEW in index.html
    iv_pattern = re.compile(r'/\* ---------- INTERVIEW BANK ---------- \*/\s*const INTERVIEW = \{.*?\n\};', re.DOTALL)
    if not iv_pattern.search(content):
        # Fallback search without comment
        iv_pattern = re.compile(r'const INTERVIEW = \{.*?\n\};', re.DOTALL)
    
    assert iv_pattern.search(content), "Could not find const INTERVIEW in index.html!"
    content = iv_pattern.sub(lambda _: new_interview_js, content, count=1)
    print("Replaced const INTERVIEW in index.html.")

    # 2. Add / Update CSS styles for interview portal
    css_patch = """
.iv-portal-wrap{margin-top:6px;}
.iv-hero{background:linear-gradient(135deg, rgba(59,130,246,0.08) 0%, rgba(139,92,246,0.06) 100%); border:1px solid var(--border); border-radius:12px; padding:18px 22px; margin-bottom:18px;}
.iv-stats-grid{display:grid; grid-template-columns:repeat(auto-fit, minmax(130px, 1fr)); gap:10px; margin-top:14px;}
.iv-stat-card{background:var(--bg-card); border:1px solid var(--border); border-radius:8px; padding:10px 14px; text-align:center;}
.iv-stat-val{font-size:20px; font-weight:700; color:var(--accent); font-family:var(--font-mono);}
.iv-stat-lbl{font-size:11.5px; color:var(--text-dim); text-transform:uppercase; letter-spacing:.04em; margin-top:2px;}
.iv-tracks-bar{display:flex; gap:8px; flex-wrap:wrap; margin-bottom:14px;}
.iv-track-tab{display:inline-flex; align-items:center; gap:6px; padding:8px 16px; border-radius:8px; font-size:13.5px; font-weight:600; cursor:pointer; border:1px solid var(--border); background:var(--bg-card); color:var(--text); transition:all .2s;}
.iv-track-tab:hover{border-color:var(--accent); color:var(--accent);}
.iv-track-tab.active{background:var(--accent); color:#fff; border-color:var(--accent);}
.iv-controls{background:var(--bg-card); border:1px solid var(--border); border-radius:10px; padding:14px 16px; margin-bottom:16px;}
.iv-sub-pills{display:flex; gap:6px; flex-wrap:wrap; margin-bottom:12px; max-height:120px; overflow-y:auto; padding-bottom:2px;}
.iv-sub-pill{padding:4px 11px; font-size:12px; border-radius:16px; border:1px solid var(--border); background:var(--bg); color:var(--text-dim); cursor:pointer; transition:all .15s; white-space:nowrap;}
.iv-sub-pill:hover{border-color:var(--accent); color:var(--text);}
.iv-sub-pill.active{background:rgba(59,130,246,0.15); color:var(--accent); border-color:var(--accent); font-weight:600;}
.iv-search-row{display:flex; gap:10px; flex-wrap:wrap; align-items:center;}
.iv-search-box{flex:1; min-width:220px; padding:8px 12px; border-radius:6px; border:1px solid var(--border); background:var(--bg); color:var(--text); font-size:13.5px;}
.iv-select{padding:7px 10px; border-radius:6px; border:1px solid var(--border); background:var(--bg); color:var(--text); font-size:13px;}
.iv-action-btn{padding:7px 12px; border-radius:6px; border:1px solid var(--border); background:var(--bg); color:var(--text); font-size:12.5px; cursor:pointer;}
.iv-action-btn:hover{background:var(--accent-dim); color:var(--accent);}
.iv-q{border:1px solid var(--border); border-radius:10px; padding:14px 16px; margin-bottom:12px; background:var(--bg-card); transition:border-color .2s;}
.iv-q:hover{border-color:var(--accent);}
.iv-badges{display:flex; gap:6px; flex-wrap:wrap; margin-bottom:8px; align-items:center;}
.iv-badge{font-size:11px; padding:2px 7px; border-radius:4px; font-weight:600; text-transform:uppercase; letter-spacing:.03em;}
.iv-badge-track{background:rgba(59,130,246,0.12); color:#3b82f6;}
.iv-badge-sub{background:rgba(16,185,129,0.12); color:#10b981;}
.iv-badge-diff{background:rgba(245,158,11,0.12); color:#f59e0b;}
.iv-badge-comp{background:rgba(139,92,246,0.12); color:#8b5cf6;}
.iv-badge-reviewed{background:rgba(16,185,129,0.2); color:var(--ok);}
.iv-q .qt{font-weight:600; font-size:14.5px; cursor:pointer; color:var(--text); line-height:1.45;}
.iv-q .qt:hover{color:var(--accent);}
.iv-q .ans{margin-top:12px; padding-top:12px; border-top:1px solid var(--border); font-size:13.5px; line-height:1.7; color:var(--text-dim);}
.iv-ans-block{display:flex; flex-direction:column; gap:10px; margin-top:6px;}
.iv-lead, .iv-intent{padding:10px 14px; border-radius:6px; background:rgba(59,130,246,0.08); border-left:3px solid #3b82f6;}
.iv-tech, .iv-framework{padding:10px 14px; border-radius:6px; background:rgba(16,185,129,0.08); border-left:3px solid #10b981;}
.iv-model{padding:12px 14px; border-radius:6px; background:rgba(139,92,246,0.08); border-left:3px solid #8b5cf6; font-style:normal;}
.iv-tips, .iv-mistakes{padding:10px 14px; border-radius:6px; background:rgba(239,68,68,0.08); border-left:3px solid #ef4444;}
.iv-legacy-details{margin-top:14px; padding:10px 12px; border:1px dashed var(--border); border-radius:8px; font-size:12.5px;}
.iv-legacy-summary{cursor:pointer; color:var(--text-faint); font-weight:600; display:flex; align-items:center; justify-content:space-between;}
.iv-legacy-pills{display:flex; gap:6px; flex-wrap:wrap; margin-top:10px;}
.iv-legacy-btn{font-size:11.5px; padding:3px 8px;}
"""

    if ".iv-portal-wrap" not in content:
        # Insert after line 333 (.iv-q .ans{...})
        content = content.replace(".iv-q .ans{margin-top:10px; font-size:14px; line-height:1.7; color:var(--text-dim);}",
                                  ".iv-q .ans{margin-top:10px; font-size:14px; line-height:1.7; color:var(--text-dim);}\n" + css_patch)
        print("Inserted CSS styles for interview portal.")
    else:
        print("CSS styles already present.")

    # 3. Replace pageInterview and wireInterviewHandlers
    new_interview_code = """/* ---------- INTERVIEW ---------- */
function pageInterview(cat){
  const allEntries = Object.entries(INTERVIEW);
  const totalCount = allEntries.length;
  const cats = [...new Set(allEntries.map(([_, q]) => q.cat))];
  
  // Track counts
  const trackCounts = {
    core: allEntries.filter(([_, q]) => (q.track || "core") === "core").length,
    software: allEntries.filter(([_, q]) => q.track === "software").length,
    aiml: allEntries.filter(([_, q]) => q.track === "aiml").length,
    logical: allEntries.filter(([_, q]) => q.track === "logical" || q.cat === "Logical").length,
    behavioral: allEntries.filter(([_, q]) => q.track === "behavioral" || q.cat === "Behavioral").length,
  };

  // Determine active filtering
  // If an exact legacy category is passed (e.g. from nav or test runner), filter strictly by that category!
  const isExactCategory = cat && cats.includes(cat);
  const activeCat = isExactCategory ? cat : null;

  // Determine active track: if category matches Logical or Behavioral, map to that track; otherwise if track passed
  let activeTrack = "all";
  if(activeCat === "Logical") activeTrack = "logical";
  else if(activeCat === "Behavioral" || activeCat === "HR/Basic") activeTrack = "behavioral";
  else if(activeCat && (activeCat.includes("Power") || activeCat.includes("Circuit") || activeCat.includes("Control") || activeCat.includes("Embedded") || activeCat.includes("Measurements"))) activeTrack = "core";

  // Filter questions for initial render
  let list;
  if(isExactCategory){
    list = allEntries.filter(([_, q]) => q.cat === activeCat);
  } else if(ROUTE && ROUTE.track && ROUTE.track !== "all"){
    activeTrack = ROUTE.track;
    list = allEntries.filter(([_, q]) => (q.track || "core") === activeTrack);
  } else {
    // Default: show all questions
    list = allEntries;
  }

  // Generate track navigation buttons
  const trackTabs = [
    { id: "all", label: "All Questions", icon: "📚", count: totalCount },
    { id: "core", label: "Core Engineering", icon: "⚡", count: trackCounts.core },
    { id: "software", label: "Software & IT", icon: "💻", count: trackCounts.software },
    { id: "aiml", label: "AI & Machine Learning", icon: "🤖", count: trackCounts.aiml },
    { id: "logical", label: "Logical & Puzzles", icon: "🧠", count: trackCounts.logical },
    { id: "behavioral", label: "Behavioral & HR", icon: "🤝", count: trackCounts.behavioral },
  ].map(t => `<button class="iv-track-tab ${activeTrack===t.id && !isExactCategory ? 'active' : ''}" data-ivtrack="${t.id}">${t.icon} ${t.label} (${t.count})</button>`).join("");

  // Sub-discipline pills for active view
  const subCategories = [...new Set(list.map(([_, q]) => q.sub || q.subj || q.cat).filter(Boolean))];
  const subPills = subCategories.map(s => `<button class="iv-sub-pill" data-ivsub="${encodeURIComponent(s)}">${s}</button>`).join("");



  // Render question cards
  const qs = list.map(([id, q]) => {
    const seen = !!(PROGRESS.interviewSeen && PROGRESS.interviewSeen[id]);
    const trackName = q.track === "core" ? "Core" : q.track === "software" ? "Software" : q.track === "aiml" ? "AI/ML" : q.track === "logical" ? "Puzzle" : "HR";
    const subName = q.sub || q.subj || q.cat || "Engineering";
    const diffName = q.diff || "Placement";
    const compName = q.company || "Top Tier";
    return `
      <div class="iv-q" data-ivid="${id}" data-ivtrack="${q.track || 'core'}" data-ivsub="${(q.sub || q.subj || q.cat || '').toLowerCase()}" data-ivcat="${q.cat || ''}" data-ivdiff="${(q.diff || '').toLowerCase()}">
        <div class="iv-badges">
          <span class="iv-badge iv-badge-track">${trackName}</span>
          <span class="iv-badge iv-badge-sub">${subName}</span>
          <span class="iv-badge iv-badge-diff">${diffName}</span>
          <span class="iv-badge iv-badge-comp">${compName}</span>
          ${seen ? '<span class="iv-badge iv-badge-reviewed">✓ Reviewed</span>' : ''}
        </div>
        <div class="qt" data-iv="${id}">▸ ${q.q}</div>
        <div class="ans" id="ans-${id}" style="display:none;">
          ${q.a}
          ${q.lesson && LESSONS[q.lesson] ? `<div style="margin-top:10px;"><a class="link" data-nav="lesson:${q.lesson}" style="display:inline-flex;align-items:center;gap:4px;font-weight:600;">📖 Study Full Lesson →</a></div>` : ''}
        </div>
      </div>
    `;
  }).join("");

  return `
    <div class="iv-portal-wrap">
      <div class="iv-hero">
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;">
          <div>
            <h2 style="font-size:22px;margin:0 0 4px;font-weight:700;">Placement & Technical Interview Portal</h2>
            <p style="color:var(--text-dim);margin:0;font-size:13.5px;">Master 1,000+ curated placement-grade technical, algorithm, system design, logical puzzle, and behavioral questions with comprehensive step-by-step model answers.</p>
          </div>
          <div style="display:flex;gap:8px;">
            <button class="iv-action-btn" id="ivExpandAllBtn">Expand All</button>
            <button class="iv-action-btn" id="ivCollapseAllBtn">Collapse All</button>
          </div>
        </div>

        <div class="iv-stats-grid">
          <div class="iv-stat-card"><div class="iv-stat-val">${trackCounts.core}</div><div class="iv-stat-lbl">⚡ Core Eng.</div></div>
          <div class="iv-stat-card"><div class="iv-stat-val">${trackCounts.software}</div><div class="iv-stat-lbl">💻 Software & IT</div></div>
          <div class="iv-stat-card"><div class="iv-stat-val">${trackCounts.aiml}</div><div class="iv-stat-lbl">🤖 AI & ML</div></div>
          <div class="iv-stat-card"><div class="iv-stat-val">${trackCounts.logical}</div><div class="iv-stat-lbl">🧠 Logic & Puzzles</div></div>
          <div class="iv-stat-card"><div class="iv-stat-val">${trackCounts.behavioral}</div><div class="iv-stat-lbl">🤝 Behavioral HR</div></div>
          <div class="iv-stat-card"><div class="iv-stat-val">${totalCount}</div><div class="iv-stat-lbl">📚 Total Bank</div></div>
        </div>
      </div>

      <div class="iv-tracks-bar">${trackTabs}</div>

      <div class="iv-controls">
        <div class="iv-search-row">
          <input type="text" id="ivSearchInput" class="iv-search-box" placeholder="🔍 Real-time search questions, concepts, formulas, or companies (e.g. 'Buck', 'B+ Tree', 'STAR', 'Bosch')..." autocomplete="off">
          <select id="ivDiffSelect" class="iv-select">
            <option value="all">All Difficulties</option>
            <option value="fresher">Fresher / Foundation</option>
            <option value="intermediate">Intermediate / Placement</option>
            <option value="advanced">Advanced / System-Level</option>
          </select>
          <button class="iv-action-btn" id="ivResetBtn">Reset Filters</button>
        </div>
        ${subPills ? `<div style="font-size:11.5px;color:var(--text-faint);text-transform:uppercase;letter-spacing:.04em;margin:10px 0 6px;">Sub-Disciplines &amp; Topics:</div><div class="iv-sub-pills" id="ivSubPillContainer"><button class="iv-sub-pill active" data-ivsub="all">All Topics</button>${subPills}</div>` : ''}
        <div id="ivFilterStatus" style="font-size:12.5px;color:var(--text-dim);margin-top:6px;">Showing <b>${list.length}</b> questions${isExactCategory ? ` for category: <span class="pill pill-neutral">${activeCat}</span> <a class="link" data-nav="interview" style="margin-left:6px;cursor:pointer;">Clear category filter</a>` : ''}</div>
      </div>



      <div id="ivCardsContainer" style="margin-top:16px;">
        ${qs}
      </div>
    </div>
  `;
}

function wireInterviewHandlers(){
  // 1. Accordion click handling for questions
  document.querySelectorAll("[data-iv]").forEach(el => {
    el.addEventListener("click", () => {
      const id = el.getAttribute("data-iv");
      const a = document.getElementById("ans-" + id);
      if(!a) return;
      const open = a.style.display === "none";
      a.style.display = open ? "block" : "none";
      el.textContent = (open ? "▾ " : "▸ ") + INTERVIEW[id].q;
      if(open){
        PROGRESS.interviewSeen = PROGRESS.interviewSeen || {};
        PROGRESS.interviewSeen[id] = true;
        const card = el.closest(".iv-q");
        if(card && !card.querySelector(".iv-badge-reviewed")){
          const badges = card.querySelector(".iv-badges");
          if(badges) badges.insertAdjacentHTML("beforeend", '<span class="iv-badge iv-badge-reviewed">✓ Reviewed</span>');
        }
        const l = INTERVIEW[id].lesson;
        if(l && LESSONS[l]) markTopicActivity(l, "interview"); else saveProgress(PROGRESS);
      }
    });
  });

  // 2. Track tab switching
  document.querySelectorAll("[data-ivtrack]").forEach(btn => {
    if(btn.tagName.toLowerCase() !== "button" || !btn.classList.contains("iv-track-tab")) return;
    btn.addEventListener("click", () => {
      const trackId = btn.getAttribute("data-ivtrack");
      nav({ page: "interview", track: trackId });
    });
  });

  // 3. Expand All / Collapse All
  const expBtn = document.getElementById("ivExpandAllBtn");
  const colBtn = document.getElementById("ivCollapseAllBtn");
  if(expBtn){
    expBtn.addEventListener("click", () => {
      document.querySelectorAll("#ivCardsContainer .iv-q").forEach(card => {
        if(card.style.display === "none") return;
        const id = card.getAttribute("data-ivid");
        const a = document.getElementById("ans-" + id);
        const qt = card.querySelector(".qt");
        if(a && qt && a.style.display === "none"){
          a.style.display = "block";
          qt.textContent = "▾ " + INTERVIEW[id].q;
          PROGRESS.interviewSeen = PROGRESS.interviewSeen || {};
          PROGRESS.interviewSeen[id] = true;
        }
      });
      saveProgress(PROGRESS);
    });
  }
  if(colBtn){
    colBtn.addEventListener("click", () => {
      document.querySelectorAll("#ivCardsContainer .iv-q").forEach(card => {
        const id = card.getAttribute("data-ivid");
        const a = document.getElementById("ans-" + id);
        const qt = card.querySelector(".qt");
        if(a && qt && a.style.display !== "none"){
          a.style.display = "none";
          qt.textContent = "▸ " + INTERVIEW[id].q;
        }
      });
    });
  }

  // 4. Live Search and Filtering
  const searchInput = document.getElementById("ivSearchInput");
  const diffSelect = document.getElementById("ivDiffSelect");
  const resetBtn = document.getElementById("ivResetBtn");
  let activeSub = "all";

  function applyClientFilters(){
    const query = (searchInput ? searchInput.value : "").trim().toLowerCase();
    const diff = (diffSelect ? diffSelect.value : "all").toLowerCase();
    const cards = document.querySelectorAll("#ivCardsContainer .iv-q");
    let visibleCount = 0;

    cards.forEach(card => {
      const id = card.getAttribute("data-ivid");
      const qObj = INTERVIEW[id] || {};
      const cardSub = (card.getAttribute("data-ivsub") || "").toLowerCase();
      const cardDiff = (card.getAttribute("data-ivdiff") || "").toLowerCase();
      
      // Check query match (in question, answer, company, sub, or topic)
      let matchesQuery = true;
      if(query){
        const textToSearch = (qObj.q + " " + qObj.a + " " + (qObj.company || "") + " " + (qObj.sub || "") + " " + (qObj.topic || "")).toLowerCase();
        matchesQuery = textToSearch.includes(query);
      }

      // Check diff match
      let matchesDiff = true;
      if(diff !== "all"){
        matchesDiff = cardDiff.includes(diff);
      }

      // Check sub match
      let matchesSub = true;
      if(activeSub !== "all"){
        matchesSub = cardSub.includes(activeSub.toLowerCase());
      }

      if(matchesQuery && matchesDiff && matchesSub){
        card.style.display = "block";
        visibleCount++;
      } else {
        card.style.display = "none";
      }
    });

    const statusEl = document.getElementById("ivFilterStatus");
    if(statusEl){
      statusEl.innerHTML = `Showing <b>${visibleCount}</b> of ${cards.length} questions` + (query ? ` matching "<em>${query}</em>"` : "");
    }
  }

  if(searchInput) searchInput.addEventListener("input", applyClientFilters);
  if(diffSelect) diffSelect.addEventListener("change", applyClientFilters);
  if(resetBtn){
    resetBtn.addEventListener("click", () => {
      if(searchInput) searchInput.value = "";
      if(diffSelect) diffSelect.value = "all";
      activeSub = "all";
      document.querySelectorAll(".iv-sub-pill").forEach(p => p.classList.toggle("active", p.getAttribute("data-ivsub") === "all"));
      applyClientFilters();
    });
  }

  // 5. Sub-discipline pill clicks
  document.querySelectorAll(".iv-sub-pill").forEach(pill => {
    pill.addEventListener("click", () => {
      document.querySelectorAll(".iv-sub-pill").forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      activeSub = decodeURIComponent(pill.getAttribute("data-ivsub"));
      applyClientFilters();
    });
  });
}
"""

    fn_pattern = re.compile(r'function pageInterview\(cat\)\{.*?function wireInterviewHandlers\(\)\{.*?\n\}', re.DOTALL)
    assert fn_pattern.search(content), "Could not find pageInterview & wireInterviewHandlers in index.html!"
    content = fn_pattern.sub(lambda _: new_interview_code, content, count=1)
    print("Replaced pageInterview & wireInterviewHandlers in index.html.")

    # 4. Standardize pageLearn (remove 17-Stage Learning Path tab and make card standard)
    new_learn_code = """function pageLearn(){
  let semCards = Object.keys(SYLLABUS).map(n=>{
    const s = SYLLABUS[n];
    const total = s.courses.length;
    return `<div class="card sem-card" data-nav="sem:${n}">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div><div style="font-weight:600;font-size:15px;">${s.label}</div><div class="course-meta">${total} course${total>1?'s':''} · ${s.courses.reduce((a,c)=>a+courseTopics(c).length,0)} Core Topics · Full Curriculum</div></div>
        <span style="font-size:18px;color:var(--text-faint);">→</span>
      </div>
    </div>`;
  }).join("");
  const foundList = FOUNDATION.topics.map(id=>{
    const l = LESSONS[id]; const done = isFoundationLessonDone(id);
    return `<div class="topic-row" data-nav="lesson:${id}">
      <div class="topic-left"><span class="topic-dot ${done?'done':''}"></span>${l.title}</div>
      <span style="font-size:12px;color:var(--text-faint);">→</span>
    </div>`;
  }).join("");

  return `
    <h2 style="font-size:20px;margin-bottom:16px;">Learn & Core Curriculum</h2>
    
    <div class="section-title" style="margin-bottom:12px;"><h2>Foundation Curriculum</h2></div>
    <div style="margin-bottom:24px;">
      <div class="card sem-card" data-nav="eeezero" style="cursor:pointer;padding:16px 20px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <div>
            <div style="font-weight:700;font-size:16px;color:var(--text);display:flex;align-items:center;gap:8px;">
              <span>⚡ EEE From Zero</span>
              <span class="badge" style="background:rgba(59,130,246,0.15);color:var(--accent);font-size:11px;padding:2px 8px;border-radius:10px;font-weight:600;">Foundation Track</span>
            </div>
            <div class="course-meta" style="font-size:13px;line-height:1.4;margin-top:4px;">40 Knowledge Domains (A–AN) · 201 Foundation Lessons · Electrical &amp; Electronics Engineering Fundamentals</div>
          </div>
          <div style="display:flex;align-items:center;gap:12px;">
            <span class="course-meta" style="font-size:13px;font-weight:600;color:var(--accent);">201 Lessons</span>
            <span style="font-size:18px;color:var(--text-faint);">→</span>
          </div>
        </div>
      </div>
    </div>

    <div class="section-title" style="margin-bottom:12px;"><h2>Semesters 3–7 (University Curriculum)</h2></div>
    <div class="grid" style="display:flex;flex-direction:column;gap:12px;">${semCards}</div>
  `;
}"""

    learn_pattern = re.compile(r'function pageLearn\(\)\{.*?\n\}', re.DOTALL)
    assert learn_pattern.search(content), "Could not find pageLearn in index.html!"
    content = learn_pattern.sub(lambda _: new_learn_code, content, count=1)
    print("Standardized pageLearn in index.html.")

    # 5. Save to index.html and eee-platform.html
    print("Writing index.html...")
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)

    print("Writing eee-platform.html (maintaining 100% exact binary parity)...")
    with open("eee-platform.html", "w", encoding="utf-8") as f:
        f.write(content)

    # 5. Verify byte parity
    idx_bytes = open("index.html", "rb").read()
    eee_bytes = open("eee-platform.html", "rb").read()
    assert idx_bytes == eee_bytes, "Parity check failed between index.html and eee-platform.html!"
    print(f"[OK] Exact byte parity verified ({len(idx_bytes)} bytes)!")

if __name__ == "__main__":
    update_portal()
