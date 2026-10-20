# tools/redesign_ui_alignment.py
# Redesigns global layout alignment (uniform 100% width across all pages)
# Implements dedicated Topic Learning Workspace / Reader Window with Prev/Next navigation

import re

def update_ui():
    print("Reading index.html...")
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update CSS in index.html to make widths uniform
    print("Updating CSS for uniform alignment and topic workspace...")

    # Replace .content width and max-width
    content = content.replace(
        ".content{padding:26px 28px 90px; max-width:1180px; width:100%; margin:0 auto;}",
        ".content{padding:24px 28px 90px; max-width:1240px; width:100%; margin:0 auto; box-sizing:border-box;}"
    )

    # Replace .lesson-wrap max-width: 760px with width: 100%; max-width: 100%
    content = content.replace(
        "/* Lesson page */ .lesson-wrap{max-width:760px;}",
        "/* Lesson page */ .lesson-wrap{width:100%; max-width:100%; margin:0 auto;}"
    )

    # Replace .mcq-card max-width: 680px with width: 100%; max-width: 100%
    content = content.replace(
        "/* MCQ */ .mcq-card{max-width:680px;}",
        "/* MCQ */ .mcq-card{width:100%; max-width:100%;}"
    )

    # Replace mock test widths
    content = content.replace(
        ".mock-bar{display:flex; justify-content:space-between; align-items:flex-end; max-width:680px; margin-bottom:14px; padding-bottom:10px; border-bottom:1px solid var(--border);}",
        ".mock-bar{display:flex; justify-content:space-between; align-items:flex-end; width:100%; max-width:100%; margin-bottom:14px; padding-bottom:10px; border-bottom:1px solid var(--border);}"
    )
    content = content.replace(
        ".mock-pal{display:flex; flex-wrap:wrap; gap:6px; max-width:680px;}",
        ".mock-pal{display:flex; flex-wrap:wrap; gap:6px; width:100%; max-width:100%;}"
    )
    content = content.replace(
        ".mock-confirm{max-width:680px; margin-top:16px; border-color:var(--accent);}",
        ".mock-confirm{width:100%; max-width:100%; margin-top:16px; border-color:var(--accent);}"
    )
    content = content.replace(
        ".mock-rev{margin-bottom:12px; max-width:760px;}",
        ".mock-rev{margin-bottom:12px; width:100%; max-width:100%;}"
    )

    # Add Topic Learning Workspace styles if not present
    workspace_css = """
/* Dedicated Topic Learning Workspace & Reader Window */
.topic-workspace{
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 24px 28px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.12);
  margin-top: 8px;
  box-sizing: border-box;
}
.topic-window-header{
  padding-bottom: 20px;
  margin-bottom: 24px;
  border-bottom: 1px solid var(--border);
}
.topic-window-toprow{
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 14px;
}
.topic-context-tag{
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.topic-context-badge{
  font-size: 12px;
  font-weight: 700;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: .04em;
  background: rgba(59,130,246,0.12);
  padding: 4px 10px;
  border-radius: 6px;
  border: 1px solid rgba(59,130,246,0.25);
}
.topic-mod-pill{
  font-size: 12px;
  color: var(--text-dim);
  background: var(--bg);
  padding: 4px 10px;
  border-radius: 6px;
  border: 1px solid var(--border);
}
.topic-practice-toolbar{
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 16px;
  padding: 12px 14px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 10px;
}
.topic-content-body{
  font-size: 15px;
  line-height: 1.75;
  color: var(--text);
  width: 100%;
}
.topic-content-body .card{
  margin: 18px 0;
  background: var(--bg);
  border: 1px solid var(--border);
}
.topic-window-footer{
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 36px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
}
.topic-pager-prev, .topic-pager-next{
  flex: 1;
  min-width: 180px;
}
.topic-pager-next{
  display: flex;
  justify-content: flex-end;
}
.topic-pager-center{
  display: flex;
  gap: 8px;
  align-items: center;
}
.topic-nav-btn{
  display: inline-flex;
  flex-direction: column;
  padding: 8px 14px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--text);
  cursor: pointer;
  text-decoration: none;
  transition: all .15s ease;
  max-width: 280px;
}
.topic-nav-btn:hover{
  border-color: var(--accent);
  background: var(--bg-card);
  color: var(--accent);
}
.topic-nav-btn .dir{
  font-size: 11px;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: .04em;
  font-weight: 600;
}
.topic-nav-btn .tit{
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}
"""

    if ".topic-workspace" not in content:
        content = content.replace("/* Lesson page */", workspace_css + "\n/* Lesson page */")
        print("Added topic workspace CSS.")

    # 2. Update pageLesson to render dedicated learning workspace with Previous/Next topic navigation
    new_page_lesson = """/* ---------- LESSON PAGE (TOPIC LEARNING WORKSPACE) ---------- */
function getLessonContext(lessonId){
  if(typeof SYLLABUS !== 'undefined'){
    for(const semKey in SYLLABUS){
      const sem = SYLLABUS[semKey];
      for(const course of sem.courses){
        const allCourseTopics = [];
        for(let mi = 0; mi < course.modules.length; mi++){
          const mod = course.modules[mi];
          for(let ti = 0; ti < mod.topics.length; ti++){
            const tName = mod.topics[ti];
            const lId = findLessonIdForTopic(tName);
            allCourseTopics.push({ topicName: tName, lessonId: lId, modName: mod.name, modIndex: mi + 1 });
          }
        }
        const idx = allCourseTopics.findIndex(t => t.lessonId === lessonId);
        if(idx !== -1){
          return {
            type: "syllabus",
            semKey: semKey,
            semLabel: sem.label,
            courseCode: course.code,
            courseTitle: course.title,
            modName: allCourseTopics[idx].modName,
            modIndex: allCourseTopics[idx].modIndex,
            prev: idx > 0 ? allCourseTopics[idx - 1] : null,
            next: idx < allCourseTopics.length - 1 ? allCourseTopics[idx + 1] : null
          };
        }
      }
    }
  }

  if(typeof EEE_ZERO_CATEGORIES !== 'undefined'){
    for(const cat of EEE_ZERO_CATEGORIES){
      const tIdx = cat.topics.findIndex(t => t.lessonId === lessonId);
      if(tIdx !== -1){
        return {
          type: "eeezero",
          catId: cat.id,
          catName: cat.name,
          catIcon: cat.icon,
          prev: tIdx > 0 ? { topicName: cat.topics[tIdx - 1].title, lessonId: cat.topics[tIdx - 1].lessonId } : null,
          next: tIdx < cat.topics.length - 1 ? { topicName: cat.topics[tIdx + 1].title, lessonId: cat.topics[tIdx + 1].lessonId } : null
        };
      }
    }
  }

  return null;
}

function pageLesson(id){
  let l = LESSONS[id];
  const LESSON_ALIASES = {
    "tfr-losses": "xfmr-losses-allday-efficiency",
    "power-system-transients-traveling-waves-bewley": "emt-transmission-lines",
    "pe-cycloconverters-matrix-converters": "z-matrix-converters",
    "pq-interruption-prevention-immunity": "pq-interruption-prevention-immunity",
    "aiml-types-ml": "aiml-types-ml",
    "ac-ind-circle-diagram": "ac-ind-motor-circle-diagram",
    "ac-ind-motor-equiv": "ac-ind-motor-phasor-equivalent-circuit",
    "ac-ind-motor-principle": "ac-ind-motor-construction-principle",
    "ac-ind-motor-torque-slip": "ac-ind-motor-power-torque-slip",
    "ac-to-dc-rectifiers": "single-three-phase-controlled-rectifiers-converters",
    "control-time-domain": "cse-time-domain-specs",
    "ct-three-phase-circuits": "three-phase-power",
    "ct-two-port-parameters": "ct-two-port-intro",
    "dc-dc-buck-converter": "pe-buck-converter",
    "digital-logic-basics": "logic-gates-truth-tables",
    "inverter-spwm-threephase": "voltage-source-inverters-sinusoidal-pwm-modulation",
    "lead-acid-batteries": "z-battery-chemistries",
    "pe-inverters-vsi-csi": "voltage-source-inverters-sinusoidal-pwm-modulation",
    "pe-rectifiers-single-three-phase": "single-three-phase-controlled-rectifiers-converters",
    "ps-fault-types": "symmetrical-unsymmetrical-fault-analysis",
    "ps-protection-relays": "eps-protective-relays-fundamentals",
    "ps-scada-ems": "psa-scada-systems",
    "signals-ct-dt": "sig-classification-operations",
    "signals-dtft": "sig-dtft-frequency-response",
    "synchronous-machine-phasor": "synchronous-generator-alternator-regulation",
    "three-phase-im-equivalent-circuit": "ac-ind-motor-phasor-equivalent-circuit",
    "three-phase-transformer-connections": "xfmr-3phase-connections-vector"
  };
  if(!l && LESSON_ALIASES[id]) l = LESSONS[LESSON_ALIASES[id]];
  if(!l) return `<div class="empty-state">Lesson not found.</div>`;
  const lTitle = l.title || (typeof TOPIC_TO_LESSON !== 'undefined' ? Object.keys(TOPIC_TO_LESSON).find(t => TOPIC_TO_LESSON[t] === id) : '') || id;
  const lArea = l.area || (typeof courseOfTopic !== 'undefined' && lTitle ? courseOfTopic(lTitle) : '') || 'Electrical Engineering Core';
  const studied = !!(PROGRESS.completedTopics[id]||{}).concept;
  
  // Context resolution
  const ctx = getLessonContext(id);

  // Breadcrumbs path
  let crumbHtml = `<span data-nav="learn" style="cursor:pointer;">Learn</span>`;
  if(ctx && ctx.type === "syllabus"){
    crumbHtml += ` / <span data-nav="sem:${ctx.semKey}" style="cursor:pointer;">${ctx.semLabel}</span> / <span data-nav="course:${ctx.courseCode}" style="cursor:pointer;">${ctx.courseTitle}</span> / ${lTitle}`;
  } else if(ctx && ctx.type === "eeezero"){
    crumbHtml += ` / <span data-nav="eeezero" style="cursor:pointer;">EEE From Zero</span> / <span data-nav="eeezero:${ctx.catId}" style="cursor:pointer;">${ctx.catName}</span> / ${lTitle}`;
  } else {
    crumbHtml += ` / ${lArea} / ${lTitle}`;
  }

  // Back button
  let backBtnHtml = `<button class="btn btn-ghost" data-nav="learn">← Back to Learn</button>`;
  if(ctx && ctx.type === "syllabus"){
    backBtnHtml = `<button class="btn btn-ghost" data-nav="course:${ctx.courseCode}">← Back to ${ctx.courseTitle}</button>`;
  } else if(ctx && ctx.type === "eeezero"){
    backBtnHtml = `<button class="btn btn-ghost" data-nav="eeezero:${ctx.catId}">← Back to ${ctx.catName}</button>`;
  }

  // Previous & Next topic buttons
  let prevBtnHtml = '';
  if(ctx && ctx.prev && ctx.prev.lessonId){
    prevBtnHtml = `<div class="topic-nav-btn" data-nav="lesson:${ctx.prev.lessonId}"><span class="dir">← Previous Topic</span><span class="tit">${ctx.prev.topicName}</span></div>`;
  } else if(ctx && ctx.type === "syllabus"){
    prevBtnHtml = `<div class="topic-nav-btn" data-nav="course:${ctx.courseCode}"><span class="dir">← Course Overview</span><span class="tit">${ctx.courseTitle}</span></div>`;
  }

  let nextBtnHtml = '';
  if(ctx && ctx.next && ctx.next.lessonId){
    nextBtnHtml = `<div class="topic-nav-btn" data-nav="lesson:${ctx.next.lessonId}"><span class="dir">Next Topic →</span><span class="tit">${ctx.next.topicName}</span></div>`;
  } else if(ctx && ctx.type === "syllabus"){
    nextBtnHtml = `<div class="topic-nav-btn" data-nav="course:${ctx.courseCode}"><span class="dir">Course Complete →</span><span class="tit">Review All Modules</span></div>`;
  }

  // Practice buttons
  const mcqBtn = l.mcqIds && l.mcqIds.length ? `<button class="btn btn-primary" data-nav="mcq:${id}" data-ids='${JSON.stringify(l.mcqIds)}'>Practice ${l.mcqIds.length} MCQ${l.mcqIds.length>1?'s':''} →</button>` : '';
  const nums = numericalsFor(id);
  const numBtn = nums.length ? `<button class="btn btn-secondary" data-nav="numerical:${nums[0]}">Solve ${nums.length} numerical${nums.length>1?'s':''} →</button>` : '';
  const ivs = interviewFor(id);
  const ivBtn = ivs.length ? `<button class="btn btn-secondary" data-nav="ivcat:${INTERVIEW[ivs[0]].cat}">${ivs.length} interview question${ivs.length>1?'s':''} →</button>` : '';
  const hasPractice = mcqBtn || numBtn || ivBtn;

  // Level computed
  const cl = typeof contentLevel === 'function' ? contentLevel(id) : 'PLACEMENT READY';

  return `
    <div class="crumb">${crumbHtml}</div>
    <div class="lesson-wrap lesson topic-workspace">
      <div class="topic-window-header">
        <div class="topic-window-toprow">
          <div class="topic-context-tag">
            <span class="topic-context-badge">📖 ${ctx && ctx.type === "syllabus" ? ctx.courseTitle : (ctx && ctx.type === "eeezero" ? ctx.catName : lArea)}</span>
            ${ctx && ctx.modName ? `<span class="topic-mod-pill">Module ${ctx.modIndex}: ${ctx.modName}</span>` : ''}
          </div>
          <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
            ${backBtnHtml}
            <button class="btn btn-ghost" id="markStudiedBtn">${studied?"Studied ✓":"Mark as studied"}</button>
          </div>
        </div>

        <h1 class="lesson-title">${lTitle}</h1>
        
        <div class="lesson-sub" style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-top:10px;">
          <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
            <span class="pill pill-ok">Verified Lesson</span>
            <span class="pill pill-neutral">${cl}</span>
            <span style="font-size:12.5px;color:var(--text-dim);">${studied?"Marked as studied ✓":"Not yet marked as studied"}</span>
          </div>
        </div>

        ${hasPractice ? `<div class="topic-practice-toolbar">${mcqBtn}${numBtn}${ivBtn}</div>` : ''}
      </div>

      <div class="topic-content-body">
        ${l.body}
      </div>

      <div class="topic-window-footer">
        <div class="topic-pager-prev">${prevBtnHtml}</div>
        <div class="topic-pager-center">
          <button class="btn btn-ghost" data-nav="learn">← Back to Learn</button>
          <button class="btn btn-secondary" data-nav="progress">View progress</button>
        </div>
        <div class="topic-pager-next">${nextBtnHtml}</div>
      </div>
    </div>
  `;
}
"""

    lesson_pattern = re.compile(r'(/\* ---------- LESSON PAGE[^*]*\*/\s*)?(function getLessonContext\(lessonId\)\{.*?)?function pageLesson\(id\)\{.*?\n\}', re.DOTALL)
    assert lesson_pattern.search(content), "Could not find pageLesson in index.html!"
    content = lesson_pattern.sub(lambda _: new_page_lesson, content, count=1)
    print("Replaced pageLesson with Topic Learning Workspace.")

    # 3. Write index.html and eee-platform.html with exact binary parity
    print("Writing index.html...")
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)

    print("Writing eee-platform.html (maintaining 100% exact binary parity)...")
    with open("eee-platform.html", "w", encoding="utf-8") as f:
        f.write(content)

    # 4. Verify byte parity
    idx_bytes = open("index.html", "rb").read()
    eee_bytes = open("eee-platform.html", "rb").read()
    assert idx_bytes == eee_bytes, "Parity check failed between index.html and eee-platform.html!"
    print(f"[OK] Exact byte parity verified ({len(idx_bytes)} bytes)!")

if __name__ == "__main__":
    update_ui()
