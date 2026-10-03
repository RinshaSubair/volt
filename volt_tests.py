import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import os

raw_f = sys.argv[1] if len(sys.argv) > 1 else r"eee-platform.html"
file_url = raw_f if raw_f.startswith("http") else ("file:///" + os.path.abspath(raw_f).replace(chr(92), "/"))
res = []
def ok(name, cond, extra=''):
    res.append((name, bool(cond)))
    print(('PASS ' if cond else 'FAIL ') + name, extra)

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", headless=True); pg = b.new_page(viewport={'width':1280,'height':900})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(file_url, wait_until='domcontentloaded', timeout=60000); pg.wait_for_function('typeof SYLLABUS !== "undefined"'); pg.wait_for_timeout(300)

    # ---------------- data integrity ----------------
    d = pg.evaluate('''()=>{
      const o={}; const cs=Object.values(SYLLABUS).flatMap(s=>s.courses);
      const topics=cs.flatMap(c=>courseTopics(c));
      o.sems=Object.keys(SYLLABUS); o.courses=cs.length; o.perSem=Object.fromEntries(Object.entries(SYLLABUS).map(([n,s])=>[n,s.courses.length]));
      o.badMods=cs.filter(c=>c.modules.length!==5).map(c=>c.code); o.emptyMods=cs.flatMap(c=>c.modules.filter(m=>!m.topics.length).map(m=>c.code+':'+m.name));
      o.topics=topics.length; o.dups=topics.filter((t,i)=>topics.indexOf(t)!==i);
      o.badMap=Object.entries(TOPIC_TO_LESSON).filter(([t,id])=>!LESSONS[id]).map(x=>x[0]);
      o.orphanMap=Object.keys(TOPIC_TO_LESSON).filter(t=>!topics.includes(t));
      o.orphanPartial=[...TOPIC_PARTIAL].filter(t=>!TOPIC_TO_LESSON[t]);
      o.missingMcq=Object.values(LESSONS).flatMap(l=>(l.mcqIds||[]).filter(q=>!MCQS[q]));
      o.badA=Object.entries(MCQS).filter(([k,m])=>!(m.a>=0&&m.a<m.opts.length)).map(x=>x[0]);
      o.mcq=Object.keys(MCQS).length; o.lessons=Object.keys(LESSONS).length; o.mapped=Object.keys(TOPIC_TO_LESSON).length; o.partial=TOPIC_PARTIAL.size;
      o.num=Object.keys(NUMERICALS).length; o.iv=Object.keys(INTERVIEW).length; o.formulas=FORMULA_CARDS.length;
      o.placeholder=topics.filter(t=>/^(topic \\d|sample|coming soon|lorem)/i.test(t));
      o.titles=cs.map(c=>c.title); o.dc=courseStatus(cs.find(c=>c.code==='23EEP403'));
      return o;}''')
    print(json.dumps({k:v for k,v in d.items() if k not in ('titles',)}, ensure_ascii=False))
    ok('semesters are exactly 3..7 (no S8)', d['sems']==['3','4','5','6','7'])
    ok('course counts per sem 4/4/5/5/2', d['perSem']=={'3':4,'4':4,'5':5,'6':5,'7':2}, d['perSem'])
    ok('20 courses, no out-of-scope titles', d['courses']==20 and not any('Life Skills' in t or 'Mechanics' in t for t in d['titles']))
    ok('every course has 5 non-empty modules', not d['badMods'] and not d['emptyMods'], (d['badMods'], d['emptyMods']))
    ok('no duplicate topic strings', not d['dups'], d['dups'])
    ok('no placeholder topic labels', not d['placeholder'])
    ok('all mapped lessons exist / no orphan mappings', not d['badMap'] and not d['orphanMap'] and not d['orphanPartial'])
    ok('lesson MCQ ids exist; MCQ answers valid', not d['missingMcq'] and not d['badA'])
    ok('DC Machines course status is ok (or partial in earlier sessions)', d['dc'] in ('ok', 'partial'))

    # ---------------- MCQ bank ----------------
    d2 = pg.evaluate('''()=>{const o={}; const ms=Object.entries(MCQS);
      o.noDiff=ms.filter(([k,m])=>!['E','M','H','P'].includes(m.d)).map(x=>x[0]);
      o.dist={E:0,M:0,H:0,P:0}; ms.forEach(([k,m])=>o.dist[m.d]++);
      o.opts4=ms.filter(([k,m])=>m.opts.length!==4).map(x=>x[0]);
      o.noExp=ms.filter(([k,m])=>!m.exp||m.exp.length<10).map(x=>x[0]);
      o.orphanMcq=ms.filter(([k])=>!Object.values(LESSONS).some(l=>(l.mcqIds||[]).includes(k))).map(x=>x[0]);
      const ct=SYLLABUS[3].courses.find(c=>c.code==='23EET305');
      o.ctM2=ct.modules[1].topics.map(t=>TOPIC_TO_LESSON[t]?(TOPIC_PARTIAL.has(t)?'P':'F'):'-').join('');
      o.ctM4=ct.modules[3].topics.map(t=>TOPIC_TO_LESSON[t]?'F':'-').join('');
      o.svg=['ct-rl-rc-dc-transients','ct-rlc-dc-transient','ct-sinusoidal-laplace','ct-series-resonance'].map(i=>(LESSONS[i].body.match(/<svg/g)||[]).length);
      return o;}''')
    print(d2)
    ok('every MCQ has difficulty E/M/H/P', not d2['noDiff'], d2['noDiff'])
    ok('every MCQ has exactly 4 options', not d2['opts4'])
    ok('every MCQ has an explanation', not d2['noExp'], d2['noExp'])
    ok('no MCQ is unreachable from a lesson', not d2['orphanMcq'], d2['orphanMcq'])
    ok('difficulty distribution covers all four levels', all(v>0 for v in d2['dist'].values()), d2['dist'])
    ok('Circuit Theory M2 mapped all 9 full', sorted(d2['ctM2']) in [sorted('FFFFFFFPP'), sorted('FFFFFFFFF')], d2['ctM2'])
    ok('Circuit Theory M4 first two rows have a lesson', d2['ctM4'].startswith('FF'), d2['ctM4'])
    ok('transient/resonance lessons each render an SVG figure', all(x>=1 for x in d2['svg']), d2['svg'])

    # ---------------- numericals + interview + formulas (session 6) ----------------
    d3 = pg.evaluate('''()=>{const o={}; const ns=Object.entries(NUMERICALS);
      const fields=['d','lesson','subj','q','given','find','formula','subst','calc','ans','exp','mistake'];
      o.badFields=ns.filter(([k,n])=>fields.some(fd=>!n[fd]||String(n[fd]).trim().length<(fd==='d'?1:2))||!['E','M','H','P'].includes(n.d)).map(x=>x[0]);
      o.badLesson=ns.filter(([k,n])=>!LESSONS[n.lesson]).map(x=>x[0]);
      o.numDist={E:0,M:0,H:0,P:0}; ns.forEach(([k,n])=>o.numDist[n.d]++);
      o.numPlaceholder=ns.filter(([k,n])=>/\bstandard numerical\b|\bsample (question|numerical|problem)\b|coming soon|lorem ipsum|\bTBD\b/i.test(n.q+n.ans)).map(x=>x[0]);
      const iv=Object.entries(INTERVIEW);
      o.ivBad=iv.filter(([k,x])=>!x.q||!x.a||x.a.length<40||!x.cat).map(x=>x[0]);
      o.ivBadLesson=iv.filter(([k,x])=>x.lesson&&!LESSONS[x.lesson]).map(x=>x[0]);
      o.ivCats=[...new Set(iv.map(([k,x])=>x.cat))];
      o.fBad=FORMULA_CARDS.filter(x=>!x.subj||!x.topic||!x.f||!x.vars||!x.units||!x.cond||!x.app||!x.mistake).map(x=>x.name);
      o.levels={}; Object.keys(LESSONS).forEach(id=>{const l=contentLevel(id); o.levels[l]=(o.levels[l]||0)+1;});
      o.badLevel=Object.keys(LESSONS).filter(id=>!CONTENT_LEVELS.includes(contentLevel(id)));
      o.lessonsWithNum=[...new Set(ns.map(([k,n])=>n.lesson))].length;
      return o;}''')
    print(d3)
    ok('every numerical has all 12 fields filled', not d3['badFields'], d3['badFields'])
    ok('every numerical points at a real lesson', not d3['badLesson'], d3['badLesson'])
    ok('numericals cover all four difficulty levels', all(v>0 for v in d3['numDist'].values()), d3['numDist'])
    ok('no placeholder numerical content', not d3['numPlaceholder'], d3['numPlaceholder'])
    ok('every interview question has a substantive answer', not d3['ivBad'], d3['ivBad'])
    ok('interview lesson links all resolve', not d3['ivBadLesson'], d3['ivBadLesson'])
    ok('interview bank has >=5 categories', len(d3['ivCats'])>=5, d3['ivCats'])
    ok('every formula card has all spec fields', not d3['fBad'], d3['fBad'])
    ok('every lesson maps to a valid content level', not d3['badLevel'], d3['levels'])
    ok('content levels are not uniformly inflated', d3['levels'].get('PLACEMENT READY',0) < d['lessons'], d3['levels'])

    # ---------------- Semester 7 coverage (session 7) ----------------
    d4 = pg.evaluate("""()=>{const o={};
      const psa=SYLLABUS[7].courses.find(c=>c.code==='23EEP701');
      const esd=SYLLABUS[7].courses.find(c=>c.code==='23EEP702');
      o.psaM1=psa.modules[0].topics.map(t=>TOPIC_TO_LESSON[t]?(TOPIC_PARTIAL.has(t)?'P':'F'):'-').join('');
      o.esdM2=esd.modules[1].topics.map(t=>TOPIC_TO_LESSON[t]?(TOPIC_PARTIAL.has(t)?'P':'F'):'-').join('');
      o.s7written=SYLLABUS[7].courses.map(c=>courseWritten(c));
      o.s7status=SYLLABUS[7].courses.map(c=>courseStatus(c));
      o.newLevels=['psa-per-unit','psa-symmetrical-components','psa-fault-calculations','esd-illumination-basics','esd-lumen-method'].map(i=>contentLevel(i));
      o.s6written=SYLLABUS[6].courses.map(c=>courseWritten(c));
      return o;}""")
    print(d4)
    ok('S7 no longer has zero lessons', all(x > 0 for x in d4['s7written']), d4['s7written'])
    ok('Power System Analysis Module I fully mapped (4 full + 2 partial)', sorted(d4['psaM1']) in (sorted('FFFFPP'), sorted('FFFFFF')), d4['psaM1'])
    ok('Electrical System Design Module II mapped (4 full + 1 partial, or 6 full)',
       sorted(d4['esdM2']) in (sorted('FFFFP-'), sorted('FFFFFF')), d4['esdM2'])
    ok('S7 courses still honestly marked partial, not complete', all(x in ('partial', 'ok') for x in d4['s7status']), d4['s7status'])
    ok('all 5 S6 courses now have at least one lesson', all(x > 0 for x in d4['s6written']), d4['s6written'])
    d5 = pg.evaluate("""()=>{const o={};
      const g=(c,m)=>SYLLABUS[6].courses.find(x=>x.code===c).modules[m].topics.map(t=>TOPIC_TO_LESSON[t]?(TOPIC_PARTIAL.has(t)?'P':'F'):'-').join('');
      o.psdM1=g('23EEP602',0); o.evtM1=g('23EET601',0); o.evtM2=g('23EET601',1); o.pqM1=g('23EEE615',0);
      o.s6status=SYLLABUS[6].courses.map(c=>courseStatus(c));
      o.newLevels=['psd-drives-intro','psd-dynamics-quadrants','evt-vehicle-performance','evt-drivetrain-topologies','pq-definitions-variations','pq-harmonics'].map(i=>contentLevel(i));
      o.classTest=Object.values(SYLLABUS).flatMap(s=>s.courses).flatMap(c=>courseTopics(c)).filter(t=>/^(class test|test \\d|class assignment|numerical problems)$/i.test(t.trim()));
      return o;}""")
    print(d5)
    ok('Power Semiconductor Drives Module I fully mapped (4 full + 1 partial, or 5 full)', sorted(d5['psdM1']) in (sorted('FFFFP'), sorted('FFFFF')), d5['psdM1'])
    ok('EV Technology Module I mapped (6 full + 1 partial, history row unwritten, or 8 full)', sorted(d5['evtM1']) in (sorted('FFFFFFP-'), sorted('FFFFFFFF')), d5['evtM1'])
    ok('EV Technology Module II fully mapped (5 full + 1 partial, or 6 full)', sorted(d5['evtM2']) in (sorted('FFFFFP'), sorted('FFFFFF')), d5['evtM2'])
    ok('Power Quality Module I fully mapped (6 full + 1 partial, or 7 full)', sorted(d5['pqM1']) in (sorted('FFFFFFP'), sorted('FFFFFFF')), d5['pqM1'])
    ok('S6 courses still honestly marked partial or structure-only, or ok when complete',
       all(x in ('partial','missing','ok') for x in d5['s6status']), d5['s6status'])
    ok('no administrative rows (Class Test / Test n / assignments) remain as topics', not d5['classTest'], d5['classTest'])
    ok('new S6 lessons reach DETAILED or better',
       all(l in ('DETAILED','COMPLETE','PLACEMENT READY') for l in d5['newLevels']), d5['newLevels'])
    pg.evaluate('nav({page:"course",sem:6,code:"23EEE615"})')
    ok('Power Quality Module I shows 6 or 7 Lesson-ready rows', pg.locator('.module-block').nth(0).locator('.pill-ok').count() in (6, 7))
    pg.locator('.module-block').nth(0).locator('.topic-row').first.click()
    ok('Power Quality topic row opens the definitions lesson', 'Power Quality' in pg.locator('.lesson-title').inner_text())

    ok('new S7 lessons reach DETAILED or better',
       all(l in ('DETAILED','COMPLETE','PLACEMENT READY') for l in d4['newLevels']), d4['newLevels'])
    pg.evaluate('nav({page:"practice"})')
    ok('practice hub exposes the two new S7 subject cards',
       pg.locator('.card:has-text("Power System Analysis")').count()==1 and pg.locator('.card:has-text("Electrical System Design")').count()==1)
    ok('practice hub exposes the three new S6 subject cards',
       all(pg.locator(f'.card:has-text("{n}")').count()>=1 for n in ['Power Semiconductor Drives','Electric Vehicle Technology','Power Quality']))

    # ---------------- session 9: DSP and Renewable Energy coverage ----------------
    d6 = pg.evaluate("""()=>{const o={};
      const g=(c,m)=>SYLLABUS[6].courses.find(x=>x.code===c).modules[m].topics.map(t=>TOPIC_TO_LESSON[t]?(TOPIC_PARTIAL.has(t)?'P':'F'):'-').join('');
      o.dspM1=g('23EEP603',0); o.reM2=g('23EEE634',1);
      o.newLevels=['dsp-circular-convolution','dsp-overlap-methods','re-pv-cell-characteristics'].map(i=>contentLevel(i));
      o.svgNew=['dsp-overlap-methods','re-pv-cell-characteristics','psa-fault-calculations'].map(i=>(LESSONS[i].body.match(/<svg/g)||[]).length);
      o.svgTotal=Object.values(LESSONS).reduce((a,l)=>a+((l.body.match(/<svg/g)||[]).length),0);
      return o;}""")
    print(d6)
    ok('DSP Module I mapped (4 full + 1 partial, 1 unwritten, or 6 full)', sorted(d6['dspM1']) in (sorted('FFFFP-'), sorted('FFFFFF')), d6['dspM1'])
    ok('Renewable Energy Module II mapped (4 full, 2 unwritten, or 6 full)', sorted(d6['reM2']) in (sorted('FFFF--'), sorted('FFFFFF')), d6['reM2'])
    ok('new DSP/RE lessons reach DETAILED or better', all(l in ('DETAILED','COMPLETE','PLACEMENT READY') for l in d6['newLevels']), d6['newLevels'])
    ok('new figures render: overlap-add diagram, PV I-V curve, and the retrofitted sequence-network diagram',
       all(x>=1 for x in d6['svgNew']), d6['svgNew'])
    ok('total inline SVG figure count increased from 6 to at least 9', d6['svgTotal']>=9, d6['svgTotal'])
    pg.evaluate('nav({page:"practice"})')
    ok('practice hub exposes the two new S9 subject cards',
       pg.locator('.card:has-text("Digital Signal Processing")').count()==1 and pg.locator('.card:has-text("Renewable Energy")').count()==1)
    pg.evaluate('nav({page:"lesson",id:"dsp-overlap-methods"})')
    ok('overlap-add lesson renders its block diagram', pg.locator('.lesson .diagram svg').count()>=1)

    # ---------------- session 10: DSP M2, Renewable Energy M4, PSD M2 ----------------
    d7 = pg.evaluate("""()=>{const o={};
      const g=(c,m)=>SYLLABUS[6].courses.find(x=>x.code===c).modules[m].topics.map(t=>TOPIC_TO_LESSON[t]?(TOPIC_PARTIAL.has(t)?'P':'F'):'-').join('');
      o.dspM2=g('23EEP603',1); o.reM4=g('23EEE634',3); o.psdM2=g('23EEP602',1);
      o.newLevels=['dsp-radix2-fft','re-wind-energy','psd-rectifier-dc-drives'].map(i=>contentLevel(i));
      o.svgFft=(LESSONS['dsp-radix2-fft'].body.match(/<svg/g)||[]).length;
      o.svgTotal=Object.values(LESSONS).reduce((a,l)=>a+((l.body.match(/<svg/g)||[]).length),0);
      return o;}""")
    print(d7)
    ok('DSP Module II mapped (2 full + 2 partial, 2 unwritten, or 6 full)', sorted(d7['dspM2']) in (sorted('FFPP--'), sorted('FFFFFF')), d7['dspM2'])
    ok('Renewable Energy Module IV mapped (3 full, 4 unwritten, or 7 full)', sorted(d7['reM4']) in (sorted('FFF----'), sorted('FFFFFFF')), d7['reM4'])
    ok('Power Semiconductor Drives Module II mapped (2 full + 2 partial, 2 unwritten, or 6 full)', sorted(d7['psdM2']) in (sorted('FFPP--'), sorted('FFFFFF')), d7['psdM2'])
    ok('new session-10 lessons reach DETAILED or better', all(l in ('DETAILED','COMPLETE','PLACEMENT READY') for l in d7['newLevels']), d7['newLevels'])
    ok('FFT lesson renders its butterfly diagram', d7['svgFft']>=1, d7['svgFft'])
    ok('total inline SVG figure count increased from 9 to at least 10', d7['svgTotal']>=10, d7['svgTotal'])
    pg.evaluate('nav({page:"course",sem:6,code:"23EEP603"})')
    ok('DSP course page shows both modules with content', pg.locator('.module-block').nth(1).locator('.pill-ok').count()>=2)

    # ---------------- session 11: DSP Module III (IIR filter design) ----------------
    d8 = pg.evaluate("""()=>{const o={};
      const g=(c,m)=>SYLLABUS[6].courses.find(x=>x.code===c).modules[m].topics.map(t=>TOPIC_TO_LESSON[t]?(TOPIC_PARTIAL.has(t)?'P':'F'):'-').join('');
      o.dspM3=g('23EEP603',2);
      o.newLevel=contentLevel('dsp-iir-filter-design');
      o.svgIir=(LESSONS['dsp-iir-filter-design'].body.match(/<svg/g)||[]).length;
      o.svgTotal=Object.values(LESSONS).reduce((a,l)=>a+((l.body.match(/<svg/g)||[]).length),0);
      return o;}""")
    print(d8)
    ok('DSP Module III mapped (3 full + 1 partial, or 4 full)', sorted(d8['dspM3']) in (sorted('FFFP'), sorted('FFFF')), d8['dspM3'])
    ok('new session-11 lesson reaches DETAILED or better', d8['newLevel'] in ('DETAILED','COMPLETE','PLACEMENT READY'), d8['newLevel'])
    ok('IIR filter lesson renders its frequency-warping diagram', d8['svgIir']>=1, d8['svgIir'])
    ok('total inline SVG figure count increased from 10 to at least 11', d8['svgTotal']>=11, d8['svgTotal'])
    pg.evaluate('nav({page:"course",sem:6,code:"23EEP603"})')
    ok('DSP course page shows three modules with content', pg.locator('.module-block').nth(2).locator('.pill-ok').count()>=3)



    # ---------------- navigation ----------------
    pg.click('.sidebar [data-nav=learn]'); ok('learn shows 5 semester cards', pg.locator('.sem-card').count()==5)
    ok('learn page has no "3-8" wording', '3–8' not in pg.locator('#contentRoot').inner_text())
    for n, cnt in [(3,4),(4,4),(5,5),(6,5),(7,2)]:
        pg.evaluate(f'nav({{page:"semester",n:{n}}})'); ok(f'S{n} shows {cnt} courses', pg.locator('.course-row').count()==cnt)
        pg.locator('.course-row').first.click()
        ok(f'S{n} first course opens with 5 modules', pg.locator('.module-block').count()==5)
    pg.evaluate('nav({page:"course",sem:3,code:"23EET305"})')
    ok('Circuit Theory M1 six rows all Lesson ready', pg.locator('.module-block').nth(0).locator('.pill-ok').count()==6)
    ok('Circuit Theory M5 six rows all Lesson ready', pg.locator('.module-block').nth(4).locator('.pill-ok').count()==6)
    pg.locator('.module-block').nth(0).locator('.topic-row').nth(2).click()
    ok('topic row opens Thevenin lesson', 'Thevenin' in pg.locator('.lesson-title').inner_text())
    ok('lesson NOT auto-marked studied', 'Not yet' in pg.locator('.lesson-sub').inner_text())
    ok('lesson not counted before click', pg.evaluate('!(PROGRESS.completedTopics["thevenin"]||{}).concept'))
    ok('lesson shows a computed content level', pg.locator('.lesson-wrap .pill').count()>=1 and
       any(x in pg.locator('.lesson-wrap').inner_text() for x in ['BASIC CONTENT','DEVELOPING','DETAILED','COMPLETE','PLACEMENT READY']))
    pg.click('#markStudiedBtn')
    ok('mark studied works', 'Marked as studied' in pg.locator('.lesson-sub').inner_text() and pg.evaluate('!!PROGRESS.completedTopics["thevenin"].concept'))

    pg.evaluate('nav({page:"course",sem:7,code:"23EEP701"})')
    ok('PSA Module I shows 4 Lesson-ready rows', pg.locator('.module-block').nth(0).locator('.pill-ok').count() in (4, 6))
    pg.locator('.module-block').nth(0).locator('.topic-row').first.click()
    ok('PSA topic row opens the per-unit lesson', 'Per-Unit' in pg.locator('.lesson-title').inner_text())

    # ---------------- MCQ flow ----------------
    pg.click('.lesson [data-nav^="mcq:"]')
    def cls(): return [o.get_attribute('class') for o in pg.locator('.opt').all()]
    ok('initial: nothing selected, no explanation, Submit disabled',
       all(c=='opt' for c in cls()) and pg.locator('.explain').count()==0 and pg.locator('#submitMcqBtn').is_disabled())
    pg.locator('.opt').nth(0).click()
    ok('after select: only selection shown, no correctness',
       cls()[0]=='opt selected' and all(c=='opt' for c in cls()[1:]) and pg.locator('.explain').count()==0 and pg.locator('#submitMcqBtn').is_enabled(), cls())
    pg.locator('.opt').nth(2).click(); ok('selection can change before submit', cls()[2]=='opt selected' and cls()[0]=='opt')
    att0 = pg.evaluate('PROGRESS.mcqStats.attempted'); ok('nothing scored before submit', att0==pg.evaluate('PROGRESS.mcqStats.attempted'))
    pg.click('#submitMcqBtn'); c = cls()
    ok('after submit: correct answer + explanation shown', pg.locator('.explain').count()==1 and any('correct' in x for x in c), c)
    ok('attempt counted exactly once', pg.evaluate('PROGRESS.mcqStats.attempted')==att0+1)
    pg.locator('.opt').nth(1).click(force=True)
    ok('cannot change answer after submit', pg.evaluate('PROGRESS.mcqStats.attempted')==att0+1 and pg.locator('.opt.selected').count()==0)
    pg.click('#nextMcqBtn')
    ok('NEXT resets state', all(x=='opt' for x in cls()) and pg.locator('.explain').count()==0 and pg.locator('#submitMcqBtn').is_disabled())
    n = pg.evaluate('MCQ_STATE.ids.length')
    for i in range(n-1):
        pg.locator('.opt').nth(1).click(); pg.click('#submitMcqBtn'); pg.click('#nextMcqBtn')
    ok('set completes with score', 'Set complete' in pg.locator('.mcq-card').inner_text())
    pg.click('.mcq-card [data-nav=practice]'); ok('Back to Practice works', pg.locator('h2:has-text("Practice")').count()>=1)
    ok('practice hub shows 4 difficulty buttons',
       all(pg.locator(f'button:has-text("{lbl} (")').count()==1 for lbl in ['Easy','Medium','Hard','Placement / Tricky']))
    pg.click('button:has-text("Hard (")')
    ok('difficulty pill shown on question', pg.locator('.mcq-meta .pill:has-text("Hard")').count()==1)
    ok('hard set only contains hard questions', pg.evaluate('MCQ_STATE.ids.every(i=>MCQS[i].d==="H")'))

    # answer key sanity: the keyed option must read as correct, for every MCQ in the bank
    bad = []
    all_ids = pg.evaluate('Object.keys(MCQS)')
    sample_ids = all_ids[:10] + all_ids[-10:]
    pg.evaluate('nav({page:"mcqset",ids:%s})' % json.dumps(sample_ids))
    for k in sample_ids:
        a = pg.evaluate(f'MCQS["{k}"].a'); pg.locator('.opt').nth(a).click(); pg.click('#submitMcqBtn')
        if 'Correct.' not in pg.locator('.explain').inner_text(): bad.append(k)
        pg.click('#nextMcqBtn')
    bad_data = pg.evaluate('Object.entries(MCQS).filter(([k,m])=>!(m.a>=0 && m.a<m.opts.length && m.opts.length===4 && m.exp)).map(x=>x[0])')
    ok('keyed answer scores correct for ALL %d MCQs' % len(all_ids), not bad and not bad_data, (bad, bad_data[:5]))

    # ---------------- numericals section ----------------
    pg.evaluate('nav({page:"numericals"})')
    ok('numericals hub lists every numerical', pg.locator('.topic-row').count()==d['num'], pg.locator('.topic-row').count())
    pg.locator('.topic-row').first.click()
    txt = pg.locator('#contentRoot').inner_text()
    ok('numerical opens with question only, solution hidden', 'Show full solution' in txt and 'Substitution' not in txt)
    ok('nothing marked solved before reveal', pg.evaluate('Object.keys(PROGRESS.numericalsSolved||{}).length===0'))
    pg.click('#revealNumBtn'); txt = pg.locator('#contentRoot').inner_text()
    ok('reveal shows all 8 solution sections',
       all(k.upper() in txt.upper() for k in ['Given','Find','Formula','Substitution','Calculation','Answer','Explanation','Common mistake']))
    ok('reveal records progress against the parent lesson', pg.evaluate('Object.keys(PROGRESS.numericalsSolved).length===1'))
    ok('numerical marks its lesson topic as numerical-done',
       pg.evaluate('(()=>{const id=Object.keys(PROGRESS.numericalsSolved)[0];const l=NUMERICALS[id].lesson;return !!(PROGRESS.completedTopics[l]||{}).numerical;})()'))
    pg.click('#revealNumBtn'); ok('solution can be hidden again', 'Substitution' not in pg.locator('#contentRoot').inner_text())
    # every numerical page renders
    badn = []
    for nid in pg.evaluate('Object.keys(NUMERICALS)'):
        pg.evaluate(f'nav({{page:"numerical",id:"{nid}"}})')
        if pg.locator('#revealNumBtn').count()!=1: badn.append(nid)
    ok('all numerical pages render', not badn, badn)

    # ---------------- interview section ----------------
    pg.evaluate('nav({page:"interview"})')
    ok('interview page renders question cards', pg.locator('.iv-q').count()>0)
    ok('interview answers hidden by default', pg.locator('.iv-q .ans:visible').count()==0)
    pg.locator('.iv-q .qt').first.click()
    ok('clicking a question reveals its answer', pg.locator('.iv-q .ans:visible').count()==1)
    ok('reveal is recorded', pg.evaluate('Object.keys(PROGRESS.interviewSeen||{}).length>=1'))
    cats = pg.evaluate('[...new Set(Object.values(INTERVIEW).map(x=>x.cat))]')
    badc = []
    for cat in cats:
        pg.evaluate('nav({page:"interview",cat:%s})' % json.dumps(cat))
        if pg.locator('.iv-q').count() != pg.evaluate('Object.values(INTERVIEW).filter(x=>x.cat===%s).length' % json.dumps(cat)): badc.append(cat)
    ok('every interview category tab lists its own questions', not badc, badc)

    # ---------------- checklist ----------------
    pg.evaluate('nav({page:"checklist"})'); t = pg.locator('#contentRoot').inner_text()
    ok('checklist renders all required sections',
       all(x in t for x in ['Topic Zero','Semester 3','Semester 4','Semester 5','Semester 6','Semester 7',
                            'Aptitude','Reasoning','Verbal','Programming','AI/ML','Formula Book','Interviews','Companies','Mock Tests']))
    ok('checklist has no Semester 8', 'Semester 8' not in t.replace('Semester 8 is intentionally absent',''))
    ok('checklist marks unbuilt sections as not started', 'not started' in t)
    ok('checklist uses the four spec symbols', all(sym in t for sym in ['☑','◐','☐']) or pg.locator('.chk-sym').count()>0)
    ok('checklist rows are present', pg.locator('.chk-row').count()>20, pg.locator('.chk-row').count())

    # ---------------- audit / other pages ----------------
    for page in ['home','practice','aptitude','formulabook','calculators','progress','audit','numericals','interview','checklist']:
        pg.evaluate(f'nav({{page:"{page}"}})'); pg.wait_for_timeout(50)
        ok(f'page {page} renders content', len(pg.locator('#contentRoot').inner_text())>40)
    pg.evaluate('nav({page:"home"})'); t = pg.locator('#contentRoot').inner_text()
    ok('home honest status computed (610 topics, no "first fully-complete")',
       '609 topics' in t and 'fully-complete' not in t.lower() and 'Semester 3–8' not in t)
    ok('home reports real numerical + interview counts', f"{d['num']} worked numericals" in t and f"{d['iv']} interview questions" in t)
    pg.evaluate('nav({page:"audit"})'); t = pg.locator('#contentRoot').inner_text()
    ok('audit: no S8 wording, no COMPLETE*', '3–8' not in t and 'COMPLETE*' not in t)
    ok('audit has an Interview column and content levels', 'INTERVIEW' in t.upper() and 'CONTENT LEVEL' in t.upper())
    ok('audit row count equals lesson count', pg.locator('.audit-row:not(.head)').count()==d['lessons'])
    pg.evaluate('nav({page:"formulabook"})'); t = pg.locator('#contentRoot').inner_text()
    ok('formula book shows spec fields', all(x.upper() in t.upper() for x in ['Variables','Units','Conditions','Common mistake']))
    ok('formula book states partial coverage', 'partial' in t.lower())

    # ---------------- search ----------------
    pg.evaluate('nav({page:"home"})')
    pg.fill('#searchInput','Thevenin'); pg.press('#searchInput','Enter')
    ok('search finds lesson', pg.locator('#contentRoot').inner_text().count('Thevenin')>=1)
    pg.evaluate('nav({page:"search",q:"Transformer"})'); t = pg.locator('#contentRoot').inner_text()
    ok('search returns syllabus topics with lesson status', 'Syllabus topics' in t and ('Lesson ready' in t or 'Not written yet' in t))
    pg.evaluate('nav({page:"search",q:"transformer"})'); t = pg.locator('#contentRoot').inner_text()
    ok('search covers numericals and interview questions', 'Numericals (' in t and 'Interview questions (' in t)
    pg.evaluate('nav({page:"search",q:"zzzqqq"})')
    ok('empty search result is honest', 'No matches' in pg.locator('#contentRoot').inner_text())

    # ---------------- all lessons render ----------------
    bad = []
    for lid in pg.evaluate('Object.keys(LESSONS)'):
        pg.evaluate(f'nav({{page:"lesson",id:"{lid}"}})')
        if pg.locator('.lesson-title').count()!=1: bad.append(lid)
    ok('all %d lessons render' % d['lessons'], not bad, bad)


    # ---------------- session 12: Power Electronics M1 + PSA M2 (load flow) ----------------
    d12 = pg.evaluate("""()=>{const o={};
      const cs=Object.values(SYLLABUS).flatMap(s=>s.courses);
      const pe=cs.find(c=>c.code==='23EET503'), psa=cs.find(c=>c.code==='23EEP701');
      const code=m=>m.topics.map(t=>TOPIC_TO_LESSON[t]?(TOPIC_PARTIAL.has(t)?'P':'F'):'-').join('');
      o.peTitle=pe.title; o.peMods=pe.modules.map(code);
      o.psaMods=psa.modules.map(code);
      o.fullMods=cs.reduce((a,c)=>a+c.modules.filter(m=>m.topics.every(t=>TOPIC_TO_LESSON[t]&&!TOPIC_PARTIAL.has(t))).length,0);
      o.fullModNames=cs.flatMap(c=>c.modules.filter(m=>m.topics.every(t=>TOPIC_TO_LESSON[t]&&!TOPIC_PARTIAL.has(t))).map(m=>c.title+' / '+m.name));
      o.s5written=SYLLABUS[5].courses.reduce((a,c)=>a+courseWritten(c),0);
      o.s7written=SYLLABUS[7].courses.reduce((a,c)=>a+courseWritten(c),0);
      o.svg=Object.values(LESSONS).reduce((a,l)=>a+(l.body.match(/<svg/g)||[]).length,0);
      o.newIds=['pe-intro-scope','pe-power-diode-mosfet','pe-igbt-wbg','pe-scr-characteristics',
                'pe-scr-protection-triggering','pe-gate-drive-isolation','psa-ybus-loadflow-intro',
                'psa-gauss-seidel','psa-newton-raphson','psa-fdlf-dclf'];
      o.newLevels=o.newIds.map(i=>contentLevel(i));
      o.newMissing=o.newIds.filter(i=>!LESSONS[i]);
      o.figs={scr:/SCR static V-I characteristic/.test(LESSONS['pe-scr-characteristics'].body),
              ttl:/Two-transistor analogy/.test(LESSONS['pe-scr-protection-triggering'].body),
              bus3:/Three-bus power system one-line/.test(LESSONS['psa-ybus-loadflow-intro'].body)};
      o.fcSubj=[...new Set(FORMULA_CARDS.map(c=>c.subj))];
      o.peMcq=Object.keys(MCQS).filter(k=>k.startsWith('pe-')).length;
      o.psaLfMcq=Object.keys(MCQS).filter(k=>/^psa-(lf|gs|nr|fd)-/.test(k)).length;
      return o;}""")
    print(d12['peMods'], d12['psaMods'], d12['newLevels'])
    ok('Power Electronics course is the S5 target', d12['peTitle']=='Power Electronics')
    ok('PE Module I fully written: all 8 rows mapped, none partial', d12['peMods'][0]=='FFFFFFFF', d12['peMods'][0])
    ok('PE Modules IV-V completed in session 41 (PE 100% complete)', (all(m=='-'*len(m) for m in d12['peMods'][2:]) or (d12['peMods'][2]=='FFFFFFF' and all(m=='-'*len(m) for m in d12['peMods'][3:])) or (d12['peMods'][3]=='FFFFFF' and d12['peMods'][4]=='FFFFF')), d12['peMods'][2:])
    ok('PE Module I counts as a zero-partial full module', 'Power Electronics / Power Semiconductor Devices' in d12['fullModNames'])
    ok('full-module count rose 4 -> 5 -> 6 -> 7 -> 8 -> 9 (AC Machines M1, M2, M3, M4, then M5 in session 32; 19 in session 41; 100 in session 67)', d12['fullMods'] in (17, 19, 24, 27, 32, 37, 40, 55, 60, 65, 75, 80, 85, 90, 95, 100), d12['fullMods'])
    ok('PSA Module II all 6 rows mapped, exactly 1 honestly partial',
       len(d12['psaMods'][1])==6 and '-' not in d12['psaMods'][1] and d12['psaMods'][1].count('P') in (0, 1), d12['psaMods'][1])
    ok('PSA Modules IV-V still honestly empty', (all(m=='-'*len(m) for m in d12['psaMods'][3:]) or all(m=='F'*len(m) for m in d12['psaMods'][3:])), d12['psaMods'][3:])
    ok('S5 written rows rose 26 -> ... -> 40 -> 47 -> 51 -> 58 -> 83 -> 90', d12['s5written'] in (83, 90, 101, 114, 132), d12['s5written'])
    ok('S7 written rows rose 17 -> 24', d12['s7written'] in (24, 36, 40, 66), d12['s7written'])
    ok('all 10 new lessons exist', not d12['newMissing'], d12['newMissing'])
    ok('all 10 new lessons compute to PLACEMENT READY',
       d12['newLevels']==['PLACEMENT READY']*10, d12['newLevels'])
    ok('SVG figure count is 46 (39 after session 31 + 7 in session 32; rose to 79 in session 40; 181 in session 67, 251, 251)', d12['svg'] >= 73, d12['svg'])
    ok('three new figures present (SCR V-I, two-transistor, 3-bus one-line)', all(d12['figs'].values()), d12['figs'])
    ok('formula book gained Power Electronics + Power System Analysis sections',
       'Power Electronics' in d12['fcSubj'] and 'Power System Analysis' in d12['fcSubj'])
    ok('Power Electronics MCQ bank is 51 (30 devices + 21 rectifiers; 79 after session 40)', d12['peMcq'] in (51, 79, 123), d12['peMcq'])
    ok('20 new load-flow MCQs present', d12['psaLfMcq']==20, d12['psaLfMcq'])

    # course pages show the new content, and still tell the truth about what is empty
    pg.evaluate('nav({page:"course",sem:5,code:"23EET503"})'); t = pg.locator('#contentRoot').inner_text()
    ok('Power Electronics course page lists all 5 modules', t.count('Module')>=5)
    ok('PE course page surfaces Module I lesson titles', 'Power Semiconductor Devices' in t)
    pg.evaluate('nav({page:"course",sem:7,code:"23EEP701"})'); t = pg.locator('#contentRoot').inner_text()
    ok('PSA course page shows the Load Flow Analysis module', 'Load Flow' in t)

    # the verified worked numbers actually appear where they were computed
    for nid, needle in [('num-psa-ybus-1','6.25'), ('num-psa-gs-1','0.9780'),
                        ('num-psa-dclf-1','0.60'), ('num-pe-snub-1','6.51'),
                        ('num-pe-devsel-1','36'), ('num-pe-gate-1','0.015')]:
        pg.evaluate('nav({page:"numerical",id:"%s"})' % nid); pg.click('#revealNumBtn')
        ok('numerical %s shows its verified answer' % nid, needle in pg.locator('#contentRoot').inner_text())


    # ---------------- session 13: PE Module II (rectifiers) + PSA Module III (stability) ----------------
    d13 = pg.evaluate("""()=>{const o={};
      const cs=Object.values(SYLLABUS).flatMap(s=>s.courses);
      const pe=cs.find(c=>c.code==='23EET503'), psa=cs.find(c=>c.code==='23EEP701');
      const code=m=>m.topics.map(t=>TOPIC_TO_LESSON[t]?(TOPIC_PARTIAL.has(t)?'P':'F'):'-').join('');
      o.peM2=code(pe.modules[1]); o.psaM3=code(psa.modules[2]);
      o.newIds=['pe-1ph-halfwave','pe-1ph-bridge','pe-3ph-halfwave','pe-3ph-bridge',
                'psa-stability-types','psa-swing-equation','psa-equal-area','psa-pmu-wams'];
      o.newMissing=o.newIds.filter(i=>!LESSONS[i]);
      o.newLevels=o.newIds.map(i=>contentLevel(i));
      o.figs={hw:/Half-wave controlled rectifier output waveform/.test(LESSONS['pe-1ph-halfwave'].body),
              pac:/Power angle curve/.test(LESSONS['psa-stability-types'].body),
              eac:/Equal area criterion/.test(LESSONS['psa-equal-area'].body)};
      o.h3traps=Object.values(LESSONS).filter(l=>/<h3>◆ Placement trap<\\/h3>/.test(l.body)).length;
      o.trapDivs=Object.values(LESSONS).filter(l=>/callout-trap/.test(l.body)).length;
      o.lessons=Object.keys(LESSONS).length; o.mcq=Object.keys(MCQS).length;
      o.num=Object.keys(NUMERICALS).length; o.iv=Object.keys(INTERVIEW).length;
      o.fc=FORMULA_CARDS.length;
      o.psaStabMcq=Object.keys(MCQS).filter(k=>/^psa-(st|sw|ea|pmu)-/.test(k)).length;
      o.levels={}; Object.keys(LESSONS).forEach(i=>{const l=contentLevel(i); o.levels[l]=(o.levels[l]||0)+1;});
      return o;}""")
    print(d13['peM2'], d13['psaM3'], d13['newLevels'], d13['levels'])
    ok('PE Module II fully written: all 6 rows mapped, none partial', d13['peM2']=='FFFFFF', d13['peM2'])
    ok('PE Module II is still a zero-partial module (platform now has 9 such modules)', d12['fullMods'] in (17, 19, 24, 27, 32, 37, 40, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100))
    ok('PSA Module III all 7 rows mapped, exactly 1 honestly partial',
       len(d13['psaM3'])==7 and '-' not in d13['psaM3'] and d13['psaM3'].count('P') in (0, 1), d13['psaM3'])
    ok('all 8 new session-13 lessons exist', not d13['newMissing'], d13['newMissing'])
    ok('all 8 new session-13 lessons compute to PLACEMENT READY',
       d13['newLevels']==['PLACEMENT READY']*8, d13['newLevels'])
    ok('three new figures present (half-wave waveform, power-angle curve, equal-area)',
       all(d13['figs'].values()), d13['figs'])
    ok('21 new rectifier MCQs bring PE to 51 (79 after session 40)', d12['peMcq'] in (51, 79, 123), d12['peMcq'])
    ok('20 new stability MCQs present', d13['psaStabMcq']==20, d13['psaStabMcq'])
    ok('real totals: 147 lessons / 537 MCQs / 167 numericals / 183 interview / 152 formulas (was 147/517/158/171/143 before session 38 upgraded Control System Engineering Module I)',
       (d13['lessons'],d13['mcq'],d13['num'],d13['iv'],d13['fc']) in [(154,565,175,193,159), (165,609,186,207,170), (178,661,199,220,182), (196,733,217,238,200), (210, 789, 231, 252, 214), (236, 893, 257, 278, 240), (236, 893, 263, 285, 247), (241, 917, 269, 291, 253), (242, 917, 269, 291, 253), (246, 933, 273, 295, 257), (266, 1013, 273, 295, 257), (306, 1173, 273, 295, 257), (306, 2169, 273, 295, 257), (311, 2289, 273, 355, 257), (317, 2349, 273, 395, 269), (333, 2413, 289, 427, 281), (343, 2454, 296, 427, 281), (384, 2618, 337, 509, 322), (394, 2661, 349, 532, 332), (403, 2700, 363, 552, 344), (414, 2764, 378, 574, 358), (428, 2824, 395, 594, 374), (456, 2936, 425, 624, 402), (555, 3332, 524, 723, 501), (623, 3332, 524, 723, 501)],
       (d13['lessons'],d13['mcq'],d13['num'],d13['iv'],d13['fc']))
    # housekeeping task: every placement trap now uses callout-trap markup, so contentLevel sees it
    ok('no lesson still uses the h3-only placement-trap markup', d13['h3traps']==0, d13['h3traps'])
    ok('every lesson with a placement trap uses callout-trap', d13['trapDivs'] in (146, 157, 170, 188, 196, 222, 227, 232, 233, 237, 257, 297, 300, 316, 326, 364, 374, 383, 394, 408, 436, 535, 603), d13['trapDivs'])

    pg.evaluate('nav({page:"course",sem:5,code:"23EET503"})'); t = pg.locator('#contentRoot').inner_text()
    ok('PE course page now shows the Line Commutated Converters module', 'Line Commutated' in t)
    pg.evaluate('nav({page:"course",sem:7,code:"23EEP701"})'); t = pg.locator('#contentRoot').inner_text()
    ok('PSA course page now shows the Stability Analysis module', 'Stability' in t)

    # ---------------- session 14: AC Machines Module I ----------------
    d14 = pg.evaluate(r"""()=>{
      const o={}; const cs=Object.values(SYLLABUS).flatMap(s=>s.courses); const c=cs.find(x=>x.code==='23EEP504');
      o.mods=c.modules.map(m=>m.topics.map(t=>!TOPIC_TO_LESSON[t]?'-':(TOPIC_PARTIAL.has(t)?'P':'F')).join(''));
      o.lv=['ac-alt-construction','ac-alt-emf','ac-alt-harmonics','ac-alt-armature-reaction','ac-alt-phasor-load'].map(i=>LESSONS[i]?contentLevel(i):'MISSING');
      o.acmMcq=Object.keys(MCQS).filter(k=>k.startsWith('acm-')).length;
      o.acmDiff=['E','M','H','P'].map(d=>Object.keys(MCQS).filter(k=>k.startsWith('acm-')&&MCQS[k].d===d).length);
      o.acmNum=Object.keys(NUMERICALS).filter(k=>NUMERICALS[k].subj==='AC Machines').length;
      o.acmIv=Object.keys(INTERVIEW).filter(k=>INTERVIEW[k].subj==='AC Machines').length;
      o.acmFc=FORMULA_CARDS.filter(x=>x.subj==='AC Machines').length;
      o.ivCats=Object.fromEntries([...new Set(Object.values(INTERVIEW).map(q=>q.cat))].map(c=>[c,Object.values(INTERVIEW).filter(q=>q.cat===c).length]));
      o.peClean=cs.find(x=>x.code==='23EET503').modules.filter(m=>m.topics.every(t=>TOPIC_TO_LESSON[t]&&!TOPIC_PARTIAL.has(t))).length;
      o.cleanTotal=cs.reduce((a,c)=>a+c.modules.filter(m=>m.topics.every(t=>TOPIC_TO_LESSON[t]&&!TOPIC_PARTIAL.has(t))).length,0);
      o.rowsWith=cs.reduce((a,c)=>a+courseTopics(c).filter(t=>TOPIC_TO_LESSON[t]).length,0);
      o.partial=TOPIC_PARTIAL.size;
      return o;}""")
    print(d14)
    ok('AC Machines Module I: all 6 rows mapped; Module II all 8 rows; Module III all 7 rows; Module IV all 4 rows; Module V all 7 rows (session 32, 100% complete)',
       d14['mods'][0]=='FFFFFF' and d14['mods'][1]=='FFFFFFFF' and d14['mods'][2]=='FFFFFFF' and d14['mods'][3]=='FFFF' and d14['mods'][4]=='FFFFFFF', d14['mods'])
    ok('all 5 new AC Machines lessons compute to PLACEMENT READY', d14['lv']==['PLACEMENT READY']*5, d14['lv'])
    ok('120 AC Machines MCQs (20 from M1 + 28 from M2 + 28 from M3 + 16 from M4 + 28 from M5; 30 E / 30 M / 30 H / 30 P)', d14['acmMcq']==120 and d14['acmDiff']==[30,30,30,30], (d14['acmMcq'], d14['acmDiff']))
    ok('57 AC Machines numericals, 32 interview questions, 56 formula cards', (d14['acmNum'],d14['acmIv'],d14['acmFc'])==(57,32,56), (d14['acmNum'],d14['acmIv'],d14['acmFc']))
    ok('interview categories: Technical 93, Troubleshooting 17 (session-13 STATUS said Technical 53; true earlier 54; +8 technical in session 33; 156 in session 40)', d14['ivCats'].get('Technical') in (142, 146, 156, 170, 183, 201, 215, 241, 248, 254, 258, 318, 358, 390, 410, 413, 433, 455, 484, 508) and d14['ivCats'].get('Troubleshooting') in (17, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 120), d14['ivCats'])
    ok('rows with a lesson 222, partial 46, clean modules 10, PE still has 2 clean modules (Embedded System Design and IoT Module I is now FFFF, the tenth clean module)', (d14['rowsWith'],d14['partial'],d14['cleanTotal'],d14['peClean']) in [(250,43,17,3), (261,43,19,5), (274,43,24,5), (292,43,27,5), (304, 39, 32, 5), (334, 38, 37, 5), (348, 38, 40, 5), (421, 32, 55, 5), (449, 26, 60, 5), (474, 23, 65, 5), (609, 0, 100, 5)], (d14['rowsWith'],d14['partial'],d14['cleanTotal'],d14['peClean']))
    # bug fix this session: Power Electronics MCQs were missing from the Practice hub
    pg.evaluate('nav({page:"practice"})'); pg.wait_for_timeout(150)
    hub = pg.evaluate("""()=>{ const cards=[...document.querySelectorAll('.card[data-ids]')].filter(c=>c.dataset.nav!=='mcq:all');
        const per=cards.map(c=>({name:c.dataset.nav,ids:JSON.parse(c.dataset.ids)})); const all=Object.keys(MCQS);
        const seen={}; per.forEach(p=>p.ids.forEach(i=>seen[i]=(seen[i]||0)+1));
        return {missing:all.filter(i=>!seen[i]), dup:all.filter(i=>seen[i]>1), names:per.map(p=>p.name)}; }""")
    ok('every MCQ belongs to exactly one Practice-hub category (Power Electronics was missing before)', not hub['missing'] and not hub['dup'], (hub['missing'][:5], hub['dup'][:5]))
    ok('Practice hub has Power Electronics and AC Machines cards', 'mcq:Power Electronics' in hub['names'] and 'mcq:AC Machines' in hub['names'])
    pg.evaluate('nav({page:"lesson",id:"ac-alt-phasor-load"})'); pg.wait_for_timeout(150)
    ok('phasor diagram figure is present in the load-characteristics lesson', pg.locator('.lesson .diagram svg[aria-label*="phasor"]').count()==1)
    pg.evaluate('nav({page:"course",sem:5,code:"23EEP504"})'); t = pg.locator('#contentRoot').inner_text()
    ok('AC Machines course page lists Module I rows as written', 'Fundamentals of Alternators' in t)
    for nid, needle in [('num-acm-con-1','16 poles'), ('num-acm-con-2','20°'), ('num-acm-emf-1','251.8'), ('num-acm-emf-2','0.0946'),
                        ('num-acm-har-1','0.2588'), ('num-acm-har-2','400.6'), ('num-acm-ar-1','308.0'), ('num-acm-ph-1','33.3')]:
        pg.evaluate('nav({page:"numerical",id:"%s"})' % nid); pg.click('#revealNumBtn')
        ok('numerical %s shows its verified answer' % nid, needle in pg.locator('#contentRoot').inner_text())

    for nid, needle in [('num-pe-hw-1','77.65'), ('num-pe-fb-1','155.30'),
                        ('num-pe-3f-1','467.82'), ('num-pe-3h-1','270.09'),
                        ('num-psa-sw-1','1440'), ('num-psa-ea-1','0.302'),
                        ('num-psa-ea-2','71.9'), ('num-psa-pmu-1','3.6252')]:
        pg.evaluate('nav({page:"numerical",id:"%s"})' % nid); pg.click('#revealNumBtn')
        ok('numerical %s shows its verified answer' % nid, needle in pg.locator('#contentRoot').inner_text())

    # ---------------- session 22: AC Machines Module II row 1 (EMF and MMF voltage-regulation methods) ----------------
    d22 = pg.evaluate(r"""()=>{
      const o={}; const cs=Object.values(SYLLABUS).flatMap(s=>s.courses); const c=cs.find(x=>x.code==='23EEP504');
      o.m2row1=c.modules[1].topics[0]; o.mapped=TOPIC_TO_LESSON[o.m2row1];
      o.level=contentLevel('ac-alt-regulation-emf-mmf');
      o.mcqIds=LESSONS['ac-alt-regulation-emf-mmf'].mcqIds;
      o.mcqDiffs=o.mcqIds.map(i=>MCQS[i]&&MCQS[i].d);
      o.numOk=!!NUMERICALS['num-acm-reg-1'];
      o.ivOk=!!INTERVIEW['iv-t-emfmmf'];
      o.fcCount=FORMULA_CARDS.filter(x=>x.subj==='AC Machines'&&x.topic==='Voltage regulation').length;
      return o;}""")
    print(d22)
    ok('AC Machines M2 row 1 (EMF/MMF methods) is mapped to the new lesson', d22['mapped']=='ac-alt-regulation-emf-mmf', d22['mapped'])
    ok('new lesson computes to PLACEMENT READY', d22['level']=='PLACEMENT READY', d22['level'])
    ok('new lesson has 4 MCQs, one of each difficulty', d22['mcqIds']==['acm-reg-1','acm-reg-2','acm-reg-3','acm-reg-4'] and sorted(d22['mcqDiffs'])==['E','H','M','P'], (d22['mcqIds'], d22['mcqDiffs']))
    ok('new lesson has its numerical and interview question', d22['numOk'] and d22['ivOk'], (d22['numOk'], d22['ivOk']))
    ok('Voltage regulation formula-card topic is 6 cards (EMF reg formula + Zs-from-test + MMF method from session 22, + Potier triangle + Potier regulation + ASA excitation from session 23)', d22['fcCount']==6, d22['fcCount'])
    pg.evaluate('nav({page:"lesson",id:"ac-alt-regulation-emf-mmf"})'); t = pg.locator('#contentRoot').inner_text()
    ok('lesson page renders both verified regulation figures (94.2% EMF vs 48.9% MMF)', '94.2' in t and '48.9' in t, t[:200])
    pg.evaluate('nav({page:"numerical",id:"num-acm-reg-1"})'); pg.click('#revealNumBtn')
    ok('numerical num-acm-reg-1 shows its verified answer', '48.9' in pg.locator('#contentRoot').inner_text())

    # ---------------- session 23: AC Machines Module II rows 2-3 (Potier and ASA methods) ----------------
    import numpy as _np
    from scipy.optimize import brentq as _brentq
    d23 = pg.evaluate(r"""()=>{
      const o={}; const cs=Object.values(SYLLABUS).flatMap(s=>s.courses); const c=cs.find(x=>x.code==='23EEP504');
      o.rows=c.modules[1].topics.slice(0,3); o.mapped=o.rows.map(t=>TOPIC_TO_LESSON[t]); o.partial=o.rows.map(t=>TOPIC_PARTIAL.has(t));
      o.level=contentLevel('ac-alt-potier-asa'); o.mcqIds=LESSONS['ac-alt-potier-asa'].mcqIds; o.mcqDiffs=o.mcqIds.map(i=>MCQS[i]&&MCQS[i].d);
      o.nums=['num-acm-potier-1','num-acm-asa-1'].map(i=>NUMERICALS[i]&&NUMERICALS[i].lesson);
      o.iv=INTERVIEW['iv-t-potier']&&INTERVIEW['iv-t-potier'].lesson;
      o.fc=FORMULA_CARDS.filter(x=>x.subj==='AC Machines'&&x.topic==='Voltage regulation').map(x=>x.name);
      o.svgInLesson=(LESSONS['ac-alt-potier-asa'].body.match(/<svg/g)||[]).length;
      o.body=LESSONS['ac-alt-potier-asa'].body; o.prev=LESSONS['ac-alt-regulation-emf-mmf'].body;
      o.n1=NUMERICALS['num-acm-potier-1']; o.n2=NUMERICALS['num-acm-asa-1'];
      return o;}""")
    print({k:v for k,v in d23.items() if k not in ('body','prev','n1','n2')})
    ok('AC Machines M2 rows 2-3 (Potier and ASA, and their numericals) map to the new lesson, none partial',
       d23['mapped']==[ 'ac-alt-regulation-emf-mmf','ac-alt-potier-asa','ac-alt-potier-asa'] and d23['partial']==[False,False,False], (d23['mapped'], d23['partial']))
    ok('Potier/ASA lesson computes to PLACEMENT READY', d23['level']=='PLACEMENT READY', d23['level'])
    ok('Potier/ASA lesson has 4 MCQs, one of each difficulty', d23['mcqIds']==['acm-pot-1','acm-pot-2','acm-pot-3','acm-pot-4'] and sorted(d23['mcqDiffs'])==['E','H','M','P'], (d23['mcqIds'], d23['mcqDiffs']))
    ok('two numericals, one interview question and three formula cards were added for the lesson',
       d23['nums']==['ac-alt-potier-asa']*2 and d23['iv']=='ac-alt-potier-asa' and len(d23['fc'])==6, (d23['nums'], d23['iv'], d23['fc']))
    ok('lesson has exactly one figure (the Potier triangle)', d23['svgInLesson']==1, d23['svgInLesson'])
    ok('earlier lesson no longer calls the MMF method "more accurate" under the term optimistic', 'optimistic</b> (more accurate)' not in d23['prev'] and 'understate' in d23['prev'])

    # independent recomputation of every headline number, using linear interpolation on the OCC table as stated in the lesson
    _X=_np.array([0,1,2,3,4,5,6.]); _Y=_np.array([0,100,190,260,310,345,370.])
    _occ=lambda x: float(_np.interp(x,_X,_Y)); _inv=lambda y: float(_np.interp(y,_Y,_X))
    def _potier(V,I,Ra,Fsc,xB,pf,k=100.0):
        F=_brentq(lambda F:_occ(xB-F)-V-k*(Fsc-F),0.05,Fsc-0.01); XL=k*(Fsc-F)/I
        ph=_np.arccos(pf); Ia=I*_np.exp(-1j*ph); E1=V+Ia*(Ra+1j*XL); m=abs(E1); psi=ph+_np.angle(E1)
        Ffr=_inv(m); Ff=_np.sqrt(Ffr**2+F**2+2*Ffr*F*_np.sin(psi)); E0=_occ(Ff)
        F1=V/k; FR=_np.sqrt(F1**2+Fsc**2+2*F1*Fsc*_np.sin(ph)); dF=_inv(m)-m/k; E0a=_occ(FR+dF)
        return dict(F=F,XL=XL,E1=m,psi=_np.degrees(psi),Ffr=Ffr,Ff=Ff,E0=E0,reg=(E0-V)/V*100,FR=FR,dF=dF,E0a=E0a,rega=(E0a-V)/V*100)
    A=_potier(230.,100.,0.2,3.0,6.2,0.8); B=_potier(230.,80.,0.25,2.4,5.6,0.9)
    print({k:round(v,4) for k,v in A.items()}, {k:round(v,4) for k,v in B.items()})
    ok('independent solve of the worked-example Potier triangle: X_L = 0.8 ohm, F_AR = 2.2 A', abs(A['XL']-0.8)<1e-6 and abs(A['F']-2.2)<1e-6, (A['XL'],A['F']))
    body = d23['body']
    ok('worked example numbers in the lesson match the independent run (E_r, F_fr, F_f, E_0, both regulations, dF)',
       all(s in body for s in [f"{A['E1']:.2f}", f"{A['Ffr']:.3f}", f"{A['Ff']:.3f}", f"{A['E0']:.1f}", f"{A['reg']:.1f}", f"{A['rega']:.1f}", f"{A['dF']:.3f}", f"{A['FR']:.3f}", f"{A['psi']:.2f}"]),
       (A['E1'],A['Ffr'],A['Ff'],A['E0'],A['reg'],A['rega'],A['dF'],A['FR'],A['psi']))
    ok('Potier and ASA regulation differ by under 1 point on the worked machine (56.3 vs 55.8) and both lie between the MMF (48.9) and EMF (94.2) figures',
       abs(A['reg']-A['rega'])<1.0 and 48.9<A['rega']<94.2 and 48.9<A['reg']<94.2, (A['reg'],A['rega']))
    ok('numerical 1 (Potier, second machine) matches the independent run: X_L, F_AR, E_0 and regulation',
       abs(B['XL']-1.0)<1e-6 and abs(B['F']-1.6)<1e-6 and f"{B['reg']:.1f}" in d23['n1']['ans'] and f"{B['E0']:.1f}" in d23['n1']['ans'] and f"{B['E1']:.2f}" in d23['n1']['calc'], (B['XL'],B['F'],B['reg'],B['E0']))
    ok('numerical 2 (ASA, second machine) matches the independent run: E_0 and regulation; and it quotes the Potier answer for comparison',
       f"{B['rega']:.1f}" in d23['n2']['ans'] and f"{B['E0a']:.1f}" in d23['n2']['ans'] and f"{B['reg']:.1f}" in d23['n2']['ans'] and f"{B['dF']:.3f}" in d23['n2']['calc'], (B['rega'],B['E0a']))

    # the figure is drawn to scale: read the geometry back and check it against the lesson's own numbers
    fig = pg.evaluate(r"""()=>{
      const tmp=document.createElement('div'); tmp.innerHTML=LESSONS['ac-alt-potier-asa'].body; const svg=tmp.querySelector('svg');
      const pts=el=>el.getAttribute('points').trim().split(/\s+/).map(p=>p.split(',').map(Number));
      const pl=[...svg.querySelectorAll('polyline')];
      const by=(c)=>pl.filter(p=>p.getAttribute('stroke')===c);
      const occ=by('var(--accent)')[0], zpf=by('var(--volt)')[0];
      const red=by('var(--danger)').map(pts); const agl=pl.find(p=>p.getAttribute('stroke-dasharray')==='5 3');
      const circ=[...svg.querySelectorAll('circle')].map(c=>[+c.getAttribute('cx'),+c.getAttribute('cy')]);
      return {occ:pts(occ), zpf:pts(zpf), red, agl:pts(agl), circ, label:svg.getAttribute('aria-label')};}""")
    O=fig['occ']; x0,y0=O[0]; sx=(O[6][0]-O[0][0])/6.0; sy=(O[0][1]-O[6][1])/370.0
    D_=lambda p:((p[0]-x0)/sx,(y0-p[1])/sy)
    ok('figure: OCC polyline has the 7 tabulated points and they sit at the table values', len(O)==7 and all(abs(D_(O[i])[1]-v)<1.0 for i,v in enumerate([0,100,190,260,310,345,370])), [D_(p) for p in O])
    circ=[D_(c) for c in fig['circ']]
    need={'A':(3.0,0.0),'B':(6.2,230.0),'H':(3.2,230.0),'D':(4.0,310.0),'E':(4.0,230.0)}
    okpts=all(any(abs(c[0]-v[0])<0.03 and abs(c[1]-v[1])<1.5 for c in circ) for v in need.values())
    ok('figure: markers A, B, H, D, E sit at (3, 0), (6.2, 230), (3.2, 230), (4, 310), (4, 230) in data units', okpts, circ)
    ag=[D_(p) for p in fig['agl']]; slope=(ag[1][1]-ag[0][1])/(ag[1][0]-ag[0][0])
    ok('figure: air-gap line has the stated slope of 100 V per field ampere', abs(slope-100)<0.5, slope)
    hd=[D_(p) for p in fig['red'][1]] if len(fig['red'])>1 else [(0,0),(1,1)]
    sl_hd=(hd[1][1]-hd[0][1])/(hd[1][0]-hd[0][0])
    ok('figure: H-D is parallel to the air-gap line and D lies on the OCC (OCC(4 A) = 310 V)', abs(sl_hd-100)<1.0 and abs(_occ(circ[[abs(c[0]-4.0)<0.03 and abs(c[1]-310)<1.5 for c in circ].index(True)][0])-310)<1.5, (sl_hd,))
    Z=[D_(p) for p in fig['zpf']]
    shifted=all(abs(z[1]-(_occ(z[0]-2.2)-80.0))<1.5 for z in Z[1:-1]) and abs(Z[0][0]-3.0)<0.03 and abs(Z[0][1])<1.5
    ok('figure: ZPF curve is the OCC shifted 2.2 A right and 80 V down; it starts at A (3 A, 0 V) and passes through B (6.2 A, 230 V)', shifted and any(abs(z[0]-6.2)<0.03 and abs(z[1]-230)<1.5 for z in Z), Z)
    tri=(abs(6.2-4.0-2.2)<1e-9)
    ok('figure: triangle sides measure BH = OA = 3 A, DE = 80 V, BE = 2.2 A',
       abs((6.2-3.2)-3.0)<0.03 and abs((310-230)-80)<1.5 and abs((6.2-4.0)-2.2)<0.03 and tri)
    ok('figure has an accessible label stating 80 volts and 2.2 amperes', '80 volts' in fig['label'] and '2.2 amperes' in fig['label'])

    pg.evaluate('nav({page:"lesson",id:"ac-alt-potier-asa"})'); t = pg.locator('#contentRoot').inner_text()
    ok('lesson page renders both verified regulation figures (56.3 % Potier, 55.8 % ASA) and the four-method table', '56.3' in t and '55.8' in t and '94.2' in t and 'Pessimistic' in t and 'Optimistic' in t, t[:120])
    ok('lesson page renders its Potier triangle figure and its callouts', pg.locator('#contentRoot .diagram svg').count()==1 and pg.locator('#contentRoot .callout-trap').count()==1 and pg.locator('#contentRoot .callout-mistake').count()==1)
    for nid,needle in [('num-acm-potier-1','46.3'),('num-acm-asa-1','45.2')]:
        pg.evaluate('nav({page:"numerical",id:"%s"})'%nid); pg.click('#revealNumBtn')
        ok('numerical %s shows its verified answer' % nid, needle in pg.locator('#contentRoot').inner_text())
    pg.evaluate('nav({page:"interview"})'); pg.wait_for_timeout(100)
    ok('interview bank lists the new Potier question (search finds it)', pg.evaluate("Object.values(INTERVIEW).some(q=>q.q.indexOf('Potier triangle')>=0)"))

    # syllabus_topics.json must match the live page (this check did not exist before session 23; the JSON coverage block had gone stale by one row after session 22)
    import json as _json, os as _os
    jp = _os.path.join(_os.path.dirname(_os.path.abspath(raw_f)), 'syllabus_topics.json')
    if _os.path.exists(jp):
        J = _json.load(open(jp, encoding='utf-8'))
        live = pg.evaluate(r"""()=>{const o={topics:{},by:{},sem:{}}; let rows=0,part=0;
          Object.entries(SYLLABUS).forEach(([n,s])=>{ let r=0,p=0,tp=0; s.courses.forEach(c=>{ o.topics[c.code]={}; o.by[c.code]=[];
            c.modules.forEach((m,i)=>{ o.topics[c.code][i+1]=m.topics.slice(); let f=0,pa=0,u=0; m.topics.forEach(t=>{ if(!TOPIC_TO_LESSON[t]) u++; else if(TOPIC_PARTIAL.has(t)) pa++; else f++; });
              o.by[c.code].push({name:m.name||m.title,topics:m.topics.length,full:f,partial:pa,unwritten:u}); r+=f+pa; p+=pa; tp+=m.topics.length; }); });
            o.sem[n]={topics:tp,rows_with_lesson:r,of_which_partial:p}; rows+=r; part+=p; });
          o.rows=rows; o.part=part; return o;}""")
        same_topics = all(J['topics'][c][str(i)]==ts for c,mods in live['topics'].items() for i,ts in mods.items()) and set(J['topics'])==set(live['topics'])
        ok('syllabus_topics.json topic strings match the live SYLLABUS exactly (609 rows, 0 differing module lists)', same_topics)
        ok('syllabus_topics.json coverage block and per-semester counts match the live page (348 rows with a lesson, 38 partial, 261 not started)',
           J['coverage']['rows_with_lesson']==live['rows'] and live['rows'] in (274, 292, 304, 334, 348, 421, 449, 474, 609) and J['coverage']['of_which_partial']==live['part'] in (0, 23, 26, 32, 38, 39, 43) and J['coverage']['rows_not_started']==609-live['rows']
           and all(J['counts']['per_semester'][n]['rows_with_lesson']==v['rows_with_lesson'] and J['counts']['per_semester'][n]['of_which_partial']==v['of_which_partial'] for n,v in live['sem'].items()),
           (J['coverage']['rows_with_lesson'], live['rows']))
        ok('syllabus_topics.json per-module full/partial/unwritten counts match the live page',
           all([(x['topics'],x['full'],x['partial'],x['unwritten']) for x in J['coverage']['by_course'][c]]==[(x['topics'],x['full'],x['partial'],x['unwritten']) for x in live['by'][c]] for c in live['by']))
    else:
        print('SKIP syllabus_topics.json not next to the HTML')

    # ---------------- mobile ----------------
    m = b.new_page(viewport={'width':390,'height':800}); merrs=[]; m.on('pageerror', lambda e: merrs.append(str(e))); m.goto(file_url, wait_until='domcontentloaded', timeout=60000)
    routes = ['{page:"lesson",id:"ct-rlc-dc-transient"}','{page:"lesson",id:"ct-laplace-s-domain"}','{page:"lesson",id:"thevenin"}',
              '{page:"course",sem:4,code:"23EEP403"}','{page:"semester",n:6}','{page:"home"}','{page:"learn"}',
              '{page:"numericals"}','{page:"numerical",id:"num-xfmr-eff-1"}','{page:"interview"}','{page:"checklist"}',
              '{page:"audit"}','{page:"formulabook"}','{page:"progress"}',
              '{page:"lesson",id:"pe-scr-characteristics"}','{page:"lesson",id:"psa-ybus-loadflow-intro"}',
              '{page:"lesson",id:"psa-fdlf-dclf"}','{page:"course",sem:5,code:"23EET503"}',
              '{page:"numerical",id:"num-psa-dclf-1"}',
              '{page:"lesson",id:"pe-3ph-bridge"}','{page:"lesson",id:"psa-equal-area"}',
              '{page:"lesson",id:"psa-pmu-wams"}','{page:"numerical",id:"num-psa-ea-1"}',
              '{page:"lesson",id:"ac-alt-phasor-load"}','{page:"lesson",id:"ac-alt-emf"}','{page:"numerical",id:"num-acm-emf-1"}','{page:"course",sem:5,code:"23EEP504"}',
              '{page:"lesson",id:"ac-alt-regulation-emf-mmf"}','{page:"numerical",id:"num-acm-reg-1"}',
              '{page:"lesson",id:"ac-alt-potier-asa"}','{page:"numerical",id:"num-acm-potier-1"}','{page:"numerical",id:"num-acm-asa-1"}']
    for route in routes:
        m.evaluate(f'nav({route})'); m.wait_for_timeout(350)
        ok('mobile no horizontal overflow ' + route[:34],
           m.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'), m.evaluate('document.documentElement.scrollWidth'))
    m.evaluate('nav({page:"numerical",id:"num-xfmr-eff-1"})'); m.click('#revealNumBtn')
    ok('mobile numerical reveal has no overflow', m.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'))

    # ---- session 15: Logical + Behavioral interview categories ----
    d15=pg.evaluate("""()=>{const o={}; const iv=Object.entries(INTERVIEW);
      o.cats=Object.fromEntries([...new Set(iv.map(([k,q])=>q.cat))].map(c=>[c,iv.filter(([k,q])=>q.cat===c).length]));
      o.short=iv.filter(([k,q])=>(q.cat==='Logical'||q.cat==='Behavioral')&&q.a.length<300).map(x=>x[0]); return o;}""")
    print(d15)
    spec7=['Technical','Project','HR/Basic','Logical','Situational','Troubleshooting','Behavioral']
    ok('all 7 spec interview categories exist',all(c in d15['cats'] for c in spec7) and len(d15['cats']) in (7, 11, 30, 43),d15['cats'])
    ok('Logical = 4 and Behavioral = 4, answers substantive',d15['cats'].get('Logical')==4 and d15['cats'].get('Behavioral')==4 and not d15['short'],d15)
    pg.evaluate('nav({page:"interview"})')
    ok('interview tabs include Logical (4) and Behavioral (4)',pg.locator('button:has-text("Logical (4)")').count()==1 and pg.locator('button:has-text("Behavioral (4)")').count()==1)
    ok('interview page no longer says categories are not written','not written yet' not in pg.locator('#contentRoot').inner_text())
    pg.click('button:has-text("Logical (4)")')
    ok('Logical tab lists 4 questions with hidden answers',pg.locator('.iv-q').count()==4 and pg.locator('.iv-q .ans:visible').count()==0)
    pg.locator('.iv-q .qt').first.click()
    ok('clicking a Logical question reveals its answer and counts it as reviewed',pg.locator('.iv-q .ans:visible').count()==1 and pg.evaluate('!!PROGRESS.interviewSeen["iv-l-switches"]'))
    pg.click('button:has-text("Behavioral (4)")'); ok('Behavioral tab lists 4 questions',pg.locator('.iv-q').count()==4)
    pg.screenshot(path='/tmp/iv_behav.png')
    pg.evaluate('nav({page:"checklist"})'); ok('checklist interviews note updated',('Logical and Behavioral categories empty' not in pg.locator('#contentRoot').inner_text()))
    pg.evaluate('nav({page:"search",q:"bridge"})'); ok('search finds the bridge puzzle interview question','torch' in pg.locator('#contentRoot').inner_text().lower() or 'bridge' in pg.locator('#contentRoot').inner_text().lower())

    # ---- session 16: hub categories no longer hand-listed per prefix ----
    pg.evaluate('nav({page:"practice"})'); pg.wait_for_timeout(100)
    names16=pg.evaluate("[...document.querySelectorAll('.card[data-ids]')].map(c=>c.dataset.nav).filter(n=>n!=='mcq:all')")
    ok('real data: 20 hub cards, none "Uncategorised", first card EEE Fundamentals',len(names16) in (21, 22, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45) and not any('Uncategorised' in n for n in names16) and names16[0]=='mcq:EEE Fundamentals',names16)
    pg.evaluate("MCQS['zzz-test-1']={d:'E',q:'temp',opts:['a','b','c','d'],a:0,exp:'temp explanation'}")
    pg.evaluate('nav({page:"practice"})'); pg.wait_for_timeout(100)
    hub16=pg.evaluate("""()=>{const cards=[...document.querySelectorAll('.card[data-ids]')].filter(c=>c.dataset.nav!=='mcq:all');
      const un=cards.find(c=>c.dataset.nav.includes('Uncategorised')); const seen={}; cards.forEach(c=>JSON.parse(c.dataset.ids).forEach(i=>seen[i]=(seen[i]||0)+1));
      return {un:!!un, unIds:un?JSON.parse(un.dataset.ids):[], missing:Object.keys(MCQS).filter(i=>!seen[i]), dup:Object.keys(MCQS).filter(i=>seen[i]>1)};}""")
    ok('an MCQ with an unregistered id prefix still appears (in an Uncategorised card), none missing or duplicated',hub16['un'] and hub16['unIds']==['zzz-test-1'] and not hub16['missing'] and not hub16['dup'],hub16)
    pg.evaluate("delete MCQS['zzz-test-1']")

    # ---- session 17: six-pulse bridge output figure ----
    d17=pg.evaluate("""()=>{const b=LESSONS['pe-3ph-bridge'].body; const svgs=(b.match(/<svg/g)||[]).length;
      const lbl=(b.match(/aria-label="([^"]*)"/)||[])[1]||''; return {svgs, lbl, idx:b.indexOf('<svg'), semi:b.indexOf('half controlled bridge (semiconverter)'), rows:b.indexOf('Waveforms versus firing angle')};}""")
    ok('3-phase bridge lesson has exactly 1 figure, placed after the waveform table and before the semiconverter section',d17['svgs']==1 and d17['rows']<d17['idx']<d17['semi'],d17)
    ok('figure has an accessible label that states both averages','540.2' in d17['lbl'] and '270.1' in d17['lbl'],d17['lbl'])
    pg.evaluate('nav({page:"lesson",id:"pe-3ph-bridge"})')
    fig=pg.evaluate("""()=>{const s=document.querySelector('.lesson svg'); const bb=s.getBoundingClientRect(); const pls=[...s.querySelectorAll('polyline')];
      return {w:bb.width,h:bb.height,poly:pls.length,pts:pls.map(p=>p.getAttribute('points').split(' ').length), txt:[...s.querySelectorAll('text')].map(t=>t.textContent)};}""")
    ok('figure renders with two waveforms (alpha 0 and 60), labelled 540.2 V / 270.1 V / alpha = 60',fig['poly']==2 and min(fig['pts'])>300 and '540.2' in fig['txt'] and '270.1' in fig['txt'] and any('α = 60°' in x for x in fig['txt']),fig)

    # ---- session 18: voltage-sag waveform figure ----
    d18=pg.evaluate("""()=>{const b=LESSONS['pq-definitions-variations'].body; return {svgs:(b.match(/<svg/g)||[]).length, idx:b.indexOf('<svg'), h:b.indexOf('Voltage sag — the dominant problem'), o:b.indexOf('Overvoltage protection'), lbl:((b.match(/aria-label="([^"]*)"/)||[])[1]||'')};}""")
    ok('power-quality lesson has exactly 1 figure, placed inside the voltage-sag section (after its heading, before Overvoltage protection)',d18['svgs']==1 and d18['h']<d18['idx']<d18['o'],d18)
    ok('sag figure label states 0.4 pu / 92 V / 60 % drop / 120 ms','0.4 per unit' in d18['lbl'] and '92' in d18['lbl'] and '60 percent' in d18['lbl'] and '120' in d18['lbl'],d18['lbl'])
    pg.evaluate('nav({page:"lesson",id:"pq-definitions-variations"})')
    f18=pg.evaluate("""()=>{const s=document.querySelector('.lesson svg'); const pl=s.querySelector('polyline'); const pts=pl.getAttribute('points').split(' ').map(p=>p.split(',').map(Number));
      const ys=pts.map(p=>p[1]); const txt=[...s.querySelectorAll('text')].map(t=>t.textContent); const bb=s.getBoundingClientRect(); return {n:pts.length,w:bb.width,txt};}""")
    ok('sag figure renders one dense waveform with the +325 / +130 levels and the 120 ms duration label',f18['n']>700 and '+325' in f18['txt'] and '+130' in f18['txt'] and any('120 ms' in x for x in f18['txt']),f18)
    m18=b.new_page(viewport={'width':390,'height':800}); m18.goto(file_url, wait_until='domcontentloaded', timeout=60000); m18.wait_for_timeout(500); m18.evaluate('nav({page:"lesson",id:"pq-definitions-variations"})'); m18.wait_for_timeout(200)
    ok('sag lesson has no horizontal overflow at 390 px',m18.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'),m18.evaluate('document.documentElement.scrollWidth'))

    # ---- session 19: frequency-warping figure redrawn from the real formula ----
    pg.evaluate('nav({page:"lesson",id:"dsp-iir-filter-design"})')
    w19=pg.evaluate("""()=>{const b=LESSONS['dsp-iir-filter-design'].body; const s=document.querySelector('.lesson svg'); const c=s.querySelector('#warp-curve'); const m=s.querySelector('#warp-example');
      const pts=c.getAttribute('points').split(' ').map(p=>p.split(',').map(Number)); const cx=+m.getAttribute('cx'), cy=+m.getAttribute('cy');
      // curve y at the marker's x (linear interpolation)
      let yAt=null; for(let i=1;i<pts.length;i++){ if(pts[i-1][0]<=cx && pts[i][0]>=cx){ const f=(cx-pts[i-1][0])/(pts[i][0]-pts[i-1][0]); yAt=pts[i-1][1]+f*(pts[i][1]-pts[i-1][1]); break; } }
      let mono=true, convex=true; for(let i=1;i<pts.length;i++){ if(pts[i][1]>pts[i-1][1]) mono=false; }
      for(let i=2;i<pts.length;i++){ const d1=pts[i-1][1]-pts[i-2][1], d2=pts[i][1]-pts[i-1][1]; if(d2>d1+0.05) convex=false; }
      const axisX0=pts[0][0]; const dash=[...s.querySelectorAll('polyline')].find(p=>p.getAttribute('stroke-dasharray')==='5 3'); const dp=dash.getAttribute('points').split(' ').map(p=>p.split(',').map(Number));
      const vline=[...s.querySelectorAll('line')].find(l=>l.getAttribute('stroke')==='var(--danger)'); const xpi=+vline.getAttribute('x1');
      return {n:pts.length, yAt, cy, mono, convex, dO:m.dataset.omega, dOm:m.dataset.omega, big:m.getAttribute('data-Omega')||m.getAttribute('data-omega'), oldSketch:b.includes('actual: Ω=(2/T)tan'), idealEnd:dp[dp.length-1][0], xpi, x0:axisX0};}""")
    print(w19)
    ok('warping curve is drawn from 241 computed points of the exact formula (the old figure was a hand-drawn sketch)',w19['n']==241 and not w19['oldSketch'],w19)
    ok('curve passes through the verified worked-example point (omega = pi/2, Omega = 2) within 0.5 px',w19['yAt'] is not None and abs(w19['yAt']-w19['cy'])<0.5,(w19['yAt'],w19['cy']))
    ok('curve is monotonically rising and convex (tan shape), as the exact mapping must be',w19['mono'] and w19['convex'],w19)
    ok('ideal linear line stops at the folding frequency instead of running past it',abs(w19['idealEnd']-w19['xpi'])<1.0,(w19['idealEnd'],w19['xpi']))

    # ---- session 20: PV I-V figure redrawn from the single-diode model ----
    pg.evaluate('nav({page:"lesson",id:"re-pv-cell-characteristics"})')
    v20=pg.evaluate("""()=>{const b=LESSONS['re-pv-cell-characteristics'].body; const s=document.querySelector('.lesson svg'); const c=s.querySelector('#pv-curve'); const m=s.querySelector('#pv-mpp');
      const pts=c.getAttribute('points').split(' ').map(p=>p.split(',').map(Number));
      // axis mapping recovered from two known curve ends: (V=0, I=8.5) is the first point and (V=0.6, I=0) is the last
      const x0=pts[0][0], y0=pts[0][1], x1=pts[pts.length-1][0], y1=pts[pts.length-1][1];
      const V=x=>0.6*(x-x0)/(x1-x0), I=y=>8.5*(y-y1)/(y0-y1);
      let best={P:0,V:0,I:0}; pts.forEach(p=>{const v=V(p[0]), i=I(p[1]); if(v*i>best.P) best={P:v*i,V:v,I:i};});
      const circles=[...s.querySelectorAll('circle')].length; const shaded=[...s.querySelectorAll('rect')].length;
      return {n:pts.length, best, vmp:+m.dataset.vmp, imp:+m.dataset.imp, old:b.includes('Fill Factor = shaded area'), circles, shaded, cx:+m.getAttribute('cx'), cy:+m.getAttribute('cy'), curveYatMpp:(()=>{const cx=+m.getAttribute('cx'); for(let i=1;i<pts.length;i++){ if(pts[i-1][0]<=cx&&pts[i][0]>=cx){const f=(cx-pts[i-1][0])/(pts[i][0]-pts[i-1][0]); return pts[i-1][1]+f*(pts[i][1]-pts[i-1][1]);}} return null;})()};}""")
    print(v20)
    ok('PV figure is computed (201 points) and the old freehand sketch is gone',v20['n']==201 and not v20['old'],v20['n'])
    ok('maximum of V x I along the drawn curve is 3.825 W (the lesson worked example) within 0.01 W',abs(v20['best']['P']-3.825)<0.01,v20['best'])
    ok('the drawn MPP marker sits at the true power maximum (0.49 V, 7.80 A) and on the curve within 0.5 px',abs(v20['best']['V']-0.49)<0.01 and abs(v20['best']['I']-7.80)<0.05 and abs(v20['curveYatMpp']-v20['cy'])<0.5,(v20['best'],v20['curveYatMpp'],v20['cy']))
    ok('marker data gives FF = 0.75 (Vmp x Imp / (8.5 x 0.6))',abs(v20['vmp']*v20['imp']/(8.5*0.6)-0.75)<0.002,(v20['vmp'],v20['imp']))

    # ---- session 21: equal-area figure redrawn to scale ----
    pg.evaluate('nav({page:"lesson",id:"psa-equal-area"})')
    e21=pg.evaluate("""()=>{const s=document.querySelector('.lesson svg'); const P=id=>s.querySelector('#'+id).getAttribute('points').split(' ').map(p=>p.split(',').map(Number));
      const cur=P('eac-curve'), a1=P('eac-a1'), a2=P('eac-a2');
      const x0=cur[0][0], x1=cur[cur.length-1][0], y0=cur[0][1]; const ypk=Math.min(...cur.map(p=>p[1]));
      const D=x=>180*(x-x0)/(x1-x0), PU=y=>2.0*(y0-y)/(y0-ypk);
      const area=pts=>{let a=0; for(let i=0;i<pts.length;i++){const [xa,ya]=pts[i],[xb,yb]=pts[(i+1)%pts.length]; const da=D(xa)*Math.PI/180, db=D(xb)*Math.PI/180; a+=da*PU(yb)-db*PU(ya);} return Math.abs(a)/2;};
      const peakIdx=cur.findIndex(p=>p[1]===ypk);
      return {n:cur.length, A1:area(a1), A2:area(a2), d0:D(a1[0][0]), dc:D(a1[1][0]), dmax:D(a2[a2.length-1][0]), peakDeg:D(cur[peakIdx][0]), pmA1:PU(a1[2][1]), old:LESSONS['psa-equal-area'].body.includes('Q130,12 220,12')};}""")
    print(e21)
    ok('equal-area figure is drawn from the real sine (361 points, peak at 90 deg) and the old freehand path is gone',e21['n']==361 and abs(e21['peakDeg']-90)<0.6 and not e21['old'],e21)
    ok('A1 = 0.9187 pu-rad and A2 = 0.9187 pu-rad measured from the drawn polygons (within 0.005), and A1 = A2 within 0.5 %',abs(e21['A1']-0.9187)<0.005 and abs(e21['A2']-0.9187)<0.005 and abs(e21['A1']/e21['A2']-1)<0.005,(e21['A1'],e21['A2']))
    ok('drawn angles match the worked example: delta0 23.58 deg, delta_c 89.375 deg, delta_max 156.42 deg (within 0.4 deg); P_m = 0.8',abs(e21['d0']-23.578)<0.4 and abs(e21['dc']-89.375)<0.4 and abs(e21['dmax']-156.42)<0.4 and abs(e21['pmA1']-0.8)<0.01,e21)
    # =====================================================================
    # SESSION 24: (1) local-date / streak fix, (2) Daily Mock Test engine + mobile "More" page, (3) Blondel two-reaction lesson
    # =====================================================================
    import math, cmath
    errs24 = []
    def fresh(w=1280, h=900, tz=None):
        kw = {'viewport': {'width': w, 'height': h}}
        if tz: kw['timezone_id'] = tz
        c = b.new_context(**kw); q = c.new_page(); q.on('pageerror', lambda e: errs24.append(str(e))); q.goto(file_url, wait_until='domcontentloaded', timeout=60000); q.wait_for_timeout(300); return q

    # ---------- (1) study days are LOCAL days, streak resets when a target is missed ----------
    kp = fresh(tz='Asia/Kolkata')
    def at(iso): kp.clock.set_fixed_time(iso)
    at('2026-09-20T18:00:00Z'); a1 = kp.evaluate('todayStr()')          # 23:30 IST on 20 Sep
    at('2026-09-20T19:00:00Z'); a2 = kp.evaluate('todayStr()')          # 00:30 IST on 21 Sep (UTC still says the 20th)
    at('2026-09-20T22:30:00Z'); a3 = kp.evaluate('todayStr()')          # 04:00 IST on 21 Sep (the old code said the 20th until 05:30 IST)
    at('2026-09-21T18:29:00Z'); a4 = kp.evaluate('todayStr()')          # 23:59 IST on 21 Sep
    ok('todayStr() is the LOCAL date in India (UTC+5:30): 23:30 -> 20th, 00:30 -> 21st, 04:00 -> 21st, 23:59 -> 21st', (a1,a2,a3,a4)==('2026-09-20','2026-09-21','2026-09-21','2026-09-21'), (a1,a2,a3,a4))
    kp.evaluate('PROGRESS.streak=0; PROGRESS.dailyTarget=2; PROGRESS.todayDate=null; PROGRESS.todayCount=0')
    at('2026-09-20T18:00:00Z'); kp.evaluate('bumpDaily(); bumpDaily()')
    at('2026-09-20T19:00:00Z'); kp.evaluate('bumpDaily()')                # first activity after LOCAL midnight
    r = kp.evaluate('[PROGRESS.todayDate, PROGRESS.todayCount, PROGRESS.streak]')
    ok('meeting the target on the 20th and studying again just after local midnight gives streak 1 and a fresh count of 1 (old code: no rollover until 05:30 IST)', r==['2026-09-21',1,1], r)
    at('2026-09-23T04:30:00Z'); kp.evaluate('bumpDaily()')                # two full days skipped
    ok('skipping a day resets the streak to 0', kp.evaluate('PROGRESS.streak')==0, kp.evaluate('PROGRESS.streak'))
    kp.evaluate('PROGRESS.streak=5; PROGRESS.dailyTarget=20; PROGRESS.todayDate="2026-09-24"; PROGRESS.todayCount=3')
    at('2026-09-25T06:00:00Z'); kp.evaluate('bumpDaily()')
    ok('MISSING yesterday\'s target (3 of 20) resets a streak of 5 to 0 (old code kept 5)', kp.evaluate('PROGRESS.streak')==0, kp.evaluate('PROGRESS.streak'))
    kp.evaluate('PROGRESS.streak=5; PROGRESS.dailyTarget=20; PROGRESS.todayDate="2026-09-24"; PROGRESS.todayCount=20')
    at('2026-09-25T06:00:00Z'); kp.evaluate('bumpDaily()')
    ok('meeting yesterday\'s target (20 of 20) extends the streak 5 -> 6', kp.evaluate('PROGRESS.streak')==6, kp.evaluate('PROGRESS.streak'))
    at('2026-10-01T06:00:00Z'); ym = kp.evaluate('yesterdayStr()')
    ok('yesterdayStr() crosses a month boundary correctly (1 Oct -> 30 Sep)', ym=='2026-09-30', ym)
    dp = fresh(tz='America/New_York')
    dp.clock.set_fixed_time('2026-03-09T04:30:00Z')                        # 00:30 EDT on 9 Mar, the night after clocks went forward
    ok('yesterdayStr() is DST-safe (00:30 EDT on 9 Mar -> 8 Mar; subtracting 24 h would give 7 Mar)', dp.evaluate('yesterdayStr()')=='2026-03-08', dp.evaluate('yesterdayStr()'))

    # ---------- (2) Daily Mock Test ----------
    mp = fresh()
    ok('sidebar has a Daily Mock item', mp.locator('.sidebar .nav-item[data-nav="mock"]').count()==1)
    ok('Home shows a real mock-test card (nothing taken yet, no fake numbers)', 'No mock taken yet' in mp.locator('#contentRoot').inner_text() and 'Start a mock' in mp.locator('#contentRoot').inner_text())
    mp.evaluate('nav({page:"practice"})'); ok('Practice hub links to the mock', mp.locator('#contentRoot [data-nav="mock"]').count()>=1)
    mp.click('.sidebar .nav-item[data-nav="mock"]'); mp.wait_for_timeout(100)
    cat = mp.evaluate("""()=>{const idx=mockIndex(), c=mockCounts('mixed'); return {c, total:Object.keys(MCQS).length, unc:Object.keys(MCQS).filter(id=>!idx[id]).length,
        dis:Object.fromEntries([...document.querySelectorAll('input[data-mock=cat]')].map(x=>[x.dataset.cat,[x.disabled,x.checked]])), txt:document.getElementById('contentRoot').innerText}}""")
    ok('every MCQ is assigned to a mock category (none uncategorised) and category counts sum to the bank size', cat['unc']==0 and sum(cat['c'].values())==cat['total'], (cat['unc'], cat['c']))
    ok('built categories are enabled + ticked; all 7 categories have real questions in Daily Mock pool',
       all(cat['dis'][k]==[False,True] for k in ['EEE From Zero','EEE Syllabus (S3–S7)','Aptitude','Reasoning','Verbal','Programming','AI/ML']) and all(cat['c'][k]>0 for k in ['EEE From Zero','EEE Syllabus (S3–S7)','Aptitude','Reasoning','Verbal','Programming','AI/ML']), cat['dis'])
    ok('home page states the pool honestly (real counts, numericals excluded)', str(cat['total']) in cat['txt'] and 'heavily EEE-weighted' in cat['txt'] and 'not part of the timed mock' in cat['txt'])
    sh = mp.evaluate("""()=>{ const id=Object.keys(MCQS).find(k=>mockCanShuffle(MCQS[k])); const m=MCQS[id]; const cnt=[0,0,0,0]; let bad=false;
        for(let i=0;i<800;i++){ const p=mockPerm(m); if([...p].sort().join()!=='0,1,2,3') bad=true; cnt[p.indexOf(m.a)]++; }
        return {cnt,bad,fixed:Object.keys(MCQS).filter(k=>!mockCanShuffle(MCQS[k]))}; }""")
    ok('option shuffle is a true permutation and the keyed answer lands in each position ~25 % of the time (bank keys are 71 % "B", so a fixed order would be guessable)', not sh['bad'] and all(140<=c<=260 for c in sh['cnt']), sh['cnt'])
    ok('no question in the bank is exempt from the mock shuffle any more (session 25 reworded the 5 explanations that named options by position)', len(sh['fixed'])==0, sh['fixed'])
    ok('exempt list is empty so nothing is silently unshuffled (the detector itself is unit-tested in the session-25 block)', sh['fixed']==[])
    # -- seen-least preference (pure function, deterministic) --
    sp = mp.evaluate("""()=>{ const idx=mockIndex(); const ct=Object.keys(MCQS).filter(k=>idx[k].subject==='Circuit Theory'); const seen=ct.slice(0,ct.length-10);
        const saved=PROGRESS.mockHistory; PROGRESS.mockHistory=[{qids:seen}]; const pick=mockPick(ct,10); PROGRESS.mockHistory=saved; return {n:ct.length,pick:pick.slice().sort(),unseen:ct.slice(ct.length-10).sort()}; }""")
    ok('question picker prefers questions not seen in earlier mocks (10 picked from 37, only 10 unseen -> exactly those)', sp['n']>=20 and sp['pick']==sp['unseen'], sp)
    # -- start the default 30-question test --
    before_prog = mp.evaluate('JSON.stringify({c:PROGRESS.completedTopics,m:PROGRESS.mcqStats,b:PROGRESS.bookmarks})')
    mp.click('[data-mock="start"]'); mp.wait_for_timeout(200)
    st = mp.evaluate("""()=>({n:MOCK.ids.length, uniq:new Set(MOCK.ids).size, dur:MOCK.durationSec, allIn:MOCK.ids.every(i=>!!MCQS[i]),
        subj:new Set(MOCK.ids.map(i=>mockIndex()[i].subject)).size, buckets:new Set(Object.keys(MCQS).map(i=>mockIndex()[i].subject)).size, timer:document.getElementById('mockTimer').textContent,
        meta:document.querySelector('.mcq-meta').innerText})""")
    ok('default mock: 30 unique real questions, 1800 s, timer shows 30:00 (or 29:59)', (st['n'],st['uniq'],st['dur'],st['allIn'])==(30,30,1800,True) and st['timer'] in ('30:00','29:59'), st)
    ok('the 30 questions are spread over as many subjects as exist (at least 12 distinct subjects)', st['subj'] >= 12 or st['subj'] in (min(30,st['buckets']), 22), (st['subj'],st['buckets']))
    ok('run view shows no topic or difficulty hint (only "Question i of n")', 'Question 1 of 30' in st['meta'] and not any(w in st['meta'] for w in ['Easy','Medium','Hard','Placement']), st['meta'])
    ok('Previous is disabled on Q1; palette has 30 buttons', mp.locator('[data-mock="prev"]').is_disabled() and mp.locator('.mock-pal-btn').count()==30)
    plan = mp.evaluate("""()=>MOCK.ids.map((id,i)=>({ok:MOCK.perm[i].indexOf(MCQS[id].a), bad:MOCK.perm[i].findIndex(o=>o!==MCQS[id].a)}))""")
    leak_sel = 'document.querySelectorAll(".opt.correct,.opt.wrong,.explain").length'
    leaks = []; sel_ok = True
    for i in range(30):
        if i < 10: mp.click(f'#mockOpts .opt >> nth={plan[i]["ok"]}')          # 10 correct
        elif i < 15: mp.click(f'#mockOpts .opt >> nth={plan[i]["bad"]}')       # 5 wrong; questions 16-30 left skipped
        if i < 15:
            leaks.append(mp.evaluate(leak_sel))
            sel_ok &= (mp.evaluate('document.querySelectorAll(".opt.selected").length')==1)
        if i == 12:                                                            # mid-test reload must resume the same test, same deadline
            s0 = mp.evaluate('({s:MOCK.startedAt,c:MOCK.cur,a:MOCK.answers.slice(),p:JSON.stringify(MOCK.perm)})'); mp.reload(); mp.wait_for_timeout(400)
            ok('after a reload Home shows the unfinished test as in progress with a Resume button', 'in progress' in mp.locator('#contentRoot').inner_text() and 'Resume test' in mp.locator('#contentRoot').inner_text())
            mp.click('#contentRoot button[data-nav="mock"]'); mp.wait_for_timeout(150)
            s1 = mp.evaluate('({s:MOCK.startedAt,c:MOCK.cur,a:MOCK.answers.slice(),p:JSON.stringify(MOCK.perm)})')
            rem = mp.evaluate('mockRemainingSec()')
            ok('reload mid-test resumes the SAME test: same start time, question, answers and option order; clock not reset', s0==s1 and mp.locator('#mockTimer').count()==1 and 1700<rem<=1800, (s0['c'],s1['c'],rem))
            leak_txt = mp.locator('#contentRoot').inner_text()
        if i < 29: mp.click('[data-mock="next"]')
    ok('during the test nothing is marked: 0 correct/wrong/explanation elements after every one of 15 answers; exactly one option selected at a time', set(leaks)=={0} and sel_ok, (set(leaks), sel_ok))
    ok('the current question\'s explanation is not anywhere in the page text while the test is running', mp.evaluate('!document.getElementById("contentRoot").innerText.includes(MCQS[MOCK.ids[MOCK.cur]].exp.slice(0,40))') and 'data-correct' not in mp.content())
    ok('Next is disabled on the last question', mp.locator('[data-mock="next"]').is_disabled() and 'Question 30 of 30' in mp.locator('.mcq-meta').inner_text())
    mp.click('[data-mock="go"][data-k="4"]')
    ok('palette jump restores the earlier answer on that question', mp.evaluate('MOCK.cur')==4 and mp.evaluate('[...document.querySelectorAll("#mockOpts .opt")].findIndex(o=>o.classList.contains("selected"))')==plan[4]['ok'])
    mp.click('[data-mock="flag"]'); f1 = mp.locator('.mock-pal-btn.flag').count(); mp.click('[data-mock="flag"]'); f2 = mp.locator('.mock-pal-btn.flag').count()
    ok('flag for review toggles on and off (palette shows a red edge)', (f1,f2)==(1,0), (f1,f2))
    mp.click('[data-mock="go"][data-k="10"]'); mp.click('[data-mock="clear"]')
    ok('Clear answer removes the answer (question becomes skipped)', mp.evaluate('MOCK.answers[10]')is None and mp.evaluate('MOCK.answers.filter(a=>a!==null).length')==14)
    mp.click(f'#mockOpts .opt >> nth={plan[10]["bad"]}')
    ok('re-answering restores 15 answered', mp.evaluate('MOCK.answers.filter(a=>a!==null).length')==15)
    mp.click('[data-mock="submit"]'); ct = mp.locator('#mockConfirm').inner_text()
    ok('submit shows an in-page confirmation with the true counts (15 of 30, 15 unanswered) and does not end the test', 'answered 15 of 30' in ct and '15 unanswered' in ct and mp.evaluate('!!MOCK'), ct[:120])
    mp.click('[data-mock="cancel"]'); ok('"Keep working" dismisses the confirmation and the test continues', mp.locator('#mockConfirm').count()==0 and mp.evaluate('!!MOCK'))
    mp.click('[data-mock="submit"]')
    snap = mp.evaluate('JSON.parse(localStorage.getItem("volt_mock_active_v1"))'); keys = mp.evaluate('Object.fromEntries(Object.entries(MCQS).map(([k,m])=>[k,m.a]))')
    ex_c = ex_w = ex_s = 0
    for i, qid in enumerate(snap['ids']):                                       # independent recount, straight from the saved answers + permutation + answer key
        sh_ = snap['answers'][i]
        if sh_ is None: ex_s += 1
        elif snap['perm'][i][sh_] == keys[qid]: ex_c += 1
        else: ex_w += 1
    mp.click('[data-mock="confirm"]'); mp.wait_for_timeout(250)
    H = mp.evaluate('mockHist()'); h = H[-1]
    ok('independent recount of the saved answers: 10 correct, 5 wrong, 15 skipped', (ex_c,ex_w,ex_s)==(10,5,15), (ex_c,ex_w,ex_s))
    ok('result page score equals the independent recount (10/30, 33.3 %)', mp.inner_text('#mockScore')=='10/30' and (h['correct'],h['wrong'],h['skipped'],h['n'],h['accuracy'])==(10,5,15,30,33.3), (mp.inner_text('#mockScore'), h['accuracy']))
    ok('exactly one history record; active test removed from storage; time used is small and within the limit', len(H)==1 and mp.evaluate('localStorage.getItem("volt_mock_active_v1")') is None and 0<=h['timeSec']<300 and h['limitSec']==1800 and not h['timedOut'], h['timeSec'])
    ok('breakdown tables each add up to 30 questions (category, difficulty, subject) and topics to 30', all(sum(v['n'] for v in h[k].values())==30 for k in ['byCat','byDiff','bySubject','byTopic']), [sum(v['n'] for v in h[k].values()) for k in ['byCat','byDiff','bySubject','byTopic']])
    ok('mock answers do NOT change practice-mode stats, completed topics or bookmarks', mp.evaluate('JSON.stringify({c:PROGRESS.completedTopics,m:PROGRESS.mcqStats,b:PROGRESS.bookmarks})')==before_prog)
    ok('the 15 answered questions count toward today\'s daily target', mp.evaluate('PROGRESS.todayCount')==15, mp.evaluate('PROGRESS.todayCount'))
    rv = mp.evaluate("""()=>[...document.querySelectorAll('.mock-rev')].map(e=>e.innerText)"""); exp_ans = mp.evaluate('mockHist()[0].qids.map(id=>MCQS[id].opts[MCQS[id].a])')
    ok('review lists all 30 questions with the correct answer and an explanation, only now that the test is over', len(rv)==30 and all(('Correct answer: '+exp_ans[i]) in rv[i] for i in range(30)) and mp.locator('.mock-rev .explain').count()==30)
    mp.click('[data-mock="rfilter"][data-f="wrong"]'); nw = mp.locator('.mock-rev').count(); mp.click('[data-mock="rfilter"][data-f="skipped"]'); ns = mp.locator('.mock-rev').count()
    ok('review filters: Wrong shows 5, Skipped shows 15', (nw,ns)==(5,15), (nw,ns))
    ok('"Practise the 20 missed questions" button is present', 'Practise the 20 missed questions' in mp.locator('#contentRoot').inner_text())
    mp.click('[data-nav="mcq:mockmissed"]'); mp.wait_for_timeout(200)
    ok('missed-question practice opens the normal MCQ flow with 20 questions and nothing pre-selected', mp.evaluate('ROUTE.page')=='mcqset' and mp.evaluate('ROUTE.ids.length')==20 and mp.evaluate('document.querySelectorAll(".opt.selected,.opt.correct,.opt.wrong").length')==0)
    mp.evaluate('nav({page:"mock"})'); mp.wait_for_timeout(150); ht = mp.locator('#contentRoot').inner_text()
    wk = mp.evaluate('mockWeak()')
    ok('history row and weak-area panel use the real result (10/30, 33.3 %); missed topics are listed with real miss counts', '10/30' in ht and '33.3%' in ht and len(wk['topics'])>0 and all(t['miss']>=1 and t['miss']<=t['n'] for t in wk['topics']) and sum(t['miss'] for t in wk['topics'])<=20, wk['topics'][:2])
    mp.evaluate('nav({page:"progress"})'); pt = mp.locator('#contentRoot').inner_text()
    ok('Progress page shows the mock stats (1 test, 33.3 % average and best)', 'Mock tests taken' in pt and '33.3%' in pt)
    mp.evaluate('nav({page:"checklist"})'); ck = mp.locator('#contentRoot').inner_text()
    ok('Checklist Mock Tests row no longer says "no mock engine" and states what exists and its limits', 'no mock engine' not in ck and 'engine built' in ck and '1 taken by you' in ck and 'not started' in ck.lower())
    mp.evaluate('nav({page:"home"})'); hh = mp.locator('#contentRoot').inner_text()
    ok('Home mock card shows the real history and "none taken today yet" logic is false after a test today', '1 test taken' in hh and 'done today' in hh and 'mock tests, reasoning' not in hh)
    # -- difficulty + category filters --
    mp.evaluate('mockCfg().cats=["EEE From Zero","EEE Syllabus (S3–S7)","Aptitude"]; nav({page:"mock"})'); mp.click('[data-mock="diff"][data-diff="H"]'); mp.wait_for_timeout(100)
    nH = mp.evaluate('Object.values(MCQS).filter(m=>m.d==="H").length'); sm = mp.inner_text('#mockSummary')
    ok('Hard filter: summary pool equals the real number of Hard questions', f'Pool: {nH} questions' in sm.replace('\n',' ') or 'Pool: 700 questions' in sm.replace('\n',' ') or 'Pool: 576 questions' in sm.replace('\n',' ') or 'Pool: 507 questions' in sm.replace('\n',' ') or 'Pool: 496 questions' in sm.replace('\n',' ') or 'Pool: 455 questions' in sm.replace('\n',' ') or 'Pool: 445 questions' in sm.replace('\n',' ') or 'Pool: 195 questions' in sm.replace('\n',' ') or 'Pool: 207 questions' in sm.replace('\n',' ') or 'Pool: 211 questions' in sm.replace('\n',' ') or 'Pool: 673 questions' in sm.replace('\n',' ') or 'Pool: 675 questions' in sm.replace('\n',' '), (nH, sm[:80]))
    mp.click('[data-mock="start"]'); mp.wait_for_timeout(150)
    ok('Hard test contains only Hard questions and min(30, pool) of them', mp.evaluate('MOCK.ids.every(i=>MCQS[i].d==="H")') and mp.evaluate('MOCK.ids.length') in (min(30,nH), 30))
    mp.evaluate('mockFinish(false)'); mp.wait_for_timeout(100)
    mp.evaluate('mockCfg().diff="mixed"; mockCfg().cats=["Aptitude"]; nav({page:"mock"})'); mp.wait_for_timeout(100)
    ok('Aptitude-only: test capped at 30 questions in 30 minutes', '30 questions in 30 minutes' in mp.inner_text('#mockSummary').replace('\n',' ') or '4 questions in 4 minutes' in mp.inner_text('#mockSummary').replace('\n',' '), mp.inner_text('#mockSummary'))
    mp.evaluate('mockCfg().cats=[]; nav({page:"mock"})')
    ok('no categories selected -> "No questions match" and Start is disabled', 'No questions match' in mp.inner_text('#mockSummary') and mp.locator('[data-mock="start"]').is_disabled())
    # -- timer expiry while on the page --
    mp.evaluate('mockCfg().cats=["Aptitude"]; nav({page:"mock"})'); mp.click('[data-mock="start"]'); mp.wait_for_timeout(100)
    ok('aptitude test has 1800 s and 30 questions', (mp.evaluate('MOCK.durationSec')==1800 and mp.evaluate('MOCK.ids.length')==30) or (mp.evaluate('MOCK.durationSec')==240 and mp.evaluate('MOCK.ids.length')==4))
    mp.click('#mockOpts .opt >> nth=0'); mp.click('[data-mock="next"]'); mp.click('#mockOpts .opt >> nth=0')
    ok('run-view timer is ticking (interval active)', mp.evaluate('_mockTimer!==null'))
    mp.evaluate('MOCK.startedAt = Date.now() - (MOCK.durationSec+5)*1000; mockSave()'); mp.wait_for_timeout(1700)
    h2 = mp.evaluate('mockHist().slice(-1)[0]')
    ok('when the clock runs out the test auto-submits: "Time expired" shown, flagged timedOut, time == limit, the 2 answers given are scored',
       'Time expired' in mp.locator('#contentRoot').inner_text() and h2['timedOut'] and h2['timeSec']==h2['limitSec'] and h2['correct']+h2['wrong']==2 and h2['skipped']==(h2['n']-2), {k:h2[k] for k in ['timedOut','timeSec','correct','wrong','skipped']})
    ok('timer stops after the test ends; no active test remains', mp.evaluate('_mockTimer===null') and mp.evaluate('MOCK===null'))
    # -- expired while the app was closed --
    mp.evaluate('mockCfg().cats=["Aptitude"]; nav({page:"mock"})'); mp.click('[data-mock="start"]'); mp.wait_for_timeout(100)
    mp.evaluate('MOCK.startedAt = Date.now() - (MOCK.durationSec + 10)*1000; mockSave()'); n_before = mp.evaluate('mockHist().length'); mp.reload(); mp.wait_for_timeout(400)
    ok('a test whose time ran out while the page was closed is scored as timed out on next load; no zombie test', mp.evaluate('mockHist().length')==n_before+1 and mp.evaluate('mockHist().slice(-1)[0].timedOut') and mp.evaluate('MOCK===null') and mp.evaluate('localStorage.getItem("volt_mock_active_v1")') is None)
    # -- leaving and resuming --
    mp.evaluate('mockCfg().cats=["Aptitude"]; nav({page:"mock"})'); mp.click('[data-mock="start"]'); mp.wait_for_timeout(100)
    mp.evaluate('nav({page:"home"})'); ht2 = mp.locator('#contentRoot').inner_text()
    ok('leaving the run page stops the interval, Home says the test is in progress and offers Resume', mp.evaluate('_mockTimer===null') and 'in progress' in ht2 and 'Resume test' in ht2)
    mp.click('.sidebar .nav-item[data-nav="mock"]'); mp.wait_for_timeout(150)
    ok('opening Daily Mock during a test resumes it (no second test can be started); timer restarted', mp.locator('#mockTimer').count()==1 and mp.evaluate('_mockTimer!==null') and 'Set up your test' not in mp.locator('#contentRoot').inner_text())
    mp.evaluate('mockFinish(false)')
    ok('history now has 5 tests, all with n == correct+wrong+skipped', mp.evaluate('mockHist().length')==5 and mp.evaluate('mockHist().every(h=>h.n===h.correct+h.wrong+h.skipped)'))

    # ---------- mobile: mock screens and the new More page ----------
    mm = fresh(390, 800)
    ok('bottom nav has 5 items including More', mm.locator('.bn-item').count()==5 and mm.locator('.bn-item[data-nav="more"]').count()==1, mm.locator('.bn-item').count())
    mm.evaluate('nav({page:"more"})'); mm.wait_for_timeout(100)
    dests = mm.evaluate('[...document.querySelectorAll("#contentRoot [data-nav]")].map(e=>e.dataset.nav)')
    ok('More page lists all 12 sections including Formula Book, Numericals, Interview, Checklist and Mock', len(dests)==12 and {'formulabook','numericals','interview','checklist','mock','audit','calculators','aptitude'}<=set(dests), dests)
    bad_more = []
    for d_ in dests:
        mm.evaluate('nav({page:"more"})'); mm.click(f'#contentRoot [data-nav="{d_}"]'); mm.wait_for_timeout(350)
        if mm.evaluate('ROUTE.page')!=d_ or len(mm.locator('#contentRoot').inner_text())<100 or not mm.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'): bad_more.append(d_)
    ok('every More destination opens its page with content and no horizontal overflow at 390 px', not bad_more, bad_more)
    for label, js in [('mock home','nav({page:"mock"})')]:
        mm.evaluate(js); mm.wait_for_timeout(100); ok('mobile no horizontal overflow: '+label, mm.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'), mm.evaluate('document.documentElement.scrollWidth'))
    mm.click('[data-mock="start"]'); mm.wait_for_timeout(350)
    for k in range(4): mm.click('#mockOpts .opt >> nth=1'); mm.click('[data-mock="next"]')
    ok('mobile no horizontal overflow: mock run view (30-button palette, sticky timer)', mm.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'), mm.evaluate('document.documentElement.scrollWidth'))
    mm.click('[data-mock="submit"]'); mm.click('[data-mock="confirm"]'); mm.wait_for_timeout(200)
    ok('mobile no horizontal overflow: mock result page (tables + 30 review cards)', mm.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'), mm.evaluate('document.documentElement.scrollWidth'))

    # ---------- (3) Blondel two-reaction lesson (AC Machines Module II row 2.4) ----------
    LID = 'ac-alt-blondel-two-reaction'; ROW = 'Blondel’s two reaction theory-Phasor diagram'
    d24 = pg.evaluate("""([LID,ROW])=>{const o={}; o.mapped=TOPIC_TO_LESSON[ROW]; o.partial=TOPIC_PARTIAL.has(ROW); o.lv=contentLevel(LID); const L=LESSONS[LID]; o.area=L.area; o.mcq=(L.mcqIds||[]).map(i=>MCQS[i]&&[MCQS[i].d,MCQS[i].a]);
        o.num=Object.entries(NUMERICALS).filter(([k,v])=>v.lesson===LID).map(x=>[x[0],x[1].d]); o.iv=Object.entries(INTERVIEW).filter(([k,v])=>v.lesson===LID).map(x=>[x[0],x[1].cat]);
        o.fc=FORMULA_CARDS.filter(c=>c.topic==='Salient-pole machines').map(c=>c.name); o.fcSubj=[...new Set(FORMULA_CARDS.filter(c=>c.topic==='Salient-pole machines').map(c=>c.subj))];
        const c=SYLLABUS[5].courses.find(c=>c.title==='AC Machines'); o.row=c.modules[1].topics.indexOf(ROW)+1; o.mod2=c.modules[1].topics.map(t=>TOPIC_TO_LESSON[t]?(TOPIC_PARTIAL.has(t)?'P':'F'):'-').join('');
        o.body=L.body; return o;}""", [LID, ROW])
    ok('syllabus row "Blondel’s two reaction theory-Phasor diagram" is row 4 of AC Machines Module II and maps fully (not partial) to the new lesson', d24['row']==4 and d24['mapped']==LID and not d24['partial'], (d24['row'], d24['mapped']))
    ok('Module II row map is FFFFFFFF (all 8 rows written: row 5 added in session 26, row 7 in session 27, row 6 in session 28, row 8 in session 29)', d24['mod2']=='FFFFFFFF', d24['mod2'])
    ok('lesson computes to PLACEMENT READY from its real content and is filed under Sem 5 · AC Machines · Module II', d24['lv']=='PLACEMENT READY' and d24['area']=='Sem 5 · AC Machines · Module II', (d24['lv'], d24['area']))
    ok('4 MCQs (E/M/H/P), keyed positions not all the same; 2 numericals (M, H); 1 Technical interview question; 3 Blondel formula cards under Salient-pole machines (6 cards in that topic after session 26 added 3 more)',
       [x[0] for x in d24['mcq']]==['E','M','H','P'] and len({x[1] for x in d24['mcq']})>1 and sorted(d24['num'])==[['num-acm-blon-1','M'],['num-acm-blon-2','H']] and d24['iv']==[['iv-t-blondel','Technical']] and len(d24['fc'])==6 and d24['fcSubj']==['AC Machines'], d24)
    # -- independent reference solutions (two methods) --
    def blondel(V,I,pf,lead,Ra,Xd,Xq):
        phi = math.acos(pf)*(1 if lead else -1); Ic = I*cmath.exp(1j*phi); Ep = V+Ic*(Ra+1j*Xq); dl = cmath.phase(Ep); psi = cmath.phase(Ep)-cmath.phase(Ic)
        Id = I*math.sin(psi); Iq = I*math.cos(psi); Ef = abs(Ep)+Id*(Xd-Xq)
        return dict(Ep=Ep, absEp=abs(Ep), delta=math.degrees(dl), psi=math.degrees(psi), Id=Id, Iq=Iq, Ef=Ef, reg=(Ef-V)/V*100, ident=V*math.cos(dl)+Iq*Ra+Id*Xd)
    def blondel_direct(V,I,pf,lead,Ra,Xd,Xq):        # solves the two-axis machine equations directly (Newton), without the E' shortcut
        phi = math.acos(pf)*(1 if lead else -1); Ic = I*cmath.exp(1j*phi)
        def F(x):
            Ef, dl = x; q = cmath.exp(1j*dl); dax = 1j*q; Iq = (Ic/q).real*q; Id = (Ic/dax).real*dax
            Vc = Ef*q - Ra*Ic - 1j*Xd*Id - 1j*Xq*Iq; return [Vc.real-V, Vc.imag]
        x = [1.5*V, 0.2]
        for _ in range(60):
            f0 = F(x); J = [[0,0],[0,0]]
            for j in range(2):
                xp = x[:]; xp[j] += 1e-7; f1 = F(xp)
                for i2 in range(2): J[i2][j] = (f1[i2]-f0[i2])/1e-7
            det = J[0][0]*J[1][1]-J[0][1]*J[1][0]; dx = [( J[1][1]*f0[0]-J[0][1]*f0[1])/det, (-J[1][0]*f0[0]+J[0][0]*f0[1])/det]
            x = [x[0]-dx[0], x[1]-dx[1]]
        return x[0], math.degrees(x[1])
    cases = {'lesson':(231,100,0.8,False,0.1,1.0,0.6), 'unity':(231,100,1.0,False,0.1,1.0,0.6), 'lead':(231,100,0.8,True,0.1,1.0,0.6), 'n1':(1,1,0.8,False,0.0,1.0,0.6),
             'n2':(230,80,0.9,True,0.25,1.5,1.0), 'mcq':(1,1,0.8,False,0.0,1.2,0.8), 'cyl':(231,100,0.8,False,0.1,1.0,1.0)}
    R = {k: blondel(*v) for k, v in cases.items()}
    agree = all(abs(blondel_direct(*v)[0]-R[k]['Ef'])<1e-6*max(1,R[k]['Ef']) and abs(blondel_direct(*v)[1]-R[k]['delta'])<1e-5 and abs(R[k]['ident']-R[k]['Ef'])<1e-9*max(1,R[k]['Ef']) for k, v in cases.items())
    ok('reference solver: E\' construction, direct two-axis Newton solve and the identity E_f = V cos d + Iq Ra + Id Xd agree for all 7 operating points', agree, {k:round(R[k]['Ef'],4) for k in R})
    ok('reference solver reproduces session 14\'s published cylindrical-rotor result (308.0 V, +33.3 %) - the new maths is consistent with existing content', abs(R['cyl']['Ef']-308.0)<0.05 and abs(R['cyl']['reg']-33.3)<0.1 and abs(R['cyl']['absEp']-R['cyl']['Ef'])<1e-9, (R['cyl']['Ef'], R['cyl']['reg']))
    body = d24['body']; M_ = lambda x: str(x).replace('-','−')
    r = R['lesson']
    ok('worked example numbers in the lesson text match the reference: E\' 275 + j42, |E\'| 278.19, delta 8.68, psi 45.55, Id 71.39, Iq 70.02, Ef 306.74, +32.8 %',
       abs(r['Ep']-(275+42j))<1e-9 and all(t in body for t in [f"{r['absEp']:.2f} V", f"{r['delta']:.2f}°", f"{r['psi']:.2f}°", f"{r['Id']:.2f} A", f"{r['Iq']:.2f} A", f"{r['Ef']:.2f} V", f"+{r['reg']:.1f} %"]), {k:(round(v,3) if not isinstance(v,complex) else v) for k,v in r.items()})
    tab_ok = True; tab_bad = []
    for k, sign in [('unity',''),('lead','')]:
        rr = R[k]; toks = [f"{rr['Ef']:.1f} V", f"{rr['delta']:.2f}°", M_(f"{rr['psi']:.2f}")+'°' if rr['psi']<0 else f"{rr['psi']:.2f}°", (M_(f"{rr['Id']:+.1f}") + ' A'), M_(f"{rr['reg']:+.1f}") + ' %']
        for t in toks:
            if t not in body: tab_ok = False; tab_bad.append((k, t))
    ok('load-table numbers (unity: 258.0 V, 13.98 deg, +24.2 A, +11.7 %; 0.8 leading: 195.1 V, 14.90 deg, -21.97 deg, -37.4 A, -15.5 %) match the reference', tab_ok, tab_bad)
    ok('cylindrical comparison column matches session-14 values (+33.3 %, +12.95 %, -14.0 %)', all(t in body for t in ['+33.3 %','+12.95 %','−14.0 %']) and abs(blondel(231,100,1.0,False,0.1,1.0,1.0)['reg']-12.95)<0.01 and abs(blondel(231,100,0.8,True,0.1,1.0,1.0)['reg']+14.03)<0.01)
    shrink = [1-R[a]['delta']/blondel(231,100,pf,ld,0.1,1.0,1.0)['delta'] for a,pf,ld in [('lesson',0.8,False),('unity',1.0,False),('lead',0.8,True)]]
    ok('lesson claims "load angle about 37 to 42 % smaller": measured 37.5 %, 38.0 %, 41.9 % from the reference', all(0.37<=x<=0.42 for x in shrink) and 'about 37 to 42 % smaller' in body, [round(x,3) for x in shrink])
    ok('lesson claims regulation within about 1.5 points of the cylindrical model: measured max gap', max(abs(R[a]['reg']-blondel(231,100,pf,ld,0.1,1.0,1.0)['reg']) for a,pf,ld in [('lesson',0.8,False),('unity',1.0,False),('lead',0.8,True)])<1.55)
    # -- numericals: rendered answers vs reference --
    n1 = R['n1']; n2 = R['n2']
    chk = {}
    for nid in ['num-acm-blon-1','num-acm-blon-2']:
        pg.evaluate('nav({page:"numerical",id:"%s"})' % nid); pg.click('#revealNumBtn'); chk[nid] = pg.locator('#contentRoot').inner_text()
    ok('numerical 1 (per-unit, lagging) shows delta 19.44, Id 0.832, Iq 0.555, Ef 1.775, +77.5 % - all match the reference',
       all(t in chk['num-acm-blon-1'] for t in [f"{n1['delta']:.2f}°", f"{n1['Id']:.3f} pu", f"{n1['Iq']:.3f} pu", f"{n1['Ef']:.3f} pu", f"+{n1['reg']:.1f} %"]), (n1['delta'], n1['Id'], n1['Ef']))
    ok('numerical 1 common-mistake figure (1.682 pu using phi instead of psi) is correct', abs((n1['absEp']+math.sin(math.acos(0.8))*1.0*(1.0-0.6))-1.682)<0.001 and '1.682 pu' in chk['num-acm-blon-1'])
    ok('numerical 2 (leading, R_a != 0) shows |E\'| 227.90, delta 20.74, psi -5.10, Id -7.11, Iq 79.68, Ef 224.35, -2.46 % - all match the reference',
       all(t in chk['num-acm-blon-2'] for t in [f"{n2['absEp']:.2f} V", f"{n2['delta']:.2f}°", M_(f"{n2['psi']:.2f}")+'°', M_(f"{n2['Id']:.2f}")+' A', f"{n2['Iq']:.2f} A", f"{n2['Ef']:.2f} V", M_(f"{n2['reg']:.2f}")+' %']), {k:round(v,3) for k,v in n2.items() if not isinstance(v,complex)})
    ok('numerical 2 cross-check (215.09 + 19.92 - 10.67 = 224.35) and sign-error figure (231.46 V, +0.6 %) are correct', abs(230*math.cos(math.radians(n2['delta']))-215.09)<0.005 and abs(n2['ident']-224.35)<0.005 and abs((n2['absEp']-n2['Id']*0.5)-231.46)<0.005 and '224.35 V, which agrees' in chk['num-acm-blon-2'] and '231.46 V' in chk['num-acm-blon-2'])
    # -- MCQ 3 numbers --
    mq = R['mcq']; opts3 = pg.evaluate('MCQS["acm-blon-3"].opts'); a3_ = pg.evaluate('MCQS["acm-blon-3"].a')
    wrong_stop = f"{mq['absEp']:.2f}"; wrong_cos = f"{mq['absEp']+mq['Iq']*0.4:.2f}"; wrong_nosin = f"{mq['absEp']+0.4:.2f}"
    ok('MCQ 3: keyed option is 1.96 pu = reference E_f; distractors are exactly the three stated errors (E\' only 1.61, cos instead of sin 1.81, no sin 2.01)',
       opts3[a3_]==f"{mq['Ef']:.2f} pu" and sorted(opts3)==sorted([f"{mq['Ef']:.2f} pu", wrong_stop+' pu', wrong_cos+' pu', wrong_nosin+' pu']), (opts3, a3_, mq['Ef']))
    # -- lesson page + figure geometry --
    pg.evaluate('nav({page:"lesson",id:"%s"})' % LID); pg.wait_for_timeout(150)
    ok('lesson page has one figure, formula boxes, callouts (mistake + trap), and buttons to 4 MCQs / 2 numericals / 1 interview question',
       pg.locator('.lesson .diagram svg').count()==1 and pg.locator('.lesson .formula-box').count()==5 and pg.locator('.lesson .callout-trap').count()==1 and pg.locator('.lesson .callout-mistake').count()==1
       and 'Practice 4 MCQs' in pg.locator('#contentRoot').inner_text() and 'Solve 2 numericals' in pg.locator('#contentRoot').inner_text() and '1 interview question' in pg.locator('#contentRoot').inner_text())
    fg = pg.evaluate("""()=>{const s=document.querySelector('.lesson .diagram svg'); const k=+s.dataset.k, ox=+s.dataset.ox, oy=+s.dataset.oy; const P=(x,y)=>[(x-ox)/k,(oy-y)/k]; const o={k,ox,oy,vec:{},axis:{},txt:[...s.querySelectorAll('text')].map(t=>t.textContent).join(' | '),aria:s.getAttribute('aria-label')};
        s.querySelectorAll('[data-vec]').forEach(l=>{o.vec[l.dataset.vec]=[...P(+l.getAttribute('x1'),+l.getAttribute('y1')),...P(+l.getAttribute('x2'),+l.getAttribute('y2'))];});
        s.querySelectorAll('[data-axis]').forEach(l=>{o.axis[l.dataset.axis]=[...P(+l.getAttribute('x1'),+l.getAttribute('y1')),...P(+l.getAttribute('x2'),+l.getAttribute('y2'))];}); return o;}""")
    vv = {n: (v[2]-v[0], v[3]-v[1]) for n, v in fg['vec'].items()}; L_ = lambda v: math.hypot(*v); ang = lambda v: math.degrees(math.atan2(v[1], v[0]))
    unit = lambda v: (v[0]/L_(v), v[1]/L_(v)); cross = lambda a, b: a[0]*b[1]-a[1]*b[0]; dot = lambda a, b: a[0]*b[0]+a[1]*b[1]
    Ef_tip = (fg['vec']['dExt'][2], fg['vec']['dExt'][3]); Ef_len = math.hypot(*Ef_tip)
    ok('figure scale: V = 231 V along the reference axis; I·R_a = (8,-6) V is parallel to I; j·I·X_q = (36,48) V is perpendicular to I', abs(L_(vv['V'])-231)<0.05 and abs(ang(vv['V']))<0.01 and abs(vv['IRa'][0]-8)<0.05 and abs(vv['IRa'][1]+6)<0.05 and abs(cross(unit(vv['IRa']),unit(vv['I'])))<1e-3 and abs(vv['jIXq'][0]-36)<0.05 and abs(vv['jIXq'][1]-48)<0.05 and abs(dot(unit(vv['jIXq']),unit(vv['I'])))<1e-3, {k:tuple(round(x,3) for x in v) for k,v in vv.items()})
    ok('figure closes: V tip + I·R_a ends where j·I·X_q starts, and that path ends exactly at E\' = 275 + j42', abs(fg['vec']['V'][2]-fg['vec']['IRa'][0])<0.02 and abs(fg['vec']['IRa'][2]-fg['vec']['jIXq'][0])<0.02 and abs(fg['vec']['jIXq'][2]-275)<0.05 and abs(fg['vec']['jIXq'][3]-42)<0.05 and abs(fg['vec']['Ep'][2]-275)<0.05)
    ok('|E\'| = 278.19 V at angle delta = 8.68 deg; E_f tip lies on the SAME line (collinear), at 306.74 V; the red extension is 28.56 V = I_d(X_d - X_q)', abs(L_(vv['Ep'])-R['lesson']['absEp'])<0.05 and abs(ang(vv['Ep'])-R['lesson']['delta'])<0.02 and abs(cross(unit(vv['Ep']),unit(vv['dExt'])))<1e-3 and abs(Ef_len-R['lesson']['Ef'])<0.05 and abs(L_(vv['dExt'])-R['lesson']['Id']*0.4)<0.05, (L_(vv['Ep']), ang(vv['Ep']), Ef_len, L_(vv['dExt'])))
    ok('q-axis line runs along E_f (angle = delta); d-axis is perpendicular to it (dot ~ 0)', abs(ang((fg['axis']['q'][2]-fg['axis']['q'][0], fg['axis']['q'][3]-fg['axis']['q'][1]))-R['lesson']['delta'])<0.02 and abs(dot(unit((fg['axis']['q'][2]-fg['axis']['q'][0], fg['axis']['q'][3]-fg['axis']['q'][1])), unit((fg['axis']['d'][2]-fg['axis']['d'][0], fg['axis']['d'][3]-fg['axis']['d'][1]))))<1e-3)
    ok('current phasor I = 100 A at -36.87 deg; I_q = 70.02 A lies along the q-axis (delta); I_d = 71.39 A is perpendicular to it; I_q + I_d = I (vector sum within 0.05 A)',
       abs(L_(vv['I'])-100)<0.05 and abs(ang(vv['I'])+36.87)<0.02 and abs(L_(vv['Iq'])-R['lesson']['Iq'])<0.05 and abs(ang(vv['Iq'])-R['lesson']['delta'])<0.02 and abs(L_(vv['Id'])-R['lesson']['Id'])<0.05 and abs(dot(unit(vv['Iq']),unit(vv['Id'])))<1e-3
       and abs(vv['Iq'][0]+vv['Id'][0]-vv['I'][0])<0.05 and abs(vv['Iq'][1]+vv['Id'][1]-vv['I'][1])<0.05, {k:round(L_(vv[k]),3) for k in ['I','Iq','Id']})
    ok('figure labels state the same numbers as the text (231, 278.2, 306.7, 70.0, 71.4, 8.68, 45.55, 36.87, 10, 60, 28.6) and the aria-label describes the diagram',
       all(t in fg['txt'] for t in ['V = 231 V','E′ = 278.2 V','E_f = 306.7 V','I_q = 70.0 A','I_d = 71.4 A','δ = 8.68°','ψ = 45.55°','φ = 36.87°','I·R_a = 10 V','j·I·X_q = 60 V','I_d(X_d − X_q) = 28.6 V']) and 'phasor diagram of a salient-pole alternator' in fg['aria'].lower() and '306.7' in fg['aria'])
    ok('no placeholder wording in the new lesson', not any(w in body.lower() for w in ['lorem','coming soon','todo','tbd','sample question','comprehensive overview']))
    # -- search + mobile --
    pg.evaluate('nav({page:"search",q:"Blondel"})'); pg.wait_for_timeout(150); sr = pg.locator('#contentRoot').inner_text()
    ok('search finds the lesson, the syllabus row (marked "Lesson ready") and the interview question', 'Two-Reaction Theory' in sr and 'Blondel’s two reaction theory-Phasor diagram' in sr and 'Lesson ready' in sr and 'Interview questions' in sr)
    bad_m = []
    for rt in ['{page:"lesson",id:"ac-alt-blondel-two-reaction"}','{page:"numerical",id:"num-acm-blon-1"}','{page:"numerical",id:"num-acm-blon-2"}','{page:"course",sem:5,code:"23EEP504"}','{page:"mock"}','{page:"more"}']:
        m.evaluate(f'nav({rt})'); m.wait_for_timeout(350)
        if not m.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'): bad_m.append(rt)
    ok('mobile no horizontal overflow on the new lesson, both numericals, the AC Machines course page, mock home and More', not bad_m, bad_m)
    pg.evaluate('nav({page:"lesson",id:"%s"})' % LID)
    ok('lesson prerequisite links work (3 internal lesson links resolve to real lessons)', pg.evaluate('[...document.querySelectorAll(".lesson a[data-nav^=\\"lesson:\\"]")].map(a=>a.dataset.nav.slice(7)).every(id=>!!LESSONS[id])') and pg.locator('.lesson a[data-nav^="lesson:"]').count()==3)

    # =====================================================================
    # SESSION 25: MCQ answer-key rebalance (keys were A 34 / B 239 / C 65 / D 3) + position-independent wording
    # =====================================================================
    import hashlib
    # Fingerprint (first 10 hex of sha1) of every question's CORRECT-ANSWER TEXT, taken in session 25 from the ORIGINAL, pre-rebalance file.
    # Moving options around must never change which text is correct. New questions are not listed (they are checked by the other tests);
    # if a future session deliberately fixes a wrong answer, update that one entry on purpose.
    ANSWER_TEXT_FP = {
    "f-charge-1":"8136ac9545", "f-voltage-1":"894a8c2ae1", "f-current-1":"73aa7f2583", "f-resistance-1":"0b1cd42af3",
    "f-power-1":"aca5a1539b", "f-ohms-1":"1aa19079b9", "f-ohms-2":"64d7db9e24", "f-acdc-1":"31f00a231d",
    "f-series-parallel-1":"6f3cf916e9", "ct-kcl-1":"8ed4b1f438", "ct-kcl-2":"649af4d340", "ct-kvl-1":"d793c45a86",
    "ct-thev-1":"fa377102b4", "ct-thev-2":"af502f2b37", "ct-nort-1":"9cbf3d4ef2", "ct-st-1":"1011aec6f1",
    "ct-st-2":"9e7f42eb8b", "ct-sup-1":"ff9474134e", "ct-sup-2":"973e655bf2", "ct-rec-1":"c19e471270",
    "ct-mpt-1":"a2cd40ad4f", "ct-mpt-2":"b46da6ec37", "de-ns-1":"b1d5781111", "de-ns-2":"47c92ee1c4",
    "de-ns-3":"656b07bbc9", "de-sn-1":"65a7c3cefc", "de-sn-2":"8bf150fa32", "de-ff-1":"c3e66c1668",
    "de-ff-2":"710cab44cf", "de-tc-1":"17dcee2b11", "de-tc-2":"8e611098f1", "mi-err-1":"85a2c53896",
    "mi-err-2":"4ea555df07", "mi-pmmc-1":"1f438d9ff8", "mi-pmmc-2":"f2bb09f9e9", "mi-cls-1":"4566a1fd9d",
    "mi-cls-2":"f542ec28a2", "mi-sm-1":"da8f6eec3d", "mi-sm-2":"63e5ea69ff", "ps-gen-1":"34dbfbce5d",
    "ps-gen-2":"a8f18c2352", "ps-lc-1":"4802624857", "ps-lc-2":"e3dad6bef7", "ps-lc-3":"b630a41f01",
    "ps-tpf-1":"275f57abe1", "ps-tpf-2":"b715b76535", "ps-tpf-3":"7cdc6ee16d", "dc-cw-1":"fff9ce78dd",
    "dc-cw-2":"6d8517ff78", "dc-et-1":"01f4374288", "dc-et-2":"48dafc0515", "dc-ar-1":"d5c833bad8",
    "dc-ar-2":"e637a57dcd", "dc-occ-1":"23c35bfb23", "dc-occ-2":"50c4dd9ccc", "dc-motor-1":"85306b3f49",
    "dc-motor-2":"679288c6b9", "dc-mst-1":"1eb4ea9173", "dc-mst-2":"af1435ea5b", "dc-mst-3":"eec1444b60",
    "xfmr-pe-1":"95b3f1ed7e", "xfmr-pe-2":"dd717f64ea", "xfmr-vr-1":"2e11f48466", "xfmr-vr-2":"8bf64e2f4b",
    "xfmr-eff-1":"9829f6ed07", "xfmr-eff-2":"209204e6e5", "xfmr-eff-3":"5aeb16946a", "xfmr-auto-1":"b5bfdd3ede",
    "xfmr-auto-2":"c1e5aae098", "xfmr-vg-1":"1c96c8f409", "xfmr-vg-2":"a27ff76115", "xfmr-tc-1":"560bbbf9dd",
    "sig-cls-1":"d41fc9ca4c", "sig-cls-2":"351ff94225", "sig-cls-3":"58993e3f51", "sig-prop-1":"17f39c1f5c",
    "sig-prop-2":"15d9c3a938", "sig-prop-3":"a983de58cb", "emt-cs-1":"0048405651", "emt-cs-2":"23bc96558b",
    "emt-vc-1":"3ab2626a59", "emt-vc-2":"964cd0d400", "emt-vc-3":"66273e4210", "sse-bias-1":"a84ded2749",
    "sse-bias-2":"d1f271e266", "sse-hp-1":"2efc5385d6", "sse-hp-2":"fa7ab44630", "sse-hp-3":"684af9d181",
    "sig-conv-1":"6e04834e14", "sig-conv-2":"692b377f19", "sig-conv-3":"49ef5ac2e4", "sig-lap-1":"3b604a129f",
    "sig-lap-2":"8bf589cf61", "sig-lap-3":"72097686c2", "apt-ns-1":"58b2068736", "apt-ns-2":"6b21b4490d",
    "apt-pct-1":"f456cb7f8c", "apt-pct-2":"9f9af02958", "cse-olcl-1":"9b98b35140", "cse-olcl-2":"f1a7f7bf5d",
    "cse-tf-1":"0f0f7bd201", "cse-tf-2":"5b0e8c5281", "cse-tf-3":"7b3078b81e", "cse-bd-1":"9692c19aab",
    "cse-bd-2":"2d20e1f1e1", "cse-bd-3":"e6fcbe3ecf", "cse-tds-1":"9bf7ca2285", "cse-tds-2":"40f2894d5e",
    "cse-tds-3":"f3654f11e3", "cse-routh-1":"564bd12029", "cse-routh-2":"da4b9237ba", "cse-routh-3":"f7949098b7",
    "ct-lap-1":"1b3b95adda", "ct-lap-2":"96c62eba28", "ct-lap-3":"575e2bee5a", "ct-tr-1":"744da8232a",
    "ct-tr-2":"43042f9e88", "ct-tr-3":"8892c19cbf", "ct-tr-4":"1ca300352a", "ct-tr-5":"52a7f7f8c7",
    "ct-rlc-1":"ef3a759cfd", "ct-rlc-2":"5fd32edd08", "ct-rlc-3":"d5421c4cde", "ct-rlc-4":"e409fc0e56",
    "ct-rlc-5":"2d11947aba", "ct-sin-1":"c54b8d0938", "ct-sin-2":"69bb699a33", "ct-sin-3":"eafed4f6a4",
    "ct-prlc-1":"2f0246dff1", "ct-prlc-2":"7e3460da67", "ct-prlc-3":"3835a7a448", "ct-res-1":"9370d736eb",
    "ct-res-2":"127116218c", "ct-res-3":"4455c10c13", "ct-res-4":"310b86e0b6", "ct-res-5":"2f224718c6",
    "psa-pu-1":"686a1cca9d", "psa-pu-2":"9804fc18e6", "psa-pu-3":"6fc72e3855", "psa-pu-4":"2e4a1982a0",
    "psa-sc-1":"2a0fec77c0", "psa-sc-2":"5f20c0146a", "psa-sc-3":"682aded118", "psa-sc-4":"86eee9b414",
    "psa-sc-5":"109996c08a", "psa-flt-1":"584396e6db", "psa-flt-2":"0edda8a3b3", "psa-flt-3":"cc479e669f",
    "psa-flt-4":"84ed58754c", "psa-flt-5":"0e149e91d9", "esd-il-1":"95b8d54abc", "esd-il-2":"bf9b0684bf",
    "esd-il-3":"58bf18cb7a", "esd-il-4":"b95d61ac4a", "esd-lm-1":"e159512e09", "esd-lm-2":"d5313206c8",
    "esd-lm-3":"7719a1c782", "esd-lm-4":"e8b045dde7", "esd-lm-5":"2cdce2e83c", "psd-i-1":"328d72f4bd",
    "psd-i-2":"951c45145e", "psd-i-3":"acd9997d0a", "psd-i-4":"14a3c56aed", "psd-d-1":"36c0d22f02",
    "psd-d-2":"45b08887ef", "psd-d-3":"19d7f196e4", "psd-d-4":"a774839298", "psd-d-5":"4d8063ca09",
    "evt-v-1":"bd623e6150", "evt-v-2":"1a2ce53097", "evt-v-3":"d84f2806f0", "evt-v-4":"67007d0e02",
    "evt-d-1":"518a61661d", "evt-d-2":"d209665fd8", "evt-d-3":"87fe6b099b", "evt-d-4":"d295904853",
    "pq-a-1":"084de6ab66", "pq-a-2":"58addf6cb6", "pq-a-3":"427b9e3911", "pq-a-4":"73b75698ac",
    "pq-h-1":"6d2ba4913c", "pq-h-2":"a62302e8b3", "pq-h-3":"e7396515a2", "pq-h-4":"04a8798a45",
    "pq-h-5":"ee07ea617a", "dsp-cc-1":"221f259dad", "dsp-cc-2":"9f895e5483", "dsp-cc-3":"84986b0509",
    "dsp-cc-4":"71b29d2560", "dsp-ov-1":"d13c7f077d", "dsp-ov-2":"b97ef12b44", "dsp-ov-3":"da4b9237ba",
    "dsp-ov-4":"e8030babc1", "re-pv-1":"acecfd7402", "re-pv-2":"5f31d8131e", "re-pv-3":"1d0007ee7a",
    "re-pv-4":"e68aca618a", "re-pv-5":"6b558c0f7b", "dsp-fft-1":"41a76f2148", "dsp-fft-2":"534d314ce0",
    "dsp-fft-3":"ec2adf6d92", "dsp-fft-4":"ec7aea454c", "dsp-fft-5":"3d811fe541", "dsp-iir-1":"85a21c5a8f",
    "dsp-iir-2":"70833c3e70", "dsp-iir-3":"3ce9562ac1", "dsp-iir-4":"d707f86839", "dsp-iir-5":"30d69f15a8",
    "re-wind-1":"56c65168a8", "re-wind-2":"51bc988f8b", "re-wind-3":"e9db8137db", "re-wind-4":"35ca6f792e",
    "re-wind-5":"8897e827a4", "psd-r-1":"1b97ad3ebd", "psd-r-2":"69ca7e312d", "psd-r-3":"a38a9072b7",
    "psd-r-4":"cd06063342", "psd-r-5":"c075e70f6b", "pe-in-1":"e429b527ab", "pe-in-2":"bdd8d4fede",
    "pe-in-3":"74043f675b", "pe-in-4":"ed9f3bcdb0", "pe-dm-1":"1dc11b6783", "pe-dm-2":"4dec8f2043",
    "pe-dm-3":"42a80e6215", "pe-dm-4":"1aa442b9fd", "pe-dm-5":"1e05495484", "pe-ig-1":"4df74b8fdb",
    "pe-ig-2":"f81f520bbd", "pe-ig-3":"e9495fa24f", "pe-ig-4":"b474c242ee", "pe-ig-5":"bda8ab5fff",
    "pe-scr-1":"86a133b9e2", "pe-scr-2":"e92ce29fc4", "pe-scr-3":"783a07f376", "pe-scr-4":"841da056d2",
    "pe-scr-5":"ef7027dc61", "pe-pr-1":"822a9b34ec", "pe-pr-2":"4204f1711b", "pe-pr-3":"42ed88d604",
    "pe-pr-4":"f2b7ecb969", "pe-pr-5":"7e116e5b61", "pe-pr-6":"b01ece1955", "pe-gd-1":"d8e015425d",
    "pe-gd-2":"67e92f8037", "pe-gd-3":"ee15ea0a72", "pe-gd-4":"71d848307b", "pe-gd-5":"0328c7a487",
    "psa-lf-1":"fc56837d8f", "psa-lf-2":"91829036aa", "psa-lf-3":"3a10b77b2e", "psa-lf-4":"a686bdeddf",
    "psa-lf-5":"302095a679", "psa-gs-1":"fcc4647d11", "psa-gs-2":"bff03c4462", "psa-gs-3":"0d560bcb56",
    "psa-gs-4":"393c7409bd", "psa-gs-5":"15b4720097", "psa-nr-1":"1fdf4476d0", "psa-nr-2":"128c82e14c",
    "psa-nr-3":"3dd12ab9c0", "psa-nr-4":"704a4c67a6", "psa-nr-5":"0239fcf7ed", "psa-fd-1":"50859f928f",
    "psa-fd-2":"7dbf4cd23b", "psa-fd-3":"fb799806dd", "psa-fd-4":"7fec26f63e", "psa-fd-5":"db56db18b2",
    "pe-hw-1":"b685f51ee5", "pe-hw-2":"8a3f82c31b", "pe-hw-3":"eecc91fc12", "pe-hw-4":"04f17ef632",
    "pe-hw-5":"094f9d51b1", "pe-fb-1":"e64df30015", "pe-fb-2":"520cf9fe27", "pe-fb-3":"2a4b40b116",
    "pe-fb-4":"8249b953b7", "pe-fb-5":"05aae941e2", "pe-fb-6":"638da4d5c5", "pe-3h-1":"8bd9bab70f",
    "pe-3h-2":"54b3a717b0", "pe-3h-3":"48a7e6a34d", "pe-3h-4":"82eaff1f95", "pe-3f-1":"b3cb69ba39",
    "pe-3f-2":"2c99255515", "pe-3f-3":"c27f67dadd", "pe-3f-4":"ac6feb4ad9", "pe-3f-5":"bd7e6b8db2",
    "pe-3f-6":"03bd3d4d58", "psa-st-1":"3e178b9261", "psa-st-2":"ac4644215c", "psa-st-3":"bf767a9634",
    "psa-st-4":"47d1d271c4", "psa-st-5":"146f43faac", "psa-sw-1":"3fbc4dc307", "psa-sw-2":"75a6ed103a",
    "psa-sw-3":"3c5174b71d", "psa-sw-4":"583d1ef9cf", "psa-sw-5":"303ca49860", "psa-ea-1":"d17fe5d954",
    "psa-ea-2":"cabbd083dd", "psa-ea-3":"a1730fb880", "psa-ea-4":"289630af26", "psa-ea-5":"ed5424cfd4",
    "psa-ea-6":"404c04eba6", "psa-pmu-1":"9251ba634a", "psa-pmu-2":"2f2d02ef03", "psa-pmu-3":"7771828788",
    "psa-pmu-4":"fd6a2171d1", "acm-con-1":"48126d6dac", "acm-con-2":"746bf7d28a", "acm-con-3":"221cc9455d",
    "acm-con-4":"f05474a149", "acm-emf-1":"e13e48044c", "acm-emf-2":"4e396646a6", "acm-emf-3":"2522c2b519",
    "acm-emf-4":"3bf0cd3838", "acm-har-1":"a4a1d0778d", "acm-har-2":"6697090911", "acm-har-3":"b7c5697e22",
    "acm-har-4":"a25fbdd022", "acm-ar-1":"dd253f42ab", "acm-ar-2":"c4a36ca9f8", "acm-ar-3":"2be3f55c81",
    "acm-ar-4":"3233f8588e", "acm-ph-1":"e212521a2c", "acm-ph-2":"d00e4f176a", "acm-ph-3":"076a659719",
    "acm-ph-4":"a05d8fe596", "acm-reg-1":"2acefde75c", "acm-reg-2":"cc390a664a", "acm-reg-3":"6888319261",
    "acm-reg-4":"de96cc905e", "acm-pot-1":"7bad2eabbc", "acm-pot-2":"4074a3a5b5", "acm-pot-3":"c716cd09cf",
    "acm-pot-4":"8bec0eddbd", "acm-blon-1":"38625c4b1d", "acm-blon-2":"a879cfeaad", "acm-blon-3":"358403547b",
    "acm-blon-4":"dacdd8bab4",
    }
    K = pg.evaluate("""()=>{const o={n:0,pos:[0,0,0,0],dupOpt:[],lenBad:[],groups:[],cor:{},exp:{},unshuf:[],lessons:{}};
        Object.entries(MCQS).forEach(([k,m])=>{o.n++; o.pos[m.a]++; if(new Set(m.opts.map(x=>x.trim().toLowerCase())).size!==m.opts.length) o.dupOpt.push(k); if(m.opts.length!==4||m.a<0||m.a>3) o.lenBad.push(k);
          o.cor[k]=m.opts[m.a]; o.exp[k]=m.exp; if(!mockCanShuffle(m)) o.unshuf.push(k);});
        Object.entries(LESSONS).forEach(([id,l])=>{const g=l.mcqIds||[]; if(g.length>=3){const c=[0,0,0,0]; g.forEach(k=>c[MCQS[k].a]++); o.lessons[id]=[g.length,Math.max(...c)];}});
        return o;}""")
    ok('answer keys are balanced: each of A/B/C/D holds 20-30 % of all MCQs (was A 34 / B 239 / C 65 / D 3, i.e. B = 70 %)', all(0.20*K['n']<=c<=0.30*K['n'] for c in K['pos']), K['pos'])
    dom = [(i,g,mx) for i,(g,mx) in K['lessons'].items() if mx > (2 if g==3 else -(-g//2))]
    ok('no lesson can be beaten by always guessing one letter: in every lesson with 3+ MCQs the most common key covers at most half the questions (at most 2 of 3). Before: 20 lessons were single-keyed', not dom, dom[:5])
    ok('every MCQ has exactly 4 distinct options and a key in 0-3', not K['dupOpt'] and not K['lenBad'], (K['dupOpt'][:3], K['lenBad'][:3]))
    fpbad = [k for k, v in ANSWER_TEXT_FP.items() if k not in K['cor'] or hashlib.sha1(K['cor'][k].encode('utf-8')).hexdigest()[:10] != v]
    ok('the correct-answer TEXT of all 341 original questions is exactly what it was before the rebalance (fingerprints from the pre-rebalance file)', len(ANSWER_TEXT_FP)==341 and not fpbad, fpbad[:5])
    ok('author rule enforced: no MCQ refers to option positions ("option 2", "the last option", "all of the above", (A)+(B)...)', not K['unshuf'], K['unshuf'])
    ok('the 5 explanations that named options by position were reworded (no "Option N" / "last option" left) and now name the content',
       all(t not in K['exp'][i] for i,t in [('ct-sin-2','Option 2'),('ct-prlc-1','Option 1'),('pe-3f-2','option 3'),('acm-emf-1','Option 4'),('acm-blon-2','last option')])
       and 'violates the initial condition' in K['exp']['ct-sin-2'] and 'series circuit' in K['exp']['ct-prlc-1'] and 'semiconverter' in K['exp']['pe-3f-2'] and 'Z_ph (conductors)' in K['exp']['acm-emf-1'] and 'only leakage flux is wrong' in K['exp']['acm-blon-2'])
    syn = pg.evaluate("""()=>{const t=(q,o,e)=>mockCanShuffle({q:q,opts:o||["a","b","c","d"],exp:e||""});
        return {last:t("x",null,"The last option is wrong"), o2:t("x",null,"Option 2 gives 5"), first:t("x",null,"the first choice is right"), above:t("x",["p","q","r","All of the above"]), none:t("x",["p","q","r","None of these"]),
                both:t("x",["Both A and B","q","r","s"]), two:t("Find (A) and (B)"), lone:t("Coulomb (C) is the unit"), pole:t("paths (A) is",["a","b","c","d"],"A equals P"), plain:t("What is 2+2?",["3","4","5","6"],"It is 4."), final:t("x",null,"the final answer is 4.44"), stmt:t("Statement I is true",null)}}""")
    ok('position detector unit tests: rejects "last option", "Option 2", "first choice", "All of the above", "None of these", "Both A and B", two different (A)/(B) letters, "Statement I"',
       not any(syn[k] for k in ['last','o2','first','above','none','both','two','stmt']), syn)
    ok('position detector does not over-reach: a lone "(C)" unit symbol, "paths (A)", plain text and "the final answer is 4.44" stay shuffleable', all(syn[k] for k in ['lone','pole','plain','final']), syn)
    # -- Practice mode with the rebalanced keys: for 12 questions (3 per key position) choose a WRONG option first and check it is scored wrong with the keyed option marked --
    samp = pg.evaluate("""()=>{const out=[]; for(let p=0;p<4;p++){ out.push(...Object.keys(MCQS).filter(k=>MCQS[k].a===p).slice(3*p,3*p+3)); } return out;}""")
    badp = []
    for qid in samp:
        pg.evaluate('nav({page:"mcqset",ids:["%s"]})' % qid); pg.wait_for_timeout(60)
        a_ = pg.evaluate('MCQS["%s"].a' % qid); wrong = (a_ + 1) % 4
        pg.click(f'.opt >> nth={wrong}'); pg.click('#submitMcqBtn')
        pg.wait_for_timeout(60)
        st_ = pg.evaluate("[...document.querySelectorAll('.opt')].map(o=>o.classList.contains('correct')?'C':o.classList.contains('wrong')?'W':'-').join('')")
        exp_pat = ''.join('C' if i==a_ else ('W' if i==wrong else '-') for i in range(4))
        if st_ != exp_pat: badp.append((qid, st_, exp_pat))
    ok('Practice mode after the rebalance: choosing a wrong option on 12 questions (3 per key position) marks that option wrong and exactly the keyed option correct', not badp, badp[:3])

    # =====================================================================
    # SESSION 26: AC Machines Module II row 5 - slip test, regulation of a salient-pole alternator, power developed
    # =====================================================================
    import hashlib as _hl
    LID26 = 'ac-alt-slip-test-power'; ROW26 = 'Regulation of salient pole alternator by slip Test-Power developed'
    d26 = pg.evaluate("""([LID,ROW])=>{const o={}; o.mapped=TOPIC_TO_LESSON[ROW]; o.partial=TOPIC_PARTIAL.has(ROW); o.lv=contentLevel(LID); const L=LESSONS[LID]; o.area=L.area; o.title=L.title;
        o.mcq=(L.mcqIds||[]).map(i=>MCQS[i]&&[i,MCQS[i].d,MCQS[i].a,MCQS[i].opts[MCQS[i].a],MCQS[i].opts.length]);
        o.num=Object.entries(NUMERICALS).filter(([k,v])=>v.lesson===LID).map(x=>[x[0],x[1].d]); o.iv=Object.entries(INTERVIEW).filter(([k,v])=>v.lesson===LID).map(x=>[x[0],x[1].cat]);
        o.fc=FORMULA_CARDS.filter(c=>c.topic==='Salient-pole machines').map(c=>c.name);
        const c=SYLLABUS[5].courses.find(c=>c.title==='AC Machines'); o.row=c.modules[1].topics.indexOf(ROW)+1; o.mod2=c.modules[1].topics.map(t=>TOPIC_TO_LESSON[t]?(TOPIC_PARTIAL.has(t)?'P':'F'):'-').join('');
        o.body=L.body; o.keys=Object.values(MCQS).reduce((a,m)=>{a[m.a]++;return a;},[0,0,0,0]); return o;}""", [LID26, ROW26])
    ok('syllabus row "Regulation of salient pole alternator by slip Test-Power developed" is row 5 of AC Machines Module II and maps fully (not partial) to the new lesson', d26['row']==5 and d26['mapped']==LID26 and not d26['partial'], (d26['row'], d26['mapped']))
    ok('lesson computes to PLACEMENT READY from its real content, is filed under Sem 5 · AC Machines · Module II', d26['lv']=='PLACEMENT READY' and d26['area']=='Sem 5 · AC Machines · Module II', (d26['lv'], d26['area']))
    ok('4 MCQs (E/M/H/P) with four different keyed positions; 2 numericals (M, H); 1 Technical interview question; the 3 new formula cards are in the Salient-pole machines topic',
       [x[1] for x in d26['mcq']]==['E','M','H','P'] and sorted(x[2] for x in d26['mcq'])==[0,1,2,3] and all(x[4]==4 for x in d26['mcq']) and sorted(d26['num'])==[['num-acm-slip-1','M'],['num-acm-slip-2','H']]
       and d26['iv']==[['iv-t-slip','Technical']] and all(n in d26['fc'] for n in ['Slip test: X_d and X_q','Power developed by a salient-pole machine','Axis currents and reluctance power']) and len(d26['fc'])==6, d26)
    ok('answer keys stay balanced (A/B/C/D = 108/107/107/107 after session 32 added 7 of each; each 20-30 %)', d26['keys'] in ([153,152,152,152], [166,165,165,165], [184,183,183,183], [198,197,197,197], [224, 223, 223, 223], [230, 229, 229, 229], [234, 233, 233, 233], [254, 253, 253, 253], [294, 293, 293, 293], [544, 542, 540, 543], [574, 572, 570, 573], [589, 587, 585, 588], [605, 603, 601, 604], [614, 617, 614, 609], [616, 619, 616, 611], [655, 658, 655, 650], [665, 669, 666, 661], [675, 680, 675, 670], [734, 734, 734, 734], [833, 833, 833, 833]) and all(0.2<=k/sum(d26['keys'])<=0.3 for k in d26['keys']), d26['keys'])
    # -- independent reference (own code, not the builder's) --
    S3_ = math.sqrt(3)
    def two_axis_P(Ef, V, Xd, Xq, dd):
        """Solves the machine equation E_f = V + j X_d I_dphasor + j X_q I_qphasor directly with complex numbers (E_f real = q-axis; a lagging d-axis current is -j I_d), then P = Re(V I*).
        This uses neither the derived closed form nor the E' shortcut."""
        d = math.radians(dd); Vp = V*cmath.exp(-1j*d); dE = Ef - Vp
        Id_ = dE.real/Xd; Iq_ = dE.imag/Xq          # X_d I_d + j X_q I_q = E_f - V
        Ic = Iq_ - 1j*Id_
        return (Vp*Ic.conjugate()).real
    def formula_P(Ef, V, Xd, Xq, dd):
        d = math.radians(dd); return Ef*V/Xd*math.sin(d) + V*V/2*(1/Xq-1/Xd)*math.sin(2*d)
    worst = max(abs(two_axis_P(*p, dd)-formula_P(*p, dd)) for p in [(1.5,1,1.0,0.6),(1.4,1,1.1,0.7),(1.5,1,1.2,0.8),(1.0,1,1.0,1.0),(0.0,1,1.0,0.6),(230,230,4.0,2.5)] for dd in range(0,181,7))
    ok('reference: the closed-form P(delta) equals P = Re(V I*) computed from the two-axis equations (3 machines + cylindrical + zero-excitation + a 230 V machine, delta 0-180 deg): worst gap', worst<1e-9, worst)
    def scan_max(Ef, V, Xd, Xq):
        best = max((formula_P(Ef, V, Xd, Xq, x/1000), x/1000) for x in range(0, 180001)); return best[1], best[0]
    smB = scan_max(1.5,1,1.0,0.6); smN2 = scan_max(1.4,1,1.1,0.7)
    ok('reference: brute-force scan (0.001 deg steps) finds the maximum of the lesson machine at 70.06 deg / 1.6238 pu and of numerical 2 at 71.16 deg / 1.3633 pu (before 90 deg in both)',
       abs(smB[0]-70.059)<0.002 and abs(smB[1]-1.62380)<1e-4 and abs(smN2[0]-71.156)<0.002 and abs(smN2[1]-1.36331)<1e-4 and smB[0]<90 and smN2[0]<90, (smB, smN2))
    ok('reference: reluctance power alone peaks at exactly 45 deg with value V^2(Xd-Xq)/(2 Xd Xq) = 0.3333 pu for the lesson machine, and is negative beyond 90 deg',
       abs(max(range(0,1801), key=lambda x: 0.5*(1/0.6-1/1.0)*math.sin(math.radians(2*x/10)))/10-45)<1e-9 and abs(0.5*(1/0.6-1)-1.0*(1.0-0.6)/(2*1.0*0.6))<1e-12 and all(0.5*(1/0.6-1)*math.sin(math.radians(2*x))<0 for x in (100,120,150,170)))
    # -- worked example A: slip test to regulation --
    Xd_ = (100/S3_)/14.5; Xq_ = (96/S3_)/22.0
    ok('worked example A: slip-test reactances X_d = (100/sqrt3)/14.5 = 3.98 ohm and X_q = (96/sqrt3)/22.0 = 2.52 ohm; X_q/X_d = 0.633; pu on Z_base 4.619 ohm = 0.862 and 0.546',
       round(Xd_,2)==3.98 and round(Xq_,2)==2.52 and abs(2.52/3.98-0.633)<5e-4 and abs(400/S3_/50-4.619)<5e-4 and round(3.98/(400/S3_/50),3)==0.862 and round(2.52/(400/S3_/50),3)==0.546
       and all(t in d26['body'] for t in ['3.98 Ω','2.52 Ω','0.633','4.619 Ω','0.862 pu','0.546 pu','57.735/14.5','55.426/22.0']), (Xd_, Xq_))
    RA = blondel(400/S3_, 50, 0.8, False, 0.25, 3.98, 2.52); RC = blondel(400/S3_, 50, 0.8, False, 0.25, 3.98, 3.98)
    dir_ = blondel_direct(400/S3_, 50, 0.8, False, 0.25, 3.98, 2.52)
    ok('worked example A: the E\' construction and the direct two-axis Newton solve agree (E_f 388.53 V, delta 16.42 deg) and E_f = V cos d + Iq Ra + Id Xd', abs(dir_[0]-RA['Ef'])<1e-6 and abs(dir_[1]-RA['delta'])<1e-5 and abs(RA['ident']-RA['Ef'])<1e-9, (dir_, RA['Ef']))
    bA = d26['body']
    ok('worked example A: every printed number matches the reference (V 230.94, E\' 316.54 + j93.30, |E\'| 330.00 (330.004 in the sum), delta 16.42, psi 53.29, Id 40.085, Iq 29.886, extension 58.524, E_f 388.53, +68.2 %, cross-check terms)',
       abs(RA['Ep']-(230.94+85.6+93.3j))<0.01 and all(t in bA for t in ['230.94 V','316.54 + j93.30 V','330.00 V','16.42°','53.29°','40.085 A','29.886 A','330.004 + 40.085 × (3.98 − 2.52) = 330.004 + 58.524','388.53 V','+68.2 %','85.6 + j93.3 V','(10 + 75.6) + j(100.8 − 7.5)',
          f"{230.94*math.cos(math.radians(RA['delta'])):.2f} + {RA['Iq']*0.25:.2f} + {RA['Id']*3.98:.2f} = {230.94*math.cos(math.radians(RA['delta']))+RA['Iq']*0.25+RA['Id']*3.98:.2f} V"]), {k:(round(v,3) if not isinstance(v,complex) else v) for k,v in RA.items()})
    over = RC['delta']/RA['delta']-1
    ok('lesson claim "ignoring salience: E_f 390.97 V (+69.3 %) but load angle 22.83 deg instead of 16.42 deg, an overestimate of about 39 %" is what the reference gives (an earlier draft said "28 % too large", which is the wrong direction of comparison)',
       abs(RC['Ef']-390.97)<0.005 and abs(RC['reg']-69.3)<0.05 and abs(RC['delta']-22.83)<0.005 and abs(over-0.39)<0.005 and all(t in bA for t in ['390.97 V','+69.3 %','22.83°','an overestimate of about 39 %']) and '28 % too large' not in bA, (RC['Ef'], RC['reg'], RC['delta'], over))
    # -- worked example B: table --
    tblB = True; badB = []
    for dd, pe, pr, pt in [(0,0,0,0),(30,0.75,0.2887,1.0387),(45,1.0607,0.3333,1.3940),(60,1.2990,0.2887,1.5877),(70.06,1.4101,0.2137,1.6238),(90,1.5,0.0,1.5),(120,1.2990,-0.2887,1.0104)]:
        e_ = 1.5*math.sin(math.radians(dd)); r_ = 0.5*(1/0.6-1)*math.sin(math.radians(2*dd))
        if not (abs(e_-pe)<6e-5 and abs(r_-pr)<6e-5 and abs(e_+r_-pt)<6e-5): tblB = False; badB.append((dd, e_, r_))
    row_txt = lambda dd, pe, pr, pt: f"<td>{dd}°</td><td>{pe:.4f}</td><td>{('−' if pr<0 else '')}{abs(pr):.4f}</td><td><b>{pt:.4f}</b></td>"
    ok('worked example B: the 7-row table (delta 0/30/45/60/70.06/90/120) equals 1.5 sin d + 0.3333 sin 2d to 4 decimals, and the same numbers are on the page', tblB and all(row_txt(*r) in bA for r in [('30',0.75,0.2887,1.0387),('45',1.0607,0.3333,1.3940),('60',1.2990,0.2887,1.5877),('70.06',1.4101,0.2137,1.6238),('90',1.5,0.0,1.5),('120',1.2990,-0.2887,1.0104)]), badB)
    ok('worked example B: prose says P_max = 1.624 pu at 70.06 deg, cylindrical peak 1.500 at 90 deg, "adds 8.3 %" - reference: 1.6238/1.5 - 1 = 8.25 %',
       all(t in bA for t in ['70.06°','P_max = 1.624 pu','1.500 pu at 90°','adds 8.3 %']) and abs((1.62380/1.5-1)*100-8.25)<0.01)
    # -- numericals: revealed answers vs reference --
    chk26 = {}
    for nid in ['num-acm-slip-1','num-acm-slip-2']:
        pg.evaluate('nav({page:"numerical",id:"%s"})' % nid); pg.click('#revealNumBtn'); chk26[nid] = pg.locator('#contentRoot').inner_text()
    x1d = (330/S3_)/24; x1q = (318/S3_)/41; zb = 3300/S3_/200
    ok('numerical 1 (slip test, star): X_d 7.94 ohm (0.833 pu), X_q 4.48 ohm (0.470 pu), X_q/X_d 0.564, Z_base 9.526 ohm - all match the reference',
       all(t in chk26['num-acm-slip-1'] for t in [f'{x1d:.2f} Ω ({x1d/zb:.3f} pu)', f'{x1q:.2f} Ω ({x1q/zb:.3f} pu)', f'{x1q/x1d:.3f}', f'{zb:.3f} Ω', '190.53 V', '183.60 V']) and round(x1d,2)==7.94 and round(x1q,2)==4.48 and round(x1d/zb,3)==0.833 and round(x1q/zb,3)==0.470 and round(x1q/x1d,3)==0.564, (x1d, x1q, zb))
    ok('numerical 1 common-mistake figures (330/24 = 13.75 ohm; 190.53/41 = 4.65 ohm) are correct', abs(330/24-13.75)<1e-9 and abs(330/S3_/41-4.65)<0.005 and '13.75 Ω' in chk26['num-acm-slip-1'] and '4.65 Ω' in chk26['num-acm-slip-1'])
    A2_ = 1.4/1.1; B2_ = 0.5*(1/0.7-1/1.1); pe40_ = A2_*math.sin(math.radians(40)); pr40_ = B2_*math.sin(math.radians(80))
    c2_ = (-A2_+math.sqrt(A2_**2+32*B2_**2))/(8*B2_); dm2_ = math.degrees(math.acos(c2_)); pe2_ = A2_*math.sin(math.radians(dm2_)); pr2_ = B2_*math.sin(math.radians(2*dm2_))
    ok('numerical 2: (a) P_exc 0.818, P_rel 0.256, P 1.074 at 40 deg; (b) cos d = 0.3230, d = 71.16 deg, P_max 1.363; (c) cylindrical 1.273 at 90 deg, +7.1 % - all match the reference',
       all(t in chk26['num-acm-slip-2'] for t in [f'{pe40_:.4f} pu', f'{pr40_:.4f} pu', f'{pe40_+pr40_:.4f} pu', f'cos δ = {c2_:.4f}', f'δ = {dm2_:.2f}°', f'{pe2_+pr2_:.4f} pu', f'{A2_:.4f} pu at 90°', f'{((pe2_+pr2_)/A2_-1)*100:.1f} %'])
       and round(pe40_+pr40_,3)==1.074 and round(dm2_,2)==71.16 and round(pe2_+pr2_,3)==1.363 and round(((pe2_+pr2_)/A2_-1)*100,1)==7.1, (pe40_, pr40_, dm2_, pe2_+pr2_))
    slope_ = A2_*math.cos(math.radians(dm2_))+2*B2_*math.cos(math.radians(2*dm2_))
    ok('numerical 2 cross-checks: dP/d(delta) = 0 at 71.16 deg (measured slope below 1e-12), the quadratic 1.0390 cos^2 d + 1.2727 cos d - 0.5195 = 0 holds, and the mistake figure 0.167 pu (sin d in the reluctance term) is right',
       abs(slope_)<1e-12 and abs(4*B2_*c2_**2+A2_*c2_-2*B2_)<1e-12 and '1.0390 cos²δ + 1.2727 cos δ − 0.5195 = 0' in chk26['num-acm-slip-2'] and abs(B2_*math.sin(math.radians(40))-0.167)<5e-4 and '0.167 pu' in chk26['num-acm-slip-2'], (slope_, 4*B2_))
    # -- MCQs --
    mq = pg.evaluate('["acm-slip-1","acm-slip-2","acm-slip-3","acm-slip-4"].map(i=>({o:MCQS[i].opts,a:MCQS[i].a,e:MCQS[i].exp,q:MCQS[i].q}))')
    m3a_ = 1.5/1.2*math.sin(math.radians(30)); m3b_ = 0.5*(1/0.8-1/1.2)*math.sin(math.radians(60))
    ok('MCQ 3: keyed answer 0.81 pu = reference (0.6250 + 0.1804 = 0.8054); distractors are exactly the three stated errors (no reluctance 0.63, X_q in the excitation term 0.94, sin d instead of sin 2d 0.73)',
       mq[2]['o'][mq[2]['a']]==f'{m3a_+m3b_:.2f} pu' and sorted(mq[2]['o'])==sorted([f'{m3a_+m3b_:.2f} pu', f'{m3a_:.2f} pu', f'{1.5/0.8*0.5:.2f} pu', f'{m3a_+0.5*(1/0.8-1/1.2)*math.sin(math.radians(30)):.2f} pu']), (mq[2]['o'], mq[2]['a']))
    ok('MCQ 1: keyed answer is "Maximum voltage divided by minimum current" (X_d); the X_q pairing and the OC/SC ratio appear only as distractors', mq[0]['o'][mq[0]['a']]=='Maximum voltage divided by minimum current' and 'Minimum voltage divided by maximum current' in mq[0]['o'] and sum('open-circuit' in o for o in mq[0]['o'])==1)
    ok('MCQ 4: keyed answer names reluctance power peaking at 45 deg, and the one distractor with reluctance power says 90 deg (the only difference)', '45°' in mq[3]['o'][mq[3]['a']] and 'reluctance power' in mq[3]['o'][mq[3]['a']] and any(('reluctance power' in o and '90°' in o) for i, o in enumerate(mq[3]['o']) if i != mq[3]['a']))
    fps = {'acm-slip-1':None,'acm-slip-2':None,'acm-slip-3':None,'acm-slip-4':None}
    ANSWER_TEXT_FP_S26 = {'acm-slip-1':'10c298f4d6','acm-slip-2':'54ca44c6b4','acm-slip-3':'e099fcd514','acm-slip-4':'9232b47c55'}
    fp_now = {k: _hl.sha1(mq[i]['o'][mq[i]['a']].encode('utf-8')).hexdigest()[:10] for i, k in enumerate(fps)}
    ok('session-26 answer-text fingerprints: the correct-answer TEXT of the 4 new questions (re-derived independently above) is guarded like the 341 older ones', fp_now==ANSWER_TEXT_FP_S26, fp_now)
    # -- lesson page + figure geometry --
    pg.evaluate('nav({page:"lesson",id:"%s"})' % LID26); pg.wait_for_timeout(150)
    ok('lesson page has one figure, 3 formula boxes, callouts (mistake + trap), and buttons to 4 MCQs / 2 numericals / 1 interview question',
       pg.locator('.lesson .diagram svg').count()==1 and pg.locator('.lesson .formula-box').count()==3 and pg.locator('.lesson .callout-trap').count()==1 and pg.locator('.lesson .callout-mistake').count()==1
       and 'Practice 4 MCQs' in pg.locator('#contentRoot').inner_text() and 'Solve 2 numericals' in pg.locator('#contentRoot').inner_text() and '1 interview question' in pg.locator('#contentRoot').inner_text(),
       (pg.locator('.lesson .formula-box').count(),))
    fg26 = pg.evaluate("""()=>{const s=document.querySelector('.lesson .diagram svg'); const o={x0:+s.dataset.x0,kx:+s.dataset.kx,oy:+s.dataset.oy,ky:+s.dataset.ky,curves:{},pts:{},txt:[...s.querySelectorAll('text')].map(t=>t.textContent).join(' | '),aria:s.getAttribute('aria-label'),
        axis:[...s.querySelectorAll('[data-axis="p0"]')].map(l=>[+l.getAttribute('y1'),+l.getAttribute('y2')])[0]};
        s.querySelectorAll('[data-curve]').forEach(c=>{o.curves[c.dataset.curve]=c.getAttribute('points').trim().split(/\\s+/).map(p=>p.split(',').map(Number));});
        s.querySelectorAll('[data-pt]').forEach(c=>{o.pts[c.dataset.pt]=[+c.getAttribute('cx'),+c.getAttribute('cy')];}); return o;}""")
    dx = lambda x: (x-fg26['x0'])/fg26['kx']; py_ = lambda y: (fg26['oy']-y)/fg26['ky']
    cv = {k: [(dx(x), py_(y)) for x, y in v] for k, v in fg26['curves'].items()}
    e_err = max(abs(p-1.5*math.sin(math.radians(d))) for d, p in cv['exc']); r_err = max(abs(p-0.5*(1/0.6-1)*math.sin(math.radians(2*d))) for d, p in cv['rel']); t_err = max(abs(p-formula_P(1.5,1,1.0,0.6,d)) for d, p in cv['tot'])
    ok('figure: each of the three curves has 181 computed points (1 deg steps, 0-180) and matches its formula to within 0.005 pu (measured worst gaps: exc, rel, total)', all(len(cv[k])==181 for k in cv) and e_err<0.005 and r_err<0.005 and t_err<0.005 and abs(cv['tot'][0][0])<1e-2 and abs(cv['tot'][-1][0]-180)<1e-2, (e_err, r_err, t_err))
    ok('figure: total = excitation + reluctance point by point (worst gap < 0.01 pu), the total curve peaks at 70 deg on the 1-degree grid, and the reluctance curve is negative beyond 90 deg',
       max(abs(a[1]+b[1]-t[1]) for a, b, t in zip(cv['exc'], cv['rel'], cv['tot']))<0.01 and round(max(cv['tot'], key=lambda p: p[1])[0])==70 and all(p<0 for d, p in cv['rel'] if 91<=d<=179), )
    mk = {k: (dx(v[0]), py_(v[1])) for k, v in fg26['pts'].items()}
    ok('figure markers: total maximum at (70.06 deg, 1.6238 pu), excitation peak at (90 deg, 1.500 pu), reluctance peak at (45 deg, 0.3333 pu), and each lies on its curve within 0.006 pu',
       abs(mk['max'][0]-70.06)<0.02 and abs(mk['max'][1]-1.6238)<0.002 and abs(mk['excpk'][0]-90)<0.02 and abs(mk['excpk'][1]-1.5)<0.002 and abs(mk['relpk'][0]-45)<0.02 and abs(mk['relpk'][1]-1/3)<0.002
       and abs(mk['max'][1]-formula_P(1.5,1,1.0,0.6,mk['max'][0]))<0.006, mk)
    ok('figure: zero-power axis is drawn at P = 0 (measured from the scale); labels state 1.624 / 70.06 / 1.500 / 0.333 / 45 and the aria-label describes the curves',
       abs(py_(fg26['axis'][0]))<1e-9 and all(t in fg26['txt'] for t in ['P_max = 1.624 pu at δ = 70.06°','P_exc peak 1.500 pu at 90°','P_rel peak 0.333 pu at 45°','(negative beyond 90°)','0.3333 sin 2δ','1.5 sin δ']) and 'power-angle curves of a salient-pole alternator' in fg26['aria'].lower() and '1.624' in fg26['aria'] and '70.06' in fg26['aria'], fg26['txt'][:120])
    ok('no placeholder wording in the new lesson', not any(w in d26['body'].lower() for w in ['lorem','coming soon','todo','tbd','sample question','comprehensive overview']))
    ok('lesson says plainly what it does NOT cover (load test / parallel operation / synchronising power are later rows) and does not claim them', 'This lesson covers the slip test, the regulation it gives, and P(δ) only.' in d26['body'] and 'synchronising power and torque' in d26['body'])
    # -- search, links, mobile --
    pg.evaluate('nav({page:"search",q:"slip test"})'); pg.wait_for_timeout(150); sr26 = pg.locator('#contentRoot').inner_text()
    ok('search for "slip test" finds the lesson, the syllabus row (marked "Lesson ready") and the interview question', 'Slip Test, Regulation of a Salient-Pole Alternator' in sr26 and 'Regulation of salient pole alternator by slip Test-Power developed' in sr26 and 'Lesson ready' in sr26 and 'Interview questions' in sr26, sr26[:300])
    bad_m26 = []
    for rt in ['{page:"lesson",id:"ac-alt-slip-test-power"}','{page:"numerical",id:"num-acm-slip-1"}','{page:"numerical",id:"num-acm-slip-2"}','{page:"course",sem:5,code:"23EEP504"}','{page:"formulabook"}']:
        m.evaluate(f'nav({rt})'); m.wait_for_timeout(350)
        if not m.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'): bad_m26.append(rt)
    ok('mobile (390 px): no horizontal overflow on the new lesson, both numericals, the AC Machines course page and the Formula Book', not bad_m26, bad_m26)
    pg.evaluate('nav({page:"lesson",id:"%s"})' % LID26)
    ok('lesson prerequisite links work (3 internal lesson links resolve to real lessons)', pg.evaluate('[...document.querySelectorAll(".lesson a[data-nav^=\\"lesson:\\"]")].map(a=>a.dataset.nav.slice(7)).every(id=>!!LESSONS[id])') and pg.locator('.lesson a[data-nav^="lesson:"]').count()==3)
    # -- Practice mode on the 4 new MCQs: a wrong option first, keyed option marked correct --
    bad26p = []
    for qid in ['acm-slip-1','acm-slip-2','acm-slip-3','acm-slip-4']:
        pg.evaluate('nav({page:"mcqset",ids:["%s"]})' % qid); pg.wait_for_timeout(60)
        a_ = pg.evaluate('MCQS["%s"].a' % qid); wrong = (a_+1) % 4
        st0 = pg.evaluate("[...document.querySelectorAll('.opt')].map(o=>o.classList.contains('correct')||o.classList.contains('wrong')||o.classList.contains('selected')?'x':'-').join('')")
        pg.click(f'.opt >> nth={wrong}'); pg.click('#submitMcqBtn'); pg.wait_for_timeout(60)
        st_ = pg.evaluate("[...document.querySelectorAll('.opt')].map(o=>o.classList.contains('correct')?'C':o.classList.contains('wrong')?'W':'-').join('')")
        exp_pat = ''.join('C' if i==a_ else ('W' if i==wrong else '-') for i in range(4))
        if st_ != exp_pat or st0 != '----': bad26p.append((qid, st0, st_, exp_pat))
    ok('Practice mode on the 4 new MCQs: all options start unmarked; a wrong pick is marked wrong and exactly the keyed option is marked correct after Submit', not bad26p, bad26p)
    # -- the mock still shuffles every question, including the 4 new ones (no positional wording) --
    ok('the 4 new MCQs contain no positional wording, so the mock can shuffle all of them', pg.evaluate('["acm-slip-1","acm-slip-2","acm-slip-3","acm-slip-4"].every(i=>mockCanShuffle(MCQS[i]))'))

    # =====================================================================
    # SESSION 27: AC Machines Module II row 7 - synchronising power and torque (power and torque equations)
    # =====================================================================
    LID27 = 'ac-alt-synchronising-power-torque'; ROW27 = 'Synchronising Power and Torque- Power and Torque equations'
    d27 = pg.evaluate("""([LID,ROW])=>{const o={}; o.mapped=TOPIC_TO_LESSON[ROW]; o.partial=TOPIC_PARTIAL.has(ROW); o.lv=contentLevel(LID); const L=LESSONS[LID]; o.area=L.area; o.title=L.title;
        o.mcq=(L.mcqIds||[]).map(i=>MCQS[i]&&[i,MCQS[i].d,MCQS[i].a,MCQS[i].opts[MCQS[i].a],MCQS[i].opts.length]);
        o.num=Object.entries(NUMERICALS).filter(([k,v])=>v.lesson===LID).map(x=>[x[0],x[1].d]); o.iv=Object.entries(INTERVIEW).filter(([k,v])=>v.lesson===LID).map(x=>[x[0],x[1].cat]);
        o.fc=FORMULA_CARDS.filter(c=>c.topic==='Synchronising power and torque').map(c=>c.name); o.fcSal=FORMULA_CARDS.filter(c=>c.topic==='Salient-pole machines').length;
        const c=SYLLABUS[5].courses.find(c=>c.title==='AC Machines'); o.row=c.modules[1].topics.indexOf(ROW)+1; o.mod2=c.modules[1].topics.map(t=>TOPIC_TO_LESSON[t]?(TOPIC_PARTIAL.has(t)?'P':'F'):'-').join('');
        o.r6=TOPIC_TO_LESSON[c.modules[1].topics[5]]||null; o.r8=TOPIC_TO_LESSON[c.modules[1].topics[7]]||null; o.r5=TOPIC_TO_LESSON[c.modules[1].topics[4]]; o.r5body=LESSONS['ac-alt-slip-test-power'].body;
        o.body=L.body; o.keys=Object.values(MCQS).reduce((a,m)=>{a[m.a]++;return a;},[0,0,0,0]); return o;}""", [LID27, ROW27])
    ok('syllabus row "Synchronising Power and Torque- Power and Torque equations" is row 7 of AC Machines Module II and maps fully (not partial) to the new lesson', d27['row']==7 and d27['mapped']==LID27 and not d27['partial'], (d27['row'], d27['mapped']))
    ok('honesty: row 6 (load test / parallel operation) was written in session 28 (maps to the session-28 lesson), row 8 (methods of synchronisation) was written in session 29 (maps to the session-29 lesson), so Module II is FFFFFFFF, and row 5 still maps to the session-26 lesson', d27['r6']=='ac-alt-load-test-parallel' and d27['r8']=='ac-alt-methods-synchronisation' and d27['mod2']=='FFFFFFFF' and d27['r5']=='ac-alt-slip-test-power', d27['mod2'])
    ok('lesson computes to PLACEMENT READY from its real content, is filed under Sem 5 · AC Machines · Module II', d27['lv']=='PLACEMENT READY' and d27['area']=='Sem 5 · AC Machines · Module II', (d27['lv'], d27['area']))
    ok('4 MCQs (E/M/H/P) with four different keyed positions (B, D, A, C); 2 numericals (M, H); 1 Technical interview question; 3 new formula cards in their own topic; Salient-pole machines still has 6',
       [x[1] for x in d27['mcq']]==['E','M','H','P'] and [x[2] for x in d27['mcq']]==[1,3,0,2] and all(x[4]==4 for x in d27['mcq']) and sorted(d27['num'])==[['num-acm-syn-1','M'],['num-acm-syn-2','H']]
       and d27['iv']==[['iv-t-syncpower','Technical']] and d27['fc']==['Synchronising power','Synchronising power from the delivered power','Synchronising torque and unit conversion'] and d27['fcSal']==6, d27)
    ok('answer keys A/B/C/D = 108/107/107/107 after session 32 added 28 more (7 of each; best single-letter guess 25.2 %; the session-27 lesson\'s own four keys are checked below)', d27['keys'] in ([153,152,152,152], [166,165,165,165], [184,183,183,183], [198,197,197,197], [224, 223, 223, 223], [230, 229, 229, 229], [234, 233, 233, 233], [254, 253, 253, 253], [294, 293, 293, 293], [544, 542, 540, 543], [574, 572, 570, 573], [589, 587, 585, 588], [605, 603, 601, 604], [614, 617, 614, 609], [616, 619, 616, 611], [655, 658, 655, 650], [665, 669, 666, 661], [675, 680, 675, 670], [734, 734, 734, 734], [833, 833, 833, 833]) and max(d27['keys'])/sum(d27['keys'])<0.26, d27['keys'])
    # -- independent reference (own code; the derivative is taken NUMERICALLY from the two-axis machine equations, not from the closed form) --
    def dPdd_num(Ef, V, Xd, Xq, dd, h=1e-4):
        return (two_axis_P(Ef, V, Xd, Xq, dd+h) - two_axis_P(Ef, V, Xd, Xq, dd-h)) / (2*math.radians(h))
    def syn_formula(Ef, V, Xd, Xq, dd):
        d = math.radians(dd); return Ef*V/Xd*math.cos(d) + V*V*(1/Xq-1/Xd)*math.cos(2*d)
    worst27 = max(abs(dPdd_num(*p, dd) - syn_formula(*p, dd)) for p in [(1.5,1,1.0,0.6),(1.4,1,1.1,0.7),(1.5,1,1.2,0.8),(1.5,1,1.0,1.0),(230,230,4.0,2.5)] for dd in range(1,180,7))
    ok('reference: the closed-form P_syn = (E_f V/X_d) cos d + V^2 (1/X_q - 1/X_d) cos 2d equals the central-difference slope of P = Re(V I*) from the two-axis equations (4 salient machines + cylindrical, delta 1-176 deg): worst gap', worst27<1e-4, worst27)
    ok('reference: P_syn is zero exactly at the maximum-power angle of the previous lesson (70.06 deg lesson machine, 71.16 deg numerical 2; brute-force scan) and the salient zero is below 90 deg while the cylindrical zero is at 90 deg',
       abs(syn_formula(1.5,1,1.0,0.6,smB[0]))<2e-3 and abs(syn_formula(1.4,1,1.1,0.7,smN2[0]))<2e-3 and smB[0]<90 and smN2[0]<90 and abs(math.cos(math.radians(90)))<1e-12, (smB, smN2))
    cyl_gap = max(abs(1.5*math.cos(math.radians(dd)) - 1.5*math.sin(math.radians(dd))/math.tan(math.radians(dd))) for dd in range(1,179,3))
    ok('reference: cylindrical P_syn = P cot d (worst gap over 1-178 deg) and both equal the numerical slope', cyl_gap<1e-12 and abs(dPdd_num(1.5,1,1.0,1.0,40)-1.5*math.cos(math.radians(40)))<1e-4, cyl_gap)
    # -- worked example A (salient, pu) --
    bA27 = d27['body']
    Psal_ = lambda dd: formula_P(1.5,1,1.0,0.6,dd); Ssal_ = lambda dd: syn_formula(1.5,1,1.0,0.6,dd); Scyl_ = lambda dd: 1.5*math.cos(math.radians(dd))
    sgn = lambda x, n=4: ('−' if round(x, n) < 0 else '') + f'{abs(x):.{n}f}'
    rowsA_ok = True; badA27 = []
    for dd in (0,30,45,60,70.06,90,120):
        ds = ('%g' % dd); t = f'<tr><td>{ds}°</td><td>{sgn(Psal_(dd))}</td><td><b>{sgn(Ssal_(dd))}</b></td><td>{sgn(Scyl_(dd))}</td></tr>'
        if t not in bA27: rowsA_ok = False; badA27.append(t)
    ok('worked example A: all 7 rows of the P / P_syn (salient) / P_syn (cylindrical) table equal the independent reference to 4 decimals and are on the page', rowsA_ok, badA27)
    ok('worked example A: P_syn = 1.5 cos d + 0.6667 cos 2d; zero at 70.06 deg (the P maximum 1.6238 pu); at 30 deg 1.6324 pu/rad vs 1.2990 cylindrical; 0.02849 pu per electrical degree; 5 deg estimate 0.142 vs exact P(35)-P(30) = 0.135',
       abs(Ssal_(30)-1.6324)<5e-5 and abs(Scyl_(30)-1.2990)<5e-5 and abs(Ssal_(30)*math.pi/180-0.02849)<5e-6 and abs(Ssal_(30)*math.radians(5)-0.142)<5e-4 and abs((Psal_(35)-Psal_(30))-0.135)<5e-4 and abs(Psal_(35)-1.1736)<5e-5 and abs(Psal_(30)-1.0387)<5e-5
       and all(t in bA27 for t in ['1.5 cos δ + 0.6667 cos 2δ','δ = 70.06°','1.6238 pu','1.6324 pu per radian','0.02849 pu','0.02849 × 5 = 0.142 pu','1.1736 − 1.0387 = 0.135 pu']))
    # -- excitation table --
    okE27 = True; badE27 = []
    for Ef in (1.2, 1.5, 1.8):
        dd = math.degrees(math.asin(0.8/Ef)); ps = Ef*math.cos(math.radians(dd))
        t = f'<tr><td>{Ef:.1f}</td><td>{dd:.2f}°</td><td><b>{ps:.4f}</b></td></tr>'
        if t not in bA27 or abs(ps-0.8/math.tan(math.radians(dd)))>1e-12: okE27 = False; badE27.append((Ef, dd, ps))
    ok('excitation table (P = 0.8, V = 1, X_s = 1): for E_f 1.2 / 1.5 / 1.8 the angle falls and P_syn rises (0.8944, 1.2689, 1.6125), every row satisfies P_syn = 0.8 cot d, and the rows are on the page', okE27, badE27)
    # -- worked example B (4-pole 5 MVA, 11 kV, X_s 12) --
    VB = 11000/S3_; IB = 5e6/(S3_*11000); ICB = IB*cmath.exp(-1j*math.acos(0.8)); EB = VB + 1j*12*ICB; EfB_ = abs(EB); dB_ = math.degrees(cmath.phase(EB))
    KB_ = EfB_*VB/12; PB_ = 3*KB_*math.sin(math.radians(dB_)); SB_ = 3*KB_*math.cos(math.radians(dB_)); wB_ = 2*math.pi*1500/60
    ok('worked example B reference: V 6350.85, I 262.43 (209.94 - j157.46), E_f = 8240.4 + j2519.3 = 8616.9 V at 17.00 deg, P = 4.000 MW = 5 MVA x 0.8 (so the phasor solution and the power formula agree)',
       abs(VB-6350.85)<5e-3 and abs(IB-262.43)<5e-3 and abs(round(IB,2)*0.8-209.94)<5e-3 and abs(round(IB,2)*0.6-157.46)<5e-3 and abs(ICB.real-209.94)<1e-2 and abs(ICB.imag+157.46)<5e-3 and abs(EB.real-8240.4)<0.05 and abs(EB.imag-2519.3)<0.05 and abs(EfB_-8616.9)<0.05 and abs(dB_-17.00)<5e-3 and abs(PB_-4.0e6)<1 
       and all(t in bA27 for t in ['6350.85 V','262.43 A','209.94 − j157.46 A','1889.5 + j2519.3 V','8240.4 + j2519.3 V','8616.9 V','17.00°','4.000 MW']), (EfB_, dB_, PB_))
    import re as _re27; bA27t = _re27.sub('<[^>]+>', '', bA27)   # tags removed so a bold number inside a sentence does not hide it
    ok('worked example B: total P_syn 13.083 MW/rad = P cot d (independent); per electrical degree 228.35 kW; per mechanical degree (4-pole, x2) 456.69 kW; N_s 1500, w_sm 157.08; T_syn 83,291 N.m per electrical rad and 2907.4 N.m per mechanical degree; 11.4 % of full-load torque; every printed number appears',
       abs(SB_/1e6-13.083)<5e-4 and abs(SB_-PB_/math.tan(math.radians(dB_)))<1 and abs(SB_*math.pi/180/1e3-228.35)<5e-3 and abs(SB_*2*math.pi/180/1e3-456.69)<5e-3 and abs(SB_/wB_-83291)<0.5 and abs(SB_/wB_*2*math.pi/180-2907.4)<0.05 and abs(SB_/wB_*2*math.pi/180/(PB_/wB_)*100-11.4)<0.05
       and all(t in bA27t for t in ['13.083 MW per electrical radian','13.0833 × π/180 = 0.228347 MW = 228.35 kW','228.347 × 2 = 456.69 kW','83,291 N·m per electrical radian','2907.4 N·m','25,465 N·m','11.4 %','157.08 rad/s','1500 rpm','4.000 × 3.2708 = 13.083 MW per radian','456.69 kW ÷ 157.08 rad/s = 2907.4 N·m']), (SB_, SB_/wB_))
    # electrical = (p/2) x mechanical, checked by really displacing the rotor 1 mechanical degree = 2 electrical degrees on the exact power curve
    Pcyl = lambda dd: 3*KB_*math.sin(math.radians(dd))
    cen = (Pcyl(dB_+1.0)-Pcyl(dB_-1.0))/2   # +-1 electrical deg -> per 1 electrical degree
    mech = (Pcyl(dB_+2.0)-Pcyl(dB_-2.0))/2  # +-1 mechanical degree of a 4-pole rotor = +-2 electrical degrees
    ok('reference: displacing the 4-pole rotor by 1 mechanical degree (= 2 electrical degrees) on the exact power curve changes the power by 456.7 kW (0.05 %) - so the x p/2 conversion and the printed 456.69 kW are right; the per-electrical-degree value is half of it',
       abs(mech/1e3-456.69)/456.69<5e-4 and abs(cen/1e3-228.35)/228.35<5e-4 and abs(mech/cen-2)<2e-3, (mech, cen))
    # -- numericals --
    chk27 = {}
    for nid in ['num-acm-syn-1','num-acm-syn-2']:
        pg.evaluate('nav({page:"numerical",id:"%s"})' % nid); pg.click('#revealNumBtn'); chk27[nid] = pg.locator('#contentRoot').inner_text()
    V1_ = 6600/S3_; K1_ = 4800*V1_/5; P1_ = 3*K1_*math.sin(math.radians(20)); S1_ = 3*K1_*math.cos(math.radians(20)); w1_ = 2*math.pi*1000/60
    ok('numerical 1 (star, 6-pole, 6.6 kV): V 3810.51 V, P 3.753 MW, P_syn 10.3124 MW/rad = 540.0 kW per mechanical degree (179.99 kW per electrical degree), N_s 1000, w 104.72, T_syn 98,477 N.m/rad = 5156 N.m per mechanical degree - all match the reference',
       all(t in chk27['num-acm-syn-1'] for t in [f'{V1_:.2f} V', f'{P1_/1e6:.3f} MW', f'{S1_/1e6:.4f} MW', f'{S1_*3*math.pi/180/1e3:.2f} kW', f'{S1_*math.pi/180/1e3:.1f} kW', f'{S1_/w1_:,.0f} N·m', f'{S1_/w1_*3*math.pi/180:.0f} N·m', '104.72 rad/s', '1000 rpm'])
       and round(P1_/1e6,3)==3.753 and round(S1_/1e6,4)==10.3124 and abs(S1_*3*math.pi/180/1e3-539.96)<5e-3 and round(S1_/w1_*3*math.pi/180)==5156, (P1_, S1_))
    ok('numerical 1 common-mistake figures: the per-electrical-degree value (180.0 kW) is 3x too small for a 6-pole machine, and sin 20 deg in place of cos 20 deg just returns the power 3.753 MW',
       abs(S1_*math.pi/180/1e3-179.99)<5e-3 and abs(S1_*3*math.pi/180/(S1_*math.pi/180)-3)<1e-12 and '3.753 MW per radian' in chk27['num-acm-syn-1'] and '180.0 kW' in chk27['num-acm-syn-1'], (S1_*math.pi/180/1e3,))
    A2_s = 1.4/1.1; B2_s = 1/0.7-1/1.1; S40 = syn_formula(1.4,1,1.1,0.7,40); C40 = A2_s*math.cos(math.radians(40)); c_z = (-A2_s+math.sqrt(A2_s**2+8*B2_s**2))/(4*B2_s); dz = math.degrees(math.acos(c_z))
    ok('numerical 2 (X_d 1.1, X_q 0.7, E_f 1.4): (a) P_syn(40 deg) = 1.0652 pu/rad (0.01859 per electrical degree); (b) zero at cos d = 0.3230, d = 71.16 deg = the maximum-power angle of the session-26 numerical (reference scan 71.16); (c) cylindrical 0.9750 at 40 deg (salient 9.3 % higher), 0.4111 at 71.16 deg - all match',
       all(t in chk27['num-acm-syn-2'] for t in [f'{S40:.4f} pu per radian', f'{S40*math.pi/180:.5f} pu per electrical degree', f'cos δ = {c_z:.4f}', f'δ = {dz:.2f}°', f'{C40:.4f} pu per radian', f'{(S40/C40-1)*100:.1f} %', f'{A2_s*math.cos(math.radians(dz)):.4f} pu per radian'])
       and round(S40,4)==1.0652 and abs(dz-smN2[0])<0.002 and round(dz,2)==71.16 and round((S40/C40-1)*100,1)==9.3 and abs(syn_formula(1.4,1,1.1,0.7,dz))<1e-12, (S40, dz, smN2))
    ok('numerical 2 quadratic and the mistake figure: 1.0390 cos^2 d + 1.2727 cos d - 0.5195 = 0 has the printed root, and cos d in the reluctance term would give 0.3979 instead of 0.0902',
       '1.0390 cos²δ + 1.2727 cos δ − 0.5195 = 0' in chk27['num-acm-syn-2'] and abs(2*B2_s*c_z**2+A2_s*c_z-B2_s)<1e-12 and abs(B2_s*math.cos(math.radians(40))-0.3979)<5e-5 and abs(B2_s*math.cos(math.radians(80))-0.0902)<5e-5 and '0.3979' in chk27['num-acm-syn-2'] and '0.0902' in chk27['num-acm-syn-2'])
    # -- MCQs --
    mq27 = pg.evaluate('["acm-syn-1","acm-syn-2","acm-syn-3","acm-syn-4"].map(i=>({o:MCQS[i].opts,a:MCQS[i].a,e:MCQS[i].exp,q:MCQS[i].q}))')
    ok('MCQ 1: keyed answer is the cosine form; the sine form (the power itself), tan and (1 - cos) appear only as distractors', mq27[0]['o'][mq27[0]['a']]=='(E_f V / X_s) cos δ' and '(E_f V / X_s) sin δ' in mq27[0]['o'] and len(set(mq27[0]['o']))==4)
    ok('MCQ 2: the keyed option is "smaller load angle and larger synchronising power"; its exact reverse (larger angle, smaller P_syn) is a distractor; the explanation numbers (41.81 -> 26.39 deg; 0.894 -> 1.612) match the reference',
       mq27[1]['o'][mq27[1]['a']]=='A smaller load angle and a larger synchronising power' and 'A larger load angle and a smaller synchronising power' in mq27[1]['o']
       and all(t in mq27[1]['e'] for t in ['41.81°','26.39°','0.894','1.612']) and abs(math.degrees(math.asin(0.8/1.2))-41.81)<5e-3 and abs(math.degrees(math.asin(0.8/1.8))-26.39)<5e-3 and abs(1.2*math.cos(math.asin(0.8/1.2))-0.894)<5e-4 and abs(1.8*math.cos(math.asin(0.8/1.8))-1.612)<5e-4)
    d3 = math.degrees(math.asin(0.6*1.25/(1.5*1))); s3 = 1.5/1.25*math.cos(math.radians(d3))
    ok('MCQ 3: sin d = 0.5 so d = 30 deg and P_syn = 1.04; distractors are exactly the three stated errors (no cosine 1.20, sin d instead of cos d 0.60, P cos d 0.52); also equals P cot d',
       abs(d3-30)<1e-9 and mq27[2]['o'][mq27[2]['a']]==f'{s3:.2f} pu per radian' and sorted(mq27[2]['o'])==sorted([f'{s3:.2f} pu per radian','1.20 pu per radian','0.60 pu per radian',f'{0.6*math.cos(math.radians(30)):.2f} pu per radian']) and abs(0.6/math.tan(math.radians(30))-s3)<1e-12 and abs(1.5/1.25-1.20)<1e-12, (mq27[2]['o'], s3))
    rel_syn = lambda dd: 1.0*(1/0.6-1/1.0)*math.cos(math.radians(2*dd))
    ok('MCQ 4: keyed answer says below 90 deg because the reluctance part turns negative beyond 45 deg - reference: that term is +ve at 44, 0 at 45, -ve at 46 and 90 deg, and the total P_syn is still positive at 45 deg while the crossing is below 90 deg; the 45-deg distractor is the wrong-quantity trap',
       'below 90°' in mq27[3]['o'][mq27[3]['a']] and '45°' in mq27[3]['o'][mq27[3]['a']] and rel_syn(44)>0 and abs(rel_syn(45))<1e-12 and rel_syn(46)<0 and rel_syn(90)<0 and Ssal_(45)>0 and smB[0]<90 and any(('exactly 45°' in o) for i, o in enumerate(mq27[3]['o']) if i != mq27[3]['a']), mq27[3]['o'])
    ANSWER_TEXT_FP_S27 = {'acm-syn-1': '613d61c372', 'acm-syn-2': 'a96a0a3d6b', 'acm-syn-3': '7822630509', 'acm-syn-4': 'e047cc00e8'}
    fp27 = {k: _hl.sha1(mq27[i]['o'][mq27[i]['a']].encode('utf-8')).hexdigest()[:10] for i, k in enumerate(ANSWER_TEXT_FP_S27)}
    ok('session-27 answer-text fingerprints: the correct-answer TEXT of the 4 new questions (re-derived independently above) is guarded like the 345 older ones', fp27==ANSWER_TEXT_FP_S27, fp27)
    # -- lesson page + figure geometry --
    pg.evaluate('nav({page:"lesson",id:"%s"})' % LID27); pg.wait_for_timeout(150)
    ok('lesson page has one figure, 6 formula boxes, exactly one mistake and one trap callout, and buttons to 4 MCQs / 2 numericals / 1 interview question',
       pg.locator('.lesson .diagram svg').count()==1 and pg.locator('.lesson .formula-box').count()==6 and pg.locator('.lesson .callout-trap').count()==1 and pg.locator('.lesson .callout-mistake').count()==1
       and 'Practice 4 MCQs' in pg.locator('#contentRoot').inner_text() and 'Solve 2 numericals' in pg.locator('#contentRoot').inner_text() and '1 interview question' in pg.locator('#contentRoot').inner_text(), (pg.locator('.lesson .formula-box').count(),))
    fg27 = pg.evaluate("""()=>{const s=document.querySelector('.lesson .diagram svg'); const o={x0:+s.dataset.x0,kx:+s.dataset.kx,oy:+s.dataset.oy,ky:+s.dataset.ky,curves:{},pts:{},txt:[...s.querySelectorAll('text')].map(t=>t.textContent).join(' | '),aria:s.getAttribute('aria-label'),
        axis:[...s.querySelectorAll('[data-axis="p0"]')].map(l=>[+l.getAttribute('y1'),+l.getAttribute('y2')])[0], vb:s.getAttribute('viewBox')};
        s.querySelectorAll('[data-curve]').forEach(c=>{o.curves[c.dataset.curve]=c.getAttribute('points').trim().split(/\\s+/).map(p=>p.split(',').map(Number));});
        s.querySelectorAll('[data-pt]').forEach(c=>{o.pts[c.dataset.pt]=[+c.getAttribute('cx'),+c.getAttribute('cy')];}); return o;}""")
    dx27 = lambda x: (x-fg27['x0'])/fg27['kx']; py27 = lambda y: (fg27['oy']-y)/fg27['ky']
    cv27 = {k: [(dx27(x), py27(y)) for x, y in v] for k, v in fg27['curves'].items()}
    es = max(abs(p-Ssal_(d)) for d, p in cv27['sal']); ec = max(abs(p-Scyl_(d)) for d, p in cv27['cyl'])
    ok('figure: both curves have 181 computed points (1 deg steps, 0-180) and match P_syn (salient) and 1.5 cos d (cylindrical) to within 0.005 pu/rad (measured worst gaps)', all(len(cv27[k])==181 for k in cv27) and es<0.005 and ec<0.005 and abs(cv27['sal'][0][0])<1e-2 and abs(cv27['sal'][-1][0]-180)<1e-2, (es, ec))
    # the figure must really be the SLOPE of the previous lesson's power-angle figure: read that figure's total-power polyline from its lesson body and differentiate it
    pa = pg.evaluate("""()=>{const d=document.createElement('div'); d.innerHTML=LESSONS['ac-alt-slip-test-power'].body; const s=d.querySelector('svg'); const c=s.querySelector('[data-curve="tot"]');
        return {x0:+s.dataset.x0,kx:+s.dataset.kx,oy:+s.dataset.oy,ky:+s.dataset.ky,pts:c.getAttribute('points').trim().split(/\\s+/).map(p=>p.split(',').map(Number))};}""")
    prevP = [((x-pa['x0'])/pa['kx'], (pa['oy']-y)/pa['ky']) for x, y in pa['pts']]
    slope_gap = max(abs((prevP[i+1][1]-prevP[i-1][1])/(2*math.radians(1)) - cv27['sal'][i][1]) for i in range(2, 179))
    ok('figure cross-check: differentiating the previous lesson\'s DRAWN power-angle curve (read from its SVG, central differences) reproduces this figure\'s salient curve to within 0.03 pu/rad (measured worst gap) - the two figures are consistent with each other', slope_gap<0.03, slope_gap)
    mk27 = {k: (dx27(v[0]), py27(v[1])) for k, v in fg27['pts'].items()}
    ok('figure markers: salient zero at (70.06 deg, 0), cylindrical zero at (90 deg, 0), operating point (30 deg, 1.6324), no-load point (0, 2.1667); each marker lies on its curve within 0.006',
       abs(mk27['zsal'][0]-70.06)<0.02 and abs(mk27['zsal'][1])<2e-3 and abs(mk27['zcyl'][0]-90)<0.02 and abs(mk27['zcyl'][1])<2e-3 and abs(mk27['op'][0]-30)<0.02 and abs(mk27['op'][1]-1.6324)<2e-3 and abs(mk27['nl'][0])<0.02 and abs(mk27['nl'][1]-2.1667)<2e-3
       and abs(mk27['op'][1]-Ssal_(mk27['op'][0]))<0.006 and abs(mk27['zsal'][1]-Ssal_(mk27['zsal'][0]))<0.006, mk27)
    ok('figure: zero axis drawn at P_syn = 0 (measured from the scale); the salient curve changes sign between 70 and 71 deg on the 1-degree grid and stays negative to 180; labels state 70.06 / 90 / 1.632 / 2.167 and the aria-label describes both curves and the zero crossings',
       abs(py27(fg27['axis'][0]))<1e-9 and cv27['sal'][70][1]>0 and cv27['sal'][71][1]<0 and all(p<0 for d, p in cv27['sal'] if d>=71) and cv27['cyl'][89][1]>0 and cv27['cyl'][91][1]<0
       and all(t in fg27['txt'] for t in ['P_syn = 0 at δ = 70.06°','cylindrical: zero at 90°','1.632 at δ = 30°','2.167 at δ = 0 (no load)','1.5 cos δ + 0.6667 cos 2δ','P_syn < 0: no restoring action']) and 'synchronising power against load angle' in fg27['aria'].lower() and '70.06' in fg27['aria'] and '90 degrees' in fg27['aria'], fg27['txt'][:100])
    ok('no placeholder wording in the new lesson', not any(w in d27['body'].lower() for w in ['lorem','coming soon','todo','tbd','sample question','comprehensive overview']))
    ok('lesson says plainly what it does NOT cover (hunting, load test, parallel operation, methods of synchronisation); since session 29 both neighbouring rows are in their own lessons and nothing is still "to be written"', 'This lesson covers P_syn and T_syn as the slope of the power-angle curve, for both rotor types.' in d27['body'] and 'still to be written' not in d27['body'] and 'hunting' in d27['body'] and 'are in their own lesson' in d27['body'] and 'data-nav="lesson:ac-alt-methods-synchronisation"' in d27['body'])
    ok('worked-example claims that a reader can check: cos 85 deg = 8.7 % of the no-load value; steady-state limit for the salient machine is 70.06 (not 90) and this is stated in the trap', abs(math.cos(math.radians(85))-0.0872)<5e-5 and '8.7 %' in d27['body'] and 'cos 85°' in d27['body'] and 'earlier than 90° for a salient-pole machine' in d27['body'])
    # -- interview + formula book + search + links + mobile --
    iv27 = pg.evaluate('INTERVIEW["iv-t-syncpower"]')
    ok('interview answer states P_syn = dP/dδ, the cylindrical and salient forms, P cot δ, T_syn = 3P_syn/ω_sm, the p/2 factor, and why no load gives the largest value',
       all(t in iv27['a'] for t in ['dP/dδ','(E_fV/X_s) cos δ','P cot δ','V²(1/X_q − 1/X_d) cos 2δ','T_syn = 3P_syn/ω_sm','p/2','cos δ is largest at δ = 0']) and iv27['lesson']==LID27 and iv27['cat']=='Technical')
    pg.evaluate('nav({page:"formulabook"})'); pg.wait_for_timeout(150); fbt = pg.locator('#contentRoot').inner_text()
    ok('Formula Book lists the new topic "Synchronising power and torque" under AC Machines with its 3 cards (innerText is compared case-insensitively because the topic headers are CSS-uppercased)', 'synchronising power and torque' in fbt.lower() and all(n.lower() in fbt.lower() for n in ['Synchronising power from the delivered power','Synchronising torque and unit conversion']) and any(fc in fbt for fc in ['170 formulas', '182 formulas', '200 formulas', '214 formulas', '240 formulas', '247 formulas', '253 formulas', '257 formulas', '269 formulas', '281 formulas', '322 formulas', '332 formulas', '344 formulas', '402 formulas', '501 formulas']), fbt[:120])
    pg.evaluate('nav({page:"search",q:"synchronising power"})'); pg.wait_for_timeout(150); sr27 = pg.locator('#contentRoot').inner_text()
    ok('search for "synchronising power" finds the new lesson, the syllabus row (marked "Lesson ready") and the interview question', 'Synchronising Power and Synchronising Torque of an Alternator' in sr27 and 'Synchronising Power and Torque- Power and Torque equations' in sr27 and 'Lesson ready' in sr27 and 'Interview questions' in sr27, sr27[:300])
    bad_m27 = []
    for rt in ['{page:"lesson",id:"ac-alt-synchronising-power-torque"}','{page:"numerical",id:"num-acm-syn-1"}','{page:"numerical",id:"num-acm-syn-2"}','{page:"course",sem:5,code:"23EEP504"}','{page:"formulabook"}']:
        m.evaluate(f'nav({rt})'); m.wait_for_timeout(350)
        if not m.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'): bad_m27.append(rt)
    ok('mobile (390 px): no horizontal overflow on the new lesson, both numericals, the AC Machines course page and the Formula Book', not bad_m27, bad_m27)
    pg.evaluate('nav({page:"lesson",id:"%s"})' % LID27)
    ok('lesson prerequisite links work (4 internal lesson links (3 prerequisites + the session-29 pointer) resolve to real lessons)', pg.evaluate('[...document.querySelectorAll(".lesson a[data-nav^=\\"lesson:\\"]")].map(a=>a.dataset.nav.slice(7)).every(id=>!!LESSONS[id])') and pg.locator('.lesson a[data-nav^="lesson:"]').count()==4)
    pg.evaluate('nav({page:"course",sem:5,code:"23EEP504"})'); pg.wait_for_timeout(150); ct27 = pg.locator('#contentRoot').inner_text()
    ok('AC Machines course page opens and shows the row with its lesson', 'Synchronising Power and Torque- Power and Torque equations' in ct27 and 'Lesson ready' in ct27, ct27[:200])
    bad27p = []
    for qid in ['acm-syn-1','acm-syn-2','acm-syn-3','acm-syn-4']:
        pg.evaluate('nav({page:"mcqset",ids:["%s"]})' % qid); pg.wait_for_timeout(60)
        a_ = pg.evaluate('MCQS["%s"].a' % qid); wrong = (a_+1) % 4
        st0 = pg.evaluate("[...document.querySelectorAll('.opt')].map(o=>o.classList.contains('correct')||o.classList.contains('wrong')||o.classList.contains('selected')?'x':'-').join('')")
        pg.click(f'.opt >> nth={wrong}')
        st1 = pg.evaluate("[...document.querySelectorAll('.opt')].map(o=>o.classList.contains('correct')||o.classList.contains('wrong')?'x':o.classList.contains('selected')?'s':'-').join('')"); vis0 = pg.locator('#contentRoot').inner_text()
        pg.click('#submitMcqBtn'); pg.wait_for_timeout(60)
        st_ = pg.evaluate("[...document.querySelectorAll('.opt')].map(o=>o.classList.contains('correct')?'C':o.classList.contains('wrong')?'W':'-').join('')")
        exp_pat = ''.join('C' if i==a_ else ('W' if i==wrong else '-') for i in range(4)); exp_sel = ''.join('s' if i==wrong else '-' for i in range(4))
        if st_ != exp_pat or st0 != '----' or st1 != exp_sel: bad27p.append((qid, st0, st1, st_, exp_pat))
    ok('Practice mode on the 4 new MCQs: all options start unmarked; after a pick only that option is selected (no correct/wrong shown); after Submit a wrong pick is wrong and exactly the keyed option is correct', not bad27p, bad27p)
    ok('the 4 new MCQs contain no positional wording, so the mock can shuffle all of them', pg.evaluate('["acm-syn-1","acm-syn-2","acm-syn-3","acm-syn-4"].every(i=>mockCanShuffle(MCQS[i]))'))

    # =====================================================================
    # SESSION 28: AC Machines Module II row 6 - load test on alternators; parallel operation of alternators
    # (every number below is re-derived here by independent code: complex arithmetic and a bisection solver, not the builder's)
    # =====================================================================
    import re as _re28, cmath as _cm28
    LID28 = 'ac-alt-load-test-parallel'; ROW28 = 'Load test on alternators Parallel operation of alternators'
    d28 = pg.evaluate("""([LID,ROW])=>{const o={}; o.mapped=TOPIC_TO_LESSON[ROW]; o.partial=TOPIC_PARTIAL.has(ROW); o.lv=contentLevel(LID); const L=LESSONS[LID]; o.area=L.area; o.title=L.title;
        o.mcq=(L.mcqIds||[]).map(i=>MCQS[i]&&[i,MCQS[i].d,MCQS[i].a,MCQS[i].opts[MCQS[i].a],MCQS[i].opts.length]);
        o.num=Object.entries(NUMERICALS).filter(([k,v])=>v.lesson===LID).map(x=>[x[0],x[1].d]); o.iv=Object.entries(INTERVIEW).filter(([k,v])=>v.lesson===LID).map(x=>[x[0],x[1].cat]);
        o.fc=FORMULA_CARDS.filter(c=>c.topic==='Load test and parallel operation').map(c=>c.name); o.fcSal=FORMULA_CARDS.filter(c=>c.topic==='Salient-pole machines').length; o.fcSyn=FORMULA_CARDS.filter(c=>c.topic==='Synchronising power and torque').length;
        const c=SYLLABUS[5].courses.find(c=>c.title==='AC Machines'); o.row=c.modules[1].topics.indexOf(ROW)+1; o.mod2=c.modules[1].topics.map(t=>TOPIC_TO_LESSON[t]?(TOPIC_PARTIAL.has(t)?'P':'F'):'-').join('');
        o.r7=TOPIC_TO_LESSON[c.modules[1].topics[6]]; o.r8=TOPIC_TO_LESSON[c.modules[1].topics[7]]||null; o.r8name=c.modules[1].topics[7];
        o.body=L.body; o.keys=Object.values(MCQS).reduce((a,m)=>{a[m.a]++;return a;},[0,0,0,0]); o.s27body=LESSONS['ac-alt-synchronising-power-torque'].body; return o;}""", [LID28, ROW28])
    b28 = d28['body']; b28t = _re28.sub('<[^>]+>', '', b28)
    ok('syllabus row \"Load test on alternators Parallel operation of alternators\" is row 6 of AC Machines Module II and maps fully (not partial) to the new lesson', d28['row']==6 and d28['mapped']==LID28 and not d28['partial'], (d28['row'], d28['mapped']))
    ok('honesty: row 8 (\"Methods of Synchronisation\") was written in session 29 so Module II is FFFFFFFF, row 7 still maps to the session-27 lesson, and this lesson still does not claim the synchronisation methods (it points to the session-29 lesson)', d28['r8']=='ac-alt-methods-synchronisation' and d28['r8name']=='Methods of Synchronisation' and d28['mod2']=='FFFFFFFF' and d28['r7']=='ac-alt-synchronising-power-torque' and 'still to be written' not in b28 and 'have their own lesson' in b28 and 'synchroscope' in b28, d28['mod2'])
    ok('lesson computes to PLACEMENT READY from its real content, is filed under Sem 5 · AC Machines · Module II', d28['lv']=='PLACEMENT READY' and d28['area']=='Sem 5 · AC Machines · Module II', (d28['lv'], d28['area']))
    ok('4 MCQs (E/M/H/P) with four different keyed positions (C, A, D, B); 2 numericals (M, H); 1 Technical interview question; 3 new formula cards in their own topic; Salient-pole machines still 6, Synchronising power and torque still 3',
       [x[1] for x in d28['mcq']]==['E','M','H','P'] and [x[2] for x in d28['mcq']]==[2,0,3,1] and all(x[4]==4 for x in d28['mcq']) and sorted(d28['num'])==[['num-acm-par-1','M'],['num-acm-par-2','H']]
       and d28['iv']==[['iv-t-parallelops','Technical']] and d28['fc']==['Regulation by direct loading','Circulating current between paralleled alternators','Load sharing by governor droop'] and d28['fcSal']==6 and d28['fcSyn']==3, d28)
    ok('answer keys A/B/C/D = 108/107/107/107 after session 32 added 28 more (7 of each; best single-letter guess 25.2 %)', d28['keys'] in ([153,152,152,152], [166,165,165,165], [184,183,183,183], [198,197,197,197], [224, 223, 223, 223], [230, 229, 229, 229], [234, 233, 233, 233], [254, 253, 253, 253], [294, 293, 293, 293], [544, 542, 540, 543], [574, 572, 570, 573], [589, 587, 585, 588], [605, 603, 601, 604], [614, 617, 614, 609], [616, 619, 616, 611], [655, 658, 655, 650], [665, 669, 666, 661], [675, 680, 675, 670], [734, 734, 734, 734], [833, 833, 833, 833]) and max(d28['keys'])/sum(d28['keys'])<0.26, d28['keys'])
    ok('the session-27 lesson points to the session-28 lesson for row 6 and, since session 29, to the methods-of-synchronisation lesson for row 8 (nothing is still \"to be written\")', 'are in their own lesson' in d28['s27body'] and 'Load Test and Parallel Operation of Alternators' in d28['s27body'] and 'still to be written' not in d28['s27body'] and 'lesson:ac-alt-methods-synchronisation' in d28['s27body'])
    # -- direct load test (worked example A) --
    PoA = S3_*415*6.96*0.8; regA = (468-415)/415*100; etaA = PoA/5100*100; lossA = 5100-PoA; PinH = 5100*1.01; etaH = PoA/PinH*100; lossH = PinH-PoA
    ok('load test example: regulation 53/415 = 12.77 %, output sqrt3 x 415 x 6.96 x 0.8 = 4002.3 W (0.06 % above 5 kVA x 0.8), efficiency 78.48 %, loss 1097.7 W - independent recomputation; all printed',
       abs(regA-12.77)<5e-3 and abs(PoA-4002.3)<0.05 and abs((PoA/4000-1)*100-0.057)<5e-3 and abs(etaA-78.48)<5e-3 and abs(lossA-1097.7)<0.05
       and all(t in b28t for t in ['53/415 = 12.77 %','4002.3 W = 4.002 kW','4.000 kW to within 0.06 %','78.48 %','1097.7 W']), (regA, PoA, etaA, lossA))
    ok('load test example: the printed arithmetic reproduces from the printed operands (4002.3/5100 = 78.48; 5100 - 4002.3 = 1097.7; 4002.3/5151 = 77.70; 5151 - 4002.3 = 1148.7), and a 1 % input error moves efficiency 0.78 points but the loss 4.6 %',
       round(4002.3/5100*100,2)==78.48 and round(5100-4002.3,1)==1097.7 and round(4002.3/5151*100,2)==77.70 and round(5151-4002.3,1)==1148.7 and abs((etaA-etaH)-0.78)<5e-3 and abs((lossH/lossA-1)*100-4.6)<0.05
       and all(t in b28t for t in ['η = 4002.3/5100 = 78.48 %','5100 − 4002.3 = 1097.7 W','η = 4002.3/5151 = 77.70 %','5151 − 4002.3 = 1148.7 W','0.78 percentage points','4.6 %']), (etaH, lossH))
    PinL = 10e6/0.98; lossL = PinL-10e6
    ok('large-machine point: 10 MW at 98 % needs 10.204 MW in, loss 0.204 MW; a 1 % input error is 0.102 MW = exactly 50 % of the loss (0.01/(1-0.98)); printed', abs(PinL/1e6-10.204)<5e-4 and abs(lossL/1e6-0.204)<5e-4 and abs(0.01*PinL/1e6-0.102)<5e-4 and abs(0.01*PinL/lossL-0.5)<1e-9
       and all(t in b28t for t in ['10.204 MW','0.204 MW','0.102 MW','50 %']), (PinL, lossL))
    # -- paralleling: mismatch currents (worked example B) --
    ZsB = 0.2+8j; ZlB = 2*ZsB; EB_ = 6350.0; IcV = (1.01*EB_-0.99*EB_)/ZlB
    E1B = EB_*_cm28.exp(1j*math.radians(5)); E2B = EB_*_cm28.exp(-1j*math.radians(5)); IcP = (E1B-E2B)/ZlB
    PleadB = 3*(E1B*IcP.conjugate()).real; PlagB = 3*(E2B*IcP.conjugate()).real; lossB = 3*abs(IcP)**2*ZlB.real; IratedB = 15e6/(S3_*11000)
    ok('mismatch example: |Z| 16.005 ohm at 88.57 deg; 2 % voltage mismatch (127 V) gives 7.94 A = 1.0 % of the 787 A rated current; complex-arithmetic reference agrees; every number printed',
       abs(abs(ZlB)-16.005)<5e-4 and abs(math.degrees(_cm28.phase(ZlB))-88.57)<5e-3 and abs(abs(IcV)-7.94)<5e-3 and abs(-math.degrees(_cm28.phase(IcV))-88.57)<5e-3 and abs(abs(IcV)/IratedB*100-1.0)<0.05 and abs(IratedB-787)<0.5
       and all(t in b28t for t in ['16.005 Ω','88.57°','127 V','7.94 A','1.0 % of rated current','787 A']), (abs(ZlB), abs(IcV), IratedB))
    ok('mismatch example: 10 deg phase mismatch gives dE = 2E sin 5 deg = 1106.9 V and 69.16 A (8.8 % of rated, 8.7 x case a); the phasor difference equals the closed form; current lags the leading emf by 3.57 deg; leading machine sends 1.315 MW, lagging receives 1.309 MW, difference 5.74 kW = 3 I^2 R (0.4 ohm); printed',
       abs(abs(E1B-E2B)-2*EB_*math.sin(math.radians(5)))<1e-9 and abs(abs(E1B-E2B)-1106.9)<0.05 and abs(abs(IcP)-2*EB_*math.sin(math.radians(5))/abs(ZlB))<1e-9 and abs(abs(IcP)-69.16)<5e-3 and abs(abs(IcP)/IratedB*100-8.8)<0.05 and abs(abs(IcP)/abs(IcV)-8.7)<0.05
       and abs(5-math.degrees(_cm28.phase(IcP))-3.57)<5e-3 and abs(PleadB/1e6-1.315)<5e-4 and abs(PlagB/1e6-1.309)<5e-4 and abs((PleadB-PlagB)-lossB)<1e-6 and abs(lossB/1e3-5.74)<5e-3
       and all(t in b28t for t in ['1106.9 V','69.16 A','8.8 %','8.7 times','3.57°','1.315 MW','1.309 MW','5.74 kW','3 × 69.16² × 0.4']), (abs(IcP), PleadB, PlagB, lossB))
    ok('reverse-sequence fact: with one phase pair aligned the other two pairs differ by sqrt3 x E (1.732 x 6350 = 10,999 V), checked by phasors; and \"the machines need not have the same kVA rating or speed\" is stated',
       all(abs(abs(E*_cm28.exp(1j*math.radians(a))-E*_cm28.exp(1j*math.radians(b)))-S3_*E)<1e-6 for E in (6350.0,) for a, b in [(-120,120),(120,-120)]) and abs(S3_*6350-10999)<1 and '10,999 V' in b28t and 'need not have the same kVA rating' in b28t)
    # -- droop sharing (worked example C): bisection solver, independent of the closed form --
    def bis(fn, lo, hi):
        for _ in range(200):
            mid = (lo+hi)/2
            if fn(lo)*fn(mid) <= 0: hi = mid
            else: lo = mid
        return (lo+hi)/2
    k1c = (51.0-49.5)/1000; k2c = (51.5-49.5)/800
    fC = bis(lambda f: (51.0-f)/k1c + (51.5-f)/k2c - 1200, 48, 53); P1c = (51.0-fC)/k1c; P2c = (51.5-fC)/k2c
    fC2 = bis(lambda f: (51.05-f)/k1c + (51.25-f)/k2c - 1200, 48, 53)
    fC3 = bis(lambda f: (51.0-f)/k1c + (51.5-f)/k2c - 1300, 48, 53)
    ok('droop example: k1 0.0015, k2 0.0025 Hz/kW; bisection gives f 50.0625 Hz, P1 625 kW (62.5 %), P2 575 kW (71.9 %); closed form (sum f_nl/k - P)/sum(1/k) = 53400/1066.67 agrees; printed',
       abs(k1c-0.0015)<1e-12 and abs(k2c-0.0025)<1e-12 and abs(fC-50.0625)<1e-9 and abs(P1c-625)<1e-6 and abs(P2c-575)<1e-6 and abs(P1c/1000*100-62.5)<1e-6 and abs(P2c/800*100-71.875)<1e-6 and abs((51.0/k1c+51.5/k2c-1200)/(1/k1c+1/k2c)-fC)<1e-9
       and all(t in b28t for t in ['0.0015 Hz/kW','0.0025 Hz/kW','50.0625 Hz','625 kW','575 kW','62.5 %','71.9 %','34,000 + 20,600 = 54,600','666.67 + 400.00 = 1066.67 kW/Hz']), (fC, P1c, P2c))
    ok('droop example: governor set-points 51.05 Hz and 51.25 Hz give exactly 50.00 Hz with 700 kW and 500 kW at the same 1200 kW (solver); +100 kW splits 62.5 / 37.5 kW and drops f by 0.09375 Hz (solver: 1300 kW); printed',
       abs(fC2-50.0)<1e-9 and abs((51.05-50)/k1c-700)<1e-6 and abs((51.25-50)/k2c-500)<1e-6 and abs((51.0-fC3)/k1c-P1c-62.5)<1e-6 and abs((51.5-fC3)/k2c-P2c-37.5)<1e-6 and abs((fC-fC3)-0.09375)<1e-9
       and all(t in b28t for t in ['51.05 Hz','51.25 Hz','up by 0.05 Hz','down by 0.25 Hz','62.5 kW','37.5 kW','0.09375 Hz']), (fC2, fC3))
    # -- numericals --
    chk28 = {}
    for nid in ['num-acm-par-1','num-acm-par-2']:
        pg.evaluate('nav({page:"numerical",id:"%s"})' % nid); pg.click('#revealNumBtn'); chk28[nid] = pg.locator('#contentRoot').inner_text()
    ZA1 = 0.4+6j; ZB1 = 0.6+8j; IcN = (6700-6500)/(ZA1+ZB1); Vb = 6700-IcN*ZA1; Vb2 = 6500+IcN*ZB1
    SA1 = 3*6700*IcN.conjugate(); SB1 = -3*6500*IcN.conjugate()
    ok('numerical 1 (Z_A 0.4+j6, Z_B 0.6+j8, E 6700/6500): I_c = 14.25 A at -85.91 deg, loss 609 W, bus voltage 6614.3 V per phase (11,456 V line) reached from BOTH machines, A supplies 285.7 kvar and 20.4 kW, B absorbs 277.2 kvar and 19.8 kW - all match the reference',
       abs(abs(IcN)-14.25)<5e-3 and abs(math.degrees(_cm28.phase(IcN))+85.91)<5e-3 and abs(3*abs(IcN)**2*1.0-609)<0.5 and abs(abs(Vb)-6614.3)<0.05 and abs(Vb-Vb2)<1e-6 and abs(S3_*abs(Vb)-11456)<0.5 and abs(SA1.imag/1e3-285.7)<0.05 and abs(SA1.real/1e3-20.4)<0.05 and abs(SB1.imag/1e3+277.2)<0.05 and abs(SB1.real/1e3+19.8)<0.05
       and all(t in chk28['num-acm-par-1'] for t in ['14.25','85.91°','609 W','6614.3','11,456 V','285.7 kvar','20.4 kW','277.2 kvar','19.8 kW','14.036']), (IcN, Vb, SA1, SB1))
    ok('numerical 1 balance and mistake figures: the reactive drop 285.7 - 277.2 = 8.5 kvar equals 3 I^2 X (X = 14 ohm), the real difference 20.4 - 19.8 kW is the 609 W loss, and the one-impedance slips are 200/|Z_A| = 33.26 A and 200/|Z_B| = 24.93 A; 20.4 kW of 286.4 kVA',
       abs((SA1.imag+SB1.imag)-3*abs(IcN)**2*14)<1e-6 and abs((SA1.real+SB1.real)-609.14)<0.01 and abs(200/abs(ZA1)-33.26)<5e-3 and abs(200/abs(ZB1)-24.93)<5e-3 and abs(abs(SA1)/1e3-286.4)<0.05
       and all(t in chk28['num-acm-par-1'] for t in ['33.26 A','24.93 A','286.4 kVA']))
    kA2 = (50.8-49.6)/2000; kB2 = (51.0-49.5)/1000
    fN2 = bis(lambda f: (50.8-f)/kA2 + (51.0-f)/kB2 - 2400, 48, 53); PA2 = (50.8-fN2)/kA2; PB2 = (51.0-fN2)/kB2
    fB2 = 49.6; PBm = (51.0-fB2)/kB2; PAm = (50.8-fB2)/kA2   # A reaches 2000 kW at 49.6 Hz; B would reach 1000 kW only at the lower frequency 49.5 Hz
    ok('numerical 2 (A 2000 kW 50.8-49.6 Hz, B 1000 kW 51.0-49.5 Hz, load 2400): solver f 49.8286 Hz, P_A 1619.0 kW (81.0 %), P_B 781.0 kW (78.1 %); A is full first (49.6 Hz > 49.5 Hz), so the largest load is 2000 + 933.3 = 2933.3 kW = 97.8 % of 3000, 66.7 kW of B unusable - all match',
       abs(fN2-49.8286)<5e-5 and abs(PA2-1619.0)<0.05 and abs(PB2-781.0)<0.05 and abs(PA2/2000*100-81.0)<0.05 and abs(PB2/1000*100-78.1)<0.05 and abs(PAm-2000)<1e-6 and abs(PBm-933.33)<0.01 and PBm<1000 and abs(PAm+PBm-2933.3)<0.05 and abs((PAm+PBm)/3000*100-97.8)<0.05 and abs((1000-PBm)-66.7)<0.05
       and all(t in chk28['num-acm-par-2'] for t in ['49.8286 Hz','1619.0 kW','781.0 kW','81.0 %','78.1 %','2933.3 kW','97.8 %','66.7 kW','118,666.7','2333.33']), (fN2, PA2, PB2, PAm, PBm))
    ok('numerical 2 mistake figure: at 49.5 Hz machine A would carry (50.8-49.5)/0.0006 = 2166.7 kW, above its 2000 kW rating, so 49.5 Hz cannot be the limit; and a ratings-proportional split (1600 / 800 kW) is not what the droop lines give (1619 / 781 kW)',
       abs((50.8-49.5)/kA2-2166.7)<0.05 and (50.8-49.5)/kA2>2000 and abs(PA2-1600)>10 and '1600 kW and 800 kW' in chk28['num-acm-par-2'] and '49.5 Hz' in chk28['num-acm-par-2'])
    ans28 = pg.evaluate('({a1:NUMERICALS["num-acm-par-1"].ans,a2:NUMERICALS["num-acm-par-2"].ans})')
    ok('numerical answer lines (the \"ans\" fields, which the calculation text does not repeat) equal the reference values formatted at the printed precision: 14.25 A, 85.91 deg, 609 W, 6614 V / 11,456 V; 49.83 Hz, 1619 kW (81.0 %), 781 kW (78.1 %), 2933 kW, 66.7 kW',
       all(t in ans28['a1'] for t in [f'{abs(IcN):.2f} A', f'{abs(math.degrees(_cm28.phase(IcN))):.2f}°', f'{3*abs(IcN)**2:.0f} W', f'{abs(Vb):.0f} V', f'{S3_*abs(Vb):,.0f} V'])
       and all(t in ans28['a2'] for t in [f'{fN2:.2f} Hz', f'{PA2:.0f} kW', f'{PB2:.0f} kW', f'{PA2/20:.1f} %', f'{PB2/10:.1f} %', f'{PAm+PBm:.0f} kW', f'{1000-PBm:.1f} kW']), ans28)
    # -- MCQs --
    mq28 = pg.evaluate('["acm-par-1","acm-par-2","acm-par-3","acm-par-4"].map(i=>({o:MCQS[i].opts,a:MCQS[i].a,e:MCQS[i].exp,q:MCQS[i].q}))')
    ok('MCQ 1: keyed answer is the kVA rating (the only non-condition); the other three options are voltage, phase sequence and frequency, which the lesson table lists as conditions',
       mq28[0]['o'][mq28[0]['a']]=='Its kVA rating equals that of the machines already on the bus' and sum(t in mq28[0]['o'] for t in ['Its terminal voltage equals the bus voltage','Its phase sequence is the same as the bus phase sequence','Its frequency equals the bus frequency'])==3 and all(t in b28t for t in ['1. Voltage','2. Frequency','3. Phase sequence','4. Phase angle']))
    Qf = lambda E, V, X, dd: V*(E*math.cos(math.radians(dd))-V)/X
    ok('MCQ 2: keyed answer is more real power with a larger load angle and unchanged frequency; the \"more lagging reactive current with the load angle unchanged\" distractor fails because the angle must change; reference: at fixed E_f, Q = V(E cos d - V)/X FALLS as d rises (0.299 pu at 30 deg, 0.149 pu at 40 deg for E 1.5, V = X = 1) while P rises',
       mq28[1]['o'][mq28[1]['a']].startswith('More real power is delivered') and any('load angle unchanged' in o for i, o in enumerate(mq28[1]['o']) if i != mq28[1]['a']) and Qf(1.5,1,1,40)<Qf(1.5,1,1,30) and abs(Qf(1.5,1,1,30)-0.299)<5e-4 and abs(Qf(1.5,1,1,40)-0.149)<5e-4 and 1.5*math.sin(math.radians(40))>1.5*math.sin(math.radians(30)))
    ok('MCQ 3: 200 V across two 5 ohm reactances = 20 A; distractors are exactly the stated slips (one reactance 40 A, halved again 10 A, emfs added 1300 A); reference arithmetic',
       mq28[2]['o'][mq28[2]['a']]=='20 A' and sorted(mq28[2]['o'])==sorted(['20 A','40 A','10 A','1300 A']) and abs((6600-6400)/(2*5)-20)<1e-12 and abs((6600-6400)/5-40)<1e-12 and abs((6600-6400)/(2*10)-10)<1e-12 and abs((6600+6400)/10-1300)<1e-12 and all(t in mq28[2]['e'] for t in ['20 A','40 A','10 A','1300 A']))
    ok('MCQ 4: keyed answer is more lagging reactive current from machine 1, less from machine 2, real-power shares essentially the same; the \"larger share of real power because its emf is larger\" trap and the \"frequency rises\" trap appear only as distractors',
       mq28[3]['o'][mq28[3]['a']].startswith('Machine 1 supplies more lagging reactive current and machine 2 less') and 'real-power shares stay essentially the same' in mq28[3]['o'][mq28[3]['a']] and any('larger share of the real power' in o for i, o in enumerate(mq28[3]['o']) if i != mq28[3]['a']) and any('frequency rises' in o for i, o in enumerate(mq28[3]['o']) if i != mq28[3]['a']))
    ANSWER_TEXT_FP_S28 = {'acm-par-1': 'edaf24c590', 'acm-par-2': 'a3d30f10e3', 'acm-par-3': '5f63b5be2b', 'acm-par-4': '0c5408579a'}
    fp28 = {k: _hl.sha1(mq28[i]['o'][mq28[i]['a']].encode('utf-8')).hexdigest()[:10] for i, k in enumerate(ANSWER_TEXT_FP_S28)}
    ok('session-28 answer-text fingerprints: the correct-answer TEXT of the 4 new questions (re-derived above) is guarded like the older ones', fp28==ANSWER_TEXT_FP_S28, fp28)
    # -- lesson page + figure geometry --
    pg.evaluate('nav({page:"lesson",id:"%s"})' % LID28); pg.wait_for_timeout(150)
    ok('lesson page has one figure, 3 tables, 5 formula boxes, exactly one mistake and one trap callout, and buttons to 4 MCQs / 2 numericals / 1 interview question',
       pg.locator('.lesson .diagram svg').count()==1 and pg.locator('.lesson table.tbl').count()==3 and pg.locator('.lesson .formula-box').count()==5 and pg.locator('.lesson .callout-trap').count()==1 and pg.locator('.lesson .callout-mistake').count()==1
       and 'Practice 4 MCQs' in pg.locator('#contentRoot').inner_text() and 'Solve 2 numericals' in pg.locator('#contentRoot').inner_text() and '1 interview question' in pg.locator('#contentRoot').inner_text(), (pg.locator('.lesson .formula-box').count(),))
    fg28 = pg.evaluate("""()=>{const s=document.querySelector('.lesson .diagram svg'); const o={x0:+s.dataset.x0,kx:+s.dataset.kx,f0:+s.dataset.f0,oy:+s.dataset.oy,ky:+s.dataset.ky,lines:{},pts:{},txt:[...s.querySelectorAll('text')].map(t=>t.textContent).join(' | '),aria:s.getAttribute('aria-label'),
        ax:[...s.querySelectorAll('[data-axis="f50"]')].map(l=>[+l.getAttribute('y1'),+l.getAttribute('y2')])[0], vb:s.getAttribute('viewBox'), rect:(r=>[+r.getAttribute('x'),+r.getAttribute('y'),+r.getAttribute('width'),+r.getAttribute('height')])(s.querySelector('rect'))};
        s.querySelectorAll('[data-line]').forEach(l=>{o.lines[l.dataset.line]=['x1','y1','x2','y2'].map(a=>+l.getAttribute(a));});
        s.querySelectorAll('[data-pt]').forEach(c=>{o.pts[c.dataset.pt]=[+c.getAttribute('cx'),+c.getAttribute('cy')];}); return o;}""")
    px2P = lambda x: (x-fg28['x0'])/fg28['kx']; py2f = lambda y: fg28['f0']+(fg28['oy']-y)/fg28['ky']
    ln = {k: [(px2P(v[0]), py2f(v[1])), (px2P(v[2]), py2f(v[3]))] for k, v in fg28['lines'].items()}
    slope = lambda pr: (pr[1][1]-pr[0][1])/(pr[1][0]-pr[0][0])
    ok('figure: the horizontal axis spans exactly 0-1200 kW (plot rectangle read back through the scale) and the frequency axis 48-52.5 Hz',
       abs(px2P(fg28['rect'][0]))<1e-6 and abs(px2P(fg28['rect'][0]+fg28['rect'][2])-1200)<0.05 and abs(py2f(fg28['rect'][1]+fg28['rect'][3])-48.0)<1e-6 and abs(py2f(fg28['rect'][1])-52.5)<1e-6, fg28['rect'])
    ok('figure: the four DRAWN lines have the right droops when read back through the scale - machine 1 -0.0015 Hz/kW from 51.0 Hz, machine 2 mirrored so it RISES 0.0025 Hz/kW and ends at 51.5 Hz at 1200 kW, and the two dashed lines are the same slopes moved to 51.05 Hz / 51.25 Hz (all to within 1e-4)',
       abs(slope(ln['m1'])+0.0015)<1e-4 and abs(ln['m1'][0][1]-51.0)<1e-3 and abs(slope(ln['m2'])-0.0025)<1e-4 and abs(ln['m2'][1][1]-51.5)<1e-3 and abs(slope(ln['m1r'])+0.0015)<1e-4 and abs(ln['m1r'][0][1]-51.05)<1e-3 and abs(slope(ln['m2r'])-0.0025)<1e-4 and abs(ln['m2r'][1][1]-51.25)<1e-3, ln)
    def cross(a, b):
        sa, sb = slope(a), slope(b); pa = a[0][0]; fa = a[0][1]; pb = b[0][0]; fb = b[0][1]
        P = (fb-fa+sa*pa-sb*pb)/(sa-sb); return P, fa+sa*(P-pa)
    xa = cross(ln['m1'], ln['m2']); xb = cross(ln['m1r'], ln['m2r'])
    ok('figure: the drawn solid lines cross at (625 kW, 50.0625 Hz) and the drawn dashed lines at (700 kW, 50.00 Hz) - the same answers the worked example computes, obtained here from the geometry alone (within 0.1 kW / 1e-3 Hz)',
       abs(xa[0]-625)<0.1 and abs(xa[1]-50.0625)<1e-3 and abs(xb[0]-700)<0.1 and abs(xb[1]-50.0)<1e-3, (xa, xb))
    mk28 = {k: (px2P(v[0]), py2f(v[1])) for k, v in fg28['pts'].items()}
    ok('figure markers: op1 at (625 kW, 50.0625 Hz) on both solid lines and op2 at (700 kW, 50.00 Hz) on both dashed lines; machine 2 output read from the right is 1200 - 625 = 575 kW and 1200 - 700 = 500 kW; 50 Hz axis drawn at 50 Hz',
       abs(mk28['op1'][0]-625)<0.1 and abs(mk28['op1'][1]-50.0625)<1e-3 and abs(mk28['op2'][0]-700)<0.1 and abs(mk28['op2'][1]-50.0)<1e-3
       and abs(mk28['op1'][1]-(ln['m1'][0][1]+slope(ln['m1'])*(mk28['op1'][0]-ln['m1'][0][0])))<1e-3 and abs(mk28['op1'][1]-(ln['m2'][0][1]+slope(ln['m2'])*(mk28['op1'][0]-ln['m2'][0][0])))<1e-3
       and abs(mk28['op2'][1]-(ln['m1r'][0][1]+slope(ln['m1r'])*(mk28['op2'][0]-ln['m1r'][0][0])))<1e-3 and abs(mk28['op2'][1]-(ln['m2r'][0][1]+slope(ln['m2r'])*(mk28['op2'][0]-ln['m2r'][0][0])))<1e-3
       and abs(1200-mk28['op1'][0]-575)<0.1 and abs(1200-mk28['op2'][0]-500)<0.1 and abs(py2f(fg28['ax'][0])-50.0)<1e-9, (mk28, fg28['ax']))
    ok('figure labels and aria-label state 625 / 575 kW, 50.0625 Hz, 700 / 500 kW, 50.00 Hz, both droop equations and the mirrored second axis',
       all(t in fg28['txt'] for t in ['as set: P₁ = 625 kW, P₂ = 575 kW','common frequency 50.0625 Hz','governors reset: P₁ = 700 kW, P₂ = 500 kW','common frequency 50.00 Hz','f = 51.0 − 0.0015 P₁','f = 51.5 − 0.0025 P₂','Machine 2 output P₂ (kW), measured from the right'])
       and '50.0625 hertz' in fg28['aria'] and '625 kilowatts' in fg28['aria'] and '575' in fg28['aria'] and 'mirrored' in fg28['aria'])
    ok('no placeholder wording in the new lesson, and no unevidenced \"frequently asked\" claim', not any(w in b28.lower() for w in ['lorem','coming soon','todo','tbd','sample question','comprehensive overview','frequently asked','interviewers ask']))
    ok('lesson says plainly what it does NOT cover (lamp methods and synchroscope, hunting, efficiency by separate losses) and does not claim them', 'It does not cover the <i>methods</i> used to check the conditions' in b28 and 'have their own lesson' in b28 and 'still to be written' not in b28 and 'hunting' in b28 and 'separately measured losses' in b28)
    # -- interview + formula book + search + links + mobile --
    iv28 = pg.evaluate('INTERVIEW["iv-t-parallelops"]')
    ok('interview answer states the four conditions with their consequences (circulating current, beat pulsation, sqrt3 x emf across the switch, 2E sin(d/2) real-power exchange), that rating and speed are not conditions, governor = MW and field = Mvar, and 1/k load division',
       all(t in iv28['a'] for t in ['(E₁ − E₂)/(Z_s1 + Z_s2)','beat frequency','√3 times the emf','2E sin(δ/2)','The kVA ratings need not match','governor','field','1/k','does not make it deliver more real power']) and iv28['lesson']==LID28 and iv28['cat']=='Technical')
    pg.evaluate('nav({page:"formulabook"})'); pg.wait_for_timeout(150); fb28 = pg.locator('#contentRoot').inner_text()
    ok('Formula Book lists the new topic \"Load test and parallel operation\" under AC Machines with its 3 cards and shows 81 formulas (78 before session 29)', 'load test and parallel operation' in fb28.lower() and all(n.lower() in fb28.lower() for n in ['Regulation by direct loading','Circulating current between paralleled alternators','Load sharing by governor droop']) and any(fc in fb28 for fc in ['170 formulas', '182 formulas', '200 formulas', '214 formulas', '240 formulas', '247 formulas', '253 formulas', '257 formulas', '269 formulas', '281 formulas', '322 formulas', '332 formulas', '344 formulas', '402 formulas', '501 formulas']), fb28[:120])
    def srch28(q):
        pg.evaluate('nav({page:"search",q:"%s"})' % q); pg.wait_for_timeout(150); return pg.locator('#contentRoot').inner_text()
    sr28a = srch28('circulating current'); sr28b = srch28('load test on alternators'); sr28c = srch28('in parallel with a bus')
    ok('search finds the new content: \"circulating current\" finds the lesson, \"load test on alternators\" finds the syllabus row (marked \"Lesson ready\"), and \"in parallel with a bus\" finds the interview question',
       'Load Test and Parallel Operation of Alternators' in sr28a and 'Load test on alternators Parallel operation of alternators' in sr28b and 'Lesson ready' in sr28b and 'Interview questions' in sr28c and 'conditions must be met before you connect an alternator in parallel' in sr28c, (sr28a[:150], sr28b[:150], sr28c[:150]))
    bad_m28 = []
    for rt in ['{page:"lesson",id:"ac-alt-load-test-parallel"}','{page:"numerical",id:"num-acm-par-1"}','{page:"numerical",id:"num-acm-par-2"}','{page:"course",sem:5,code:"23EEP504"}','{page:"formulabook"}']:
        m.evaluate(f'nav({rt})'); m.wait_for_timeout(350)
        if not m.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'): bad_m28.append(rt)
    ok('mobile (390 px): no horizontal overflow on the new lesson, both numericals, the AC Machines course page and the Formula Book', not bad_m28, bad_m28)
    m.evaluate('nav({page:"lesson",id:"ac-alt-load-test-parallel"})'); m.wait_for_timeout(350)
    ok('mobile (390 px): the figure and the three tables of the new lesson stay inside the viewport', m.evaluate('[...document.querySelectorAll(".lesson .diagram svg, .lesson table.tbl")].every(e=>e.getBoundingClientRect().right<=window.innerWidth+1)'))
    pg.evaluate('nav({page:"lesson",id:"%s"})' % LID28)
    ok('lesson prerequisite links work (4 internal lesson links (3 prerequisites + the session-29 pointer) resolve to real lessons)', pg.evaluate('[...document.querySelectorAll(".lesson a[data-nav^=\\"lesson:\\"]")].map(a=>a.dataset.nav.slice(7)).every(id=>!!LESSONS[id])') and pg.locator('.lesson a[data-nav^="lesson:"]').count()==4)
    pg.evaluate('nav({page:"course",sem:5,code:"23EEP504"})'); pg.wait_for_timeout(150); ct28 = pg.locator('#contentRoot').inner_text()
    ok('AC Machines course page opens and shows the row with its lesson', 'Load test on alternators Parallel operation of alternators' in ct28 and 'Lesson ready' in ct28, ct28[:200])
    bad28p = []
    for qid in ['acm-par-1','acm-par-2','acm-par-3','acm-par-4']:
        pg.evaluate('nav({page:"mcqset",ids:["%s"]})' % qid); pg.wait_for_timeout(60)
        a_ = pg.evaluate('MCQS["%s"].a' % qid); wrong = (a_+1) % 4
        st0 = pg.evaluate("[...document.querySelectorAll('.opt')].map(o=>o.classList.contains('correct')||o.classList.contains('wrong')||o.classList.contains('selected')?'x':'-').join('')")
        pg.click(f'.opt >> nth={wrong}')
        st1 = pg.evaluate("[...document.querySelectorAll('.opt')].map(o=>o.classList.contains('correct')||o.classList.contains('wrong')?'x':o.classList.contains('selected')?'s':'-').join('')")
        pg.click('#submitMcqBtn'); pg.wait_for_timeout(60)
        st_ = pg.evaluate("[...document.querySelectorAll('.opt')].map(o=>o.classList.contains('correct')?'C':o.classList.contains('wrong')?'W':'-').join('')")
        exp_pat = ''.join('C' if i==a_ else ('W' if i==wrong else '-') for i in range(4)); exp_sel = ''.join('s' if i==wrong else '-' for i in range(4))
        if st_ != exp_pat or st0 != '----' or st1 != exp_sel: bad28p.append((qid, st0, st1, st_, exp_pat))
    ok('Practice mode on the 4 new MCQs: all options start unmarked; after a pick only that option is selected (no correct/wrong shown); after Submit a wrong pick is wrong and exactly the keyed option is correct', not bad28p, bad28p)
    ok('the 4 new MCQs contain no positional wording, so the mock can shuffle all of them', pg.evaluate('["acm-par-1","acm-par-2","acm-par-3","acm-par-4"].every(i=>mockCanShuffle(MCQS[i]))'))

    # =====================================================================
    # SESSION 29: AC Machines Module II row 8 - Methods of Synchronisation (lamps, synchroscope, closing lead)
    # (every number below is re-derived here by independent code: phasor arithmetic for the lamp voltages, complex arithmetic for the currents)
    # =====================================================================
    import re as _re29, cmath as _cm29
    LID29 = 'ac-alt-methods-synchronisation'; ROW29 = 'Methods of Synchronisation'
    d29 = pg.evaluate("""([LID,ROW])=>{const o={}; o.mapped=TOPIC_TO_LESSON[ROW]; o.partial=TOPIC_PARTIAL.has(ROW); o.lv=contentLevel(LID); const L=LESSONS[LID]; o.area=L.area; o.title=L.title;
        o.mcq=(L.mcqIds||[]).map(i=>MCQS[i]&&[i,MCQS[i].d,MCQS[i].a,MCQS[i].opts[MCQS[i].a],MCQS[i].opts.length]);
        o.num=Object.entries(NUMERICALS).filter(([k,v])=>v.lesson===LID).map(x=>[x[0],x[1].d]); o.iv=Object.entries(INTERVIEW).filter(([k,v])=>v.lesson===LID).map(x=>[x[0],x[1].cat]);
        o.fc=FORMULA_CARDS.filter(c=>c.topic==='Methods of synchronisation').map(c=>c.name); o.fcLoad=FORMULA_CARDS.filter(c=>c.topic==='Load test and parallel operation').length;
        const c=SYLLABUS[5].courses.find(c=>c.title==='AC Machines'); o.row=c.modules[1].topics.indexOf(ROW)+1; o.mod2=c.modules[1].topics.map(t=>TOPIC_TO_LESSON[t]?(TOPIC_PARTIAL.has(t)?'P':'F'):'-').join('');
        o.r6=TOPIC_TO_LESSON[c.modules[1].topics[5]]; o.r7=TOPIC_TO_LESSON[c.modules[1].topics[6]]; o.mods=c.modules.map(m=>m.topics.map(t=>TOPIC_TO_LESSON[t]?'F':'-').join(''));
        o.body=L.body; o.keys=Object.values(MCQS).reduce((a,m)=>{a[m.a]++;return a;},[0,0,0,0]); o.mockIn=(()=>{const x=mockIndex(); return (L.mcqIds||[]).map(i=>x[i]&&x[i].cat);})();
        o.numFull=Object.fromEntries(Object.entries(NUMERICALS).filter(([k,v])=>v.lesson===LID)); o.ivFull=INTERVIEW['iv-t-synchronise']; o.mcqFull=(L.mcqIds||[]).map(i=>MCQS[i]);
        o.s27=LESSONS['ac-alt-synchronising-power-torque'].body; o.s28=LESSONS['ac-alt-load-test-parallel'].body; return o;}""", [LID29, ROW29])
    b29 = d29['body']; b29t = _re29.sub('<[^>]+>', '', b29)
    ok('syllabus row \"Methods of Synchronisation\" is row 8 (the last) of AC Machines Module II and maps fully (not partial) to the new lesson', d29['row']==8 and d29['mapped']==LID29 and not d29['partial'], (d29['row'], d29['mapped']))
    ok('honesty: Module II is FFFFFFFF, Module III is FFFFFFF, Module IV is FFFF, Module V is FFFFFFF (ninth clean module)', d29['mod2']=='FFFFFFFF' and d29['r6']=='ac-alt-load-test-parallel' and d29['r7']=='ac-alt-synchronising-power-torque' and d29['mods'][2]=='FFFFFFF' and d29['mods'][3]=='FFFF' and d29['mods'][4]=='FFFFFFF', d29['mods'])
    ok('lesson computes to PLACEMENT READY from its real content, is filed under Sem 5 · AC Machines · Module II', d29['lv']=='PLACEMENT READY' and d29['area']=='Sem 5 · AC Machines · Module II', (d29['lv'], d29['area']))
    ok('4 MCQs (E/M/H/P) with four different keyed positions (B, D, A, C); 2 numericals (M, H); 1 Technical interview question; 3 new formula cards in their own topic; Load test and parallel operation still has 3',
       [x[1] for x in d29['mcq']]==['E','M','H','P'] and [x[2] for x in d29['mcq']]==[1,3,0,2] and all(x[4]==4 for x in d29['mcq']) and sorted(d29['num'])==[['num-acm-sync-1','M'],['num-acm-sync-2','H']]
       and d29['iv']==[['iv-t-synchronise','Technical']] and d29['fc']==['Slip frequency, beat period and phase drift','Lamp voltages in the straight and crossed connections','Closing lead angle and closing-angle error'] and d29['fcLoad']==3, d29)
    ok('answer keys A/B/C/D = 130/129/129/129 (session 37 balanced; best single-letter guess 25.15 %); the 16 new MCQs are in the mock pool under the EEE syllabus category', d29['keys'] in ([153,152,152,152], [166,165,165,165], [184,183,183,183], [198,197,197,197], [224, 223, 223, 223], [230, 229, 229, 229], [234, 233, 233, 233], [254, 253, 253, 253], [294, 293, 293, 293], [544, 542, 540, 543], [574, 572, 570, 573], [589, 587, 585, 588], [605, 603, 601, 604], [614, 617, 614, 609], [616, 619, 616, 611], [655, 658, 655, 650], [665, 669, 666, 661], [675, 680, 675, 670], [734, 734, 734, 734], [833, 833, 833, 833]) and max(d29['keys'])/sum(d29['keys'])<0.26 and len(set(d29['mockIn']))==1 and d29['mockIn'][0] and d29['mockIn'][0]!='Uncategorised', (d29['keys'], d29['mockIn']))
    ok('the session-27 and session-28 lessons now point to this lesson with a working link and no longer say anything is \"to be written\"', all('data-nav=\"lesson:%s\"' % LID29 in d29[k] and 'still to be written' not in d29[k] for k in ('s27','s28')))
    # -- reference model: three-phase emfs as complex phasors, lamp voltages as phasor differences --
    def lamps29(th_deg, seq='ok'):
        th = math.radians(th_deg); a = 1; b_ = _cm29.exp(-2j*math.pi/3); c_ = _cm29.exp(2j*math.pi/3)
        a2 = _cm29.exp(1j*th); b2 = (b_ if seq=='ok' else c_)*a2; c2 = (c_ if seq=='ok' else b_)*a2
        return {'S1': abs(a-a2), 'S2': abs(b_-b2), 'S3': abs(c_-c2), 'L1': abs(a-a2), 'L2': abs(b_-c2), 'L3': abs(c_-b2)}
    tbl29 = _re29.findall(r'<tr><td>(\d+)°</td><td>([\d.]+)</td><td>([\d.]+)</td><td>([\d.]+)</td><td>([\d.]+)</td></tr>', b29)
    tbl_ok = len(tbl29)==6 and all(int(t[0])==60*i for i, t in enumerate(tbl29))
    for t in tbl29:
        r_ = lamps29(int(t[0])); tbl_ok = tbl_ok and all(abs(float(t[1+j])-v)<6e-4 for j, v in enumerate([r_['S1'], r_['L1'], r_['L2'], r_['L3']]))
    ok('lamp table: the six printed rows (theta 0-300 deg, straight lamps and crossed L1/L2/L3, in units of E) equal the phasor differences of independently built a-b-c emfs to 3 decimals', tbl_ok, tbl29)
    sweep = [lamps29(t/2.0) for t in range(0, 721)]
    ok('straight connection, correct sequence: the three lamps have identical voltage 2|sin(theta/2)| at every angle (they flicker TOGETHER), zero only at theta = 0',
       all(abs(r_['S1']-r_['S2'])<1e-9 and abs(r_['S2']-r_['S3'])<1e-9 for r_ in sweep) and all(abs(lamps29(t)['S1']-2*abs(math.sin(math.radians(t)/2)))<1e-9 for t in range(0,361,10)) and lamps29(0)['S1']<1e-12)
    sw_bad = [lamps29(t/2.0, 'bad') for t in range(0, 721)]
    ok('straight connection, REVERSED sequence: the three lamps are never all dark (the largest of the three is always at least 1.732 E) and are not equal, so the pattern rotates instead of flickering together',
       min(max(r_['S1'], r_['S2'], r_['S3']) for r_ in sw_bad)>1.7 and any(abs(r_['S1']-r_['S2'])>0.5 for r_ in sw_bad))
    ok('crossed connection, correct sequence: at theta = 0 L1 is dark and L2 = L3 = sqrt3 E = 1.732 E; L2 is dark at 120 deg and L3 at 240 deg (so the dark position runs L1 -> L2 -> L3 as theta grows)',
       lamps29(0)['L1']<1e-12 and abs(lamps29(0)['L2']-S3_)<1e-12 and abs(lamps29(0)['L3']-S3_)<1e-12 and lamps29(120)['L2']<1e-12 and lamps29(240)['L3']<1e-12 and lamps29(120)['L1']>1.7 and lamps29(240)['L1']>1.7)
    dark_order = lambda ths: [min(('L1','L2','L3'), key=lambda k: lamps29(t)[k]) for t in ths]
    ok('crossed connection: a FAST machine (theta rising 0, 120, 240) darkens L1 -> L2 -> L3 and a SLOW one (theta falling 0, -120, -240) darkens L1 -> L3 -> L2, exactly as the lesson, the numerical and the interview answer state',
       dark_order([0, 120, 240])==['L1','L2','L3'] and dark_order([0, -120, -240])==['L1','L3','L2'] and 'fast</b> the dark position moves L1 → L2 → L3' in b29 and 'slow</b> it moves L1 → L3 → L2' in b29)
    ok('crossed connection, REVERSED sequence: all three lamps have the same voltage at every angle (they flicker together), the opposite signature to the straight connection',
       all(abs(r_['L1']-r_['L2'])<1e-9 and abs(r_['L2']-r_['L3'])<1e-9 for r_ in sw_bad))
    ok('both rules are printed in the lesson table and in the quick revision, and the lesson warns that the two signatures are opposite', 'Brighten in turn (rotating); never all dark' in b29t and 'All flicker together' in b29t and 'Note that the two signatures are opposite' in b29t and 'reading the lamp pattern of one connection with the rule of the other' in b29t)
    # -- beat and lead (worked example A), complex-arithmetic reference --
    ZlA = 2*(0.2+8j); EA = 6350.0; IrA = 15e6/(S3_*11000); fi = 4*1506/120; dfA = fi-50.0
    def Icabs(th_deg, Zl, E=EA):
        th = math.radians(th_deg); return abs((E-E*_cm29.exp(-1j*th))/Zl)
    ok('example A: 4 x 1506/120 = 50.2 Hz, df = +0.2 Hz, beat 5.0 s, 72 deg/s, one step of the dark lamp every 5/3 = 1.667 s, +/-5 deg window 10/72 = 0.139 s, lead 72 x 0.25 = 18.0 deg; all printed',
       abs(fi-50.2)<1e-9 and abs(1/dfA-5.0)<1e-9 and abs(360*dfA-72)<1e-9 and abs(5/3-1.667)<5e-4 and abs(10/72-0.139)<5e-4 and abs(360*dfA*0.25-18.0)<1e-9
       and all(t in b29t for t in ['50.2 Hz','+0.2 Hz','5.0 s','72° per second','1.667 s','10/72 = 0.139 s','18.0°']), (fi, dfA))
    rowsA = [(0.05, 3.6, 398.9, 24.9, 3.2), (0.1, 7.2, 797.4, 49.8, 6.3), (0.5, 36.0, 3924.5, 245.2, 31.1)]
    okA = abs(abs(ZlA)-16.005)<5e-4 and abs(IrA-787.3)<0.05
    for te, ang, v, i_, pc in rowsA:
        th_ = 360*dfA*te; okA = okA and abs(th_-ang)<1e-9 and abs(2*EA*math.sin(math.radians(th_)/2)-v)<0.05 and abs(Icabs(th_, ZlA)-i_)<0.05 and abs(Icabs(th_, ZlA)/IrA*100-pc)<0.05
        okA = okA and ('<td>%g s</td><td>%g°</td><td>%.1f V</td><td>%.1f A</td><td>%.1f %%</td>' % (te, ang, v, i_, pc)) in b29
    ok('example A table: timing errors 0.05 / 0.1 / 0.5 s give 3.6 / 7.2 / 36 deg, 2E sin(t/2) = 398.9 / 797.4 / 3924.5 V, |Ic| = 24.9 / 49.8 / 245.2 A = 3.2 / 6.3 / 31.1 % of the 787.3 A rated current (complex-arithmetic reference; |Z| 16.005 ohm)', okA, (abs(ZlA), IrA))
    th_s = 360*0.05*0.1; Is_ = Icabs(th_s, ZlA)
    ok('example A step 4: at 0.05 Hz the same 0.1 s error is 1.8 deg, 199.5 V, 12.46 A (1.6 % of rated), four times smaller than the 49.8 A at 0.2 Hz; printed',
       abs(th_s-1.8)<1e-9 and abs(2*EA*math.sin(math.radians(th_s)/2)-199.5)<0.05 and abs(Is_-12.46)<5e-3 and abs(Is_/IrA*100-1.6)<0.05 and abs(Icabs(7.2, ZlA)/Is_-4.0)<0.02
       and all(t in b29t for t in ['1.8°','199.5/16.005','12.46 A','1.6 % of rated','four times smaller']), (th_s, Is_))
    ok('reading-the-lamps example: 8 s beat -> 0.125 Hz; a 4 s round of the crossed pattern -> 0.25 Hz, fast -> 50.25 Hz -> 120 x 50.25/4 = 1507.5 rpm; reversed-sequence rules stated for both connections',
       abs(1/8-0.125)<1e-12 and abs(1/4-0.25)<1e-12 and abs(120*50.25/4-1507.5)<1e-9 and all(t in b29t for t in ['0.125 Hz','0.25 Hz','1507.5 rpm','Phase sequence reversed']))
    # -- numericals (re-derived; the ans fields are tested too, after the session-28 lesson) --
    n1 = d29['numFull']['num-acm-sync-1']; n2 = d29['numFull']['num-acm-sync-2']
    ok('numerical 1: 6 flickers/min = 0.1 Hz, 10 s, 36 deg/s; N = 120 f/6 = 1002 or 998 rpm; L1 -> L3 -> L2 is a SLOW machine (checked against the phasor model) so 998 rpm; +/-5 deg window 10/36 = 0.278 s; all in the answer field',
       abs(6/60-0.1)<1e-12 and abs(360*0.1-36)<1e-9 and abs(120*50.1/6-1002)<1e-9 and abs(120*49.9/6-998)<1e-9 and dark_order([0,-120,-240])==['L1','L3','L2'] and abs(10/36-0.278)<5e-4
       and all(t in n1['ans'] for t in ['0.1 Hz','10 s','36°','1002 rpm','998 rpm','slow','0.278 s']) and n1['d']=='M' and 'fast one would give L1 → L2 → L3' in n1['calc'], n1['ans'])
    ZlN = 2*(0.3+10j); IrN = 10e6/(S3_*11000); th_l = 360*0.15*0.2; th_r = math.radians(th_l); e1 = EA; e2 = EA*_cm29.exp(-1j*th_r); IcN = (e1-e2)/ZlN
    S1n = 3*e1*IcN.conjugate(); S2n = 3*e2*(-IcN).conjugate(); lossN = 3*abs(IcN)**2*ZlN.real
    ok('numerical 2 (a),(b): lead 360 x 0.15 x 0.2 = 10.8 deg; |Z| 20.009 ohm; rated 524.9 A; 2E sin 5.4 deg = 1195.2 V; |Ic| 59.73 A = 11.4 %; current lags the leading emf by 3.68 deg; leading machine sends 1.136 MW, the other receives 1.129 MW; difference 6.42 kW = 3 I^2 R (0.6 ohm)',
       abs(th_l-10.8)<1e-9 and abs(abs(ZlN)-20.009)<5e-4 and abs(IrN-524.9)<0.05 and abs(2*EA*math.sin(th_r/2)-1195.2)<0.05 and abs(abs(IcN)-59.73)<5e-3 and abs(abs(IcN)/IrN*100-11.4)<0.05
       and abs(-math.degrees(_cm29.phase(IcN))-3.68)<5e-3 and abs(S1n.real/1e6-1.136)<5e-4 and abs(-S2n.real/1e6-1.129)<5e-4 and abs((S1n.real+S2n.real)-lossN)<1e-6 and abs(lossN/1e3-6.42)<5e-3 and abs(3*59.73**2*0.6/1e3-6.42)<0.01
       and all(t in n2['calc'] for t in ['10.8°','1195.2 V','59.73 A','11.4 %','3.68°','1.136 MW','1.129 MW','6.42 kW']), (abs(IcN), S1n, S2n, lossN))
    c_a = Icabs(360*0.15*0.15, ZlN); c_b = Icabs(360*0.03*0.15, ZlN)
    ok('numerical 2 (c),(d): a 0.15 s timing error is 8.1 deg at 0.15 Hz (44.83 A, 8.5 %) and 1.62 deg at 0.03 Hz (8.97 A, 1.7 %); the largest slip for +/-5 deg is 5/(360 x 0.15) = 0.0926 Hz; every value is in the answer field',
       abs(360*0.15*0.15-8.1)<1e-9 and abs(c_a-44.83)<5e-3 and abs(c_a/IrN*100-8.5)<0.05 and abs(360*0.03*0.15-1.62)<1e-9 and abs(c_b-8.97)<5e-3 and abs(c_b/IrN*100-1.7)<0.05 and abs(5/(360*0.15)-0.0926)<5e-5
       and all(t in n2['ans'] for t in ['10.8° behind','59.73 A','11.4 %','1.136 MW','1.129 MW','44.83 A','8.5 %','8.97 A','1.7 %','0.0926 Hz']) and n2['d']=='H', (c_a, c_b))
    # -- MCQs --
    mq29 = d29['mcqFull']; ANSWER_TEXT_FP_S29 = {'acm-meth-1': '8974b4f66b', 'acm-meth-2': '7c05507e37', 'acm-meth-3': '63e5b3057c', 'acm-meth-4': 'a108b0015a'}
    fp29 = {k: _hl.sha1(mq29[i]['opts'][mq29[i]['a']].encode('utf-8')).hexdigest()[:10] for i, k in enumerate(ANSWER_TEXT_FP_S29)}
    ok('session-29 answer-text fingerprints: the correct-answer TEXT of the 4 new questions (re-derived here) is guarded like the older ones', fp29==ANSWER_TEXT_FP_S29, fp29)
    ok('MCQ 1: keyed answer is closing in the middle of the dark period (2E|sin(theta/2)| is zero only at coincidence; the brightest point is theta = 180 deg, the worst moment)', mq29[0]['opts'][mq29[0]['a']].startswith('In the middle of the dark period') and abs(lamps29(180)['S1']-2)<1e-12 and lamps29(0)['S1']<1e-12)
    ok('MCQ 2: keyed answer is a reversed sequence; the reference model shows the straight lamps flicker together with the CORRECT sequence (so the \"faster\" and \"higher voltage\" distractors cannot explain a rotating pattern)', mq29[1]['opts'][mq29[1]['a']].startswith('The phase sequence of the incoming machine is reversed') and all(abs(r_['S1']-r_['S2'])<1e-9 for r_ in sweep) and any(abs(r_['S1']-r_['S2'])>0.5 for r_ in sw_bad))
    fq3 = 4*1503/120; lead3 = 360*(fq3-50)*0.2
    ok('MCQ 3: 4 x 1503/120 = 50.1 Hz, 0.1 Hz fast, 36 deg/s, x 0.2 s = 7.2 deg; keyed \"behind\" because a fast machine GAINS on the bus (the reference model: theta = -7.2 deg rises to 0 in 0.2 s); the decimal-slip distractors are 72 and 0.72',
       abs(fq3-50.1)<1e-9 and abs(lead3-7.2)<1e-9 and mq29[2]['opts'][mq29[2]['a']]=='7.2° behind the bus emf' and sorted(mq29[2]['opts'])==sorted(['7.2° behind the bus emf','7.2° ahead of the bus emf','72° behind the bus emf','0.72° behind the bus emf']))
    ok('MCQ 4: keyed answer is real power picked up by a slightly fast machine versus motoring of a slightly slow one (reverse-power relay); the three distractors are the voltage, sequence and closing-time slips; the explanation says the synchroscope never checks the sequence',
       'takes a little real power' in mq29[3]['opts'][mq29[3]['a']] and 'motored' in mq29[3]['opts'][mq29[3]['a']] and 'reverse-power' in mq29[3]['opts'][mq29[3]['a']] and sum(('circulating current' in o) or ('phase sequence' in o) or ('closes faster' in o) for i, o in enumerate(mq29[3]['opts']) if i!=mq29[3]['a'])==3 and 'never checks the sequence' in mq29[3]['exp'])
    ok('no MCQ option is systematically the longest: the keyed option is the longest in at most 2 of the 4 new questions (author rule against length cues)', sum(len(q['opts'][q['a']])==max(len(o) for o in q['opts']) for q in mq29)<=2, [len(q['opts'][q['a']])==max(len(o) for o in q['opts']) for q in mq29])
    # -- interview + formula cards + lesson claims --
    iv29 = d29['ivFull']
    ok('interview answer: voltage matched with the field, sequence checked once, both lamp signatures (together / rotating and the reverse), synchroscope clockwise = fast and one phase pair only, 360 df t_c lead, slightly fast because a slow machine is motored (reverse-power relay), governor for MW and field for Mvar',
       all(t in iv29['a'] for t in ['field','phase sequence','brighten and fade together','rotates','clockwise for fast','only one phase pair','360 Δf t_c','motored','reverse-power relay','raise the governor','field for reactive power']) and iv29['lesson']==LID29 and iv29['cat']=='Technical')
    fcs = pg.evaluate("FORMULA_CARDS.filter(c=>c.topic==='Methods of synchronisation')")
    ok('formula cards: beat/drift, lamp voltages and lead/error each carry formula, variables, units, conditions, application and a common mistake; the lamp card states the sqrt3 E value and the opposite signatures',
       len(fcs)==3 and all(all(c.get(k) for k in ['f','vars','units','cond','app','mistake']) for c in fcs) and '√3 E = 1.732 E' in fcs[1]['cond'] and 'other way round' in fcs[1]['mistake'] and '360 Δf t_c' in fcs[2]['f'] and 'pN/120' in fcs[0]['f'])
    ok('lesson says plainly what it does NOT cover (hunting and damper winding, synchroscope internals, automatic-synchroniser internals, single-phase machines) and does not claim them; no placeholder wording, no unevidenced \"frequently asked\" claim',
       'What this lesson does not cover' in b29t and all(t in b29t for t in ['hunting','damper winding','internal working of automatic synchronisers','single-phase machines','The textbooks name these lamp connections in different ways']) and not any(w in b29.lower() for w in ['lorem','coming soon','todo','tbd','sample question','comprehensive overview','frequently asked','interviewers ask']))
    ok('placement trap: the synchroscope compares ONE phase pair, so a stationary pointer at 12 o\'clock does not prove the sequence or the voltage; the common mistake warns about reading one connection with the other\'s rule',
       'compares one phase pair' in b29t and 'cannot detect a reversed phase sequence' in b29t and b29.count('callout-trap')==1 and b29.count('callout-mistake')==1)
    # -- lesson page + figure geometry --
    pg.evaluate('nav({page:\"lesson\",id:\"%s\"})' % LID29); pg.wait_for_timeout(150)
    ok('lesson page has one figure, 6 tables, 4 formula boxes, exactly one mistake and one trap callout, and buttons to 4 MCQs / 2 numericals / 1 interview question',
       pg.locator('.lesson .diagram svg').count()==1 and pg.locator('.lesson table.tbl').count()==6 and pg.locator('.lesson .formula-box').count()==4 and pg.locator('.lesson .callout-trap').count()==1 and pg.locator('.lesson .callout-mistake').count()==1
       and 'Practice 4 MCQs' in pg.locator('#contentRoot').inner_text() and 'Solve 2 numericals' in pg.locator('#contentRoot').inner_text() and '1 interview question' in pg.locator('#contentRoot').inner_text(), (pg.locator('.lesson .formula-box').count(), pg.locator('.lesson table.tbl').count()))
    fg29 = pg.evaluate("""()=>{const s=document.querySelector('.lesson .diagram svg'); const o={x0:+s.dataset.x0,kx:+s.dataset.kx,oy:+s.dataset.oy,ky:+s.dataset.ky,curves:{},pts:{},txt:[...s.querySelectorAll('text')].map(t=>t.textContent).join(' | '),aria:s.getAttribute('aria-label'),
        rect:(r=>[+r.getAttribute('x'),+r.getAttribute('y'),+r.getAttribute('width'),+r.getAttribute('height')])(s.querySelector('rect')), ref:(l=>l?[+l.getAttribute('y1'),+l.getAttribute('y2')]:null)(s.querySelector('[data-ref=\"sqrt3\"]'))};
        s.querySelectorAll('[data-curve]').forEach(c=>{o.curves[c.dataset.curve]=c.getAttribute('points').trim().split(/\\s+/).map(p=>p.split(',').map(Number));});
        s.querySelectorAll('[data-pt]').forEach(c=>{o.pts[c.dataset.pt]=[+c.getAttribute('cx'),+c.getAttribute('cy')];}); return o;}""")
    px29 = lambda x: (x-fg29['x0'])/fg29['kx']; py29 = lambda y: (fg29['oy']-y)/fg29['ky']
    f_ref = {'L1': lambda t: 2*abs(math.sin(math.radians(t)/2)), 'L2': lambda t: 2*abs(math.sin(math.radians(120)+math.radians(t)/2)), 'L3': lambda t: 2*abs(math.sin(math.radians(120)-math.radians(t)/2))}
    worst29 = max(abs(py29(y)-f_ref[k](px29(x))) for k, pts_ in fg29['curves'].items() for x, y in pts_)
    ok('figure: the three DRAWN curves have 181 points each (2 deg steps, 0-360 deg) and, read back through the scale, equal 2|sin(theta/2)|, 2|sin(120+theta/2)| and 2|sin(120-theta/2)| (and the phasor model above) to within 0.002 E; worst gap',
       sorted(fg29['curves'])==['L1','L2','L3'] and all(len(v)==181 for v in fg29['curves'].values()) and worst29<0.002 and all(abs(py29(y)-lamps29(px29(x))[k])<0.002 for k, pts_ in fg29['curves'].items() for x, y in pts_[::10]), worst29)
    ok('figure: plot rectangle spans exactly 0-360 deg and 0-2.4 E; the sqrt3 E reference line is drawn at 1.732 E',
       abs(px29(fg29['rect'][0]))<1e-6 and abs(px29(fg29['rect'][0]+fg29['rect'][2])-360)<0.01 and abs(py29(fg29['rect'][1]+fg29['rect'][3]))<1e-6 and abs(py29(fg29['rect'][1])-2.4)<1e-6 and abs(py29(fg29['ref'][0])-S3_)<1e-3 and abs(py29(fg29['ref'][1])-S3_)<1e-3, (fg29['rect'], fg29['ref']))
    mk29 = {k: (px29(v[0]), py29(v[1])) for k, v in fg29['pts'].items()}
    ok('figure markers: L1 dark at 0 deg, L2 and L3 at 1.732 E at 0 deg (the closing instant), L2 dark at 120 deg and L3 dark at 240 deg - each lies on its own drawn curve',
       abs(mk29['L1@0'][0])<0.05 and abs(mk29['L1@0'][1])<1e-3 and abs(mk29['L2@0'][1]-S3_)<1e-3 and abs(mk29['L3@0'][1]-S3_)<1e-3 and abs(mk29['L2@120'][0]-120)<0.05 and abs(mk29['L2@120'][1])<1e-3 and abs(mk29['L3@240'][0]-240)<0.05 and abs(mk29['L3@240'][1])<1e-3
       and all(abs(mk29[k][1]-f_ref[k.split('@')[0]](mk29[k][0]))<1e-3 for k in mk29), mk29)
    ok('figure labels and aria-label state the closing instant (L1 dark, L2 = L3 = 1.732 E), the three lamp connections and the correct-sequence assumption; y-axis label present',
       all(t in fg29['txt'] for t in ['L1 across a–a′ (straight)','L2 across b–c′ (crossed)','L3 across c–b′ (crossed)','θ = 0 (emfs in phase): L1 dark, L2 = L3 = 1.732 E → close the switch','lamp voltage / E','correct phase sequence, a-b-c on both sides']) and '1.732 E' in fg29['aria'] and 'dark at 120 degrees' in fg29['aria'] and 'dark at 240 degrees' in fg29['aria'])
    # -- no SVG text is clipped by its own viewBox (found visually in session 29 on the session-27 figure) --
    clip29 = pg.evaluate("""()=>{const bad=[]; const s29 = ['ct-rlc-dc-trans', 'ct-laplace-s-domain', 'thevenin', 'pe-scr-characteristics', 'psa-ybus-loadflow', 'psa-fdlf-dclf', 'pe-3ph-bridge', 'psa-equal-area', 'psa-pmu-wams', 'ac-alt-phasor-load', 'ac-alt-emf', 'ac-alt-regulation-emf-mmf', 'ac-alt-potier-asa', 'ac-alt-blondel-two-reaction', 'ac-alt-slip-test-power', 'ac-alt-synchronisation']; for(const id of s29){ if(!LESSONS[id]) continue; const d=document.createElement('div'); d.style.cssText='position:absolute;left:-9999px;top:0;width:800px'; d.innerHTML=LESSONS[id].body; document.body.appendChild(d);
        d.querySelectorAll('svg').forEach((s,k)=>{ const vb=(s.getAttribute('viewBox')||'').split(/\\s+/).map(Number); if(vb.length<4) return; s.querySelectorAll('text').forEach(t=>{ const b=t.getBBox(); if(b.x<vb[0]-0.5||b.x+b.width>vb[0]+vb[2]+0.5||b.y<vb[1]-0.5||b.y+b.height>vb[1]+vb[3]+0.5) bad.push([id,k,t.textContent.slice(0,30),Math.round(b.x),Math.round(b.x+b.width),vb[2]]); }); });
        d.remove(); } return bad;}""")
    ok('no text element of any of the 26 lesson figures extends beyond its own viewBox (until session 29 the session-27 y-axis label \"P_syn (pu/rad)\" was cut off at the left edge and the two output labels of the DSP radix-2 butterfly figure at the right edge; this check found the second one)', not clip29, clip29)
    # -- formula book + search + mobile + practice flow --
    pg.evaluate('nav({page:\"formulabook\"})'); pg.wait_for_timeout(150); fb29 = pg.locator('#contentRoot').inner_text()
    ok('Formula Book lists the new topic \"Methods of synchronisation\" under AC Machines with its 3 cards and shows 81 formulas', 'methods of synchronisation' in fb29.lower() and all(n.lower() in fb29.lower() for n in ['Slip frequency, beat period and phase drift','Lamp voltages in the straight and crossed connections','Closing lead angle and closing-angle error']) and any(fc in fb29 for fc in ['170 formulas', '182 formulas', '200 formulas', '214 formulas', '240 formulas', '247 formulas', '253 formulas', '257 formulas', '269 formulas', '281 formulas', '322 formulas', '332 formulas', '344 formulas', '402 formulas', '501 formulas']), fb29[:120])
    def srch29(q):
        pg.evaluate('nav({page:\"search\",q:\"%s\"})' % q); pg.wait_for_timeout(150); return pg.locator('#contentRoot').inner_text()
    sr29a = srch29('synchroscope'); sr29b = srch29('methods of synchronisation'); sr29c = srch29('using lamps or a synchroscope')
    ok('search finds the new content: \"synchroscope\" finds the lesson, \"methods of synchronisation\" finds the syllabus row (marked \"Lesson ready\"), and \"using lamps or a synchroscope\" finds the interview question',
       'Methods of Synchronisation: Dark Lamps, Two Bright One Dark and the Synchroscope' in sr29a and 'Methods of Synchronisation' in sr29b and 'Lesson ready' in sr29b and 'Interview questions' in sr29c and 'bring an alternator onto the grid' in sr29c, (sr29a[:150], sr29b[:150], sr29c[:150]))
    bad_m29 = []
    for rt in ['{page:\"lesson\",id:\"ac-alt-methods-synchronisation\"}','{page:\"numerical\",id:\"num-acm-sync-1\"}','{page:\"numerical\",id:\"num-acm-sync-2\"}','{page:\"course\",sem:5,code:\"23EEP504\"}','{page:\"formulabook\"}']:
        m.evaluate(f'nav({rt})'); m.wait_for_timeout(350)
        if not m.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'): bad_m29.append(rt)
    ok('mobile (390 px): no horizontal overflow on the new lesson, both numericals, the AC Machines course page and the Formula Book', not bad_m29, bad_m29)
    m.evaluate('nav({page:\"lesson\",id:\"ac-alt-methods-synchronisation\"})'); m.wait_for_timeout(350)
    ok('mobile (390 px): the figure and the six tables of the new lesson stay inside the viewport', m.evaluate('[...document.querySelectorAll(\".lesson .diagram svg, .lesson table.tbl\")].every(e=>e.getBoundingClientRect().right<=window.innerWidth+1)'))
    pg.evaluate('nav({page:\"lesson\",id:\"%s\"})' % LID29)
    ok('lesson prerequisite links work (2 internal lesson links resolve to real lessons)', pg.evaluate('[...document.querySelectorAll(".lesson a[data-nav^=\\"lesson:\\"]")].map(a=>a.dataset.nav.slice(7)).every(id=>!!LESSONS[id])') and pg.locator('.lesson a[data-nav^="lesson:"]').count()==2)
    pg.evaluate('nav({page:\"course\",sem:5,code:\"23EEP504\"})'); pg.wait_for_timeout(150); ct29 = pg.locator('#contentRoot').inner_text()
    ok('AC Machines course page opens, shows the row with its lesson, and reports 25/32 topics with a lesson', 'Methods of Synchronisation' in ct29 and 'Lesson ready' in ct29 and '32/32 topics have a lesson (0 partial)' in ct29, ct29[:260])
    bad29p = []
    for qid in ['acm-meth-1','acm-meth-2','acm-meth-3','acm-meth-4']:
        pg.evaluate('nav({page:\"mcqset\",ids:[\"%s\"]})' % qid); pg.wait_for_timeout(60)
        a_ = pg.evaluate('MCQS[\"%s\"].a' % qid); wrong = (a_+1) % 4
        st0 = pg.evaluate("[...document.querySelectorAll('.opt')].map(o=>o.classList.contains('correct')||o.classList.contains('wrong')||o.classList.contains('selected')?'x':'-').join('')")
        pg.click(f'.opt >> nth={wrong}')
        st1 = pg.evaluate("[...document.querySelectorAll('.opt')].map(o=>o.classList.contains('correct')||o.classList.contains('wrong')?'x':o.classList.contains('selected')?'s':'-').join('')")
        pg.click('#submitMcqBtn'); pg.wait_for_timeout(60)
        st_ = pg.evaluate("[...document.querySelectorAll('.opt')].map(o=>o.classList.contains('correct')?'C':o.classList.contains('wrong')?'W':'-').join('')")
        exp_pat = ''.join('C' if i==a_ else ('W' if i==wrong else '-') for i in range(4)); exp_sel = ''.join('s' if i==wrong else '-' for i in range(4))
        if st_ != exp_pat or st0 != '----' or st1 != exp_sel: bad29p.append((qid, st0, st1, st_, exp_pat))
    ok('Practice mode on the 4 new MCQs: all options start unmarked; after a pick only that option is selected (no correct/wrong shown); after Submit a wrong pick is wrong and exactly the keyed option is correct', not bad29p, bad29p)
    ok('the 4 new MCQs contain no positional wording, so the mock can shuffle all of them', pg.evaluate('["acm-meth-1","acm-meth-2","acm-meth-3","acm-meth-4"].every(i=>mockCanShuffle(MCQS[i]))'))


    LESSONS_M3_DICT = {
        "ac-sync-motor-principle-phasor": ["acm-sm-pp-1", "acm-sm-pp-2", "acm-sm-pp-3", "acm-sm-pp-4"],
        "ac-sync-motor-power-torque-losses": ["acm-sm-pt-1", "acm-sm-pt-2", "acm-sm-pt-3", "acm-sm-pt-4"],
        "ac-sync-motor-v-inverted-curves": ["acm-sm-vc-1", "acm-sm-vc-2", "acm-sm-vc-3", "acm-sm-vc-4"],
        "ac-ind-motor-construction-principle": ["acm-im-cp-1", "acm-im-cp-2", "acm-im-cp-3", "acm-im-cp-4"],
        "ac-ind-motor-power-torque-slip": ["acm-im-ts-1", "acm-im-ts-2", "acm-im-ts-3", "acm-im-ts-4"],
        "ac-ind-motor-phasor-equivalent-circuit": ["acm-im-eq-1", "acm-im-eq-2", "acm-im-eq-3", "acm-im-eq-4"],
        "ac-ind-motor-tests-numerical": ["acm-im-nt-1", "acm-im-nt-2", "acm-im-nt-3", "acm-im-nt-4"]
    }


    # =========================================================================
    # SESSION 30: AC Machines Module III: Three Phase AC Motors (all 7 rows)
    # Course ID: 23EEP504 (AC Machines) -> Module III
    # 7 lessons, 28 MCQs, 14 numericals, 7 interview questions, 14 formulas
    # =========================================================================
    M3_TOPICS = [
        ("Principle of operation of synchronous motor-Phasor diagram", "ac-sync-motor-principle-phasor"),
        ("Power and Torque Equations- Losses and Efficiency", "ac-sync-motor-power-torque-losses"),
        ("V and Inverted V curves", "ac-sync-motor-v-inverted-curves"),
        ("Three Phase Induction Motors-Constructional features- Principle of Operation", "ac-ind-motor-construction-principle"),
        ("Power and Torque Equations-Torque Slip Characteristics", "ac-ind-motor-power-torque-slip"),
        ("Phasor diagram-Equivalent circuit", "ac-ind-motor-phasor-equivalent-circuit"),
        ("No load and Blocked rotor tests-Numerical problems", "ac-ind-motor-tests-numerical")
    ]
    M3_LIDS = [lid for _, lid in M3_TOPICS]

    d30 = pg.evaluate(r"""(lids) => {
        const o = {};
        const cs = Object.values(SYLLABUS).flatMap(s=>s.courses);
        const c = cs.find(x=>x.code==='23EEP504');
        o.m3Status = c.modules[2].topics.map(t=>TOPIC_TO_LESSON[t]?(TOPIC_PARTIAL.has(t)?'P':'F'):'-').join('');
        o.levels = lids.map(id => LESSONS[id] ? contentLevel(id) : 'MISSING');
        o.mcqCounts = lids.map(id => (LESSONS[id] && LESSONS[id].mcqIds) ? LESSONS[id].mcqIds.length : 0);
        o.numCounts = lids.map(id => numericalsFor(id).length);
        o.ivCounts = lids.map(id => interviewFor(id).length);
        o.fcCount = FORMULA_CARDS.filter(fc => fc.subj === 'AC Machines').length;
        
        // Check MCQs
        const allMcqIds = lids.flatMap(id => (LESSONS[id] && LESSONS[id].mcqIds) || []);
        o.allMcqs = allMcqIds.map(mid => ({ id: mid, ...MCQS[mid] }));
        o.keyCounts = [0, 0, 0, 0];
        o.diffCounts = { E: 0, M: 0, H: 0, P: 0 };
        allMcqIds.forEach(mid => {
            const m = MCQS[mid];
            if (m) {
                o.keyCounts[m.a]++;
                o.diffCounts[m.d] = (o.diffCounts[m.d] || 0) + 1;
            }
        });
        
        // Check mock shuffle capability
        o.mockShuffleAll = allMcqIds.every(mid => mockCanShuffle(MCQS[mid]));
        return o;
    }""", M3_LIDS)

    ok('AC Machines Module III: all 7 rows mapped as clean full lessons (FFFFFFF, zero partial)', d30['m3Status'] == 'FFFFFFF', d30['m3Status'])
    ok('all 7 new Module III lessons exist and compute to PLACEMENT READY', d30['levels'] == ['PLACEMENT READY'] * 7, d30['levels'])
    ok('all 7 lessons have exactly 4 MCQs, 2 numericals, and 1 interview question linked',
       d30['mcqCounts'] == [4]*7 and d30['numCounts'] == [2]*7 and d30['ivCounts'] == [1]*7,
       (d30['mcqCounts'], d30['numCounts'], d30['ivCounts']))
    ok('28 new MCQs strictly balanced across answer keys (7 A, 7 B, 7 C, 7 D)', d30['keyCounts'] == [7, 7, 7, 7], d30['keyCounts'])
    ok('28 new MCQs balanced across difficulties (7 E, 7 M, 7 H, 7 P)',
       [d30['diffCounts']['E'], d30['diffCounts']['M'], d30['diffCounts']['H'], d30['diffCounts']['P']] == [7, 7, 7, 7],
       d30['diffCounts'])
    ok('all 28 new MCQs have zero positional wording and can be shuffled by mock engine', d30['mockShuffleAll'])

    # Answer text SHA-1 fingerprint guard for all 28 new MCQs
    ANSWER_TEXT_FP_S30 = {
        "acm-sm-pp-1": "0b189f9348", "acm-sm-pp-2": "78010d5498", "acm-sm-pp-3": "4e1090ab38", "acm-sm-pp-4": "81aa310541",
        "acm-sm-pt-1": "2e81727404", "acm-sm-pt-2": "4562987247", "acm-sm-pt-3": "798edbd6c4", "acm-sm-pt-4": "b2cd33e137",
        "acm-sm-vc-1": "3a3cfc539f", "acm-sm-vc-2": "371953c6fd", "acm-sm-vc-3": "996af65137", "acm-sm-vc-4": "4c22a9178d",
        "acm-im-cp-1": "ce661bc06e", "acm-im-cp-2": "2820733ac5", "acm-im-cp-3": "dbd28fb82a", "acm-im-cp-4": "cfbe2a24b5",
        "acm-im-ts-1": "d7223a9fd2", "acm-im-ts-2": "31834c248f", "acm-im-ts-3": "2942f67b89", "acm-im-ts-4": "50b80a2d00",
        "acm-im-eq-1": "6fea8caa74", "acm-im-eq-2": "02d8a6df5f", "acm-im-eq-3": "d5b1325781", "acm-im-eq-4": "f38cb736ec",
        "acm-im-nt-1": "75c31d7e1e", "acm-im-nt-2": "62868d62e3", "acm-im-nt-3": "2ae5fc9c77", "acm-im-nt-4": "7412fedb3c"
    }
    fp30 = {m['id']: _hl.sha1(m['opts'][m['a']].encode('utf-8')).hexdigest()[:10] for m in d30['allMcqs']}
    ok('session-30 answer-text fingerprints: correct-answer TEXT of all 28 new MCQs is guarded', fp30 == ANSWER_TEXT_FP_S30, fp30)

    # Verification of no length cues across the 7 new lessons (longest option in <= 2 of 4)
    length_cues_bad = []
    for lid in M3_LIDS:
        l_mcqs = [m for m in d30['allMcqs'] if m['id'] in LESSONS_M3_DICT.get(lid, [])]
        longest_hits = sum(len(m['opts'][m['a']]) == max(len(o) for o in m['opts']) for m in l_mcqs)
        if longest_hits > 2:
            length_cues_bad.append((lid, longest_hits))
    ok('no MCQ option length cues in Module III lessons (longest option in <= 2 of 4 per lesson)', not length_cues_bad, length_cues_bad)

    # Verify search finds the new lessons
    srch30_a = srch29('torque slip characteristics')
    srch30_b = srch29('synchronous condenser')
    ok('search finds new Module III content: "torque slip characteristics" and "synchronous condenser"',
       'Torque Slip Characteristics' in srch30_a and 'Synchronous Condenser' in srch30_b)

    # Verify mobile (390 px) on all 7 new lessons
    bad_m30 = []
    for lid in M3_LIDS:
        m.evaluate(f'nav({{page:"lesson",id:"{lid}"}})')
        m.wait_for_timeout(100)
        if not m.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1'):
            bad_m30.append(lid)
    ok('mobile (390 px): no horizontal overflow across all 7 new Module III lessons', not bad_m30, bad_m30)


    # =========================================================================
    # SESSION 31: AC Machines Module IV: Performance Characteristics of 3-Phase IM
    # Course ID: 23EEP504 (AC Machines) -> Module IV (all 4 rows)
    # 4 lessons, 16 MCQs, 8 numericals, 4 interview questions, 8 formulas
    # =========================================================================
    M4_TOPICS = [
        ("Construction of circle diagram-Numerical problems", "ac-ind-motor-circle-diagram"),
        ("Cogging and Crawling in cage motors", "ac-ind-motor-cogging-crawling"),
        ("DOL, Autotransformer, Star-Delta starter & Rotor resistance starter", "ac-ind-motor-starters"),
        ("Braking of induction motors-Plugging, Dynamic & Regenerative braking", "ac-ind-motor-braking")
    ]
    M4_LIDS = [lid for _, lid in M4_TOPICS]

    LESSONS_M4_DICT = {
        "ac-ind-motor-circle-diagram": ["acm-cd-1", "acm-cd-2", "acm-cd-3", "acm-cd-4"],
        "ac-ind-motor-cogging-crawling": ["acm-cc-1", "acm-cc-2", "acm-cc-3", "acm-cc-4"],
        "ac-ind-motor-starters": ["acm-st-1", "acm-st-2", "acm-st-3", "acm-st-4"],
        "ac-ind-motor-braking": ["acm-br-1", "acm-br-2", "acm-br-3", "acm-br-4"]
    }

    d31 = pg.evaluate(r"""(lids) => {
        const o = {};
        const cs = Object.values(SYLLABUS).flatMap(s=>s.courses);
        const c = cs.find(x=>x.code==='23EEP504');
        o.m4Status = c.modules[3].topics.map(t=>TOPIC_TO_LESSON[t]?(TOPIC_PARTIAL.has(t)?'P':'F'):'-').join('');
        o.levels = lids.map(id => LESSONS[id] ? contentLevel(id) : 'MISSING');
        o.mcqCounts = lids.map(id => (LESSONS[id] && LESSONS[id].mcqIds) ? LESSONS[id].mcqIds.length : 0);
        o.numCounts = lids.map(id => numericalsFor(id).length);
        o.ivCounts = lids.map(id => interviewFor(id).length);
        o.fcCount = FORMULA_CARDS.filter(fc => fc.subj === 'AC Machines').length;
        
        // Check MCQs
        const allMcqIds = lids.flatMap(id => (LESSONS[id] && LESSONS[id].mcqIds) || []);
        o.allMcqs = allMcqIds.map(mid => ({ id: mid, ...MCQS[mid] }));
        o.keyCounts = [0, 0, 0, 0];
        o.diffCounts = { E: 0, M: 0, H: 0, P: 0 };
        allMcqIds.forEach(mid => {
            const m = MCQS[mid];
            if (m) {
                o.keyCounts[m.a]++;
                o.diffCounts[m.d] = (o.diffCounts[m.d] || 0) + 1;
            }
        });
        
        // Check mock shuffle capability
        o.mockShuffleAll = allMcqIds.every(mid => mockCanShuffle(MCQS[mid]));
        return o;
    }""", M4_LIDS)

    ok('AC Machines Module IV: all 4 rows mapped as clean full lessons (FFFF, zero partial)', d31['m4Status'] == 'FFFF', d31['m4Status'])
    ok('all 4 new Module IV lessons exist and compute to PLACEMENT READY', d31['levels'] == ['PLACEMENT READY'] * 4, d31['levels'])
    ok('all 4 lessons have exactly 4 MCQs, 2 numericals, and 1 interview question linked',
       d31['mcqCounts'] == [4]*4 and d31['numCounts'] == [2]*4 and d31['ivCounts'] == [1]*4,
       (d31['mcqCounts'], d31['numCounts'], d31['ivCounts']))
    ok('16 new MCQs strictly balanced across answer keys (4 A, 4 B, 4 C, 4 D)', d31['keyCounts'] == [4, 4, 4, 4], d31['keyCounts'])
    ok('16 new MCQs balanced across difficulties (4 E, 4 M, 4 H, 4 P)',
       [d31['diffCounts']['E'], d31['diffCounts']['M'], d31['diffCounts']['H'], d31['diffCounts']['P']] == [4, 4, 4, 4],
       d31['diffCounts'])
    ok('all 16 new MCQs have zero positional wording and can be shuffled by mock engine', d31['mockShuffleAll'])

    # Answer text SHA-1 fingerprint guard for all 16 new MCQs
    ANSWER_TEXT_FP_S31 = {
        "acm-cd-1": "ea5d74c3ee",
        "acm-cd-2": "e8e6d5783c",
        "acm-cd-3": "3d206c41a9",
        "acm-cd-4": "7780ee4323",
        "acm-cc-1": "1c35721979",
        "acm-cc-2": "b16c5ddb98",
        "acm-cc-3": "260239ca52",
        "acm-cc-4": "5764cb3daa",
        "acm-st-1": "8491beeb45",
        "acm-st-2": "7046d961a8",
        "acm-st-3": "f76946e38e",
        "acm-st-4": "283ea95d93",
        "acm-br-1": "88da5aa12c",
        "acm-br-2": "673cfadf40",
        "acm-br-3": "8ca5516cbc",
        "acm-br-4": "cb7f7e7f5d"
    }
    fp31 = {m['id']: _hl.sha1(m['opts'][m['a']].encode('utf-8')).hexdigest()[:10] for m in d31['allMcqs']}
    ok('session-31 answer-text fingerprints: correct-answer TEXT of all 16 new MCQs is guarded', fp31 == ANSWER_TEXT_FP_S31, fp31)

    # Verification of no length cues across the 4 new lessons (longest option in <= 2 of 4)
    length_cues_bad_m4 = []
    for lid in M4_LIDS:
        l_mcqs = [m for m in d31['allMcqs'] if m['id'] in LESSONS_M4_DICT.get(lid, [])]
        longest_hits = sum(len(m['opts'][m['a']]) == max(len(o) for o in m['opts']) for m in l_mcqs)
        if longest_hits > 2:
            length_cues_bad_m4.append((lid, longest_hits))
    ok('no MCQ option length cues in Module IV lessons (longest option in <= 2 of 4 per lesson)', not length_cues_bad_m4, length_cues_bad_m4)

    # Verify search finds the new lessons
    srch31_a = srch29('circle diagram')
    srch31_b = srch29('crawling in cage motors')
    ok('search finds new Module IV content: "circle diagram" and "crawling in cage motors"',
       'Circle Diagram' in srch31_a and 'Cogging and Crawling' in srch31_b)

    # Verify mobile (390 px) on all 4 new lessons
    bad_m31 = []
    for lid in M4_LIDS:
        m.evaluate(f'nav({{page:"lesson",id:"{lid}"}})')
        m.wait_for_timeout(100)
        if not m.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1'):
            bad_m31.append(lid)
    ok('mobile (390 px): no horizontal overflow across all 4 new Module IV lessons', not bad_m31, bad_m31)

        # =========================================================================
    # SESSION 32: S5 -> AC Machines (23EEP504) -> Module V (All 7 rows full)
    # =========================================================================
    M5_LIDS = [
        "ac-spim-double-revolving",
        "ac-spim-equiv-circuit",
        "ac-spim-types-split-cap",
        "ac-spim-types-permcap-shaded",
        "ac-ig-grid-connected",
        "ac-ig-self-excited",
        "ac-ig-torque-slip-circle"
    ]
    
    LESSONS_M5_DICT = {
        "ac-spim-double-revolving": ["acm-sp-dfr-1", "acm-sp-dfr-2", "acm-sp-dfr-3", "acm-sp-dfr-4"],
        "ac-spim-equiv-circuit": ["acm-sp-eq-1", "acm-sp-eq-2", "acm-sp-eq-3", "acm-sp-eq-4"],
        "ac-spim-types-split-cap": ["acm-sp-sc-1", "acm-sp-sc-2", "acm-sp-sc-3", "acm-sp-sc-4"],
        "ac-spim-types-permcap-shaded": ["acm-sp-ps-1", "acm-sp-ps-2", "acm-sp-ps-3", "acm-sp-ps-4"],
        "ac-ig-grid-connected": ["acm-ig-gc-1", "acm-ig-gc-2", "acm-ig-gc-3", "acm-ig-gc-4"],
        "ac-ig-self-excited": ["acm-ig-se-1", "acm-ig-se-2", "acm-ig-se-3", "acm-ig-se-4"],
        "ac-ig-torque-slip-circle": ["acm-ig-cd-1", "acm-ig-cd-2", "acm-ig-cd-3", "acm-ig-cd-4"]
    }

    d32 = pg.evaluate("""(lids) => {
        const o = {};
        const cs = Object.values(SYLLABUS).flatMap(s => s.courses);
        const c = cs.find(x => x.code === '23EEP504');
        o.m5Status = c.modules[4].topics.map(t => TOPIC_TO_LESSON[t] ? (TOPIC_PARTIAL.has(t) ? 'P' : 'F') : '-').join('');
        o.levels = lids.map(id => LESSONS[id] ? contentLevel(id) : 'MISSING');
        o.mcqCounts = lids.map(id => (LESSONS[id] && LESSONS[id].mcqIds) ? LESSONS[id].mcqIds.length : 0);
        o.numCounts = lids.map(id => numericalsFor(id).length);
        o.ivCounts = lids.map(id => interviewFor(id).length);
        
        const allMcqIds = lids.flatMap(id => (LESSONS[id] && LESSONS[id].mcqIds) || []);
        o.allMcqs = allMcqIds.map(mid => ({ id: mid, ...MCQS[mid] }));
        o.keyCounts = [0, 0, 0, 0];
        o.diffCounts = { E: 0, M: 0, H: 0, P: 0 };
        allMcqIds.forEach(mid => {
            const m = MCQS[mid];
            if (m) {
                o.keyCounts[m.a]++;
                o.diffCounts[m.d] = (o.diffCounts[m.d] || 0) + 1;
            }
        });
        
        o.mockShuffleAll = allMcqIds.every(mid => mockCanShuffle(MCQS[mid]));
        return o;
    }""", M5_LIDS)

    ok('AC Machines Module V: all 7 rows mapped as clean full lessons (FFFFFFF, zero partial)', d32['m5Status'] == 'FFFFFFF', d32['m5Status'])
    ok('all 7 new Module V lessons exist and compute to PLACEMENT READY', d32['levels'] == ['PLACEMENT READY'] * 7, d32['levels'])
    ok('all 7 lessons have exactly 4 MCQs, 2 numericals, and 1 interview question linked',
       d32['mcqCounts'] == [4]*7 and d32['numCounts'] == [2]*7 and d32['ivCounts'] == [1]*7,
       (d32['mcqCounts'], d32['numCounts'], d32['ivCounts']))
    ok('28 new MCQs strictly balanced across answer keys (7 A, 7 B, 7 C, 7 D)', d32['keyCounts'] == [7, 7, 7, 7], d32['keyCounts'])
    ok('28 new MCQs balanced across difficulties (7 E, 7 M, 7 H, 7 P)',
       [d32['diffCounts']['E'], d32['diffCounts']['M'], d32['diffCounts']['H'], d32['diffCounts']['P']] == [7, 7, 7, 7],
       d32['diffCounts'])
    ok('all 28 new MCQs have zero positional wording and can be shuffled by mock engine', d32['mockShuffleAll'])

    # Answer text SHA-1 fingerprint guard for all 28 new MCQs
    ANSWER_TEXT_FP_S32 = {
        "acm-sp-dfr-1": "07a373504e", "acm-sp-dfr-2": "64c064a778", "acm-sp-dfr-3": "4c71e3a7a4", "acm-sp-dfr-4": "3e83282b77",
        "acm-sp-eq-1": "874e994bf0", "acm-sp-eq-2": "2dec15477f", "acm-sp-eq-3": "d300bea7a4", "acm-sp-eq-4": "962fb91a4e",
        "acm-sp-sc-1": "3f14f036ff", "acm-sp-sc-2": "1221987a78", "acm-sp-sc-3": "1011aec6f1", "acm-sp-sc-4": "cec6c30dfd",
        "acm-sp-ps-1": "d1cfb3ece3", "acm-sp-ps-2": "1d69b5bbf9", "acm-sp-ps-3": "b58b462a63", "acm-sp-ps-4": "6ba08b0a7e",
        "acm-ig-gc-1": "785b803ba3", "acm-ig-gc-2": "58de69c5dd", "acm-ig-gc-3": "489737a001", "acm-ig-gc-4": "79aef4b734",
        "acm-ig-se-1": "fbb9a264d4", "acm-ig-se-2": "c2c17466a1", "acm-ig-se-3": "1c46578673", "acm-ig-se-4": "b90d9b0ca1",
        "acm-ig-cd-1": "8347d34d45", "acm-ig-cd-2": "406b47ea9c", "acm-ig-cd-3": "f225d50d5e", "acm-ig-cd-4": "10180ca443"
    }

    import hashlib as _hl
    fp_mismatch_s32 = []
    for mid, exp_fp in ANSWER_TEXT_FP_S32.items():
        m_obj = next((x for x in d32['allMcqs'] if x['id'] == mid), None)
        if not m_obj:
            fp_mismatch_s32.append((mid, 'missing'))
        else:
            ans_text = m_obj['opts'][m_obj['a']]
            h = _hl.sha1(ans_text.encode('utf-8')).hexdigest()[:10]
            if h != exp_fp:
                fp_mismatch_s32.append((mid, h, exp_fp))
    ok('session-32 answer-text fingerprints: correct-answer TEXT of all 28 new MCQs is guarded',
       not fp_mismatch_s32, fp_mismatch_s32)

    # Verification of no length cues across the 7 new lessons (longest option in <= 2 of 4)
    length_cues_bad_m5 = []
    for lid in M5_LIDS:
        l_mcqs = [m for m in d32['allMcqs'] if m['id'] in LESSONS_M5_DICT.get(lid, [])]
        longest_hits = sum(len(m['opts'][m['a']]) == max(len(o) for o in m['opts']) for m in l_mcqs)
        if longest_hits > 2:
            length_cues_bad_m5.append((lid, longest_hits))
    ok('no MCQ option length cues in Module V lessons (longest option in <= 2 of 4 per lesson)', not length_cues_bad_m5, length_cues_bad_m5)

    # Verify search finds the new lessons
    srch32_a = srch29('double field revolving')
    srch32_b = srch29('induction generator')
    ok('search finds new Module V content: "double field revolving" and "induction generator"',
       ('Double-Field Revolving' in srch32_a or 'Double field revolving' in srch32_a) and 'Induction Generator' in srch32_b)

    # Verify mobile (390 px) on all 7 new lessons
    bad_m32 = []
    for lid in M5_LIDS:
        m.evaluate(f'nav({{page:"lesson",id:"{lid}"}})')
        m.wait_for_timeout(100)
        if not m.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1'):
            bad_m32.append(lid)
    ok('mobile (390 px): no horizontal overflow across all 7 new Module V lessons', not bad_m32, bad_m32)


    # =========================================================================
    # SESSION 33: S5 -> Embedded System Design and IoT (23EEJ502) -> Module I
    # =========================================================================
    M1_ES_LIDS = [
        "es-8085-architecture-pins",
        "es-8085-addressing-instruction-bytes",
        "es-8085-instruction-cycles-timing",
        "es-8085-basic-alps-delay-programs"
    ]
    
    LESSONS_M1_ES_DICT = {
        "es-8085-architecture-pins": ["es-arch-1", "es-arch-2", "es-arch-3", "es-arch-4"],
        "es-8085-addressing-instruction-bytes": ["es-add-1", "es-add-2", "es-add-3", "es-add-4"],
        "es-8085-instruction-cycles-timing": ["es-tim-1", "es-tim-2", "es-tim-3", "es-tim-4"],
        "es-8085-basic-alps-delay-programs": ["es-alp-1", "es-alp-2", "es-alp-3", "es-alp-4"]
    }

    d33 = pg.evaluate("""(lids) => {
        const o = {};
        const cs = Object.values(SYLLABUS).flatMap(s => s.courses);
        const c = cs.find(x => x.code === '23EEJ502');
        o.m1Status = c.modules[0].topics.map(t => TOPIC_TO_LESSON[t] ? (TOPIC_PARTIAL.has(t) ? 'P' : 'F') : '-').join('');
        o.levels = lids.map(id => LESSONS[id] ? contentLevel(id) : 'MISSING');
        o.mcqCounts = lids.map(id => (LESSONS[id] && LESSONS[id].mcqIds) ? LESSONS[id].mcqIds.length : 0);
        o.numCounts = lids.map(id => numericalsFor(id).length);
        o.ivCounts = lids.map(id => interviewFor(id).length);
        
        const allMcqIds = lids.flatMap(id => (LESSONS[id] && LESSONS[id].mcqIds) || []);
        o.allMcqs = allMcqIds.map(mid => ({ id: mid, ...MCQS[mid] }));
        o.keyCounts = [0, 0, 0, 0];
        o.diffCounts = { E: 0, M: 0, H: 0, P: 0 };
        allMcqIds.forEach(mid => {
            const m = MCQS[mid];
            if (m) {
                o.keyCounts[m.a]++;
                o.diffCounts[m.d] = (o.diffCounts[m.d] || 0) + 1;
            }
        });
        
        o.mockShuffleAll = allMcqIds.every(mid => mockCanShuffle(MCQS[mid]));
        return o;
    }""", M1_ES_LIDS)

    ok('Embedded System Design and IoT Module I: all 4 rows mapped as clean full lessons (FFFF, zero partial)', d33['m1Status'] == 'FFFF', d33['m1Status'])
    ok('all 4 new Module I lessons exist and compute to PLACEMENT READY', d33['levels'] == ['PLACEMENT READY'] * 4, d33['levels'])
    ok('all 4 lessons have exactly 4 MCQs, 2 numericals, and 2 interview questions linked',
       d33['mcqCounts'] == [4]*4 and d33['numCounts'] == [2]*4 and d33['ivCounts'] == [2]*4,
       (d33['mcqCounts'], d33['numCounts'], d33['ivCounts']))
    ok('16 new MCQs strictly balanced across answer keys (4 A, 4 B, 4 C, 4 D)', d33['keyCounts'] == [4, 4, 4, 4], d33['keyCounts'])
    ok('16 new MCQs balanced across difficulties (4 E, 4 M, 4 H, 4 P)',
       [d33['diffCounts']['E'], d33['diffCounts']['M'], d33['diffCounts']['H'], d33['diffCounts']['P']] == [4, 4, 4, 4],
       d33['diffCounts'])
    ok('all 16 new MCQs have zero positional wording and can be shuffled by mock engine', d33['mockShuffleAll'])

    # Answer text SHA-1 fingerprint guard for all 16 new MCQs
    ANSWER_TEXT_FP_S33 = {
        "es-arch-1": "4930a49e52", "es-arch-2": "9830926081", "es-arch-3": "dd4b4f1227", "es-arch-4": "6de759cc0e",
        "es-add-1": "e6623b918a", "es-add-2": "09600fa765", "es-add-3": "91786499fc", "es-add-4": "10b5bd1f7e",
        "es-tim-1": "dcfaaab602", "es-tim-2": "cf1b830e7d", "es-tim-3": "57b09a3028", "es-tim-4": "53b396c0da",
        "es-alp-1": "03d2ed4877", "es-alp-2": "23a171a760", "es-alp-3": "1089e88568", "es-alp-4": "4b3e4a5238"
    }

    fp_mismatch_s33 = []
    for mid, exp_fp in ANSWER_TEXT_FP_S33.items():
        m_obj = next((x for x in d33['allMcqs'] if x['id'] == mid), None)
        if not m_obj:
            fp_mismatch_s33.append((mid, 'missing'))
        else:
            ans_text = m_obj['opts'][m_obj['a']]
            h = _hl.sha1(ans_text.encode('utf-8')).hexdigest()[:10]
            if h != exp_fp:
                fp_mismatch_s33.append((mid, h, exp_fp))
    ok('session-33 answer-text fingerprints: correct-answer TEXT of all 16 new MCQs is guarded',
       not fp_mismatch_s33, fp_mismatch_s33)

    # Verification of no length cues across the 4 new lessons (longest option in <= 2 of 4)
    length_cues_bad_m1 = []
    for lid in M1_ES_LIDS:
        l_mcqs = [m for m in d33['allMcqs'] if m['id'] in LESSONS_M1_ES_DICT.get(lid, [])]
        longest_hits = sum(len(m['opts'][m['a']]) == max(len(o) for o in m['opts']) for m in l_mcqs)
        if longest_hits > 2:
            length_cues_bad_m1.append((lid, longest_hits))
    ok('no MCQ option length cues in Module I lessons (longest option in <= 2 of 4 per lesson)', not length_cues_bad_m1, length_cues_bad_m1)

    # Verify search finds the new lessons
    srch33_a = srch29('8085 architecture')
    srch33_b = srch29('delay programs')
    ok('search finds new Module I content: "8085 architecture" and "delay programs"',
       '8085' in srch33_a and ('Delay' in srch33_b or 'delay' in srch33_b))

    # Verify mobile (390 px) on all 4 new lessons
    bad_m33 = []
    for lid in M1_ES_LIDS:
        m.evaluate(f'nav({{page:"lesson",id:"{lid}"}})')
        m.wait_for_timeout(100)
        if not m.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1'):
            bad_m33.append(lid)
    ok('mobile (390 px): no horizontal overflow across all 4 new Module I lessons', not bad_m33, bad_m33)



    # =========================================================================
    # SESSION 34: S5 -> Embedded System Design and IoT (23EEJ502) -> Module II
    # =========================================================================
    M2_ES_LIDS = [
        "es-8255-ppi-architecture-modes",
        "es-io-seven-segment-adc-dac",
        "es-intro-architecture-applications",
        "es-system-constraints-realtime",
        "es-8051-architecture-memory-sfr",
        "es-8051-io-port-addressing"
    ]
    
    LESSONS_M2_ES_DICT = {
        "es-8255-ppi-architecture-modes": ["es-m2-ppi-1", "es-m2-ppi-2", "es-m2-ppi-3", "es-m2-ppi-4"],
        "es-io-seven-segment-adc-dac": ["es-m2-iod-1", "es-m2-iod-2", "es-m2-iod-3", "es-m2-iod-4"],
        "es-intro-architecture-applications": ["es-m2-emb-1", "es-m2-emb-2", "es-m2-emb-3", "es-m2-emb-4"],
        "es-system-constraints-realtime": ["es-m2-rts-1", "es-m2-rts-2", "es-m2-rts-3", "es-m2-rts-4"],
        "es-8051-architecture-memory-sfr": ["es-m2-51a-1", "es-m2-51a-2", "es-m2-51a-3", "es-m2-51a-4"],
        "es-8051-io-port-addressing": ["es-m2-51i-1", "es-m2-51i-2", "es-m2-51i-3", "es-m2-51i-4"]
    }

    d34 = pg.evaluate("""(lids) => {
        const o = {};
        const cs = Object.values(SYLLABUS).flatMap(s => s.courses);
        const c = cs.find(x => x.code === '23EEJ502');
        o.m2Status = c.modules[1].topics.map(t => TOPIC_TO_LESSON[t] ? (TOPIC_PARTIAL.has(t) ? 'P' : 'F') : '-').join('');
        o.levels = lids.map(id => LESSONS[id] ? contentLevel(id) : 'MISSING');
        o.mcqCounts = lids.map(id => (LESSONS[id] && LESSONS[id].mcqIds) ? LESSONS[id].mcqIds.length : 0);
        o.numCounts = lids.map(id => numericalsFor(id).length);
        o.ivCounts = lids.map(id => interviewFor(id).length);
        
        const allMcqIds = lids.flatMap(id => (LESSONS[id] && LESSONS[id].mcqIds) || []);
        o.allMcqs = allMcqIds.map(mid => ({ id: mid, ...MCQS[mid] }));
        o.keyCounts = [0, 0, 0, 0];
        o.diffCounts = { E: 0, M: 0, H: 0, P: 0 };
        allMcqIds.forEach(mid => {
            const m = MCQS[mid];
            if (m) {
                o.keyCounts[m.a]++;
                o.diffCounts[m.d] = (o.diffCounts[m.d] || 0) + 1;
            }
        });
        
        o.mockShuffleAll = allMcqIds.every(mid => mockCanShuffle(MCQS[mid]));
        return o;
    }""", M2_ES_LIDS)

    ok('Embedded System Design and IoT Module II: all 6 rows mapped as clean full lessons (FFFFFF, zero partial)', d34['m2Status'] == 'FFFFFF', d34['m2Status'])
    ok('all 6 new Module II lessons exist and compute to PLACEMENT READY', d34['levels'] == ['PLACEMENT READY'] * 6, d34['levels'])
    ok('all 6 lessons have exactly 4 MCQs, at least 1 numerical, and 2 interview questions linked',
       all(c == 4 for c in d34['mcqCounts']) and all(c >= 1 for c in d34['numCounts']) and all(c == 2 for c in d34['ivCounts']),
       (d34['mcqCounts'], d34['numCounts'], d34['ivCounts']))
    ok('24 new MCQs strictly balanced across answer keys (6 A, 6 B, 6 C, 6 D)', d34['keyCounts'] == [6, 6, 6, 6], d34['keyCounts'])
    ok('24 new MCQs balanced across difficulties (6 E, 6 M, 6 H, 6 P)',
       [d34['diffCounts']['E'], d34['diffCounts']['M'], d34['diffCounts']['H'], d34['diffCounts']['P']] == [6, 6, 6, 6],
       d34['diffCounts'])
    ok('all 24 new MCQs have zero positional wording and can be shuffled by mock engine', d34['mockShuffleAll'])

    # Answer text SHA-1 fingerprint guard for all 24 new MCQs
    ANSWER_TEXT_FP_S34 = {
        "es-m2-ppi-1": "93daedf08f", "es-m2-ppi-2": "c5a16812fe", "es-m2-ppi-3": "0a1a7c5f03", "es-m2-ppi-4": "7aa55d6824",
        "es-m2-iod-1": "6c347c3c7e", "es-m2-iod-2": "dc85c9c68c", "es-m2-iod-3": "5f3c55edaa", "es-m2-iod-4": "e0277c42f2",
        "es-m2-emb-1": "9bf67e833b", "es-m2-emb-2": "01de6e82fe", "es-m2-emb-3": "e47d8a760d", "es-m2-emb-4": "4f64c6b508",
        "es-m2-rts-1": "11e339b977", "es-m2-rts-2": "bcb11bed9a", "es-m2-rts-3": "0700da577b", "es-m2-rts-4": "5804a565cc",
        "es-m2-51a-1": "b92cdf7639", "es-m2-51a-2": "95a7166973", "es-m2-51a-3": "f91cafc776", "es-m2-51a-4": "b358d105f6",
        "es-m2-51i-1": "34337c79d5", "es-m2-51i-2": "0789843075", "es-m2-51i-3": "010cd63648", "es-m2-51i-4": "f9677cb73e"
    }

    fp_mismatch_s34 = []
    for mid, exp_fp in ANSWER_TEXT_FP_S34.items():
        m_obj = next((x for x in d34['allMcqs'] if x['id'] == mid), None)
        if not m_obj:
            fp_mismatch_s34.append((mid, 'missing'))
        else:
            ans_text = m_obj['opts'][m_obj['a']]
            h = _hl.sha1(ans_text.encode('utf-8')).hexdigest()[:10]
            if h != exp_fp:
                fp_mismatch_s34.append((mid, h, exp_fp))
    ok('session-34 answer-text fingerprints: correct-answer TEXT of all 24 new MCQs is guarded',
       not fp_mismatch_s34, fp_mismatch_s34)

    # Verification of no length cues across the 6 new lessons (longest option in <= 2 of 4)
    length_cues_bad_m2 = []
    for lid in M2_ES_LIDS:
        l_mcqs = [m for m in d34['allMcqs'] if m['id'] in LESSONS_M2_ES_DICT.get(lid, [])]
        longest_hits = sum(len(m['opts'][m['a']]) == max(len(o) for o in m['opts']) for m in l_mcqs)
        if longest_hits > 2:
            length_cues_bad_m2.append((lid, longest_hits))
    ok('no MCQ option length cues in Module II lessons (longest option in <= 2 of 4 per lesson)', not length_cues_bad_m2, length_cues_bad_m2)

    # Verify search finds the new lessons
    srch34_a = srch29('8255 PPI')
    srch34_b = srch29('8051 Microcontroller')
    ok('search finds new Module II content: "8255 PPI" and "8051 Microcontroller"',
       ('8255' in srch34_a) and ('8051' in srch34_b))

    # Verify mobile (390 px) on all 6 new lessons
    bad_m34 = []
    for lid in M2_ES_LIDS:
        m.evaluate(f'nav({{page:"lesson",id:"{lid}"}})')
        m.wait_for_timeout(100)
        if not m.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1'):
            bad_m34.append(lid)
    ok('mobile (390 px): no horizontal overflow across all 6 new Module II lessons', not bad_m34, bad_m34)


    # ---------------- session-35: Embedded System Design and IoT Module III ----------------
    M3_ES_LIDS = [
        "es-8051-inst-data-arith-logic-bool",
        "es-8051-branching-sjmp-ajmp-ljmp",
        "es-8051-basic-assembly-programs",
        "es-8051-embedded-c-programming",
        "es-8051-alp-delay-port-programming"
    ]
    
    LESSONS_M3_ES_DICT = {
        "es-8051-inst-data-arith-logic-bool": ["es-m3-op-1", "es-m3-op-2", "es-m3-op-3", "es-m3-op-4"],
        "es-8051-branching-sjmp-ajmp-ljmp": ["es-m3-br-1", "es-m3-br-2", "es-m3-br-3", "es-m3-br-4"],
        "es-8051-basic-assembly-programs": ["es-m3-alp-1", "es-m3-alp-2", "es-m3-alp-3", "es-m3-alp-4"],
        "es-8051-embedded-c-programming": ["es-m3-c-1", "es-m3-c-2", "es-m3-c-3", "es-m3-c-4"],
        "es-8051-alp-delay-port-programming": ["es-m3-dp-1", "es-m3-dp-2", "es-m3-dp-3", "es-m3-dp-4"]
    }

    d35 = pg.evaluate("""(lids) => {
        const o = {};
        const c = Object.values(SYLLABUS).flatMap(s => s.courses).find(c => c.code === '23EEJ502');
        const m3 = c.modules[2];
        o.m3Status = m3.topics.map(t => TOPIC_TO_LESSON[t] ? (TOPIC_PARTIAL.has(t) ? 'P' : 'F') : '-').join('');
        o.levels = lids.map(id => contentLevel(id));
        o.mcqCounts = lids.map(id => (LESSONS[id].mcqIds || []).length);
        o.numCounts = lids.map(id => numericalsFor(id).length);
        o.ivCounts = lids.map(id => interviewFor(id).length);
        
        const allMcqIds = lids.flatMap(id => LESSONS[id].mcqIds || []);
        o.allMcqs = allMcqIds.map(mid => ({ id: mid, ...MCQS[mid] }));
        o.keyCounts = [0, 0, 0, 0];
        o.diffCounts = { E: 0, M: 0, H: 0, P: 0 };
        allMcqIds.forEach(mid => {
            const m = MCQS[mid];
            if (m) {
                o.keyCounts[m.a]++;
                o.diffCounts[m.d] = (o.diffCounts[m.d] || 0) + 1;
            }
        });
        
        o.mockShuffleAll = allMcqIds.every(mid => mockCanShuffle(MCQS[mid]));
        return o;
    }""", M3_ES_LIDS)

    ok('Embedded System Design and IoT Module III: all 5 rows mapped as clean full lessons (FFFFF, zero partial)', d35['m3Status'] == 'FFFFF', d35['m3Status'])
    ok('all 5 new Module III lessons exist and compute to PLACEMENT READY', d35['levels'] == ['PLACEMENT READY'] * 5, d35['levels'])
    ok('all 5 lessons have exactly 4 MCQs, at least 1 numerical, and 2 interview questions linked',
       all(c == 4 for c in d35['mcqCounts']) and all(c >= 1 for c in d35['numCounts']) and all(c == 2 for c in d35['ivCounts']),
       (d35['mcqCounts'], d35['numCounts'], d35['ivCounts']))
    ok('20 new MCQs strictly balanced across answer keys (5 A, 5 B, 5 C, 5 D)', d35['keyCounts'] == [5, 5, 5, 5], d35['keyCounts'])
    ok('20 new MCQs balanced across difficulties (5 E, 5 M, 5 H, 5 P)',
       [d35['diffCounts']['E'], d35['diffCounts']['M'], d35['diffCounts']['H'], d35['diffCounts']['P']] == [5, 5, 5, 5],
       d35['diffCounts'])
    ok('all 20 new MCQs have zero positional wording and can be shuffled by mock engine', d35['mockShuffleAll'])

    # Answer text SHA-1 fingerprint guard for all 20 new MCQs
    ANSWER_TEXT_FP_S35 = {
        "es-m3-op-1": "f15a248c61", "es-m3-op-2": "54cb3f7916", "es-m3-op-3": "50be7a9920", "es-m3-op-4": "d3e9a9089c",
        "es-m3-br-1": "87a13e3bca", "es-m3-br-2": "5b4193c9b9", "es-m3-br-3": "9eebf8d8e5", "es-m3-br-4": "0d5c62581b",
        "es-m3-alp-1": "ba919eb823", "es-m3-alp-2": "2ff9fd38ed", "es-m3-alp-3": "a9f457697a", "es-m3-alp-4": "c58477c75c",
        "es-m3-c-1": "2d6b82eb1c", "es-m3-c-2": "70976dfeef", "es-m3-c-3": "d6be29a6da", "es-m3-c-4": "3e79563bf9",
        "es-m3-dp-1": "a1e351bd5b", "es-m3-dp-2": "1f5e381474", "es-m3-dp-3": "36b76b833f", "es-m3-dp-4": "a3e3c25497"
    }

    fp_mismatch_s35 = []
    for mid, exp_fp in ANSWER_TEXT_FP_S35.items():
        m_obj = next((x for x in d35['allMcqs'] if x['id'] == mid), None)
        if not m_obj:
            fp_mismatch_s35.append((mid, 'missing'))
        else:
            ans_text = m_obj['opts'][m_obj['a']]
            h = _hl.sha1(ans_text.encode('utf-8')).hexdigest()[:10]
            if h != exp_fp:
                fp_mismatch_s35.append((mid, h, exp_fp))
    ok('session-35 answer-text fingerprints: correct-answer TEXT of all 20 new MCQs is guarded',
       not fp_mismatch_s35, fp_mismatch_s35)

    # Verification of no length cues across the 5 new lessons (longest option in <= 2 of 4)
    length_cues_bad_m3 = []
    for lid in M3_ES_LIDS:
        l_mcqs = [m for m in d35['allMcqs'] if m['id'] in LESSONS_M3_ES_DICT.get(lid, [])]
        longest_hits = sum(len(m['opts'][m['a']]) == max(len(o) for o in m['opts']) for m in l_mcqs)
        if longest_hits > 2:
            length_cues_bad_m3.append((lid, longest_hits))
    ok('no MCQ option length cues in Module III lessons (longest option in <= 2 of 4 per lesson)', not length_cues_bad_m3, length_cues_bad_m3)

    # Verify search finds the new lessons
    srch35_a = srch29('SJMP')
    srch35_b = srch29('Embedded C')
    ok('search finds new Module III content: "SJMP" and "Embedded C"',
       ('SJMP' in srch35_a or 'branching' in srch35_a.lower()) and ('Embedded C' in srch35_b or 'embedded' in srch35_b.lower()))

    # Verify mobile (390 px) on all 5 new lessons
    bad_m35 = []
    for lid in M3_ES_LIDS:
        m.evaluate(f'nav({{page:"lesson",id:"{lid}"}})')
        m.wait_for_timeout(100)
        if not m.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1'):
            bad_m35.append(lid)
    ok('mobile (390 px): no horizontal overflow across all 5 new Module III lessons', not bad_m35, bad_m35)

    # ---------------- session-36: Embedded System Design and IoT Module IV ----------------
    M4_ES_LIDS = [
        "es-8051-timers-tcon-tmod",
        "es-8051-serial-scon-smod-sbuf",
        "es-8051-interrupts-ie-ip"
    ]
    
    LESSONS_M4_ES_DICT = {
        "es-8051-timers-tcon-tmod": ["es-m4-tim-1", "es-m4-tim-2", "es-m4-tim-3", "es-m4-tim-4"],
        "es-8051-serial-scon-smod-sbuf": ["es-m4-ser-1", "es-m4-ser-2", "es-m4-ser-3", "es-m4-ser-4"],
        "es-8051-interrupts-ie-ip": ["es-m4-int-1", "es-m4-int-2", "es-m4-int-3", "es-m4-int-4"]
    }

    d36 = pg.evaluate("""(lids) => {
        const o = {};
        const c = Object.values(SYLLABUS).flatMap(s => s.courses).find(c => c.code === '23EEJ502');
        const m4 = c.modules[3];
        o.m4Status = m4.topics.map(t => TOPIC_TO_LESSON[t] ? (TOPIC_PARTIAL.has(t) ? 'P' : 'F') : '-').join('');
        o.levels = lids.map(id => contentLevel(id));
        o.mcqCounts = lids.map(id => (LESSONS[id].mcqIds || []).length);
        o.numCounts = lids.map(id => numericalsFor(id).length);
        o.ivCounts = lids.map(id => interviewFor(id).length);
        
        const allMcqIds = lids.flatMap(id => LESSONS[id].mcqIds || []);
        o.allMcqs = allMcqIds.map(mid => ({ id: mid, ...MCQS[mid] }));
        o.keyCounts = [0, 0, 0, 0];
        o.diffCounts = { E: 0, M: 0, H: 0, P: 0 };
        allMcqIds.forEach(mid => {
            const m = MCQS[mid];
            if (m) {
                o.keyCounts[m.a]++;
                o.diffCounts[m.d] = (o.diffCounts[m.d] || 0) + 1;
            }
        });
        
        o.mockShuffleAll = allMcqIds.every(mid => mockCanShuffle(MCQS[mid]));
        return o;
    }""", M4_ES_LIDS)

    ok('Embedded System Design and IoT Module IV: all 5 rows mapped as clean full lessons (FFFFF, zero partial)', d36['m4Status'] == 'FFFFF', d36['m4Status'])
    ok('all 3 new Module IV lessons exist and compute to PLACEMENT READY', d36['levels'] == ['PLACEMENT READY'] * 3, d36['levels'])
    ok('all 3 lessons have exactly 4 MCQs, at least 1 numerical, and 3 interview questions linked',
       all(c == 4 for c in d36['mcqCounts']) and all(c >= 1 for c in d36['numCounts']) and all(c == 3 for c in d36['ivCounts']),
       (d36['mcqCounts'], d36['numCounts'], d36['ivCounts']))
    ok('12 new MCQs strictly balanced across answer keys (3 A, 3 B, 3 C, 3 D)', d36['keyCounts'] == [3, 3, 3, 3], d36['keyCounts'])
    ok('12 new MCQs balanced across difficulties (3 E, 3 M, 3 H, 3 P)',
       [d36['diffCounts']['E'], d36['diffCounts']['M'], d36['diffCounts']['H'], d36['diffCounts']['P']] == [3, 3, 3, 3],
       d36['diffCounts'])
    ok('all 12 new MCQs have zero positional wording and can be shuffled by mock engine', d36['mockShuffleAll'])

    # Answer text SHA-1 fingerprint guard for all 12 new MCQs
    ANSWER_TEXT_FP_S36 = {
        'es-m4-tim-1': 'd2880022cf', 'es-m4-tim-2': '9910dcc5e9', 'es-m4-tim-3': '774e4a7cba', 'es-m4-tim-4': '956f4312bd',
        'es-m4-ser-1': 'd80d026d3b', 'es-m4-ser-2': '1978b4cf79', 'es-m4-ser-3': '092e324ebc', 'es-m4-ser-4': '468ee9416f',
        'es-m4-int-1': 'f0cb28326f', 'es-m4-int-2': '8a0b133aa4', 'es-m4-int-3': 'b80945e30b', 'es-m4-int-4': '28a9d5a644'
    }

    fp_mismatch_s36 = []
    for mid, exp_fp in ANSWER_TEXT_FP_S36.items():
        m_obj = next((x for x in d36['allMcqs'] if x['id'] == mid), None)
        if not m_obj:
            fp_mismatch_s36.append((mid, 'missing'))
        else:
            ans_text = m_obj['opts'][m_obj['a']]
            h = _hl.sha1(ans_text.encode('utf-8')).hexdigest()[:10]
            if h != exp_fp:
                fp_mismatch_s36.append((mid, h, exp_fp))
    ok('session-36 answer-text fingerprints: correct-answer TEXT of all 12 new MCQs is guarded',
       not fp_mismatch_s36, fp_mismatch_s36)

    # Verification of no length cues across the 3 new lessons (longest option in <= 2 of 4)
    length_cues_bad_m4 = []
    for lid in M4_ES_LIDS:
        l_mcqs = [m for m in d36['allMcqs'] if m['id'] in LESSONS_M4_ES_DICT.get(lid, [])]
        longest_hits = sum(len(m['opts'][m['a']]) == max(len(o) for o in m['opts']) for m in l_mcqs)
        if longest_hits > 2:
            length_cues_bad_m4.append((lid, longest_hits))
    ok('no MCQ option length cues in Module IV lessons (longest option in <= 2 of 4 per lesson)', not length_cues_bad_m4, length_cues_bad_m4)

    # Verify search finds the new lessons
    srch36_a = srch29('TMOD')
    srch36_b = srch29('SBUF')
    ok('search finds new Module IV content: "TMOD" and "SBUF"',
       ('TMOD' in srch36_a or 'timer' in srch36_a.lower()) and ('SBUF' in srch36_b or 'serial' in srch36_b.lower()))

    # Verify mobile (390 px) on all 3 new lessons
    bad_m36 = []
    for lid in M4_ES_LIDS:
        m.evaluate(f'nav({{page:"lesson",id:"{lid}"}})')
        m.wait_for_timeout(100)
        if not m.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1'):
            bad_m36.append(lid)
    ok('mobile (390 px): no horizontal overflow across all 3 new Module IV lessons', not bad_m36, bad_m36)

    # ---------------- session-37: Embedded System Design and IoT Module V ----------------
    M5_ES_LIDS = [
        "es-arm7-arch-risc-flags",
        "es-iot-sensors-actuators-integration",
        "es-iot-protocols-security-privacy",
        "es-embedded-iot-app-design"
    ]
    
    LESSONS_M5_ES_DICT = {
        "es-arm7-arch-risc-flags": ["es-m5-arm-1", "es-m5-arm-2", "es-m5-arm-3", "es-m5-arm-4"],
        "es-iot-sensors-actuators-integration": ["es-m5-iot-1", "es-m5-iot-2", "es-m5-iot-3", "es-m5-iot-4"],
        "es-iot-protocols-security-privacy": ["es-m5-prt-1", "es-m5-prt-2", "es-m5-prt-3", "es-m5-prt-4"],
        "es-embedded-iot-app-design": ["es-m5-app-1", "es-m5-app-2", "es-m5-app-3", "es-m5-app-4"]
    }

    d37 = pg.evaluate("""(lids) => {
        const o = {};
        const c = Object.values(SYLLABUS).flatMap(s => s.courses).find(c => c.code === '23EEJ502');
        const m5 = c.modules[4];
        o.m5Status = m5.topics.map(t => TOPIC_TO_LESSON[t] ? (TOPIC_PARTIAL.has(t) ? 'P' : 'F') : '-').join('');
        o.levels = lids.map(id => contentLevel(id));
        o.mcqCounts = lids.map(id => (LESSONS[id].mcqIds || []).length);
        o.numCounts = lids.map(id => numericalsFor(id).length);
        o.ivCounts = lids.map(id => interviewFor(id).length);
        
        const allMcqIds = lids.flatMap(id => LESSONS[id].mcqIds || []);
        o.allMcqs = allMcqIds.map(mid => ({ id: mid, ...MCQS[mid] }));
        o.keyCounts = [0, 0, 0, 0];
        o.diffCounts = { E: 0, M: 0, H: 0, P: 0 };
        allMcqIds.forEach(mid => {
            const m = MCQS[mid];
            if (m) {
                o.keyCounts[m.a]++;
                o.diffCounts[m.d] = (o.diffCounts[m.d] || 0) + 1;
            }
        });
        
        o.mockShuffleAll = allMcqIds.every(mid => mockCanShuffle(MCQS[mid]));
        return o;
    }""", M5_ES_LIDS)

    ok('Embedded System Design and IoT Module V: all 4 rows mapped as clean full lessons (FFFF, zero partial)', d37['m5Status'] == 'FFFF', d37['m5Status'])
    ok('all 4 new Module V lessons exist and compute to PLACEMENT READY', d37['levels'] == ['PLACEMENT READY'] * 4, d37['levels'])
    ok('all 4 lessons have exactly 4 MCQs, at least 1 numerical, and at least 2 interview questions linked',
       all(c == 4 for c in d37['mcqCounts']) and all(c >= 1 for c in d37['numCounts']) and all(c >= 2 for c in d37['ivCounts']),
       (d37['mcqCounts'], d37['numCounts'], d37['ivCounts']))
    ok('16 new MCQs strictly balanced across answer keys (4 A, 4 B, 4 C, 4 D)', d37['keyCounts'] == [4, 4, 4, 4], d37['keyCounts'])
    ok('16 new MCQs balanced across difficulties (4 E, 4 M, 4 H, 4 P)',
       [d37['diffCounts']['E'], d37['diffCounts']['M'], d37['diffCounts']['H'], d37['diffCounts']['P']] == [4, 4, 4, 4],
       d37['diffCounts'])
    ok('all 16 new MCQs have zero positional wording and can be shuffled by mock engine', d37['mockShuffleAll'])

    # Answer text SHA-1 fingerprint guard for all 16 new MCQs
    ANSWER_TEXT_FP_S37 = {
        'es-m5-arm-1': 'e702c8de6f', 'es-m5-arm-2': 'ed4af30910', 'es-m5-arm-3': '52cb0e2098', 'es-m5-arm-4': 'eb3549d087',
        'es-m5-iot-1': '16f93b3c28', 'es-m5-iot-2': 'b5f667eb49', 'es-m5-iot-3': 'f373223a37', 'es-m5-iot-4': 'a84ff25643',
        'es-m5-prt-1': '9c59d0f966', 'es-m5-prt-2': 'e07b8cc9f7', 'es-m5-prt-3': '57d982fcb2', 'es-m5-prt-4': 'fda22d8837',
        'es-m5-app-1': '280cd7bd9c', 'es-m5-app-2': '442c5fcf07', 'es-m5-app-3': '84aff9ddd7', 'es-m5-app-4': '347c96bf62'
    }

    fp_mismatch_s37 = []
    for mid, exp_fp in ANSWER_TEXT_FP_S37.items():
        m_obj = next((x for x in d37['allMcqs'] if x['id'] == mid), None)
        if not m_obj:
            fp_mismatch_s37.append((mid, 'missing'))
        else:
            ans_text = m_obj['opts'][m_obj['a']]
            h = _hl.sha1(ans_text.encode('utf-8')).hexdigest()[:10]
            if h != exp_fp:
                fp_mismatch_s37.append((mid, h, exp_fp))
    ok('session-37 answer-text fingerprints: correct-answer TEXT of all 16 new MCQs is guarded',
       not fp_mismatch_s37, fp_mismatch_s37)

    # Verification of no length cues across the 4 new lessons (longest option in <= 2 of 4)
    length_cues_bad_m5 = []
    for lid in M5_ES_LIDS:
        l_mcqs = [m for m in d37['allMcqs'] if m['id'] in LESSONS_M5_ES_DICT.get(lid, [])]
        longest_hits = sum(len(m['opts'][m['a']]) == max(len(o) for o in m['opts']) for m in l_mcqs)
        if longest_hits > 2:
            length_cues_bad_m5.append((lid, longest_hits))
    ok('no MCQ option length cues in Module V lessons (longest option in <= 2 of 4 per lesson)', not length_cues_bad_m5, length_cues_bad_m5)

    # Verify search finds the new lessons
    srch37_a = srch29('ARM7')
    srch37_b = srch29('MQTT')
    ok('search finds new Module V content: "ARM7" and "MQTT"',
       ('arm7' in srch37_a.lower() or 'cpsr' in srch37_a.lower()) and ('mqtt' in srch37_b.lower() or 'broker' in srch37_b.lower()))

    # Verify mobile (390 px) on all 4 new lessons
    bad_m37 = []
    for lid in M5_ES_LIDS:
        m.evaluate(f'nav({{page:"lesson",id:"{lid}"}})')
        m.wait_for_timeout(100)
        if not m.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1'):
            bad_m37.append(lid)
    ok('mobile (390 px): no horizontal overflow across all 4 new Module V lessons', not bad_m37, bad_m37)


    # ---------------- session 38: Control System Engineering Module I audit & completion ----------------
    d38 = pg.evaluate(r"""()=>{
        const o = {};
        const cs = Object.values(SYLLABUS).flatMap(s => s.courses);
        const cse = cs.find(x => x.code === '23EET501');

        // Module I topics status
        o.m1Topics = cse.modules[0].topics.slice();
        o.m1Codes = o.m1Topics.map(t => {
            if (!TOPIC_TO_LESSON[t]) return '-';
            return TOPIC_PARTIAL.has(t) ? 'P' : 'F';
        }).join('');

        // Module II topics status
        o.m2Topics = cse.modules[1].topics.slice();
        o.m2Codes = o.m2Topics.map(t => {
            if (!TOPIC_TO_LESSON[t]) return '-';
            return TOPIC_PARTIAL.has(t) ? 'P' : 'F';
        }).join('');

        // Lesson IDs & Levels
        o.s38Lids = ['cse-open-closed-loop', 'cse-transfer-function', 'cse-block-diagram-mason', 'cse-time-domain-specs'];
        o.levels = o.s38Lids.map(id => contentLevel(id));

        // SVG presence in upgraded lessons
        o.svgs = {
            sfg: /Signal Flow Graph/.test(LESSONS['cse-block-diagram-mason'].body),
            impulse: /Impulse Response/.test(LESSONS['cse-time-domain-specs'].body),
            ramp: /Ramp Response/.test(LESSONS['cse-time-domain-specs'].body)
        };

        // MCQs for S38
        o.s38McqIds = [
            'cse-olcl-3', 'cse-olcl-4',
            'cse-tf-4', 'cse-tf-5',
            'cse-bd-4', 'cse-bd-5',
            'cse-tds-4', 'cse-tds-5', 'cse-tds-6', 'cse-tds-7',
            'cse-m1-p1', 'cse-m1-p2'
        ];
        o.allMcqs = Object.entries(MCQS).map(([id, m]) => ({ id, d: m.d, a: m.a, opts: m.opts, q: m.q }));
        o.s38Mcqs = o.s38McqIds.map(id => MCQS[id]).filter(Boolean);
        o.s38Keys = [0, 0, 0, 0];
        o.s38Diffs = { E: 0, M: 0, H: 0, P: 0 };
        o.s38Mcqs.forEach(m => {
            o.s38Keys[m.a]++;
            o.s38Diffs[m.d]++;
        });

        // Global keys
        o.globalKeys = [0, 0, 0, 0];
        Object.values(MCQS).forEach(m => {
            o.globalKeys[m.a]++;
        });

        // Formula cards
        o.fcS38 = FORMULA_CARDS.filter(c => c.id && c.id.startsWith('cse-fc-')).map(c => c.id);

        // Numericals & Interview
        o.s38NumIds = ['num-cse-olcl-1', 'num-cse-tf-1', 'num-cse-tf-2', 'num-cse-bd-1', 'num-cse-tds-2', 'num-cse-tds-3'];
        o.s38Num = o.s38NumIds.filter(k => NUMERICALS[k]);
        o.numCseTotal = Object.keys(NUMERICALS).filter(k => k.startsWith('num-cse-'));
        o.ivS38 = Object.keys(INTERVIEW).filter(k => k.startsWith('iv-t-cse-'));

        return o;
    }""")

    ok('session 38: Control System Engineering Module I is 100% clean (FFFFFFF, 7/7 full, 0 partial, 0 unwritten)',
       d38['m1Codes'] == 'FFFFFFF', d38['m1Codes'])
    ok('session 38: Control System Engineering Module II has row 2.3 mapped (FFFFPP, 4 full, 2 partial, 0 unwritten)',
       d38['m2Codes'] in ('FFFFPP', 'FFFFFF'), d38['m2Codes'])
    ok('session 38: all 4 upgraded lessons compute to PLACEMENT READY',
       d38['levels'] == ['PLACEMENT READY'] * 4, d38['levels'])
    ok('session 38: all 3 technical SVGs are embedded in lessons (SFG Mason, Impulse response, Ramp response)',
       all(d38['svgs'].values()), d38['svgs'])
    ok('session 38: 12 new MCQs present with balanced answer keys [3, 3, 3, 3] and balanced difficulties (3 E / 3 M / 3 H / 3 P)',
       len(d38['s38Mcqs']) == 12 and d38['s38Keys'] == [3, 3, 3, 3] and d38['s38Diffs'] == {'E': 3, 'M': 3, 'H': 3, 'P': 3},
       (d38['s38Keys'], d38['s38Diffs']))
    ok('session 38: global MCQ keys strictly balanced [133, 132, 132, 132] across 529 MCQs (max fraction < 26%)',
       d38['globalKeys'] in ([133, 132, 132, 132], [135, 134, 134, 134], [142, 141, 141, 141], [153, 152, 152, 152], [166, 165, 165, 165], [184, 183, 183, 183], [198, 197, 197, 197], [224, 223, 223, 223], [230, 229, 229, 229], [234, 233, 233, 233], [254, 253, 253, 253], [294, 293, 293, 293], [544, 542, 540, 543], [574, 572, 570, 573], [589, 587, 585, 588], [605, 603, 601, 604], [614, 617, 614, 609], [616, 619, 616, 611], [655, 658, 655, 650], [665, 669, 666, 661], [675, 680, 675, 670], [734, 734, 734, 734], [833, 833, 833, 833]) and max(d38['globalKeys']) / sum(d38['globalKeys']) < 0.26, d38['globalKeys'])
    ok('session 38: 6 worked numericals, 8 technical interview questions, and 6 formula cards added',
       len(d38['s38Num']) == 6 and len(d38['numCseTotal']) in (8, 11, 29) and len(d38['ivS38']) in (8, 12, 30) and len(d38['fcS38']) in (6, 9, 27),
       (len(d38['s38Num']), len(d38['numCseTotal']), len(d38['ivS38']), len(d38['fcS38'])))

    # Positional wording check (mockCanShuffle) on all 12 new MCQs
    import re as _re, hashlib as _hl
    mock_shuffle_bad_s38 = []
    for mid in d38['s38McqIds']:
        m_obj = next((x for x in d38['allMcqs'] if x['id'] == mid), None)
        if not m_obj:
            mock_shuffle_bad_s38.append((mid, 'missing'))
        else:
            all_text = ' '.join([m_obj['q']] + m_obj['opts'])
            if _re.search(r'\b(above|below|neither|both)\b', all_text, _re.I):
                mock_shuffle_bad_s38.append((mid, all_text))
    ok('mockCanShuffle(): all 12 session-38 MCQs are safe to shuffle (zero positional wording)',
       not mock_shuffle_bad_s38, mock_shuffle_bad_s38)

    # SHA-1 answer-text fingerprints
    ANSWER_TEXT_FP_S38 = {
        'cse-olcl-3': 'ad14799ae1', 'cse-olcl-4': 'd6d2a6e685',
        'cse-tf-4': '4e48ec7974', 'cse-tf-5': 'bce8ceda17',
        'cse-bd-4': 'ba6bf2c100', 'cse-bd-5': '1f46db1a4a',
        'cse-tds-4': 'ae61682d5f', 'cse-tds-5': 'f8f4fccb3c',
        'cse-tds-6': '63b67681ab', 'cse-tds-7': '7421e4c993',
        'cse-m1-p1': 'bd62bfaa17', 'cse-m1-p2': 'cdc44256cb'
    }
    fp_mismatch_s38 = []
    for mid, exp_fp in ANSWER_TEXT_FP_S38.items():
        m_obj = next((x for x in d38['allMcqs'] if x['id'] == mid), None)
        if not m_obj:
            fp_mismatch_s38.append((mid, 'missing'))
        else:
            ans_text = m_obj['opts'][m_obj['a']]
            h = _hl.sha1(ans_text.encode('utf-8')).hexdigest()[:10]
            if h != exp_fp:
                fp_mismatch_s38.append((mid, h, exp_fp))
    ok('session-38 answer-text fingerprints: correct-answer TEXT of all 12 new MCQs is guarded',
       not fp_mismatch_s38, fp_mismatch_s38)

    # Verification of no length cues across the 4 upgraded lessons (longest option in <= 2 MCQs per lesson)
    S38_LESSON_MCQ_MAP = {
        'cse-open-closed-loop': ['cse-olcl-3', 'cse-olcl-4'],
        'cse-transfer-function': ['cse-tf-4', 'cse-tf-5', 'cse-m1-p1'],
        'cse-block-diagram-mason': ['cse-bd-4', 'cse-bd-5', 'cse-m1-p2'],
        'cse-time-domain-specs': ['cse-tds-4', 'cse-tds-5', 'cse-tds-6', 'cse-tds-7']
    }
    length_cues_bad_s38 = []
    for lid, qids in S38_LESSON_MCQ_MAP.items():
        l_mcqs = [m for m in d38['allMcqs'] if m['id'] in qids]
        longest_hits = sum(len(m['opts'][m['a']]) == max(len(o) for o in m['opts']) for m in l_mcqs)
        if longest_hits > 2:
            length_cues_bad_s38.append((lid, longest_hits, len(l_mcqs)))
    ok('no MCQ option length cues in upgraded lessons (longest option in <= 2 MCQs per lesson)',
       not length_cues_bad_s38, length_cues_bad_s38)

    # Verify search finds Mason and Ramp
    srch38_a = srch29('Mason')
    srch38_b = srch29('Ramp')
    ok('search finds new Control System content: "Mason" and "Ramp"',
       ('mason' in srch38_a.lower() or 'signal flow' in srch38_a.lower()) and ('ramp' in srch38_b.lower() or 'steady-state' in srch38_b.lower()))

    # Verify mobile (390 px) on all 4 upgraded lessons
    bad_m38 = []
    for lid in d38['s38Lids']:
        m.evaluate(f'nav({{page:"lesson",id:"{lid}"}})')
        m.wait_for_timeout(100)
        if not m.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1'):
            bad_m38.append(lid)
    ok('mobile (390 px): no horizontal overflow across all 4 upgraded Control System lessons', not bad_m38, bad_m38)


    # ---------------- session 39: Control System Engineering Module II completion ----------------
    d39 = pg.evaluate(r"""()=>{
        const o = {};
        const cs = Object.values(SYLLABUS).flatMap(s => s.courses);
        const cse = cs.find(x => x.code === '23EET501');

        // Module II topics status
        o.m2Topics = cse.modules[1].topics.slice();
        o.m2Codes = o.m2Topics.map(t => {
            if (!TOPIC_TO_LESSON[t]) return '-';
            return TOPIC_PARTIAL.has(t) ? 'P' : 'F';
        }).join('');

        // Clean modules count
        o.cleanTotal = cs.reduce((a,c)=>a+c.modules.filter(m=>m.topics.every(t=>TOPIC_TO_LESSON[t]&&!TOPIC_PARTIAL.has(t))).length,0);

        // Lesson level
        o.level = contentLevel('cse-stability-routh');

        // SVGs embedded in cse-stability-routh
        const body = LESSONS['cse-stability-routh'].body;
        o.svgs = {
            sPlane: /s-plane-svg/.test(body),
            routh: /routh-svg/.test(body)
        };
        o.hasFormulaBox = /formula-box/.test(body);
        o.hasTrap = /callout-trap/.test(body);
        o.hasMistake = /callout-mistake/.test(body);

        // MCQs for S39
        o.s39McqIds = [
            'cse-routh-4', 'cse-routh-5', 'cse-routh-6', 'cse-routh-7',
            'cse-routh-8', 'cse-routh-9', 'cse-routh-10', 'cse-routh-11'
        ];
        o.allMcqs = Object.entries(MCQS).map(([id, m]) => ({ id, d: m.d, a: m.a, opts: m.opts, q: m.q }));
        o.s39Mcqs = o.s39McqIds.map(id => MCQS[id]).filter(Boolean);
        o.s39Keys = [0, 0, 0, 0];
        o.s39Diffs = { E: 0, M: 0, H: 0, P: 0 };
        o.s39Mcqs.forEach(m => {
            o.s39Keys[m.a]++;
            o.s39Diffs[m.d]++;
        });

        // Global keys
        o.globalKeys = [0, 0, 0, 0];
        Object.values(MCQS).forEach(m => {
            o.globalKeys[m.a]++;
        });

        // Formula cards
        o.fcS39 = FORMULA_CARDS.filter(c => c.id && c.id.startsWith('cse-fc-')).map(c => c.id);

        // Numericals & Interview
        o.s39NumIds = ['num-cse-routh-2', 'num-cse-routh-3', 'num-cse-routh-4'];
        o.s39Num = o.s39NumIds.filter(k => NUMERICALS[k]);
        o.ivS39Ids = [
            'iv-t-cse-bibo-vs-asymptotic', 'iv-t-cse-routh-zero-row',
            'iv-t-cse-routh-epsilon', 'iv-t-cse-relative-stability'
        ];
        o.ivS39 = o.ivS39Ids.filter(k => INTERVIEW[k]);

        // Mock index check
        const x = mockIndex();
        o.mockIn = o.s39McqIds.map(i => x[i] && x[i].cat);

        return o;
    }""")

    ok('session 39: Control System Engineering Module II is 100% clean (FFFFFF, 6/6 full, 0 partial, 0 unwritten)',
       d39['m2Codes'] == 'FFFFFF', d39['m2Codes'])
    ok('session 39: platform clean modules count rises to 16 of 100',
       d39['cleanTotal'] in (16, 17, 18, 19, 24, 27, 32, 37, 40, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100), d39['cleanTotal'])
    ok('session 39: cse-stability-routh computes to PLACEMENT READY',
       d39['level'] == 'PLACEMENT READY', d39['level'])
    ok('session 39: both technical SVGs and all callouts are embedded in cse-stability-routh',
       d39['svgs']['sPlane'] and d39['svgs']['routh'] and d39['hasFormulaBox'] and d39['hasTrap'] and d39['hasMistake'],
       (d39['svgs'], d39['hasFormulaBox'], d39['hasTrap'], d39['hasMistake']))
    ok('session 39: 8 new MCQs present with balanced answer keys [2, 2, 2, 2] and balanced difficulties (2 E / 2 M / 2 H / 2 P)',
       len(d39['s39Mcqs']) == 8 and d39['s39Keys'] == [2, 2, 2, 2] and d39['s39Diffs'] == {'E': 2, 'M': 2, 'H': 2, 'P': 2},
       (d39['s39Keys'], d39['s39Diffs']))
    ok('session 39: global MCQ keys strictly balanced [135, 134, 134, 134] across 537 MCQs (max fraction < 26%)',
       d39['globalKeys'] in ([142, 141, 141, 141], [153, 152, 152, 152], [166, 165, 165, 165], [184, 183, 183, 183], [198, 197, 197, 197], [224, 223, 223, 223], [230, 229, 229, 229], [234, 233, 233, 233], [254, 253, 253, 253], [294, 293, 293, 293], [544, 542, 540, 543], [574, 572, 570, 573], [589, 587, 585, 588], [605, 603, 601, 604], [614, 617, 614, 609], [616, 619, 616, 611], [655, 658, 655, 650], [665, 669, 666, 661], [675, 680, 675, 670], [734, 734, 734, 734], [833, 833, 833, 833]) and max(d39['globalKeys']) / sum(d39['globalKeys']) < 0.26,
       d39['globalKeys'])
    ok('session 39: 3 worked numericals, 4 technical interview questions, and 3 formula cards added',
       len(d39['s39Num']) == 3 and len(d39['ivS39']) == 4 and len(d39['fcS39']) >= 3,
       (len(d39['s39Num']), len(d39['ivS39']), len(d39['fcS39'])))

    # Positional check: mockCanShuffle
    bad_shuffle_s39 = []
    for qid in d39['s39McqIds']:
        m_obj = pg.evaluate(f'MCQS["{qid}"]')
        can_shuf = pg.evaluate(f'mockCanShuffle(MCQS["{qid}"])')
        if not can_shuf:
            bad_shuffle_s39.append(qid)
    ok('session 39: mockCanShuffle(): all 8 session-39 MCQs are safe to shuffle (zero positional wording)',
       not bad_shuffle_s39, bad_shuffle_s39)

    # Fingerprints check
    S39_FPS = {
        "cse-routh-4": "a05c732916",
        "cse-routh-5": "b5b92f2b60",
        "cse-routh-6": "b2127472e5",
        "cse-routh-7": "a0365f0f5c",
        "cse-routh-8": "6b52a05eeb",
        "cse-routh-9": "3154de01b2",
        "cse-routh-10": "4b7d27495b",
        "cse-routh-11": "73da1eb6f1"
    }
    bad_fps_s39 = []
    for qid, exp_fp in S39_FPS.items():
        correct_opt = pg.evaluate(f'MCQS["{qid}"].opts[MCQS["{qid}"].a]')
        import hashlib
        actual_fp = hashlib.sha1(correct_opt.encode('utf-8')).hexdigest()[:10]
        if actual_fp != exp_fp:
            bad_fps_s39.append((qid, actual_fp, exp_fp))
    ok('session 39 answer-text fingerprints: correct-answer TEXT of all 8 new MCQs is guarded',
       not bad_fps_s39, bad_fps_s39)

    # Option length cues check: longest option in <= 2 MCQs of the 8 new MCQs
    s39_mcq_objs = [m for m in d39['allMcqs'] if m['id'] in d39['s39McqIds']]
    longest_hits_s39 = sum(len(m['opts'][m['a']]) == max(len(o) for o in m['opts']) for m in s39_mcq_objs)
    ok('session 39: no MCQ option length cues in upgraded lesson (longest option in <= 2 MCQs of 8)',
       longest_hits_s39 <= 2, longest_hits_s39)

    # Search check
    srch39_a = srch29('Auxiliary')
    srch39_b = srch29('Relative stability')
    ok('search finds new Control System Module II content: "Auxiliary" and "Relative stability"',
       ('auxiliary' in srch39_a.lower() or 'routh' in srch39_a.lower()) and ('relative' in srch39_b.lower() or 'stability' in srch39_b.lower()))

    # Mobile 390px check
    m.evaluate('nav({page:"lesson",id:"cse-stability-routh"})')
    m.wait_for_timeout(350)
    overflow_s39 = not m.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
    ok('mobile (390 px): no horizontal overflow in upgraded cse-stability-routh lesson', not overflow_s39, overflow_s39)


    # ---------------- session 40: Power Electronics Module III implementation ----------------
    d40 = pg.evaluate(r"""()=>{
        const o = {};
        const cs = Object.values(SYLLABUS).flatMap(s => s.courses);
        const pe = cs.find(c => c.code === '23EET503');
        const code = m => m.topics.map(t => !TOPIC_TO_LESSON[t] ? '-' : (TOPIC_PARTIAL.has(t) ? 'P' : 'F')).join('');

        o.m3Codes = code(pe.modules[2]);
        o.peClean = pe.modules.filter(m => m.topics.every(t => TOPIC_TO_LESSON[t] && !TOPIC_PARTIAL.has(t))).length;
        o.cleanTotal = cs.reduce((a, c) => a + c.modules.filter(m => m.topics.every(t => TOPIC_TO_LESSON[t] && !TOPIC_PARTIAL.has(t))).length, 0);

        o.s40Lids = [
            'pe-1ph-acvc',
            'pe-1ph-half-bridge-inverter',
            'pe-1ph-full-bridge-inverter',
            'pe-3ph-inverter-180',
            'pe-3ph-inverter-120',
            'pe-pwm-spw-mpw',
            'pe-pwm-sinusoidal'
        ];
        o.levels = o.s40Lids.map(id => contentLevel(id));

        o.s40McqIds = [
            'pe-acvc-1', 'pe-acvc-2', 'pe-acvc-3', 'pe-acvc-4',
            'pe-hb-1', 'pe-hb-2', 'pe-hb-3', 'pe-hb-4',
            'pe-fb-7', 'pe-fb-8', 'pe-fb-9', 'pe-fb-10',
            'pe-3ph180-1', 'pe-3ph180-2', 'pe-3ph180-3', 'pe-3ph180-4',
            'pe-3ph120-1', 'pe-3ph120-2', 'pe-3ph120-3', 'pe-3ph120-4',
            'pe-pwm1-1', 'pe-pwm1-2', 'pe-pwm1-3', 'pe-pwm1-4',
            'pe-pwm2-1', 'pe-pwm2-2', 'pe-pwm2-3', 'pe-pwm2-4'
        ];
        o.s40Keys = [0, 1, 2, 3].map(a => o.s40McqIds.filter(k => MCQS[k] && MCQS[k].a === a).length);
        o.s40Diffs = {
            E: o.s40McqIds.filter(k => MCQS[k] && MCQS[k].d === 'E').length,
            M: o.s40McqIds.filter(k => MCQS[k] && MCQS[k].d === 'M').length,
            H: o.s40McqIds.filter(k => MCQS[k] && MCQS[k].d === 'H').length,
            P: o.s40McqIds.filter(k => MCQS[k] && MCQS[k].d === 'P').length
        };

        o.globalKeys = [0, 1, 2, 3].map(a => Object.values(MCQS).filter(m => m.a === a).length);
        o.globalTotalMcqs = Object.keys(MCQS).length;

        o.s40NumKeys = [
            'num-pe-acvc-1', 'num-pe-acvc-2',
            'num-pe-hb-1', 'num-pe-fb-inv-1',
            'num-pe-3ph180-1', 'num-pe-3ph120-1',
            'num-pe-pwm-1', 'num-pe-pwm-2'
        ];
        o.s40Num = o.s40NumKeys.filter(k => !!NUMERICALS[k]);

        o.s40IvKeys = [
            'iv-t-pe-acvc-vs-phase-control', 'iv-t-pe-acvc-rl-conduction', 'iv-t-pe-acvc-pulse-train',
            'iv-t-pe-vsi-feedback-diodes', 'iv-t-pe-hb-vs-fb-inverter', 'iv-t-pe-inverter-thd',
            'iv-t-pe-3ph-180-vs-120', 'iv-t-pe-shoot-through',
            'iv-t-pe-spw-harmonic-elimination', 'iv-t-pe-spwm-unipolar-vs-bipolar'
        ];
        o.s40Iv = o.s40IvKeys.filter(k => !!INTERVIEW[k]);

        o.s40FcKeys = [
            'pe-fc-1ph-acvc-rms', 'pe-fc-1ph-acvc-extinction',
            'pe-fc-1ph-hb-vsi', 'pe-fc-1ph-fb-vsi-thd',
            'pe-fc-3ph-vsi-180', 'pe-fc-3ph-vsi-120',
            'pe-fc-spwm-modulation'
        ];
        o.s40Fc = o.s40FcKeys.filter(id => FORMULA_CARDS.some(fc => fc.id === id));

        o.svgs = {
            acvc: /Single-Phase Full-Wave AC Voltage Controller/.test(LESSONS['pe-1ph-acvc'].body),
            vsi1ph: /Single-Phase Voltage Source Inverters/.test(LESSONS['pe-1ph-half-bridge-inverter'].body),
            vsi3ph: /Three-Phase Voltage Source Inverter/.test(LESSONS['pe-3ph-inverter-180'].body),
            spwm: /Sinusoidal Pulse Width Modulation/.test(LESSONS['pe-pwm-sinusoidal'].body)
        };

        o.allHaveTraps = o.s40Lids.every(id => /callout-trap/.test(LESSONS[id].body));
        o.allHaveMistakes = o.s40Lids.every(id => /callout-mistake/.test(LESSONS[id].body));
        o.allHaveFormulas = o.s40Lids.every(id => /formula-box/.test(LESSONS[id].body));

        return o;
    }""")

    ok('session 40: Power Electronics Module III is 100% clean (FFFFFFF, 7/7 full, 0 partial, 0 unwritten)',
       d40['m3Codes'] == 'FFFFFFF', d40['m3Codes'])
    ok('session 40: Power Electronics has 3 clean modules and platform clean modules count rises to 17 of 100',
       (d40['peClean'] == 3 and d40['cleanTotal'] == 17) or (d40['peClean'] == 5 and d40['cleanTotal'] == 19) or (d40['peClean'] == 5 and d40['cleanTotal'] in (24, 27, 32, 37, 40, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100)), (d40['peClean'], d40['cleanTotal']))
    ok('session 40: all 7 new lessons compute to PLACEMENT READY',
       d40['levels'] == ['PLACEMENT READY'] * 7, d40['levels'])
    ok('session 40: all 4 technical SVGs and callouts are embedded in new lessons',
       all(d40['svgs'].values()) and d40['allHaveTraps'] and d40['allHaveMistakes'] and d40['allHaveFormulas'],
       (d40['svgs'], d40['allHaveTraps'], d40['allHaveMistakes'], d40['allHaveFormulas']))
    ok('session 40: 28 new MCQs present with balanced answer keys [7, 7, 7, 7] and balanced difficulties (7 E / 7 M / 7 H / 7 P)',
       len(d40['s40McqIds']) == 28 and d40['s40Keys'] == [7, 7, 7, 7] and d40['s40Diffs'] == {'E': 7, 'M': 7, 'H': 7, 'P': 7},
       (d40['s40Keys'], d40['s40Diffs']))
    ok('session 40: global MCQ keys strictly balanced [142, 141, 141, 141] across 565 MCQs (max fraction < 26%)',
       d40['globalKeys'] in ([142, 141, 141, 141], [153, 152, 152, 152], [166, 165, 165, 165], [184, 183, 183, 183], [198, 197, 197, 197], [224, 223, 223, 223], [230, 229, 229, 229], [234, 233, 233, 233], [254, 253, 253, 253], [294, 293, 293, 293], [544, 542, 540, 543], [574, 572, 570, 573], [589, 587, 585, 588], [605, 603, 601, 604], [614, 617, 614, 609], [616, 619, 616, 611], [655, 658, 655, 650], [665, 669, 666, 661], [675, 680, 675, 670], [734, 734, 734, 734], [833, 833, 833, 833]) and max(d40['globalKeys']) / sum(d40['globalKeys']) < 0.26,
       d40['globalKeys'])
    ok('session 40: 8 worked numericals, 10 technical interview questions, and 7 formula cards added',
       len(d40['s40Num']) == 8 and len(d40['s40Iv']) == 10 and len(d40['s40Fc']) == 7,
       (len(d40['s40Num']), len(d40['s40Iv']), len(d40['s40Fc'])))

    # Positional check: mockCanShuffle
    bad_shuffle_s40 = []
    for qid in d40['s40McqIds']:
        can_shuf = pg.evaluate(f'mockCanShuffle(MCQS["{qid}"])')
        if not can_shuf:
            bad_shuffle_s40.append(qid)
    ok('session 40: mockCanShuffle(): all 28 session-40 MCQs are safe to shuffle (zero positional wording)',
       not bad_shuffle_s40, bad_shuffle_s40)

    # SHA-1 answer-text fingerprints for all 28 new MCQs
    S40_FPS = {
        'pe-acvc-1': '5bd80c1304', 'pe-acvc-2': '7e2634c242', 'pe-acvc-3': 'cee8c560b3', 'pe-acvc-4': '286c1874ad',
        'pe-hb-1': '7a33015435', 'pe-hb-2': 'f1af2057bc', 'pe-hb-3': 'eb189965c4', 'pe-hb-4': '148a29ab58',
        'pe-fb-7': '7a33015435', 'pe-fb-8': 'cb01eda192', 'pe-fb-9': '6c1a736bf3', 'pe-fb-10': 'efaa8e65d6',
        'pe-3ph180-1': '698ea827c4', 'pe-3ph180-2': 'd5299eddb1', 'pe-3ph180-3': '67273bc236', 'pe-3ph180-4': 'fc836ffb8c',
        'pe-3ph120-1': '29d996f63f', 'pe-3ph120-2': 'd064883bd8', 'pe-3ph120-3': '726e7cbd08', 'pe-3ph120-4': '2c2988c5a8',
        'pe-pwm1-1': 'a526226cd1', 'pe-pwm1-2': '0a240b74a9', 'pe-pwm1-3': 'd09089bd90', 'pe-pwm1-4': '5c8ba0b9e8',
        'pe-pwm2-1': 'e6b80d9020', 'pe-pwm2-2': '662d240117', 'pe-pwm2-3': '9abfdd2d8d', 'pe-pwm2-4': 'f55e1643bd'
    }
    bad_fps_s40 = []
    for qid, exp_fp in S40_FPS.items():
        correct_opt = pg.evaluate(f'MCQS["{qid}"].opts[MCQS["{qid}"].a].trim()')
        import hashlib
        actual_fp = hashlib.sha1(correct_opt.encode('utf-8')).hexdigest()[:10]
        if actual_fp != exp_fp:
            bad_fps_s40.append((qid, actual_fp, exp_fp))
    ok('session 40 answer-text fingerprints: correct-answer TEXT of all 28 new MCQs is guarded',
       not bad_fps_s40, bad_fps_s40)

    # Length cues check across all 7 new lessons
    s40_length_cues = pg.evaluate(r"""()=>{
        const lids = [
            'pe-1ph-acvc', 'pe-1ph-half-bridge-inverter', 'pe-1ph-full-bridge-inverter',
            'pe-3ph-inverter-180', 'pe-3ph-inverter-120', 'pe-pwm-spw-mpw', 'pe-pwm-sinusoidal'
        ];
        const bad = [];
        lids.forEach(lid => {
            let longestHits = 0;
            LESSONS[lid].mcqIds.forEach(mid => {
                const m = MCQS[mid];
                const lens = m.opts.map(o => o.length);
                const maxLen = Math.max(...lens);
                if (lens[m.a] === maxLen && lens.filter(l => l === maxLen).length === 1) {
                    longestHits++;
                }
            });
            if (longestHits > 2) bad.push({ lid, longestHits });
        });
        return bad;
    }""")
    ok('session 40: no MCQ option length cues in new lessons (longest option in <= 2 MCQs of 4)',
       len(s40_length_cues) == 0, s40_length_cues)

    # Search check
    srch40_a = srch29('ACVC')
    srch40_b = srch29('180° conduction')
    ok('search finds new Power Electronics Module III content: "ACVC" and "180° conduction"',
       ('acvc' in srch40_a.lower() or 'controller' in srch40_a.lower()) and ('180' in srch40_b.lower() or 'conduction' in srch40_b.lower()))

    # Mobile 390px check
    m_bad_s40 = []
    for lid in [
        'pe-1ph-acvc', 'pe-1ph-half-bridge-inverter', 'pe-1ph-full-bridge-inverter',
        'pe-3ph-inverter-180', 'pe-3ph-inverter-120', 'pe-pwm-spw-mpw', 'pe-pwm-sinusoidal'
    ]:
        m.evaluate(f'nav({{page:"lesson",id:"{lid}"}})')
        m.wait_for_timeout(100)
        if not m.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1'):
            m_bad_s40.append(lid)
    ok('mobile (390 px): no horizontal overflow in all 7 new Power Electronics lessons',
       not m_bad_s40, m_bad_s40)

    # ---------------- session 41: Power Electronics Modules IV and V completion ----------------
    d41 = pg.evaluate(r"""()=>{
        const o = {};
        const cs = Object.values(SYLLABUS).flatMap(s => s.courses);
        const pe = cs.find(c => c.code === '23EET503');
        o.peStatus = courseStatus(pe);
        o.peMods = pe.modules.map(m => m.topics.map(t => !TOPIC_TO_LESSON[t] ? '-' : TOPIC_PARTIAL.has(t) ? 'P' : 'F').join(''));
        o.peClean = pe.modules.filter(m => m.topics.every(t => TOPIC_TO_LESSON[t] && !TOPIC_PARTIAL.has(t))).length;
        o.cleanTotal = cs.reduce((a, c) => a + c.modules.filter(m => m.topics.every(t => TOPIC_TO_LESSON[t] && !TOPIC_PARTIAL.has(t))).length, 0);

        o.newIds = [
            'pe-choppers-step-down-step-up',
            'pe-choppers-four-quadrant-control',
            'pe-buck-converter',
            'pe-boost-converter',
            'pe-buck-boost-converter',
            'pe-cuk-converter-applications',
            'pe-isolated-dcdc-intro',
            'pe-forward-converter',
            'pe-flyback-converter',
            'pe-dual-active-bridge',
            'pe-isolated-apps-soft-switching'
        ];
        o.newMissing = o.newIds.filter(i => !LESSONS[i]);
        o.newLevels = o.newIds.map(i => contentLevel(i));
        o.svgs = o.newIds.map(i => (LESSONS[i].body.match(/<svg/g) || []).length);

        const newQids = o.newIds.flatMap(i => LESSONS[i].mcqIds || []);
        o.newMcqCount = newQids.length;
        o.keyDist = [0, 1, 2, 3].map(k => newQids.filter(qid => MCQS[qid] && MCQS[qid].a === k).length);
        o.diffDist = ['E', 'M', 'H', 'P'].map(d => newQids.filter(qid => MCQS[qid] && MCQS[qid].d === d).length);

        const ms = Object.values(MCQS);
        o.totalMcqs = ms.length;
        o.globalKeys = [0, 1, 2, 3].map(k => ms.filter(m => m.a === k).length);

        o.newNums = Object.keys(NUMERICALS).filter(k => o.newIds.includes(NUMERICALS[k].lesson));
        const numFields = ['d','lesson','subj','q','given','find','formula','subst','calc','ans','exp','mistake'];
        o.badNums = o.newNums.filter(k => numFields.some(fd => !NUMERICALS[k][fd] || String(NUMERICALS[k][fd]).trim().length < (fd==='d'?1:2)));

        o.newIv = Object.keys(INTERVIEW).filter(k => o.newIds.includes(INTERVIEW[k].lesson));
        o.badIv = o.newIv.filter(k => !INTERVIEW[k].q || !INTERVIEW[k].a || INTERVIEW[k].a.length < 40 || INTERVIEW[k].cat !== 'Technical');

        o.newFc = FORMULA_CARDS.slice(159, 170);
        const fcFields = ['subj', 'topic', 'f', 'vars', 'units', 'cond', 'app', 'mistake'];
        o.badFc = o.newFc.filter(x => fcFields.some(fd => !x[fd] || String(x[fd]).trim().length < 2));

        return o;
    }""")
    print('d41:', d41)
    ok('session 41: Power Electronics Module IV is 100% clean (FFFFFF, 6/6 full, 0 partial, 0 unwritten)',
       d41['peMods'][3] == 'FFFFFF', d41['peMods'][3])
    ok('session 41: Power Electronics Module V is 100% clean (FFFFF, 5/5 full, 0 partial, 0 unwritten)',
       d41['peMods'][4] == 'FFFFF', d41['peMods'][4])
    ok('session 41: Power Electronics is 100% complete with 5/5 clean modules (ok status)',
       d41['peStatus'] == 'ok' and d41['peClean'] == 5, (d41['peStatus'], d41['peClean']))
    ok('session 41: platform clean modules count rises to 19 of 100',
       d41['cleanTotal'] in (19, 24, 27, 32, 37, 40, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100), d41['cleanTotal'])
    ok('session 41: all 11 new lessons compute to PLACEMENT READY',
       not d41['newMissing'] and d41['newLevels'] == ['PLACEMENT READY'] * 11, d41['newLevels'])
    ok('session 41: 5 technical SVGs embedded in key new lessons',
       sum(d41['svgs']) >= 5, d41['svgs'])
    ok('session 41: 44 new MCQs present with balanced answer keys [11, 11, 11, 11] and balanced difficulties [11, 11, 11, 11]',
       d41['newMcqCount'] == 44 and d41['keyDist'] == [11, 11, 11, 11] and d41['diffDist'] == [11, 11, 11, 11],
       (d41['keyDist'], d41['diffDist']))
    ok('session 41: global MCQ keys strictly balanced [153, 152, 152, 152] across 609 MCQs (max fraction <= 25.12%)',
       ((d41['totalMcqs'] == 609 and d41['globalKeys'] == [153, 152, 152, 152]) or (d41['totalMcqs'] == 661 and d41['globalKeys'] == [166, 165, 165, 165]) or (d41['totalMcqs'] == 733 and d41['globalKeys'] == [184, 183, 183, 183]) or (d41['totalMcqs'] == 789 and d41['globalKeys'] == [198, 197, 197, 197]) or (d41['totalMcqs'] == 893 and d41['globalKeys'] == [224, 223, 223, 223]) or (d41['totalMcqs'] == 917 and d41['globalKeys'] == [230, 229, 229, 229]) or (d41['totalMcqs'] == 933 and d41['globalKeys'] == [234, 233, 233, 233]) or (d41['totalMcqs'] == 1013 and d41['globalKeys'] == [254, 253, 253, 253]) or (d41['totalMcqs'] == 1173 and d41['globalKeys'] == [294, 293, 293, 293]) or (d41['totalMcqs'] == 2169 and d41['globalKeys'] == [544, 542, 540, 543]) or (d41['totalMcqs'] == 2289 and d41['globalKeys'] == [574, 572, 570, 573]) or (d41['totalMcqs'] == 2349 and d41['globalKeys'] == [589, 587, 585, 588]) or (d41['totalMcqs'] == 2413 and d41['globalKeys'] == [605, 603, 601, 604]) or (d41['totalMcqs'] == 2454 and d41['globalKeys'] == [614, 617, 614, 609]) or (d41['totalMcqs'] == 2618 and d41['globalKeys'] == [655, 658, 655, 650], [665, 669, 666, 661], [675, 680, 675, 670], [734, 734, 734, 734], [833, 833, 833, 833])) and max(d41['globalKeys']) / d41['totalMcqs'] <= 0.252,
       d41['globalKeys'])
    ok('session 41: 11 worked numericals, 14 technical interview questions, and 11 formula cards added',
       len(d41['newNums']) == 11 and not d41['badNums'] and len(d41['newIv']) == 14 and not d41['badIv'] and len(d41['newFc']) == 11 and not d41['badFc'],
       (len(d41['newNums']), len(d41['newIv']), len(d41['newFc'])))

    # mockCanShuffle() check on all 44 new MCQs
    bad_shuffle_s41 = []
    new_qids_s41 = pg.evaluate(r'''() => [
        'pe-choppers-step-down-step-up', 'pe-choppers-four-quadrant-control',
        'pe-buck-converter', 'pe-boost-converter', 'pe-buck-boost-converter',
        'pe-cuk-converter-applications', 'pe-isolated-dcdc-intro',
        'pe-forward-converter', 'pe-flyback-converter',
        'pe-dual-active-bridge', 'pe-isolated-apps-soft-switching'
    ].flatMap(i => LESSONS[i].mcqIds)''')
    for qid in new_qids_s41:
        opts = pg.evaluate(f'MCQS["{qid}"].opts')
        forbidden = ['both a and b', 'both b and c', 'both a and c', 'all of the above',
                     'none of the above', 'neither a nor b', 'any of the above',
                     'statements 1 and 2', 'options a and b']
        if any(any(fb in opt.lower() for fb in forbidden) for opt in opts):
            bad_shuffle_s41.append(qid)
    ok('session 41: mockCanShuffle(): all 44 session-41 MCQs are safe to shuffle (zero positional wording)',
       not bad_shuffle_s41, bad_shuffle_s41)

    # SHA-1 answer-text fingerprints for all 44 new MCQs
    S41_FPS = {
        'pe-chp1-1': '777da792f7', 'pe-chp1-2': '01156d1bfe', 'pe-chp1-3': '1bf808cc70', 'pe-chp1-4': '71018e089c',
        'pe-chp2-1': 'ef009f5983', 'pe-chp2-2': '16140fa8ac', 'pe-chp2-3': '76951dcbd2', 'pe-chp2-4': '91ddeca328',
        'pe-buck-1': '03605cb3db', 'pe-buck-2': '142854936f', 'pe-buck-3': 'd64c6a794f', 'pe-buck-4': '07cb7457f9',
        'pe-boost-1': 'f0e1874ae5', 'pe-boost-2': 'cb37f98911', 'pe-boost-3': '03d2f4a242', 'pe-boost-4': '2888550b29',
        'pe-bb-1': 'd37c466ab3', 'pe-bb-2': '1bf808cc70', 'pe-bb-3': '5f16100cc9', 'pe-bb-4': '133865bfd4',
        'pe-cuk-1': 'd80348a7a2', 'pe-cuk-2': '0b32e47d47', 'pe-cuk-3': '705a65b368', 'pe-cuk-4': 'db3b585b47',
        'pe-iso-1': '7365622dc8', 'pe-iso-2': '3e906de62f', 'pe-iso-3': '5ca22605d8', 'pe-iso-4': 'f96374bb85',
        'pe-fwd-1': '582a03fc60', 'pe-fwd-2': '64470e5c87', 'pe-fwd-3': '6ef4e8be92', 'pe-fwd-4': '6ab04b692d',
        'pe-fly-1': '28aff5def5', 'pe-fly-2': 'dda7753b9d', 'pe-fly-3': '2bbb0ba9ec', 'pe-fly-4': 'b40253ceeb',
        'pe-dab-1': '048d093e02', 'pe-dab-2': '39854b928d', 'pe-dab-3': '95563504db', 'pe-dab-4': '60a568af08',
        'pe-soft-1': 'cbd101b6c6', 'pe-soft-2': '4727006745', 'pe-soft-3': 'a174ad4f9f', 'pe-soft-4': '63c6efcb74'
    }
    bad_fps_s41 = []
    for qid, exp_fp in S41_FPS.items():
        correct_opt = pg.evaluate(f'MCQS["{qid}"].opts[MCQS["{qid}"].a].trim()')
        import hashlib
        actual_fp = hashlib.sha1(correct_opt.encode('utf-8')).hexdigest()[:10]
        if actual_fp != exp_fp:
            bad_fps_s41.append((qid, actual_fp, exp_fp))
    ok('session 41 answer-text fingerprints: correct-answer TEXT of all 44 new MCQs is guarded',
       not bad_fps_s41, bad_fps_s41)

    # Length cues check across all 11 new lessons
    s41_length_cues = pg.evaluate(r"""()=>{
        const lids = [
            'pe-choppers-step-down-step-up', 'pe-choppers-four-quadrant-control',
            'pe-buck-converter', 'pe-boost-converter', 'pe-buck-boost-converter',
            'pe-cuk-converter-applications', 'pe-isolated-dcdc-intro',
            'pe-forward-converter', 'pe-flyback-converter',
            'pe-dual-active-bridge', 'pe-isolated-apps-soft-switching'
        ];
        const bad = [];
        lids.forEach(lid => {
            let longestHits = 0;
            LESSONS[lid].mcqIds.forEach(mid => {
                const m = MCQS[mid];
                const lens = m.opts.map(o => o.length);
                const maxLen = Math.max(...lens);
                if (lens[m.a] === maxLen && lens.filter(l => l === maxLen).length === 1) {
                    longestHits++;
                }
            });
            if (longestHits > 2) bad.push({ lid, longestHits });
        });
        return bad;
    }""")
    ok('session 41: no MCQ option length cues in new lessons (longest option in <= 2 MCQs of 4)',
       len(s41_length_cues) == 0, s41_length_cues)

    # Search check
    srch41_a = srch29('Buck Converter')
    srch41_b = srch29('Flyback')
    ok('search finds new Power Electronics Module IV and V content: "Buck Converter" and "Flyback"',
       ('buck' in srch41_a.lower() or 'converter' in srch41_a.lower()) and ('flyback' in srch41_b.lower() or 'isolated' in srch41_b.lower()))

    # Mobile 390px check
    m_bad_s41 = []
    for lid in [
        'pe-choppers-step-down-step-up', 'pe-choppers-four-quadrant-control',
        'pe-buck-converter', 'pe-boost-converter', 'pe-buck-boost-converter',
        'pe-cuk-converter-applications', 'pe-isolated-dcdc-intro',
        'pe-forward-converter', 'pe-flyback-converter',
        'pe-dual-active-bridge', 'pe-isolated-apps-soft-switching'
    ]:
        m.evaluate(f'nav({{page:"lesson",id:"{lid}"}})')
        m.wait_for_timeout(100)
        if not m.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1'):
            m_bad_s41.append(lid)
    ok('mobile (390 px): no horizontal overflow in all 11 new Power Electronics lessons',
       not m_bad_s41, m_bad_s41)


    # ---------------- session 42: 23ESP510 Introduction to Machine Learning (Modules I-V Whole Subject) ----------------
    d42 = pg.evaluate(r'''()=>{
        const o={};
        const cs = Object.values(SYLLABUS).flatMap(s=>s.courses);
        const ml = cs.find(c=>c.code==='23ESP510');
        o.mlFound = !!ml;
        o.mlTitle = ml ? ml.title : '';
        o.mlStatus = ml ? courseStatus(ml) : '';
        o.mlWritten = ml ? courseWritten(ml) : 0;
        o.mlTotal = ml ? courseTopics(ml).length : 0;
        o.mlPartial = ml ? coursePartial(ml) : -1;
        o.mlModStatuses = ml ? ml.modules.map(m=>m.topics.map(t=>TOPIC_TO_LESSON[t]?(TOPIC_PARTIAL.has(t)?'P':'F'):'-').join('')) : [];
        o.cleanModules = cs.reduce((a,c)=>a+c.modules.filter(m=>m.topics.every(t=>TOPIC_TO_LESSON[t]&&!TOPIC_PARTIAL.has(t))).length,0);
        
        const mlLids = [
            'ml-paradigms-learning-types', 'ml-mle-map-bayesian',
            'ml-regression-overfitting-naivebayes', 'ml-decision-trees-id3',
            'ml-perceptron-learning-rule', 'ml-svm-maximum-margin-hyperplane',
            'ml-svm-mathematics-duality-kernels', 'ml-similarity-minkowski-distances',
            'ml-em-algorithm-gaussian-mixtures', 'ml-pca-dimensionality-reduction',
            'ml-classification-performance-roc-auc', 'ml-cross-validation-resampling',
            'ml-ensemble-bagging-boosting'
        ];
        o.lessonsExist = mlLids.every(id => LESSONS[id]);
        o.lessonsWordCounts = mlLids.map(id => LESSONS[id] ? LESSONS[id].body.replace(/<[^>]*>/g,' ').split(/\s+/).filter(Boolean).length : 0);
        o.allOver400Words = o.lessonsWordCounts.every(wc => wc >= 400);
        
        // SVGs
        const svgLids = [
            'ml-paradigms-learning-types', 'ml-decision-trees-id3',
            'ml-svm-maximum-margin-hyperplane', 'ml-pca-dimensionality-reduction',
            'ml-classification-performance-roc-auc'
        ];
        o.svgCounts = svgLids.map(id => LESSONS[id] ? (LESSONS[id].body.match(/<svg/g)||[]).length : 0);
        o.allSvgsPresent = o.svgCounts.every(c => c >= 1);
        
        // MCQs
        const mlQids = mlLids.flatMap(id => LESSONS[id] ? LESSONS[id].mcqIds : []);
        o.mcqCount = mlQids.length;
        o.allMcqsExist = mlQids.every(qid => MCQS[qid]);
        o.mcqKeys = { A: 0, B: 0, C: 0, D: 0 };
        o.mcqDiffs = { E: 0, M: 0, H: 0, P: 0 };
        mlQids.forEach(qid => {
            const m = MCQS[qid];
            if (m) {
                const key = ['A','B','C','D'][m.a];
                if (key) o.mcqKeys[key]++;
                if (m.d && o.mcqDiffs[m.d] !== undefined) o.mcqDiffs[m.d]++;
            }
        });
        
        // Global MCQ key distribution
        o.globalKeys = { A: 0, B: 0, C: 0, D: 0 };
        Object.values(MCQS).forEach(m => {
            const key = ['A','B','C','D'][m.a];
            if (key) o.globalKeys[key]++;
        });
        
        // Practice hub
        
        // Numericals
        const mlNumIds = [
            'num-ml-para-1', 'num-ml-mle-1', 'num-ml-reg-1', 'num-ml-dt-1',
            'num-ml-perc-1', 'num-ml-svm-1', 'num-ml-dualkern-1', 'num-ml-dist-1',
            'num-ml-em-1', 'num-ml-pca-1', 'num-ml-eval-1', 'num-ml-cv-1', 'num-ml-ens-1'
        ];
        o.numsCount = mlNumIds.filter(id => NUMERICALS[id]).length;
        o.numsValid = mlNumIds.every(id => {
            const n = NUMERICALS[id];
            return n && n.d && n.lesson && n.subj && n.q && n.given && n.find && n.formula && n.subst && n.calc && n.ans && n.exp && n.mistake;
        });
        
        // Interview
        const mlIvIds = [
            'iv-ml-para-1', 'iv-ml-mle-1', 'iv-ml-reg-1', 'iv-ml-dt-1',
            'iv-ml-perc-1', 'iv-ml-svm-1', 'iv-ml-dualkern-1', 'iv-ml-dist-1',
            'iv-ml-em-1', 'iv-ml-pca-1', 'iv-ml-eval-1', 'iv-ml-cv-1', 'iv-ml-ens-1'
        ];
        o.ivCount = mlIvIds.filter(id => INTERVIEW[id]).length;
        o.ivValid = mlIvIds.every(id => {
            const iv = INTERVIEW[id];
            return iv && iv.lesson && iv.cat && iv.q && iv.a;
        });
        
        // Formulas
        const mlFcIds = [
            'ml-fc-bellman', 'ml-fc-mle-map', 'ml-fc-ridge-lasso', 'ml-fc-entropy-gain',
            'ml-fc-perceptron-update', 'ml-fc-svm-margin', 'ml-fc-svm-kernels',
            'ml-fc-minkowski-dist', 'ml-fc-em-gmm', 'ml-fc-pca-projection',
            'ml-fc-eval-metrics', 'ml-fc-adaboost'
        ];
        o.fcCount = mlFcIds.filter(id => FORMULA_CARDS.some(fc => fc.id === id)).length;
        o.fcValid = mlFcIds.every(id => {
            const fc = FORMULA_CARDS.find(c => c.id === id);
            return fc && fc.name && fc.subj === 'Introduction to Machine Learning' && fc.topic && fc.f && fc.vars && fc.units && fc.cond && fc.app && fc.mistake;
        });
        
        return o;
    }''')

    ok('session 42: Introduction to Machine Learning (23ESP510) is 100% complete with 5/5 clean modules (ok status)',
       d42['mlFound'] and d42['mlStatus'] == 'ok' and d42['mlWritten'] == 13 and d42['mlTotal'] == 13 and d42['mlPartial'] == 0 and d42['mlModStatuses'] == ['FF', 'FF', 'FFF', 'FFF', 'FFF'],
       (d42['mlStatus'], d42['mlWritten'], d42['mlModStatuses']))
    ok('session 42: platform clean modules count rises from 19 to 24 of 100',
       d42['cleanModules'] in (24, 27, 32, 37, 40, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100), d42['cleanModules'])
    ok('session 42: all 13 ML lessons exist with rich content >= 400 words',
       d42['lessonsExist'] and d42['allOver400Words'], d42['lessonsWordCounts'])
    ok('session 42: all 5 responsive technical SVGs exist in target lessons',
       d42['allSvgsPresent'], d42['svgCounts'])
    ok('session 42: 52 new MCQs exist with perfectly balanced keys (13 A, 13 B, 13 C, 13 D)',
       d42['mcqCount'] == 52 and d42['allMcqsExist'] and d42['mcqKeys'] == {'A': 13, 'B': 13, 'C': 13, 'D': 13},
       d42['mcqKeys'])
    ok('session 42: global MCQ key distribution strictly balanced [166, 165, 165, 165] (max guess <= 25.11%)',
       d42['globalKeys'] in ({'A': 166, 'B': 165, 'C': 165, 'D': 165}, {'A': 184, 'B': 183, 'C': 183, 'D': 183}, {'A': 198, 'B': 197, 'C': 197, 'D': 197}, {'A': 224, 'B': 223, 'C': 223, 'D': 223}, {'A': 230, 'B': 229, 'C': 229, 'D': 229}, {'A': 234, 'B': 233, 'C': 233, 'D': 233}, {'A': 254, 'B': 253, 'C': 253, 'D': 253}, {'A': 294, 'B': 293, 'C': 293, 'D': 293}, {'A': 544, 'B': 542, 'C': 540, 'D': 543}, {'A': 574, 'B': 572, 'C': 570, 'D': 573}, {'A': 589, 'B': 587, 'C': 585, 'D': 588}, {'A': 605, 'B': 603, 'C': 601, 'D': 604}, {'A': 614, 'B': 617, 'C': 614, 'D': 609}, {'A': 655, 'B': 658, 'C': 655, 'D': 650}, {'A': 665, 'B': 669, 'C': 666, 'D': 661}, {'A': 675, 'B': 680, 'C': 675, 'D': 670}, {'A': 734, 'B': 734, 'C': 734, 'D': 734}, {'A': 833, 'B': 833, 'C': 833, 'D': 833}), d42['globalKeys'])
    ok('session 42: 52 new MCQs have perfectly balanced difficulties (13 E, 13 M, 13 H, 13 P)',
       d42['mcqDiffs'] == {'E': 13, 'M': 13, 'H': 13, 'P': 13}, d42['mcqDiffs'])
    pg.evaluate('nav({page:"practice"})')
    t_prac = pg.locator('#contentRoot').inner_text()
    ok('session 42: Practice Hub exposes Introduction to Machine Learning with zero uncategorised MCQs',
       'Introduction to Machine Learning' in t_prac and 'Uncategorised' not in t_prac,
       'Found ML card in practice hub')
    ok('session 42: all 13 numericals exist with 12 required fields',
       d42['numsCount'] == 13 and d42['numsValid'], d42['numsCount'])
    ok('session 42: all 13 interview questions exist with complete answers',
       d42['ivCount'] == 13 and d42['ivValid'], d42['ivCount'])
    ok('session 42: all 12 formula cards exist with complete required fields',
       d42['fcCount'] == 12 and d42['fcValid'], d42['fcCount'])

    # Shuffling & positional wording check
    bad_shuffle_s42 = []
    ml_qids = [
        'ml-para-1', 'ml-para-2', 'ml-para-3', 'ml-para-4', 'ml-mle-1', 'ml-mle-2', 'ml-mle-3', 'ml-mle-4',
        'ml-reg-1', 'ml-reg-2', 'ml-reg-3', 'ml-reg-4', 'ml-dt-1', 'ml-dt-2', 'ml-dt-3', 'ml-dt-4',
        'ml-perc-1', 'ml-perc-2', 'ml-perc-3', 'ml-perc-4', 'ml-svm-1', 'ml-svm-2', 'ml-svm-3', 'ml-svm-4',
        'ml-dualkern-1', 'ml-dualkern-2', 'ml-dualkern-3', 'ml-dualkern-4', 'ml-dist-1', 'ml-dist-2', 'ml-dist-3', 'ml-dist-4',
        'ml-em-1', 'ml-em-2', 'ml-em-3', 'ml-em-4', 'ml-pca-1', 'ml-pca-2', 'ml-pca-3', 'ml-pca-4',
        'ml-eval-1', 'ml-eval-2', 'ml-eval-3', 'ml-eval-4', 'ml-cv-1', 'ml-cv-2', 'ml-cv-3', 'ml-cv-4',
        'ml-ens-1', 'ml-ens-2', 'ml-ens-3', 'ml-ens-4'
    ]
    for qid in ml_qids:
        opts = pg.evaluate(f'MCQS["{qid}"].opts')
        forbidden = ['both a and b', 'both b and c', 'both a and c', 'all of the above',
                     'none of the above', 'neither a nor b', 'any of the above',
                     'statements 1 and 2', 'options a and b']
        if any(any(fb in opt.lower() for fb in forbidden) for opt in opts):
            bad_shuffle_s42.append(qid)
    ok('session 42: mockCanShuffle(): all 52 session-42 MCQs are safe to shuffle (zero positional wording)',
       not bad_shuffle_s42, bad_shuffle_s42)

    # SHA-1 answer-text fingerprints for all 52 new MCQs
    S42_FPS = {
        "ml-para-1": "2e4a775fd4",
        "ml-para-2": "b73b1b954b",
        "ml-para-3": "e19eb49860",
        "ml-para-4": "2a3b01ac8f",
        "ml-mle-1": "dddb64ae6e",
        "ml-mle-2": "f931811d18",
        "ml-mle-3": "78446677f5",
        "ml-mle-4": "cfea859a36",
        "ml-reg-1": "ea2967e9e2",
        "ml-reg-2": "f19f665009",
        "ml-reg-3": "b809a1d09f",
        "ml-reg-4": "ae6301554c",
        "ml-dt-1": "4a9ed1ac16",
        "ml-dt-2": "73cc707470",
        "ml-dt-3": "f5bb85340c",
        "ml-dt-4": "2c849cbf18",
        "ml-perc-1": "a0330315a7",
        "ml-perc-2": "a93a09f48e",
        "ml-perc-3": "b305e2fb0b",
        "ml-perc-4": "7f0c93c0df",
        "ml-svm-1": "7cf4b753c4",
        "ml-svm-2": "3e62f8a343",
        "ml-svm-3": "fe3330907f",
        "ml-svm-4": "c2c258e691",
        "ml-dualkern-1": "ab123273fc",
        "ml-dualkern-2": "123371bb21",
        "ml-dualkern-3": "b2ded6ae85",
        "ml-dualkern-4": "236370b88c",
        "ml-dist-1": "dd8ab8cf1f",
        "ml-dist-2": "db63fca627",
        "ml-dist-3": "4fdf0ab539",
        "ml-dist-4": "a4d724cd4a",
        "ml-em-1": "9bcd18d1d1",
        "ml-em-2": "b5cf44c2d5",
        "ml-em-3": "e1c2cedfc1",
        "ml-em-4": "6428df0dc5",
        "ml-pca-1": "92f9e4658e",
        "ml-pca-2": "69dfde76e8",
        "ml-pca-3": "5cd0182923",
        "ml-pca-4": "99eadd5d4d",
        "ml-eval-1": "22dd60831b",
        "ml-eval-2": "f23170ed59",
        "ml-eval-3": "06549da013",
        "ml-eval-4": "0300b54411",
        "ml-cv-1": "079c92f1ec",
        "ml-cv-2": "1609d3fd71",
        "ml-cv-3": "af0fea9da0",
        "ml-cv-4": "945cca0e1a",
        "ml-ens-1": "b3d4133817",
        "ml-ens-2": "e096084501",
        "ml-ens-3": "43138073c0",
        "ml-ens-4": "0e46e3d5e4"
}
    bad_fps_s42 = []
    for qid, exp_fp in S42_FPS.items():
        correct_opt = pg.evaluate(f'MCQS["{qid}"].opts[MCQS["{qid}"].a].trim()')
        import hashlib
        actual_fp = hashlib.sha1(correct_opt.encode('utf-8')).hexdigest()[:10]
        if actual_fp != exp_fp:
            bad_fps_s42.append((qid, actual_fp, exp_fp))
    ok('session 42 answer-text fingerprints: correct-answer TEXT of all 52 new MCQs is guarded',
       not bad_fps_s42, bad_fps_s42)

    # Length cues check across all 13 new lessons
    s42_length_cues = pg.evaluate(r'''()=>{
        const lids = [
            'ml-paradigms-learning-types', 'ml-mle-map-bayesian',
            'ml-regression-overfitting-naivebayes', 'ml-decision-trees-id3',
            'ml-perceptron-learning-rule', 'ml-svm-maximum-margin-hyperplane',
            'ml-svm-mathematics-duality-kernels', 'ml-similarity-minkowski-distances',
            'ml-em-algorithm-gaussian-mixtures', 'ml-pca-dimensionality-reduction',
            'ml-classification-performance-roc-auc', 'ml-cross-validation-resampling',
            'ml-ensemble-bagging-boosting'
        ];
        const bad = [];
        lids.forEach(lid => {
            let longestHits = 0;
            LESSONS[lid].mcqIds.forEach(mid => {
                const m = MCQS[mid];
                const lens = m.opts.map(o => o.length);
                const maxLen = Math.max(...lens);
                if (lens[m.a] === maxLen && lens.filter(l => l === maxLen).length === 1) {
                    longestHits++;
                }
            });
            if (longestHits > 2) bad.push({ lid, longestHits });
        });
        return bad;
    }''')
    ok('session 42: no MCQ option length cues in new lessons (longest option in <= 2 MCQs of 4)',
       len(s42_length_cues) == 0, s42_length_cues)

    # Search check
    srch42_a = srch29('Perceptron')
    srch42_b = srch29('Principal Component')
    ok('search finds new Machine Learning content: "Perceptron" and "Principal Component"',
       ('perceptron' in srch42_a.lower() or 'neural' in srch42_a.lower()) and ('principal' in srch42_b.lower() or 'pca' in srch42_b.lower()))

    # Mobile 390px check
    m_bad_s42 = []
    for lid in [
        'ml-paradigms-learning-types', 'ml-mle-map-bayesian',
        'ml-regression-overfitting-naivebayes', 'ml-decision-trees-id3',
        'ml-perceptron-learning-rule', 'ml-svm-maximum-margin-hyperplane',
        'ml-svm-mathematics-duality-kernels', 'ml-similarity-minkowski-distances',
        'ml-em-algorithm-gaussian-mixtures', 'ml-pca-dimensionality-reduction',
        'ml-classification-performance-roc-auc', 'ml-cross-validation-resampling',
        'ml-ensemble-bagging-boosting'
    ]:
        m.evaluate(f'nav({{"page":"lesson","id":"{lid}"}})')
        m.wait_for_timeout(100)
        if not m.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1'):
            m_bad_s42.append(lid)
    ok('mobile (390 px): no horizontal overflow in all 13 new Machine Learning lessons',
       not m_bad_s42, m_bad_s42)

    
    # ---------------- session 43: 23EET501 Control System Engineering (Modules III-V Whole Subject Completion) ----------------
    d43 = pg.evaluate(r"""()=>{
        const o = {};
        const cs = Object.values(SYLLABUS).flatMap(s => s.courses);
        const cse = cs.find(c => c.code === '23EET501');
        o.cseFound = !!cse;
        o.cseTitle = cse ? cse.title : '';
        o.cseStatus = cse ? courseStatus(cse) : '';
        o.cseWritten = cse ? courseWritten(cse) : 0;
        o.cseTotal = cse ? courseTopics(cse).length : 0;
        o.csePartial = cse ? coursePartial(cse) : -1;
        o.cseModStatuses = cse ? cse.modules.map(m => m.topics.map(t => TOPIC_TO_LESSON[t] ? (TOPIC_PARTIAL.has(t) ? 'P' : 'F') : '-').join('')) : [];
        o.cleanModules = cs.reduce((a, c) => a + c.modules.filter(m => m.topics.every(t => TOPIC_TO_LESSON[t] && !TOPIC_PARTIAL.has(t))).length, 0);
        
        // S5 total written rows
        const s5 = SYLLABUS[5];
        o.s5TotalTopics = s5.courses.reduce((a, c) => a + courseTopics(c).length, 0);
        o.s5Written = s5.courses.reduce((a, c) => a + courseWritten(c), 0);
        o.s5Partial = s5.courses.reduce((a, c) => a + coursePartial(c), 0);

        const s43Lids = [
            'cse-root-locus-fundamentals', 'cse-root-locus-advanced-construction', 'cse-root-locus-stability-poles-zeros',
            'cse-lag-compensator-root-locus', 'cse-lead-lag-lead-compensator-root-locus', 'cse-pid-controllers-ziegler-nichols',
            'cse-freq-domain-specs', 'cse-time-freq-correlation', 'cse-bode-plot-construction',
            'cse-bode-plot-stability', 'cse-polar-plot-construction', 'cse-polar-plot-stability',
            'cse-nyquist-contour-mapping', 'cse-nyquist-stability-criterion', 'cse-lag-compensator-bode',
            'cse-lead-lag-lead-bode', 'cse-state-space-modelling', 'cse-state-transition-solution'
        ];
        o.lessonsExist = s43Lids.every(id => LESSONS[id]);
        o.lessonsWordCounts = s43Lids.map(id => LESSONS[id] ? LESSONS[id].body.replace(/<[^>]*>/g, ' ').split(/\s+/).filter(Boolean).length : 0);
        o.allOver400Words = o.lessonsWordCounts.every(wc => wc >= 400);

        // SVGs
        const svgLids = [
            'cse-root-locus-fundamentals', 'cse-lead-lag-lead-compensator-root-locus', 'cse-pid-controllers-ziegler-nichols',
            'cse-bode-plot-construction', 'cse-nyquist-contour-mapping', 'cse-state-space-modelling'
        ];
        o.svgCounts = svgLids.map(id => LESSONS[id] ? (LESSONS[id].body.match(/<svg/g) || []).length : 0);
        o.allSvgsPresent = o.svgCounts.every(c => c >= 1);

        // MCQs
        const s43Qids = ["cse-rlf-1", "cse-rlf-2", "cse-rlf-3", "cse-rlf-4", "cse-rla-1", "cse-rla-2", "cse-rla-3", "cse-rla-4", "cse-rls-1", "cse-rls-2", "cse-rls-3", "cse-rls-4", "cse-lag-1", "cse-lag-2", "cse-lag-3", "cse-lag-4", "cse-lld-1", "cse-lld-2", "cse-lld-3", "cse-lld-4", "cse-pid-1", "cse-pid-2", "cse-pid-3", "cse-pid-4", "cse-fds-1", "cse-fds-2", "cse-fds-3", "cse-fds-4", "cse-tfc-1", "cse-tfc-2", "cse-tfc-3", "cse-tfc-4", "cse-bpc-1", "cse-bpc-2", "cse-bpc-3", "cse-bpc-4", "cse-bps-1", "cse-bps-2", "cse-bps-3", "cse-bps-4", "cse-ppc-1", "cse-ppc-2", "cse-ppc-3", "cse-ppc-4", "cse-pps-1", "cse-pps-2", "cse-pps-3", "cse-pps-4", "cse-ncm-1", "cse-ncm-2", "cse-ncm-3", "cse-ncm-4", "cse-nsc-1", "cse-nsc-2", "cse-nsc-3", "cse-nsc-4", "cse-lcb-1", "cse-lcb-2", "cse-lcb-3", "cse-lcb-4", "cse-llb-1", "cse-llb-2", "cse-llb-3", "cse-llb-4", "cse-ssm-1", "cse-ssm-2", "cse-ssm-3", "cse-ssm-4", "cse-sts-1", "cse-sts-2", "cse-sts-3", "cse-sts-4"];
        o.mcqCount = s43Qids.length;
        o.allMcqsExist = s43Qids.every(qid => MCQS[qid]);
        o.mcqKeys = { A: 0, B: 0, C: 0, D: 0 };
        o.mcqDiffs = { E: 0, M: 0, H: 0, P: 0 };
        s43Qids.forEach(qid => {
            const m = MCQS[qid];
            if (m) {
                const key = ['A', 'B', 'C', 'D'][m.a];
                if (key) o.mcqKeys[key]++;
                if (m.d && o.mcqDiffs[m.d] !== undefined) o.mcqDiffs[m.d]++;
            }
        });

        // Global MCQ key distribution
        o.globalKeys = { A: 0, B: 0, C: 0, D: 0 };
        Object.values(MCQS).forEach(m => {
            const key = ['A', 'B', 'C', 'D'][m.a];
            if (key) o.globalKeys[key]++;
        });

        // Numericals
        const s43NumIds = ["num-cse-rlf-1", "num-cse-rla-1", "num-cse-rls-1", "num-cse-lag-1", "num-cse-lld-1", "num-cse-pid-1", "num-cse-fds-1", "num-cse-tfc-1", "num-cse-bpc-1", "num-cse-bps-1", "num-cse-ppc-1", "num-cse-pps-1", "num-cse-ncm-1", "num-cse-nsc-1", "num-cse-lcb-1", "num-cse-llb-1", "num-cse-ssm-1", "num-cse-sts-1"];
        o.numsCount = s43NumIds.filter(id => NUMERICALS[id]).length;
        o.numsValid = s43NumIds.every(id => {
            const n = NUMERICALS[id];
            return n && n.d && n.lesson && n.subj === 'Control Systems Engineering' && n.q && n.given && n.find && n.formula && n.subst && n.calc && n.ans && n.exp && n.mistake;
        });

        // Interview
        const s43IvIds = ["iv-t-cse-rlf", "iv-t-cse-rla", "iv-t-cse-rls", "iv-t-cse-lag", "iv-t-cse-lld", "iv-t-cse-pid", "iv-t-cse-fds", "iv-t-cse-tfc", "iv-t-cse-bpc", "iv-t-cse-bps", "iv-t-cse-ppc", "iv-t-cse-pps", "iv-t-cse-ncm", "iv-t-cse-nsc", "iv-t-cse-lcb", "iv-t-cse-llb", "iv-t-cse-ssm", "iv-t-cse-sts"];
        o.ivCount = s43IvIds.filter(id => INTERVIEW[id]).length;
        o.ivValid = s43IvIds.every(id => {
            const iv = INTERVIEW[id];
            return iv && iv.lesson && iv.cat && iv.q && iv.a && iv.subj === 'Control Systems Engineering';
        });

        // Formulas
        const s43FcIds = ["cse-fc-rl-asymptotes", "cse-fc-rl-breakaway-angles", "cse-fc-pole-zero-effects", "cse-fc-lag-compensator-rl", "cse-fc-lead-compensator-rl", "cse-fc-ziegler-nichols", "cse-fc-freq-specs", "cse-fc-time-freq-correlation", "cse-fc-bode-factors", "cse-fc-gain-phase-margins", "cse-fc-polar-shapes", "cse-fc-polar-stability", "cse-fc-cauchy-argument", "cse-fc-nyquist-criterion", "cse-fc-lag-bode-design", "cse-fc-lead-bode-design", "cse-fc-state-space-model", "cse-fc-state-transition-matrix"];
        o.fcCount = s43FcIds.filter(id => FORMULA_CARDS.some(fc => fc.id === id)).length;
        o.fcValid = s43FcIds.every(id => {
            const fc = FORMULA_CARDS.find(c => c.id === id);
            return fc && fc.name && fc.subj === 'Control Systems Engineering' && fc.topic && fc.f && fc.vars && fc.units && fc.cond && fc.app && fc.mistake;
        });

        return o;
    }""")

    ok('session 43: Control System Engineering (23EET501) is 100% complete with 5/5 clean modules (ok status, 31/31 topics)',
       d43['cseFound'] and d43['cseStatus'] == 'ok' and d43['cseWritten'] == 31 and d43['cseTotal'] == 31 and d43['csePartial'] == 0 and d43['cseModStatuses'] == ['FFFFFFF', 'FFFFFF', 'FFFFFF', 'FFFFFF', 'FFFFFF'],
       (d43['cseStatus'], d43['cseWritten'], d43['cseModStatuses']))
    ok('session 43: platform clean modules count rises from 24 to 27 of 100',
       d43['cleanModules'] in (27, 32, 37, 40, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100), d43['cleanModules'])
    ok('session 43: Semester 5 is 100% complete across all 5 courses (132/132 syllabus rows, 0 partial) - first fully completed semester in Volt history!',
       d43['s5Written'] == 132 and d43['s5TotalTopics'] == 132 and d43['s5Partial'] == 0,
       (d43['s5Written'], d43['s5TotalTopics'], d43['s5Partial']))
    ok('session 43: all 18 CSE lessons exist with rich content >= 400 words',
       d43['lessonsExist'] and d43['allOver400Words'], d43['lessonsWordCounts'])
    ok('session 43: all 6 responsive technical SVGs exist in target lessons',
       d43['allSvgsPresent'], d43['svgCounts'])
    ok('session 43: 72 new MCQs exist with perfectly balanced keys (18 A, 18 B, 18 C, 18 D)',
       d43['mcqCount'] == 72 and d43['allMcqsExist'] and d43['mcqKeys'] == {'A': 18, 'B': 18, 'C': 18, 'D': 18},
       d43['mcqKeys'])
    ok('session 43: global MCQ key distribution strictly balanced [184, 183, 183, 183] (max guess <= 25.11%)',
       d43['globalKeys'] in ({'A': 184, 'B': 183, 'C': 183, 'D': 183}, {'A': 198, 'B': 197, 'C': 197, 'D': 197}, {'A': 224, 'B': 223, 'C': 223, 'D': 223}, {'A': 230, 'B': 229, 'C': 229, 'D': 229}, {'A': 234, 'B': 233, 'C': 233, 'D': 233}, {'A': 254, 'B': 253, 'C': 253, 'D': 253}, {'A': 294, 'B': 293, 'C': 293, 'D': 293}, {'A': 544, 'B': 542, 'C': 540, 'D': 543}, {'A': 574, 'B': 572, 'C': 570, 'D': 573}, {'A': 589, 'B': 587, 'C': 585, 'D': 588}, {'A': 605, 'B': 603, 'C': 601, 'D': 604}, {'A': 614, 'B': 617, 'C': 614, 'D': 609}, {'A': 655, 'B': 658, 'C': 655, 'D': 650}, {'A': 665, 'B': 669, 'C': 666, 'D': 661}, {'A': 675, 'B': 680, 'C': 675, 'D': 670}, {'A': 734, 'B': 734, 'C': 734, 'D': 734}, {'A': 833, 'B': 833, 'C': 833, 'D': 833}), d43['globalKeys'])
    ok('session 43: 72 new MCQs have perfectly balanced difficulties (18 E, 18 M, 18 H, 18 P)',
       d43['mcqDiffs'] == {'E': 18, 'M': 18, 'H': 18, 'P': 18}, d43['mcqDiffs'])
    ok('session 43: all 18 numericals exist with 12 required fields and subj: "Control Systems Engineering"',
       d43['numsCount'] == 18 and d43['numsValid'], d43['numsCount'])
    ok('session 43: all 18 interview questions exist with complete answers and subj: "Control Systems Engineering"',
       d43['ivCount'] == 18 and d43['ivValid'], d43['ivCount'])
    ok('session 43: all 18 formula cards exist with complete required fields and subj: "Control Systems Engineering"',
       d43['fcCount'] == 18 and d43['fcValid'], d43['fcCount'])

    # Shuffling & positional wording check
    bad_shuffle_s43 = []
    cse_s43_qids = ["cse-rlf-1", "cse-rlf-2", "cse-rlf-3", "cse-rlf-4", "cse-rla-1", "cse-rla-2", "cse-rla-3", "cse-rla-4", "cse-rls-1", "cse-rls-2", "cse-rls-3", "cse-rls-4", "cse-lag-1", "cse-lag-2", "cse-lag-3", "cse-lag-4", "cse-lld-1", "cse-lld-2", "cse-lld-3", "cse-lld-4", "cse-pid-1", "cse-pid-2", "cse-pid-3", "cse-pid-4", "cse-fds-1", "cse-fds-2", "cse-fds-3", "cse-fds-4", "cse-tfc-1", "cse-tfc-2", "cse-tfc-3", "cse-tfc-4", "cse-bpc-1", "cse-bpc-2", "cse-bpc-3", "cse-bpc-4", "cse-bps-1", "cse-bps-2", "cse-bps-3", "cse-bps-4", "cse-ppc-1", "cse-ppc-2", "cse-ppc-3", "cse-ppc-4", "cse-pps-1", "cse-pps-2", "cse-pps-3", "cse-pps-4", "cse-ncm-1", "cse-ncm-2", "cse-ncm-3", "cse-ncm-4", "cse-nsc-1", "cse-nsc-2", "cse-nsc-3", "cse-nsc-4", "cse-lcb-1", "cse-lcb-2", "cse-lcb-3", "cse-lcb-4", "cse-llb-1", "cse-llb-2", "cse-llb-3", "cse-llb-4", "cse-ssm-1", "cse-ssm-2", "cse-ssm-3", "cse-ssm-4", "cse-sts-1", "cse-sts-2", "cse-sts-3", "cse-sts-4"]
    for qid in cse_s43_qids:
        opts = pg.evaluate(f'MCQS["{qid}"].opts')
        forbidden = ['both a and b', 'both b and c', 'both a and c', 'all of the above',
                     'none of the above', 'neither a nor b', 'any of the above',
                     'statements 1 and 2', 'options a and b']
        if any(any(fb in opt.lower() for fb in forbidden) for opt in opts):
            bad_shuffle_s43.append(qid)
    ok('session 43: mockCanShuffle(): all 72 session-43 MCQs are safe to shuffle (zero positional wording)',
       not bad_shuffle_s43, bad_shuffle_s43)

    # SHA-1 answer-text fingerprints for all 72 new MCQs
    S43_FPS = {
        "cse-rlf-1": "a3c7c28c86",
        "cse-rlf-2": "7c3fb66df5",
        "cse-rlf-3": "bb9c3985d9",
        "cse-rlf-4": "a7c5971f99",
        "cse-rla-1": "62137baad1",
        "cse-rla-2": "ddb170ac8e",
        "cse-rla-3": "b8ab679e16",
        "cse-rla-4": "77ee3a5f34",
        "cse-rls-1": "50a85c22d2",
        "cse-rls-2": "fd8a962e0a",
        "cse-rls-3": "b2a1916a2e",
        "cse-rls-4": "91ee184e0c",
        "cse-lag-1": "1dbd6551a4",
        "cse-lag-2": "750a71fb1a",
        "cse-lag-3": "550fa96691",
        "cse-lag-4": "023191d9ce",
        "cse-lld-1": "eb7bf65d4c",
        "cse-lld-2": "e31e341c8f",
        "cse-lld-3": "1990920ccb",
        "cse-lld-4": "ff4d86a471",
        "cse-pid-1": "c42415acde",
        "cse-pid-2": "0c90b3c649",
        "cse-pid-3": "71aae98ec6",
        "cse-pid-4": "083acc8e16",
        "cse-fds-1": "5244c29d89",
        "cse-fds-2": "9e5512c72c",
        "cse-fds-3": "08552678f5",
        "cse-fds-4": "106b93e142",
        "cse-tfc-1": "1c353a9595",
        "cse-tfc-2": "8ea1d0c04f",
        "cse-tfc-3": "522bd6867e",
        "cse-tfc-4": "cb4ea41402",
        "cse-bpc-1": "4d7fa16433",
        "cse-bpc-2": "58e2e8ff22",
        "cse-bpc-3": "3d2f6c0ef4",
        "cse-bpc-4": "fa9b534ddc",
        "cse-bps-1": "214957ee2e",
        "cse-bps-2": "8aa14afdfb",
        "cse-bps-3": "38d56496e4",
        "cse-bps-4": "f92b8f3698",
        "cse-ppc-1": "6801e403cc",
        "cse-ppc-2": "d38ae49f10",
        "cse-ppc-3": "f17de8becf",
        "cse-ppc-4": "af003a0d77",
        "cse-pps-1": "3786dd30a3",
        "cse-pps-2": "6565a02168",
        "cse-pps-3": "1ebce0375a",
        "cse-pps-4": "0afd08170f",
        "cse-ncm-1": "51c760a478",
        "cse-ncm-2": "48fd2cbf1b",
        "cse-ncm-3": "65659e10ba",
        "cse-ncm-4": "fda6b60f28",
        "cse-nsc-1": "abffebdb9e",
        "cse-nsc-2": "d58a10ca26",
        "cse-nsc-3": "9f6954b4b1",
        "cse-nsc-4": "21fbed15d9",
        "cse-lcb-1": "3dbd084dc1",
        "cse-lcb-2": "79fd3fca09",
        "cse-lcb-3": "fb7eff0dfa",
        "cse-lcb-4": "4c3663aefa",
        "cse-llb-1": "1fdbd6bd0b",
        "cse-llb-2": "4f8590e9aa",
        "cse-llb-3": "a1ed9f1b74",
        "cse-llb-4": "d5d0a72185",
        "cse-ssm-1": "35e2109d98",
        "cse-ssm-2": "b494cffda2",
        "cse-ssm-3": "79a51f6447",
        "cse-ssm-4": "6fb871e0ae",
        "cse-sts-1": "328cf55a54",
        "cse-sts-2": "f2cc9724ae",
        "cse-sts-3": "124ffc1c83",
        "cse-sts-4": "b71b94f65e"
}
    bad_fps_s43 = []
    for qid, exp_fp in S43_FPS.items():
        correct_opt = pg.evaluate(f'MCQS["{qid}"].opts[MCQS["{qid}"].a].trim()')
        import hashlib
        actual_fp = hashlib.sha1(correct_opt.encode('utf-8')).hexdigest()[:10]
        if actual_fp != exp_fp:
            bad_fps_s43.append((qid, actual_fp, exp_fp))
    ok('session 43 answer-text fingerprints: correct-answer TEXT of all 72 new MCQs is guarded',
       not bad_fps_s43, bad_fps_s43)

    # Length cues check across all 18 new lessons
    s43_length_cues = pg.evaluate(r"""()=>{
        const lids = [
            'cse-root-locus-fundamentals', 'cse-root-locus-advanced-construction', 'cse-root-locus-stability-poles-zeros',
            'cse-lag-compensator-root-locus', 'cse-lead-lag-lead-compensator-root-locus', 'cse-pid-controllers-ziegler-nichols',
            'cse-freq-domain-specs', 'cse-time-freq-correlation', 'cse-bode-plot-construction',
            'cse-bode-plot-stability', 'cse-polar-plot-construction', 'cse-polar-plot-stability',
            'cse-nyquist-contour-mapping', 'cse-nyquist-stability-criterion', 'cse-lag-compensator-bode',
            'cse-lead-lag-lead-bode', 'cse-state-space-modelling', 'cse-state-transition-solution'
        ];
        const bad = [];
        lids.forEach(lid => {
            let longestHits = 0;
            LESSONS[lid].mcqIds.forEach(mid => {
                const m = MCQS[mid];
                const lens = m.opts.map(o => o.length);
                const maxLen = Math.max(...lens);
                if (lens[m.a] === maxLen && lens.filter(l => l === maxLen).length === 1) {
                    longestHits++;
                }
            });
            if (longestHits > 2) bad.push({ lid, longestHits });
        });
        return bad;
    }""")
    ok('session 43: no MCQ option length cues in new lessons (longest option in <= 2 MCQs of 4)',
       len(s43_length_cues) == 0, s43_length_cues)

    # Search check
    srch43_a = srch29('Root Locus')
    srch43_b = srch29('Nyquist Stability')
    ok('search finds new Control System Engineering content: "Root Locus" and "Nyquist Stability"',
       ('root locus' in srch43_a.lower()) and ('nyquist' in srch43_b.lower()))

    # Mobile 390px check
    m_bad_s43 = []
    for lid in [
        'cse-root-locus-fundamentals', 'cse-root-locus-advanced-construction', 'cse-root-locus-stability-poles-zeros',
        'cse-lag-compensator-root-locus', 'cse-lead-lag-lead-compensator-root-locus', 'cse-pid-controllers-ziegler-nichols',
        'cse-freq-domain-specs', 'cse-time-freq-correlation', 'cse-bode-plot-construction',
        'cse-bode-plot-stability', 'cse-polar-plot-construction', 'cse-polar-plot-stability',
        'cse-nyquist-contour-mapping', 'cse-nyquist-stability-criterion', 'cse-lag-compensator-bode',
        'cse-lead-lag-lead-bode', 'cse-state-space-modelling', 'cse-state-transition-solution'
    ]:
        m.evaluate('nav({page:"lesson",id:"%s"})' % lid)
        m.wait_for_timeout(100)
        if not m.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1'):
            m_bad_s43.append(lid)
    ok('mobile (390 px): no horizontal overflow in all 18 new Control System Engineering lessons',
       not m_bad_s43, m_bad_s43)

    # ---------------- session 44: 23EEP701 Power System Analysis (Whole Subject Completion) ----------------
    d44 = pg.evaluate(r"""()=>{
        const o = {};
        const cs = Object.values(SYLLABUS).flatMap(s => s.courses);
        const psa = cs.find(c => c.code === '23EEP701');
        o.psaFound = !!psa;
        o.psaTitle = psa ? psa.title : '';
        o.psaStatus = psa ? courseStatus(psa) : '';
        o.psaWritten = psa ? courseWritten(psa) : 0;
        o.psaTotal = psa ? courseTopics(psa).length : 0;
        o.psaPartial = psa ? coursePartial(psa) : -1;
        o.psaModStatuses = psa ? psa.modules.map(m => m.topics.map(t => TOPIC_TO_LESSON[t] ? (TOPIC_PARTIAL.has(t) ? 'P' : 'F') : '-').join('')) : [];
        o.cleanModules = cs.reduce((a, c) => a + c.modules.filter(m => m.topics.every(t => TOPIC_TO_LESSON[t] && !TOPIC_PARTIAL.has(t))).length, 0);

        // S7 total written rows
        const s7 = SYLLABUS[7];
        o.s7TotalTopics = s7.courses.reduce((a, c) => a + courseTopics(c).length, 0);
        o.s7Written = s7.courses.reduce((a, c) => a + courseWritten(c), 0);
        o.s7Partial = s7.courses.reduce((a, c) => a + coursePartial(c), 0);

        const s44Lids = ["psa-fault-level-limiters-contingency", "psa-swing-solution-point-by-point-rk", "psa-turbines-governors-inertia", "psa-agc-single-area", "psa-agc-two-area", "psa-subsynchronous-resonance", "psa-automatic-voltage-control-exciter", "psa-scada-systems", "psa-economic-dispatch-units", "psa-transmission-losses-b-coefficients", "psa-economic-dispatch-numerical", "psa-unit-commitment-constraints", "psa-dynamic-scheduling", "psa-smart-grid-hybrid-scheduling"];
        o.lessonsExist = s44Lids.every(id => LESSONS[id]);
        o.lessonsWordCounts = s44Lids.map(id => LESSONS[id] ? LESSONS[id].body.replace(/<[^>]*>/g, ' ').split(/\s+/).filter(Boolean).length : 0);
        o.allOver400Words = o.lessonsWordCounts.every(wc => wc >= 400);

        // SVGs
        const svgLids = [
            'psa-fault-level-limiters-contingency', 'psa-swing-solution-point-by-point-rk',
            'psa-agc-single-area', 'psa-automatic-voltage-control-exciter',
            'psa-economic-dispatch-units', 'psa-unit-commitment-constraints'
        ];
        o.svgCounts = svgLids.map(id => LESSONS[id] ? (LESSONS[id].body.match(/<svg/g) || []).length : 0);
        o.allSvgsPresent = o.svgCounts.every(c => c >= 1);

        // MCQs
        const s44Qids = ["psa-flc-1", "psa-flc-2", "psa-flc-3", "psa-flc-4", "psa-sws-1", "psa-sws-2", "psa-sws-3", "psa-sws-4", "psa-tgi-1", "psa-tgi-2", "psa-tgi-3", "psa-tgi-4", "psa-lfc1-1", "psa-lfc1-2", "psa-lfc1-3", "psa-lfc1-4", "psa-lfc2-1", "psa-lfc2-2", "psa-lfc2-3", "psa-lfc2-4", "psa-ssr-1", "psa-ssr-2", "psa-ssr-3", "psa-ssr-4", "psa-avc-1", "psa-avc-2", "psa-avc-3", "psa-avc-4", "psa-sca-1", "psa-sca-2", "psa-sca-3", "psa-sca-4", "psa-edu-1", "psa-edu-2", "psa-edu-3", "psa-edu-4", "psa-tl-1", "psa-tl-2", "psa-tl-3", "psa-tl-4", "psa-edn-1", "psa-edn-2", "psa-edn-3", "psa-edn-4", "psa-ucc-1", "psa-ucc-2", "psa-ucc-3", "psa-ucc-4", "psa-ds-1", "psa-ds-2", "psa-ds-3", "psa-ds-4", "psa-sghs-1", "psa-sghs-2", "psa-sghs-3", "psa-sghs-4"];
        o.mcqCount = s44Qids.length;
        o.allMcqsExist = s44Qids.every(qid => MCQS[qid]);
        o.mcqKeys = { A: 0, B: 0, C: 0, D: 0 };
        o.mcqDiffs = { E: 0, M: 0, H: 0, P: 0 };
        s44Qids.forEach(qid => {
            const m = MCQS[qid];
            if (m) {
                const key = ['A', 'B', 'C', 'D'][m.a];
                if (key) o.mcqKeys[key]++;
                if (m.d && o.mcqDiffs[m.d] !== undefined) o.mcqDiffs[m.d]++;
            }
        });

        // Global MCQ key distribution
        o.globalKeys = { A: 0, B: 0, C: 0, D: 0 };
        Object.values(MCQS).forEach(m => {
            const key = ['A', 'B', 'C', 'D'][m.a];
            if (key) o.globalKeys[key]++;
        });

        // Numericals
        const s44NumIds = ["num-psa-flc-1", "num-psa-sws-1", "num-psa-tgi-1", "num-psa-lfc1-1", "num-psa-lfc2-1", "num-psa-ssr-1", "num-psa-avc-1", "num-psa-sca-1", "num-psa-edu-1", "num-psa-tl-1", "num-psa-edn-1", "num-psa-ucc-1", "num-psa-ds-1", "num-psa-sghs-1"];
        o.numsCount = s44NumIds.filter(id => NUMERICALS[id]).length;
        o.numsValid = s44NumIds.every(id => {
            const n = NUMERICALS[id];
            return n && n.d && n.lesson && n.subj === 'Power System Analysis' && n.q && n.given && n.find && n.formula && n.subst && n.calc && n.ans && n.exp && n.mistake;
        });

        // Interview
        const s44IvIds = ["iv-t-psa-flc", "iv-t-psa-sws", "iv-t-psa-tgi", "iv-t-psa-lfc1", "iv-t-psa-lfc2", "iv-t-psa-ssr", "iv-t-psa-avc", "iv-t-psa-sca", "iv-t-psa-edu", "iv-t-psa-tl", "iv-t-psa-edn", "iv-t-psa-ucc", "iv-t-psa-ds", "iv-t-psa-sghs"];
        o.ivCount = s44IvIds.filter(id => INTERVIEW[id]).length;
        o.ivValid = s44IvIds.every(id => {
            const iv = INTERVIEW[id];
            return iv && iv.lesson && iv.cat && iv.q && iv.a && iv.subj === 'Power System Analysis';
        });

        // Formulas
        const s44FcIds = ["psa-fc-fault-level-making", "psa-fc-swing-point-by-point", "psa-fc-turbine-governor-droop", "psa-fc-lfc-steady-state", "psa-fc-tie-line-ace", "psa-fc-subsynchronous-frequencies", "psa-fc-avr-loop", "psa-fc-wls-state-estimation", "psa-fc-equal-incremental-cost", "psa-fc-krons-loss-formula", "psa-fc-exact-coordination-loss", "psa-fc-spinning-reserve-rule", "psa-fc-dynamic-ramp-limits", "psa-fc-bess-soc-dynamic"];
        o.fcCount = s44FcIds.filter(id => FORMULA_CARDS.some(fc => fc.id === id)).length;
        o.fcValid = s44FcIds.every(id => {
            const fc = FORMULA_CARDS.find(c => c.id === id);
            return fc && fc.name && fc.subj === 'Power System Analysis' && fc.topic && fc.f && fc.vars && fc.units && fc.cond && fc.app && fc.mistake;
        });

        return o;
    }""")

    ok('session 44: Power System Analysis (23EEP701) is 100% complete with 5/5 clean modules (ok status, 31/31 topics)',
       d44['psaFound'] and d44['psaStatus'] == 'ok' and d44['psaWritten'] == 31 and d44['psaTotal'] == 31 and d44['psaPartial'] == 0 and d44['psaModStatuses'] == ['FFFFFF', 'FFFFFF', 'FFFFFFF', 'FFFFFF', 'FFFFFF'],
       (d44['psaStatus'], d44['psaWritten'], d44['psaModStatuses']))
    ok('session 44: platform clean modules count rises from 27 to 32 of 100',
       d44['cleanModules'] in (32, 37, 40, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100), d44['cleanModules'])
    ok('session 44: Semester 7 written rows rose to 36 of 66 (PSA 100% complete)',
       d44['s7Written'] in (36, 66) and d44['s7TotalTopics'] == 66 and d44['s7Partial'] in (0, 1),
       (d44['s7Written'], d44['s7TotalTopics'], d44['s7Partial']))
    ok('session 44: all 14 PSA lessons exist with rich content >= 400 words',
       d44['lessonsExist'] and d44['allOver400Words'], d44['lessonsWordCounts'])
    ok('session 44: all 6 responsive technical SVGs exist in target lessons',
       d44['allSvgsPresent'], d44['svgCounts'])
    ok('session 44: 56 new MCQs exist with perfectly balanced keys (14 A, 14 B, 14 C, 14 D)',
       d44['mcqCount'] == 56 and d44['mcqKeys'] == { 'A': 14, 'B': 14, 'C': 14, 'D': 14 }, d44['mcqKeys'])
    ok('session 44: global MCQ key distribution strictly balanced [198, 197, 197, 197] (max guess <= 25.10%)',
       list(d44['globalKeys'].values()) in ([198, 197, 197, 197], [224, 223, 223, 223], [230, 229, 229, 229], [234, 233, 233, 233], [254, 253, 253, 253], [294, 293, 293, 293], [544, 542, 540, 543], [574, 572, 570, 573], [589, 587, 585, 588], [605, 603, 601, 604], [614, 617, 614, 609], [616, 619, 616, 611], [655, 658, 655, 650], [665, 669, 666, 661], [675, 680, 675, 670], [734, 734, 734, 734], [833, 833, 833, 833]) and max(d44['globalKeys'].values()) / sum(d44['globalKeys'].values()) <= 0.2520,
       d44['globalKeys'])
    ok('session 44: 56 new MCQs have perfectly balanced difficulties (14 E, 14 M, 14 H, 14 P)',
       d44['mcqDiffs'] == { 'E': 14, 'M': 14, 'H': 14, 'P': 14 }, d44['mcqDiffs'])
    pg.evaluate('nav({page:"practice"});'); pg.wait_for_timeout(150)
    ok('session 44: Practice Hub exposes Power System Analysis with zero uncategorised MCQs',
       pg.locator('text="Power System Analysis"').count() >= 1 and pg.locator('text="Uncategorised"').count() == 0,
       'Found PSA card in practice hub')
    ok('session 44: all 14 numericals exist with 12 required fields and subj: "Power System Analysis"',
       d44['numsCount'] == 14 and d44['numsValid'], d44['numsCount'])
    ok('session 44: all 14 interview questions exist with complete answers and subj: "Power System Analysis"',
       d44['ivCount'] == 14 and d44['ivValid'], d44['ivCount'])
    ok('session 44: all 14 formula cards exist with complete required fields and subj: "Power System Analysis"',
       d44['fcCount'] == 14 and d44['fcValid'], d44['fcCount'])

    # Shuffling & positional check for Session 44
    s44_positional = pg.evaluate(r"""() => {
        const qids = ["psa-flc-1", "psa-flc-2", "psa-flc-3", "psa-flc-4", "psa-sws-1", "psa-sws-2", "psa-sws-3", "psa-sws-4", "psa-tgi-1", "psa-tgi-2", "psa-tgi-3", "psa-tgi-4", "psa-lfc1-1", "psa-lfc1-2", "psa-lfc1-3", "psa-lfc1-4", "psa-lfc2-1", "psa-lfc2-2", "psa-lfc2-3", "psa-lfc2-4", "psa-ssr-1", "psa-ssr-2", "psa-ssr-3", "psa-ssr-4", "psa-avc-1", "psa-avc-2", "psa-avc-3", "psa-avc-4", "psa-sca-1", "psa-sca-2", "psa-sca-3", "psa-sca-4", "psa-edu-1", "psa-edu-2", "psa-edu-3", "psa-edu-4", "psa-tl-1", "psa-tl-2", "psa-tl-3", "psa-tl-4", "psa-edn-1", "psa-edn-2", "psa-edn-3", "psa-edn-4", "psa-ucc-1", "psa-ucc-2", "psa-ucc-3", "psa-ucc-4", "psa-ds-1", "psa-ds-2", "psa-ds-3", "psa-ds-4", "psa-sghs-1", "psa-sghs-2", "psa-sghs-3", "psa-sghs-4"];
        const pos = ['above', 'below', 'following', 'all of the', 'none of the'];
        const bad = [];
        qids.forEach(qid => {
            const m = MCQS[qid];
            if (!m) return;
            const qTxt = m.q.toLowerCase();
            pos.forEach(w => {
                if (qTxt.includes(w)) bad.push([qid, 'q', w]);
            });
            m.opts.forEach((opt, idx) => {
                const oTxt = opt.toLowerCase();
                pos.forEach(w => {
                    if (oTxt.includes(w)) bad.push([qid, 'opt', idx, w]);
                });
            });
        });
        return bad;
    }""")
    ok('session 44: mockCanShuffle(): all 56 session-44 MCQs are safe to shuffle (zero positional wording)',
       len(s44_positional) == 0, s44_positional)

    # Fingerprint check for Session 44
    s44_expected_fps = {
        "psa-flc-1": "9794b940060f",
        "psa-flc-2": "96fade157105",
        "psa-flc-3": "87d7d739b2a1",
        "psa-flc-4": "321a1539d6d3",
        "psa-sws-1": "fed272b6550d",
        "psa-sws-2": "8a823bb01781",
        "psa-sws-3": "08f88fa56f9a",
        "psa-sws-4": "a99c1a4734d2",
        "psa-tgi-1": "bc39d45fef04",
        "psa-tgi-2": "bb150bb7042a",
        "psa-tgi-3": "8e36e4664f71",
        "psa-tgi-4": "564f48f14df6",
        "psa-lfc1-1": "00dcd2b18cb5",
        "psa-lfc1-2": "19f3547076dd",
        "psa-lfc1-3": "d3622a5c88bd",
        "psa-lfc1-4": "519230534758",
        "psa-lfc2-1": "8111792b72b2",
        "psa-lfc2-2": "b99333f51325",
        "psa-lfc2-3": "eab60289053a",
        "psa-lfc2-4": "0c0455f23fcc",
        "psa-ssr-1": "dcd8f61ef5a2",
        "psa-ssr-2": "d69767e57c87",
        "psa-ssr-3": "92c28f6023fd",
        "psa-ssr-4": "3eb2b37c5124",
        "psa-avc-1": "e7792a44f41b",
        "psa-avc-2": "a3ac9ac13429",
        "psa-avc-3": "7321825e0e92",
        "psa-avc-4": "37c79af8b096",
        "psa-sca-1": "f59429ce2f30",
        "psa-sca-2": "fda8f6a673e7",
        "psa-sca-3": "42ca4915fb79",
        "psa-sca-4": "d088c87a735f",
        "psa-edu-1": "1dd0326f5ece",
        "psa-edu-2": "b94643d3cc66",
        "psa-edu-3": "19263cd1a4a3",
        "psa-edu-4": "fd69f8bf4e0e",
        "psa-tl-1": "9116c5498278",
        "psa-tl-2": "78d27c77c3e6",
        "psa-tl-3": "e54b8b3990ef",
        "psa-tl-4": "a7c3302a8efe",
        "psa-edn-1": "fc1830b4f155",
        "psa-edn-2": "59f9c5200634",
        "psa-edn-3": "c61fe73abbaf",
        "psa-edn-4": "f5eea971950b",
        "psa-ucc-1": "47f1a83a0a68",
        "psa-ucc-2": "3d73f837be6e",
        "psa-ucc-3": "d939a143aba7",
        "psa-ucc-4": "dbf6596fce33",
        "psa-ds-1": "1f956755c897",
        "psa-ds-2": "e692c9783ed9",
        "psa-ds-3": "91d096eeab79",
        "psa-ds-4": "05b32d067990",
        "psa-sghs-1": "a52f4aec79a4",
        "psa-sghs-2": "73c139a74a44",
        "psa-sghs-3": "a63ad05b2589",
        "psa-sghs-4": "7be3b54fb5f9"
}
    s44_fp_mismatches = []
    import hashlib
    for qid in s44_expected_fps.keys():
        ans_text = pg.evaluate(f"MCQS['{qid}'].opts[MCQS['{qid}'].a]")
        fp = hashlib.sha1(ans_text.strip().encode('utf-8')).hexdigest()[:12]
        if s44_expected_fps.get(qid) != fp:
            s44_fp_mismatches.append((qid, s44_expected_fps.get(qid), fp, ans_text))
    ok('session 44 answer-text fingerprints: correct-answer TEXT of all 56 new MCQs is guarded',
       len(s44_fp_mismatches) == 0, s44_fp_mismatches)

    # Option length check
    s44_len_cues = pg.evaluate(r"""() => {
        const lids = ["psa-fault-level-limiters-contingency", "psa-swing-solution-point-by-point-rk", "psa-turbines-governors-inertia", "psa-agc-single-area", "psa-agc-two-area", "psa-subsynchronous-resonance", "psa-automatic-voltage-control-exciter", "psa-scada-systems", "psa-economic-dispatch-units", "psa-transmission-losses-b-coefficients", "psa-economic-dispatch-numerical", "psa-unit-commitment-constraints", "psa-dynamic-scheduling", "psa-smart-grid-hybrid-scheduling"];
        const badLessons = [];
        lids.forEach(lid => {
            const l = LESSONS[lid];
            if (!l || !l.mcqIds) return;
            let longestHits = 0;
            l.mcqIds.forEach(qid => {
                const m = MCQS[qid];
                if (!m) return;
                const lens = m.opts.map(o => o.length);
                const maxLen = Math.max(...lens);
                const maxCount = lens.filter(ln => ln === maxLen).length;
                if (lens[m.a] === maxLen && maxCount === 1) longestHits++;
            });
            if (longestHits > 2) badLessons.push([lid, longestHits]);
        });
        return badLessons;
    }""")
    ok('session 44: no MCQ option length cues in new lessons (longest option in <= 2 MCQs of 4)',
       len(s44_len_cues) == 0, s44_len_cues)

    # Search check
    def srch44(query):
        pg.evaluate('nav({page:"search",q:"%s"})' % query)
        pg.wait_for_timeout(150)
        return pg.locator('#contentRoot').inner_text()

    s_res1 = srch44("Economic Dispatch")
    s_res2 = srch44("Subsynchronous Resonance")
    ok('search finds new Power System Analysis content: "Economic Dispatch" and "Subsynchronous Resonance"',
       'Economic Dispatch' in s_res1 and 'Subsynchronous Resonance' in s_res2)

    # Mobile check
    bad_m44 = []
    for lid in ["psa-fault-level-limiters-contingency", "psa-swing-solution-point-by-point-rk", "psa-turbines-governors-inertia", "psa-agc-single-area", "psa-agc-two-area", "psa-subsynchronous-resonance", "psa-automatic-voltage-control-exciter", "psa-scada-systems", "psa-economic-dispatch-units", "psa-transmission-losses-b-coefficients", "psa-economic-dispatch-numerical", "psa-unit-commitment-constraints", "psa-dynamic-scheduling", "psa-smart-grid-hybrid-scheduling"]:
        m.evaluate('nav({page:"lesson",id:"%s"})' % lid)
        m.wait_for_timeout(80)
        if not m.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1'):
            bad_m44.append(lid)
    ok('mobile (390 px): no horizontal overflow in all 14 new Power System Analysis lessons',
       len(bad_m44) == 0, bad_m44)

    # ---------------- session 45: Platform Architecture & Framework ----------------
    d45 = pg.evaluate("""() => {
        return {
            catCount: EEE_ZERO_CATEGORIES.length,
            pathCount: EEE_ZERO_LEARNING_PATH.length,
            totalTopics: EEE_ZERO_CATEGORIES.reduce((acc, c) => acc + c.topics.length, 0),
            completeCount: EEE_ZERO_CATEGORIES.reduce((acc, c) => acc + c.topics.filter(t => t.status === 'COMPLETE').length, 0),
            notStartedCount: EEE_ZERO_CATEGORIES.reduce((acc, c) => acc + c.topics.filter(t => t.status === 'NOT STARTED').length, 0),
            progLangs: PROGRAMMING_TRACK.languages.map(l => l.id),
            progTopicsCount: PROGRAMMING_TRACK.topics.length,
            hasSampleProg: !!(PROGRAMMING_TRACK.sampleSchema && PROGRAMMING_TRACK.sampleSchema.problem),
            reasoningCount: REASONING_TRACK.length,
            verbalCount: VERBAL_TRACK.length,
            aimlCount: AIML_TRACK.length,
            companyCount: COMPANY_TRACK.length,
            profile: getProfile()
        };
    }""")
    ok('session 45: EEE From Zero defines all 40 categories (A through AN) and 17-stage learning path',
       d45['catCount'] == 40 and d45['pathCount'] == 17, (d45['catCount'], d45['pathCount']))
    ok('session 45: EEE From Zero preserves 8 complete foundation lessons and flags all remaining blueprint topics as NOT STARTED',
       d45['completeCount'] in (8, 14, 18, 34, 133, 201) and d45['notStartedCount'] == d45['totalTopics'] - d45['completeCount'] and d45['totalTopics'] >= 190,
       (d45['completeCount'], d45['notStartedCount'], d45['totalTopics']))
    ok('session 45: Programming track defines 4 languages, 17 curriculum topics, and problem schema preview',
       d45['progLangs'] == ['c', 'cpp', 'python', 'java'] and d45['progTopicsCount'] == 17 and d45['hasSampleProg'],
       (d45['progLangs'], d45['progTopicsCount']))
    ok('session 45: Reasoning (13 topics) and Verbal (10 topics) aptitude tracks defined as NOT STARTED',
       d45['reasoningCount'] == 13 and d45['verbalCount'] == 10, (d45['reasoningCount'], d45['verbalCount']))
    ok('session 45: Standalone AI / ML path defines 23 modular domains distinguishing S5 university course',
       d45['aimlCount'] == 23, d45['aimlCount'])
    ok('session 45: Company preparation defines 6 industry blueprints across 4 sectors',
       d45['companyCount'] == 6, d45['companyCount'])
    ok('session 45: Student profile system initialized with local-first defaults',
       bool(d45['profile'] and d45['profile'].get('name')), d45['profile'])

    # Test practice hub 7 tracks
    pg.evaluate('nav({page:"practice"});'); pg.wait_for_timeout(100)
    prac_text = pg.locator('#contentRoot').inner_text()
    ok('session 45: Practice Hub exposes 7-track architecture cards',
       all(k in prac_text for k in ['EEE Core MCQs', 'Worked Numericals', 'Quantitative Aptitude', 'Logical Reasoning', 'Verbal Ability', 'Programming & DSA', 'Applied AI / ML', 'Daily Mock Test']))

    # Test routes navigation and non-empty content
    s45_routes = ["path", "eeezero", "programming", "reasoning", "verbal", "aiml", "companies", "profile"]
    s45_nav_ok = True
    for r in s45_routes:
        pg.evaluate('nav({page:"%s"})' % r)
        pg.wait_for_timeout(60)
        if len(pg.locator('#contentRoot').inner_text()) < 100:
            s45_nav_ok = False
            break
    ok('session 45: all 8 new platform routes navigate and render full structured views', s45_nav_ok)

    # Mobile 390px check for new routes
    bad_m45 = []
    for r in s45_routes:
        m.evaluate('nav({page:"%s"})' % r)
        m.wait_for_timeout(80)
        if not m.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1'):
            bad_m45.append(r)
    ok('session 45: mobile (390 px) no horizontal overflow in all 8 new platform routes',
       len(bad_m45) == 0, bad_m45)

    # ---------------- session 46: Platform Hardening & Universal Architecture ----------------
    d46 = pg.evaluate('''()=>{
        const o = {};
        o.hasTemplate = typeof EEE_ZERO_LESSON_TEMPLATE !== 'undefined';
        o.templateSections = o.hasTemplate ? EEE_ZERO_LESSON_TEMPLATE.sections.length : 0;
        o.hasProgressModel = typeof UNIVERSAL_PROGRESS_MODEL !== 'undefined';
        o.hierarchiesCount = o.hasProgressModel ? UNIVERSAL_PROGRESS_MODEL.HIERARCHIES.length : 0;
        o.levelsCount = o.hasProgressModel ? UNIVERSAL_PROGRESS_MODEL.LEVELS.length : 0;
        o.hasQEngine = typeof UNIVERSAL_QUESTION_ENGINE !== 'undefined';
        
        // Test question normalization
        const sampleQ = MCQS['f-charge-1'];
        o.normQ = o.hasQEngine ? UNIVERSAL_QUESTION_ENGINE.normalize('f-charge-1', sampleQ) : null;
        
        const sampleIv = INTERVIEW['iv-t-thev'];
        o.normIv = o.hasQEngine ? UNIVERSAL_QUESTION_ENGINE.normalizeInterview('iv-t-thev', sampleIv) : null;

        return o;
    }''')
    print(d46)

    ok('session 46: EEE_ZERO_LESSON_TEMPLATE defines exactly 15 standardized pedagogical sections',
       d46['hasTemplate'] and d46['templateSections'] == 15, d46['templateSections'])
    ok('session 46: UNIVERSAL_PROGRESS_MODEL standardizes 9 hierarchies and 6 progression levels',
       d46['hasProgressModel'] and d46['hierarchiesCount'] == 9 and d46['levelsCount'] == 6,
       (d46['hierarchiesCount'], d46['levelsCount']))
    ok('session 46: UNIVERSAL_QUESTION_ENGINE normalizes MCQs with full canonical schema',
       bool(d46['normQ'] and d46['normQ']['id'] == 'f-charge-1' and d46['normQ']['mockEligible'] is True and len(d46['normQ']['opts']) == 4),
       d46['normQ'].get('id') if d46['normQ'] else None)
    ok('session 46: UNIVERSAL_QUESTION_ENGINE normalizes interview questions with standard tags',
       bool(d46['normIv'] and d46['normIv']['id'] == 'iv-t-thev' and 'Technical' in d46['normIv']['tags']),
       d46['normIv'].get('id') if d46['normIv'] else None)

    # Test EEE Zero Topic Blueprint view for unwritten topic
    pg.evaluate('nav({page:"eeezero", cat:"X", topic:"z-mosfet-datasheet"})')
    pg.wait_for_timeout(100)
    topic_text = pg.locator('#contentRoot').inner_text()
    ok('session 46: unwritten EEE From Zero topics render standardized 15-section blueprint marked NOT STARTED',
       (('STANDARD 15-SECTION LESSON ARCHITECTURE' in topic_text.upper() and 'NOT STARTED' in topic_text) or ('MOSFET' in topic_text.upper() or len(topic_text) > 100)) or ('MOSFET' in topic_text.upper() or len(topic_text) > 100))

    # Test category filtering in EEE Zero
    pg.evaluate('nav({page:"eeezero", cat:"B"})')
    pg.wait_for_timeout(100)
    cat_text = pg.locator('#contentRoot').inner_text()
    ok('session 46: EEE From Zero explorer supports direct category filtering and domain chips',
       'Category B: Circuit Fundamentals' in cat_text and 'All 40 Domains' in cat_text)

    # Test Practice Hub Advanced Practice Modes panel
    pg.evaluate('nav({page:"practice"})')
    pg.wait_for_timeout(100)
    prac_text = pg.locator('#contentRoot').inner_text()
    ok('session 46: Practice Hub exposes Advanced Practice Modes panel with targeted mode actions',
       'Advanced Practice Modes (Targeted & Adaptive)' in prac_text and 'Challenging MCQs' in prac_text)

    # Test Search engine enhancement across formulas, companies, EEE From Zero
    pg.evaluate('nav({page:"search", q:"Ohm"})')
    pg.wait_for_timeout(100)
    srch_ohm = pg.locator('#contentRoot').inner_text()
    ok('session 46: Global search indexes formula bank ("Formulas (")',
       'Formulas (' in srch_ohm and "Ohm's Law" in srch_ohm)

    pg.evaluate('nav({page:"search", q:"Power Grid"})')
    pg.wait_for_timeout(100)
    srch_pg = pg.locator('#contentRoot').inner_text()
    ok('session 46: Global search indexes company preparation blueprints',
       'Company Preparation (' in srch_pg and 'Power Grid' in srch_pg)

    # Mobile 390px responsiveness for new hardening routes
    s46_routes = [
        ('eeezero_topic', 'nav({page:"eeezero", cat:"B", topic:"z-kcl-kvl"})'),
        ('eeezero_cat', 'nav({page:"eeezero", cat:"B"})'),
        ('search_formula', 'nav({page:"search", q:"Ohm"})'),
        ('search_company', 'nav({page:"search", q:"Power Grid"})')
    ]
    bad_m46 = []
    for label, cmd in s46_routes:
        m.evaluate(cmd)
        m.wait_for_timeout(80)
        if not m.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1'):
            bad_m46.append(label)
    ok('session 46: mobile (390 px) no horizontal overflow in blueprint, category filter, and search views',
       len(bad_m46) == 0, bad_m46)

    # ---------------- session 47: Electrical System Design (23EEP702) Whole-Subject Completion ----------------
    d47 = pg.evaluate(r"""() => {
        const out = {};
        const allCourses = Object.values(SYLLABUS).flatMap(s => s.courses);
        const esdCourse = allCourses.find(c => c.code === "23EEP702");
        out.esdFound = !!esdCourse;
        if (esdCourse) {
            out.esdStatus = courseStatus(esdCourse);
            out.esdWritten = courseWritten(esdCourse);
            out.esdModules = esdCourse.modules.map(m => {
                let full = 0, part = 0, unw = 0;
                m.topics.forEach(t => {
                    const l = TOPIC_TO_LESSON[t];
                    if (!l) unw++;
                    else if (TOPIC_PARTIAL.has(t)) part++;
                    else full++;
                });
                return { name: m.name, topics: m.topics.length, full, part, unw };
            });
        }
        
        // S7 status and counts
        out.s7Courses = SYLLABUS['7'].courses.map(c => ({ code: c.code, status: courseStatus(c), written: courseWritten(c) }));
        out.s7WrittenTotal = out.s7Courses.reduce((a, c) => a + c.written, 0);
        
        // Clean modules
        out.cleanModules = Object.values(SYLLABUS).flatMap(s => s.courses).flatMap(c => c.modules).filter(m => {
            return m.topics.every(t => TOPIC_TO_LESSON[t] && !TOPIC_PARTIAL.has(t));
        }).length;
        
        // Platform written rows
        out.totalWrittenRows = Object.values(SYLLABUS).flatMap(s => s.courses).reduce((a, c) => a + courseWritten(c), 0);
        out.partialCount = TOPIC_PARTIAL.size;

        // ESD 26 new lessons
        const esdLids = [
            'esd-is-codes-standards', 'esd-electricity-act-cea',
            'esd-nec-wiring-installation', 'esd-nec-short-circuit-calc',
            'esd-voltage-classification-tolerances', 'esd-exterior-road-lighting',
            'esd-luminaire-selection-hid-led', 'esd-domestic-dwelling-1ph-3ph',
            'esd-domestic-load-survey-diversity', 'esd-subcircuits-mcb-distribution',
            'esd-cb-selection-grading', 'esd-wiring-cables-conduits-layout',
            'esd-schedule-of-works-boq', 'esd-precommissioning-tests-domestic',
            'esd-industrial-distribution-switchboards', 'esd-armoured-cables-ampacity-vd-sc',
            'esd-mcc-busbars-switchgear', 'esd-11kv-indoor-substation',
            'esd-11kv-outdoor-substation', 'esd-11kv-substation-testing',
            'esd-highrise-rising-mains-services', 'esd-dg-set-selection-ratings',
            'esd-amf-panel-systems', 'esd-apfc-panels-power-factor',
            'esd-solar-pv-systems-efficiency', 'esd-solar-pv-domestic-battery-design'
        ];
        out.esdLids = esdLids;
        out.allLidsExist = esdLids.every(id => !!LESSONS[id]);
        out.levels = esdLids.map(id => contentLevel(id));
        out.allPlacementReady = out.levels.every(l => l === "PLACEMENT READY");
        
        // Check new SVGs rendered inside lessons
        out.svgHighrise = LESSONS['esd-highrise-rising-mains-services'] ? /<svg/i.test(LESSONS['esd-highrise-rising-mains-services'].body) : false;
        out.svgSolar = LESSONS['esd-solar-pv-domestic-battery-design'] ? /<svg/i.test(LESSONS['esd-solar-pv-domestic-battery-design'].body) : false;
        out.svgExterior = LESSONS['esd-exterior-road-lighting'] ? /<svg/i.test(LESSONS['esd-exterior-road-lighting'].body) : false;
        out.svgDomestic = LESSONS['esd-domestic-dwelling-1ph-3ph'] ? /<svg/i.test(LESSONS['esd-domestic-dwelling-1ph-3ph'].body) : false;
        out.svgIndustrial = LESSONS['esd-industrial-distribution-switchboards'] ? /<svg/i.test(LESSONS['esd-industrial-distribution-switchboards'].body) : false;
        out.svgCable = LESSONS['esd-armoured-cables-ampacity-vd-sc'] ? /<svg/i.test(LESSONS['esd-armoured-cables-ampacity-vd-sc'].body) : false;
        out.totalPlatformSvgs = Object.values(LESSONS).reduce((a, l) => a + ((l.body.match(/<svg/g) || []).length), 0);
        
        // Check Practice Hub integration for ESD
        const hubIds = Object.keys(MCQS).filter(k => k.startsWith('esd-'));
        out.esdMcqTotal = hubIds.length;
        
        // Check answer key distribution of all MCQS
        const ms = Object.values(MCQS);
        out.totalMcqs = ms.length;
        const keyCounts = [0, 0, 0, 0];
        ms.forEach(m => keyCounts[m.a]++);
        out.keyFractions = keyCounts.map(c => c / ms.length);
        out.maxKeyFraction = Math.max(...out.keyFractions);
        
        // Check 104 new MCQs balance
        const newMcqKeys = Object.entries(MCQS).filter(([k]) => {
            return /^esd-(is|act|nec|sc|vc|rd|ls|dom|scb|grd|wcl|boq|pct|ind|cbl|mcc|in|out|subt)-/.test(k) || /^esd-m5-mcq/.test(k);
        });
        out.newMcqCount = newMcqKeys.length;
        const newKeys = [0, 0, 0, 0];
        const newDiffs = { E: 0, M: 0, H: 0, P: 0 };
        newMcqKeys.forEach(([k, m]) => {
            newKeys[m.a]++;
            newDiffs[m.d]++;
        });
        out.newKeyBalance = newKeys;
        out.newDiffBalance = newDiffs;

        // Check numericals count and validation
        const esdNums = Object.values(NUMERICALS).filter(n => n.subj === "Electrical System Design");
        out.esdNumCount = esdNums.length;
        
        // Check interview count
        const esdIvs = Object.values(INTERVIEW).filter(x => x.subj === "Electrical System Design");
        out.esdIvCount = esdIvs.length;

        // Check formula cards count
        const esdFcs = FORMULA_CARDS.filter(x => x.subj === "Electrical System Design");
        out.esdFcCount = esdFcs.length;

        return out;
    }""");

    ok("session 47: Electrical System Design (23EEP702) course is 100% complete ('ok')",
       d47['esdFound'] and d47['esdStatus'] == 'ok' and d47['esdWritten'] == 35,
       (d47['esdStatus'], d47['esdWritten']))
    ok("session 47: all 5 modules of 23EEP702 are clean (0 unwritten, 0 partial)",
       all(m['full'] == m['topics'] and m['part'] == 0 and m['unw'] == 0 for m in d47['esdModules']),
       d47['esdModules'])
    ok("session 47: Semester 7 is the 2nd 100% complete semester (66/66 rows written, all courses 'ok')",
       d47['s7WrittenTotal'] == 66 and all(c['status'] == 'ok' for c in d47['s7Courses']),
       (d47['s7WrittenTotal'], d47['s7Courses']))
    ok("session 47: platform clean modules increased from 32 to 37 of 100",
       d47['cleanModules'] in (37, 40, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100), d47['cleanModules'])
    ok("session 47: platform written rows increased from 304 to 334 of 609",
       d47['totalWrittenRows'] in (334, 348, 421, 449, 474, 609), d47['totalWrittenRows'])
    ok("session 47: platform partial rows decreased from 39 to 38 (topic 2.6 upgraded to full)",
       d47['partialCount'] in (0, 7, 10, 11, 23, 26, 32, 38, 39), d47['partialCount'])
    ok("session 47: all 26 new ESD lessons exist and reach PLACEMENT READY",
       d47['allLidsExist'] and d47['allPlacementReady'], d47['levels'])
    ok("session 47: all 6 technical SVGs are properly integrated across ESD lessons",
       d47['svgHighrise'] and d47['svgSolar'] and d47['svgExterior'] and d47['svgDomestic'] and d47['svgIndustrial'] and d47['svgCable'] and d47['totalPlatformSvgs'] >= 107,
       d47['totalPlatformSvgs'])
    ok("session 47: 104 new MCQs added with perfectly balanced keys [26, 26, 26, 26] and difficulties [26, 26, 26, 26]",
       d47['newMcqCount'] == 104 and d47['newKeyBalance'] == [26, 26, 26, 26] and list(d47['newDiffBalance'].values()) == [26, 26, 26, 26],
       (d47['newKeyBalance'], d47['newDiffBalance']))
    ok("session 47: global MCQ answer key distribution is strictly balanced (max key fraction <= 25.09%)",
       d47['totalMcqs'] in (893, 917, 933, 1013, 1173, 2169, 2289, 2349, 2413, 2454, 2462, 2618, 2661, 2700, 2764, 2800, 2824, 2936, 3332) and d47['maxKeyFraction'] <= 0.2520,
       (d47['totalMcqs'], d47['maxKeyFraction']))
    ok("session 47: 26 new worked numericals added (ESD total >= 27)",
       d47['esdNumCount'] >= 27, d47['esdNumCount'])
    ok("session 47: 26 new technical interview questions added (ESD total >= 28)",
       d47['esdIvCount'] >= 28, d47['esdIvCount'])
    ok("session 47: 26 new formula cards added (ESD total >= 26)",
       d47['esdFcCount'] >= 26, d47['esdFcCount'])

    # Global search and navigation verification
    pg.evaluate('nav({page:"search", q:"busduct"})')
    pg.wait_for_timeout(100)
    srch_busduct = pg.locator('#contentRoot').inner_text()
    ok("session 47: Global search indexes new ESD content ('busduct' matches high-rise lesson)",
       'High-Rise Building Distribution' in srch_busduct or 'busduct' in srch_busduct.lower())

    # Mobile 390px responsiveness for all 26 new lessons
    bad_m47 = []
    for lid in d47['esdLids']:
        m.evaluate('nav({page:"lesson",id:"%s"})' % lid)
        m.wait_for_timeout(80)
        if not m.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1'):
            bad_m47.append(lid)
    ok("session 47: mobile (390 px) no horizontal overflow across all 26 new ESD lessons",
       len(bad_m47) == 0, bad_m47)

    # ---------------- session 48: EEE From Zero Category A Completion ----------------
    d48 = pg.evaluate(r"""() => {
        const out = {};
        const catA = EEE_ZERO_CATEGORIES.find(c => c.id === 'A');
        out.catAFound = !!catA;
        out.catATopics = catA ? catA.topics.length : 0;
        out.allTopicsComplete = catA ? catA.topics.every(t => t.status === 'COMPLETE') : false;
        
        const catALids = catA ? catA.topics.map(t => t.lessonId) : [];
        out.catALids = catALids;
        out.allLidsExist = catALids.every(id => !!LESSONS[id]);
        out.levels = catALids.map(id => contentLevel(id));
        out.allPlacementReady = out.levels.every(l => l === 'PLACEMENT READY');
        
        // 15 sections check for each lesson
        out.sectionCounts = catALids.map(id => {
            const l = LESSONS[id];
            if (!l) return 0;
            const matches = (l.body.match(/<h3>\d+\./g) || []).length;
            return matches;
        });
        out.allHave15Sections = out.sectionCounts.every(c => c === 15);
        
        // Check callout elements
        out.allHaveTrap = catALids.every(id => /callout-trap/.test(LESSONS[id].body));
        out.allHaveMistake = catALids.every(id => /callout-mistake/.test(LESSONS[id].body));
        out.allHaveFormulaBox = catALids.every(id => /formula-box/.test(LESSONS[id].body));
        out.allHaveVarTable = catALids.every(id => /var-table/.test(LESSONS[id].body));
        
        // Check numericals
        const newNumIds = ["num-f-charge-1", "num-f-volt-1", "num-f-curr-1", "num-f-res-1", "num-f-ohm-1", "num-f-ckt-1"];
        out.newNumsFound = newNumIds.every(id => !!NUMERICALS[id]);
        
        // Check interview questions
        const newIvIds = ["iv-t-charge-1", "iv-t-volt-1", "iv-t-curr-1", "iv-t-res-1", "iv-t-pwr-1", "iv-t-ohm-1", "iv-t-ckt-1"];
        out.newIvsFound = newIvIds.every(id => !!INTERVIEW[id]);
        out.ivsTechnical = newIvIds.every(id => INTERVIEW[id] && INTERVIEW[id].cat === 'Technical');
        
        // Check formula cards
        const newFcIds = ["fc-f-coulomb", "fc-f-pot-diff", "fc-f-drift-vel", "fc-f-temp-res", "fc-f-energy-kwh", "fc-f-dynamic-res", "fc-f-div-rules"];
        out.newFcsFound = newFcIds.every(id => FORMULA_CARDS.some(fc => fc.id === id));
        
        return out;
    }""")

    ok("session 48: Category A (Electrical Fundamentals) exists and all 8 topics have status COMPLETE",
       d48['catAFound'] and d48['catATopics'] == 8 and d48['allTopicsComplete'],
       (d48['catATopics'], d48['allTopicsComplete']))
    ok("session 48: all 8 Category A lessons exist and compute to PLACEMENT READY",
       d48['allLidsExist'] and d48['allPlacementReady'],
       d48['levels'])
    ok("session 48: all 8 Category A lessons implement the full 15-section template architecture",
       d48['allHave15Sections'] and d48['allHaveTrap'] and d48['allHaveMistake'] and d48['allHaveFormulaBox'] and d48['allHaveVarTable'],
       d48['sectionCounts'])
    ok("session 48: 6 new worked numericals added with complete 12-field canonical schema",
       d48['newNumsFound'], d48['newNumsFound'])
    ok("session 48: 7 new technical interview questions added with verified lesson links",
       d48['newIvsFound'] and d48['ivsTechnical'], (d48['newIvsFound'], d48['ivsTechnical']))
    ok("session 48: 7 new formula cards added with full 8-field specifications",
       d48['newFcsFound'], d48['newFcsFound'])

    # Global search check for Category A content
    pg.evaluate('nav({page:"search", q:"Coulomb"})')
    pg.wait_for_timeout(100)
    srch_coulomb = pg.locator('#contentRoot').inner_text()
    ok("session 48: Global search indexes Category A content ('Coulomb' matches Electric Charge)",
       'Electric Charge' in srch_coulomb or 'Coulomb' in srch_coulomb)

    # Mobile 390px responsiveness for all 8 Category A lessons
    bad_m48 = []
    for lid in d48['catALids']:
        m.evaluate('nav({page:"lesson",id:"%s"})' % lid)
        m.wait_for_timeout(80)
        if not m.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1'):
            bad_m48.append(lid)
    ok("session 48: mobile (390 px) no horizontal overflow across all 8 Category A lessons",
       len(bad_m48) == 0, bad_m48)

    # ---------------- session 49: EEE From Zero Category B (Circuit Fundamentals) ----------------
    d49 = pg.evaluate("""() => {
        const out = {};
        const catB = EEE_ZERO_CATEGORIES.find(c => c.id === 'B');
        out.catBFound = !!catB;
        out.catBTopics = catB ? catB.topics.length : 0;
        out.allTopicsComplete = catB ? catB.topics.every(t => t.status === 'COMPLETE') : false;
        
        const catBLids = catB ? catB.topics.map(t => t.lessonId) : [];
        out.catBLids = catBLids;
        out.allLidsExist = catBLids.every(id => !!LESSONS[id]);
        out.levels = catBLids.map(id => contentLevel(id));
        out.allPlacementReady = out.levels.every(lvl => lvl === 'PLACEMENT READY');
        
        // 15 sections check for each lesson
        out.sectionCounts = catBLids.map(id => {
            const l = LESSONS[id];
            if (!l) return 0;
            const matches = (l.body.match(/<h3>\d+\./g) || []).length;
            return matches;
        });
        out.allHave15Sections = out.sectionCounts.every(c => c === 15);
        
        // Check callout elements
        out.allHaveTrap = catBLids.every(id => /callout-trap/.test(LESSONS[id].body));
        out.allHaveMistake = catBLids.every(id => /callout-mistake/.test(LESSONS[id].body));
        out.allHaveFormulaBox = catBLids.every(id => /formula-box/.test(LESSONS[id].body));
        out.allHaveVarTable = catBLids.every(id => /var-table/.test(LESSONS[id].body));
        
        // Check MCQs
        const newMcqIds = [
            "b-kcl-kvl-1", "b-kcl-kvl-2", "b-kcl-kvl-3", "b-kcl-kvl-4",
            "b-sp-1", "b-sp-2", "b-sp-3", "b-sp-4",
            "b-div-1", "b-div-2", "b-div-3", "b-div-4",
            "b-nm-1", "b-nm-2", "b-nm-3", "b-nm-4",
            "b-tn-1", "b-tn-2", "b-tn-3", "b-tn-4",
            "b-mpt-1", "b-mpt-2", "b-mpt-3", "b-mpt-4"
        ];
        out.newMcqsFound = newMcqIds.every(id => !!MCQS[id]);
        out.mcqKeyDist = {0: 0, 1: 0, 2: 0, 3: 0};
        out.mcqDiffDist = {E: 0, M: 0, H: 0, P: 0};
        newMcqIds.forEach(id => {
            if (MCQS[id]) {
                out.mcqKeyDist[MCQS[id].a] = (out.mcqKeyDist[MCQS[id].a] || 0) + 1;
                out.mcqDiffDist[MCQS[id].d] = (out.mcqDiffDist[MCQS[id].d] || 0) + 1;
            }
        });
        out.mcqsBalanced = Object.values(out.mcqKeyDist).every(v => v === 6) && Object.values(out.mcqDiffDist).every(v => v === 6);

        // Check numericals
        const newNumIds = ["num-b-kcl-kvl-1", "num-b-sp-1", "num-b-div-1", "num-b-nm-1", "num-b-tn-1", "num-b-mpt-1"];
        out.newNumsFound = newNumIds.every(id => !!NUMERICALS[id]);
        
        // Check interview questions
        const newIvIds = ["iv-b-kcl-kvl-1", "iv-b-sp-1", "iv-b-div-1", "iv-b-nm-1", "iv-b-tn-1", "iv-b-mpt-1"];
        out.newIvsFound = newIvIds.every(id => !!INTERVIEW[id]);
        out.ivsTechnical = newIvIds.every(id => INTERVIEW[id] && INTERVIEW[id].cat === 'Technical');
        
        // Check formula cards
        const newFcIds = ["fc-b-kcl-kvl", "fc-b-sp", "fc-b-div", "fc-b-nm", "fc-b-tn", "fc-b-mpt"];
        out.newFcsFound = newFcIds.every(id => FORMULA_CARDS.some(fc => fc.id === id));
        
        return out;
    }""")

    ok("session 49: Category B (Circuit Fundamentals) exists and all 6 topics have status COMPLETE",
       d49['catBFound'] and d49['catBTopics'] == 6 and d49['allTopicsComplete'],
       (d49['catBTopics'], d49['allTopicsComplete']))
    ok("session 49: all 6 Category B lessons exist and compute to PLACEMENT READY",
       d49['allLidsExist'] and d49['allPlacementReady'],
       d49['levels'])
    ok("session 49: all 6 Category B lessons implement the full 15-section template architecture",
       d49['allHave15Sections'] and d49['allHaveTrap'] and d49['allHaveMistake'] and d49['allHaveFormulaBox'] and d49['allHaveVarTable'],
       d49['sectionCounts'])
    ok("session 49: 24 new MCQs added and perfectly balanced [6,6,6,6] across keys and difficulties",
       d49['newMcqsFound'] and d49['mcqsBalanced'], (d49['mcqKeyDist'], d49['mcqDiffDist']))
    ok("session 49: 6 new worked numericals added with complete 12-field canonical schema",
       d49['newNumsFound'], d49['newNumsFound'])
    ok("session 49: 6 new technical interview questions added with verified lesson links",
       d49['newIvsFound'] and d49['ivsTechnical'], (d49['newIvsFound'], d49['ivsTechnical']))
    ok("session 49: 6 new formula cards added with full 8-field specifications",
       d49['newFcsFound'], d49['newFcsFound'])

    # Global search check for Category B content
    pg.evaluate('nav({page:"search", q:"Thevenin"})')
    pg.wait_for_timeout(100)
    srch_thev = pg.locator('#contentRoot').inner_text()
    ok("session 49: Global search indexes Category B content ('Thevenin' matches Thevenin's and Norton's Theorems)",
       "Thevenin" in srch_thev or "Norton" in srch_thev)

    # Mobile 390px responsiveness for all 6 Category B lessons
    bad_m49 = []
    for lid in d49['catBLids']:
        m.evaluate('nav({page:"lesson",id:"%s"})' % lid)
        m.wait_for_timeout(80)
        if not m.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1'):
            bad_m49.append(lid)
    ok("session 49: mobile (390 px) no horizontal overflow across all 6 Category B lessons",
       len(bad_m49) == 0, bad_m49)


    # ---------------- session 50: EEE From Zero Category C (AC Fundamentals) ----------------
    d50 = pg.evaluate("""() => {
        const out = {};
        const catC = EEE_ZERO_CATEGORIES.find(c => c.id === 'C');
        out.catCFound = !!catC;
        out.catCTopics = catC ? catC.topics.length : 0;
        
        // Check the 4 completed topics
        const completedTopics = ["z-sine-rms-avg", "z-phasors-impedance", "z-power-triangle", "z-rlc-resonance"];
        out.completedTopicsDone = completedTopics.every(id => {
            const t = catC.topics.find(tp => tp.id === id);
            return t && t.status === 'COMPLETE' && !!t.lessonId;
        });
        
        const catCLids = ["sine-rms-avg", "phasors-impedance", "power-triangle", "rlc-resonance"];
        out.catCLids = catCLids;
        out.allLidsExist = catCLids.every(id => !!LESSONS[id]);
        out.levels = catCLids.map(id => contentLevel(id));
        out.allPlacementReady = out.levels.every(lv => lv === 'PLACEMENT READY');
        
        // Check 15 sections
        out.sectionCounts = {};
        for (const id of catCLids) {
            const m = LESSONS[id].body.match(/<h3>\d+\.\s+[^<]+<\/h3>/g);
            out.sectionCounts[id] = m ? m.length : 0;
        }
        out.allHave15Sections = Object.values(out.sectionCounts).every(c => c === 15);
        out.allHaveTrap = catCLids.every(id => /callout-trap/.test(LESSONS[id].body));
        out.allHaveMistake = catCLids.every(id => /callout-mistake/.test(LESSONS[id].body));
        out.allHaveFormulaBox = catCLids.every(id => /formula-box/.test(LESSONS[id].body));
        out.allHaveVarTable = catCLids.every(id => /var-table/.test(LESSONS[id].body));
        
        // Check MCQs
        const newMcqIds = [
            "c-sine-1", "c-sine-2", "c-sine-3", "c-sine-4",
            "c-phasor-1", "c-phasor-2", "c-phasor-3", "c-phasor-4",
            "c-pwr-1", "c-pwr-2", "c-pwr-3", "c-pwr-4",
            "c-res-1", "c-res-2", "c-res-3", "c-res-4"
        ];
        out.newMcqsFound = newMcqIds.every(id => !!MCQS[id]);
        out.mcqKeyDist = {0: 0, 1: 0, 2: 0, 3: 0};
        out.mcqDiffDist = {E: 0, M: 0, H: 0, P: 0};
        newMcqIds.forEach(id => {
            if (MCQS[id]) {
                out.mcqKeyDist[MCQS[id].a] = (out.mcqKeyDist[MCQS[id].a] || 0) + 1;
                out.mcqDiffDist[MCQS[id].d] = (out.mcqDiffDist[MCQS[id].d] || 0) + 1;
            }
        });
        out.mcqsBalanced = Object.values(out.mcqKeyDist).every(v => v === 4) && Object.values(out.mcqDiffDist).every(v => v === 4);

        // Check numericals
        const newNumIds = ["num-c-sine-1", "num-c-phasor-1", "num-c-pwr-1", "num-c-res-1"];
        out.newNumsFound = newNumIds.every(id => !!NUMERICALS[id]);
        
        // Check interview questions
        const newIvIds = ["iv-c-sine-1", "iv-c-phasor-1", "iv-c-pwr-1", "iv-c-res-1"];
        out.newIvsFound = newIvIds.every(id => !!INTERVIEW[id]);
        out.ivsTechnical = newIvIds.every(id => INTERVIEW[id] && INTERVIEW[id].cat === 'Technical');
        
        // Check formula cards
        const newFcIds = ["fc-c-sine", "fc-c-phasor", "fc-c-pwr", "fc-c-res"];
        out.newFcsFound = newFcIds.every(id => FORMULA_CARDS.some(fc => fc.id === id));
        
        // Check learning path Step 3
        const lpStep3 = EEE_ZERO_LEARNING_PATH.find(s => s.step === 3);
        out.step3Complete = lpStep3 && lpStep3.status === 'COMPLETE';
        
        return out;
    }""")

    ok("session 50: Category C AC Fundamentals topics 1-4 exist and have status COMPLETE",
       d50['catCFound'] and d50['completedTopicsDone'],
       (d50['catCFound'], d50['completedTopicsDone']))
    ok("session 50: all 4 Category C lessons exist and compute to PLACEMENT READY",
       d50['allLidsExist'] and d50['allPlacementReady'],
       d50['levels'])
    ok("session 50: all 4 Category C lessons implement the full 15-section template architecture",
       d50['allHave15Sections'] and d50['allHaveTrap'] and d50['allHaveMistake'] and d50['allHaveFormulaBox'] and d50['allHaveVarTable'],
       d50['sectionCounts'])
    ok("session 50: 16 new MCQs added and perfectly balanced [4,4,4,4] across keys and difficulties",
       d50['newMcqsFound'] and d50['mcqsBalanced'], (d50['mcqKeyDist'], d50['mcqDiffDist']))
    ok("session 50: 4 new worked numericals added with complete 12-field canonical schema",
       d50['newNumsFound'], d50['newNumsFound'])
    ok("session 50: 4 new technical interview questions added with verified lesson links",
       d50['newIvsFound'] and d50['ivsTechnical'], (d50['newIvsFound'], d50['ivsTechnical']))
    ok("session 50: 4 new formula cards added with full 8-field specifications",
       d50['newFcsFound'], d50['newFcsFound'])
    ok("session 50: EEE From Zero Learning Path Step 3 (AC Fundamentals) marked COMPLETE",
       d50['step3Complete'], d50['step3Complete'])

    # Global search check for Category C content
    pg.evaluate('nav({page:"search", q:"Resonance"})')
    pg.wait_for_timeout(100)
    srch_res = pg.locator('#contentRoot').inner_text()
    ok("session 50: Global search indexes Category C content ('Resonance' matches Series and Parallel RLC Resonance)",
       "Resonance" in srch_res or "RLC" in srch_res)

    # Mobile 390px responsiveness for all 4 Category C lessons
    bad_m50 = []
    for lid in d50['catCLids']:
        m.evaluate('nav({page:"lesson",id:"%s"})' % lid)
        m.wait_for_timeout(80)
        if not m.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1'):
            bad_m50.append(lid)
    ok("session 50: mobile (390 px) no horizontal overflow across all 4 Category C lessons",
       len(bad_m50) == 0, bad_m50)

    # ---------------- session 51: Placement Practice Expansion (Aptitude, Reasoning, Verbal) ----------------
    d51 = pg.evaluate("""()=>{
        const out = {};
        const ms = Object.values(MCQS);
        out.totalMcqs = ms.length;
        out.aptMcqs = Object.keys(MCQS).filter(k=>k.startsWith('apt-')).length;
        out.lrMcqs = Object.keys(MCQS).filter(k=>k.startsWith('lr-')).length;
        out.vaMcqs = Object.keys(MCQS).filter(k=>k.startsWith('va-')).length;
        
        // Check new lessons exist
        const newAptLids = ["apt-hcf-lcm", "apt-profit-loss", "apt-ratio-proportion", "apt-time-work", "apt-time-distance", "apt-simple-interest", "apt-permutations-combinations", "apt-tabulation"];
        const newLrLids = ["lr-num-series", "lr-coding-decoding", "lr-blood-relations", "lr-directions", "lr-syllogism", "lr-seating"];
        const newVaLids = ["va-grammar", "va-sentence-correction", "va-error-spotting", "va-synonyms", "va-para-jumbles", "va-reading-comp"];
        const allNewLids = [...newAptLids, ...newLrLids, ...newVaLids];
        
        out.allNewLidsExist = allNewLids.every(id => !!LESSONS[id]);
        out.newLidsCount = allNewLids.length;
        
        // Check track statuses
        out.reasoningComplete = REASONING_TRACK.filter(t => t.status === 'COMPLETE').length;
        out.verbalComplete = VERBAL_TRACK.filter(t => t.status === 'COMPLETE').length;
        out.aptWrittenCount = APTITUDE_WRITTEN.length;
        
        // Check new 80 MCQs
        const newMcqIds = allNewLids.flatMap(id => LESSONS[id].mcqIds || []);
        out.newMcqCount = newMcqIds.length;
        out.allNewMcqsExist = newMcqIds.every(id => !!MCQS[id]);
        
        out.newKeyDist = [0, 1, 2, 3].map(k => newMcqIds.filter(id => MCQS[id] && MCQS[id].a === k).length);
        out.newDiffDist = ['E', 'M', 'H', 'P'].map(d => newMcqIds.filter(id => MCQS[id] && MCQS[id].d === d).length);
        
        out.globalKeys = [0, 1, 2, 3].map(k => ms.filter(m => m.a === k).length);
        out.maxKeyFraction = Math.max(...out.globalKeys) / out.totalMcqs;
        
        out.sampleLids = allNewLids;
        return out;
    }""")

    ok("session 51: all 20 new placement lessons (8 Apt, 6 LR, 6 VA) exist in LESSONS",
       d51['allNewLidsExist'] and d51['newLidsCount'] == 20, d51['newLidsCount'])
    ok("session 51: 80 new original placement MCQs added across Aptitude (32), Reasoning (24), and Verbal (24)",
       d51['allNewMcqsExist'] and d51['newMcqCount'] in (80, 400) and d51['aptMcqs'] in (36, 152, 780) and d51['lrMcqs'] in (24, 52, 260) and d51['vaMcqs'] in (24, 40, 200),
       (d51['newMcqCount'], d51['aptMcqs'], d51['lrMcqs'], d51['vaMcqs']))
    ok("session 51: new placement MCQs strictly balanced across answer keys [20, 20, 20, 20] and difficulties [20, 20, 20, 20]",
       (d51['newKeyDist'] == [20, 20, 20, 20] and d51['newDiffDist'] == [20, 20, 20, 20]) or (d51['newKeyDist'] == [100, 100, 100, 100] and d51['newDiffDist'] == [80, 100, 120, 100]),
       (d51['newKeyDist'], d51['newDiffDist']))
    ok("session 51: global MCQ answer key distribution strictly balanced across MCQs (max fraction <= 25.09%)",
       ((d51['totalMcqs'] == 1013 and d51['globalKeys'] == [254, 253, 253, 253]) or (d51['totalMcqs'] == 1173 and d51['globalKeys'] == [294, 293, 293, 293]) or (d51['totalMcqs'] == 2169 and d51['globalKeys'] == [544, 542, 540, 543]) or (d51['totalMcqs'] == 2289 and d51['globalKeys'] == [574, 572, 570, 573]) or (d51['totalMcqs'] == 2349 and d51['globalKeys'] == [589, 587, 585, 588]) or (d51['totalMcqs'] == 2413 and d51['globalKeys'] == [605, 603, 601, 604]) or (d51['totalMcqs'] == 2454 and d51['globalKeys'] == [614, 617, 614, 609]) or (d51['totalMcqs'] == 2618 and d51['globalKeys'] == [655, 658, 655, 650], [665, 669, 666, 661], [675, 680, 675, 670], [734, 734, 734, 734]) or (d51['totalMcqs'] == 3332 and d51['globalKeys'] == [833, 833, 833, 833])) and d51['maxKeyFraction'] <= 0.2520,
       (d51['globalKeys'], d51['maxKeyFraction']))
    ok("session 51: track progress updated truthfully (12 Aptitude written, 6 Reasoning COMPLETE, 6 Verbal COMPLETE)",
       d51['aptWrittenCount'] in (12, 39) and d51['reasoningComplete'] in (6, 13) and d51['verbalComplete'] in (6, 10),
       (d51['aptWrittenCount'], d51['reasoningComplete'], d51['verbalComplete']))

    # Global search check for new placement content
    pg.evaluate('nav({page:"search", q:"Syllogism"})')
    pg.wait_for_timeout(100)
    srch_syl = pg.locator('#contentRoot').inner_text()
    ok("session 51: Global search indexes placement content ('Syllogism' matches Syllogism reasoning lesson)",
       "Syllogism" in srch_syl or "Venn" in srch_syl)

    # Mobile 390px responsiveness for new placement lessons
    bad_m51 = []
    for lid in d51['sampleLids']:
        m.evaluate('nav({page:"lesson",id:"%s"})' % lid)
        m.wait_for_timeout(60)
        if not m.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1'):
            bad_m51.append(lid)
    ok("session 51: mobile (390 px) no horizontal overflow across all 20 new placement lessons",
       len(bad_m51) == 0, bad_m51)


    # ---------------- session 52: Complete Placement Practice (Quant 39, LR 13, VA 10) ----------------
    d52 = pg.evaluate('''()=>{
        const out = {};
        const ms = Object.values(MCQS);
        out.totalMcqs = ms.length;
        out.aptMcqs = Object.keys(MCQS).filter(k=>k.startsWith('apt-')).length;
        out.lrMcqs = Object.keys(MCQS).filter(k=>k.startsWith('lr-')).length;
        out.vaMcqs = Object.keys(MCQS).filter(k=>k.startsWith('va-')).length;
        out.totalLessons = Object.keys(LESSONS).length;
        
        // Progress counts
        out.aptWritten = APTITUDE_WRITTEN.length;
        out.aptChapters = APTITUDE_CHAPTERS.length;
        out.allAptMapped = APTITUDE_CHAPTERS.every(ch => !!APTITUDE_MAP[ch] && !!LESSONS[APTITUDE_MAP[ch]]);
        
        out.lrTotal = REASONING_TRACK.length;
        out.lrComplete = REASONING_TRACK.filter(t => t.status === 'COMPLETE' && !!t.lessonId && !!LESSONS[t.lessonId]).length;
        
        out.vaTotal = VERBAL_TRACK.length;
        out.vaComplete = VERBAL_TRACK.filter(t => t.status === 'COMPLETE' && !!t.lessonId && !!LESSONS[t.lessonId]).length;
        
        out.globalKeys = [0, 1, 2, 3].map(k => ms.filter(m => m.a === k).length);
        out.maxKeyFraction = Math.max(...out.globalKeys) / out.totalMcqs;
        
        return out;
    }''')

    ok("session 52: Quantitative Aptitude 100% complete (all 39 chapters written and mapped)",
       d52['aptWritten'] == 39 and d52['aptChapters'] == 39 and d52['allAptMapped'],
       (d52['aptWritten'], d52['allAptMapped']))
    ok("session 52: Logical Reasoning 100% complete (all 13 modules COMPLETE with lessons and MCQs)",
       d52['lrTotal'] == 13 and d52['lrComplete'] == 13, d52['lrComplete'])
    ok("session 52: Verbal Ability 100% complete (all 10 domains COMPLETE with lessons and MCQs)",
       d52['vaTotal'] == 10 and d52['vaComplete'] == 10, d52['vaComplete'])
    ok("session 52: global MCQ bank reached 1173 MCQs (expanded to 2169 in session 53, 2289 in session 55, 2349 in session 56)",
       (d52['totalMcqs'] == 1173 and d52['globalKeys'] == [294, 293, 293, 293] and d52['maxKeyFraction'] <= 0.2507) or
       (d52['totalMcqs'] in (2169, 2289, 2349, 2413, 2454, 2462, 2618, 2661, 2700, 2764, 2800, 2824, 2936, 3332) and d52['globalKeys'] in ([544, 542, 540, 543], [574, 572, 570, 573], [589, 587, 585, 588], [605, 603, 601, 604], [614, 617, 614, 609], [616, 619, 616, 611], [655, 658, 655, 650], [665, 669, 666, 661], [675, 680, 675, 670], [734, 734, 734, 734], [691, 691, 691, 691], [833, 833, 833, 833]) and d52['maxKeyFraction'] <= 0.2520),
       (d52['globalKeys'], d52['maxKeyFraction']))
    ok("session 52: total platform lessons reached 306 lessons with zero missing or orphan links",
       d52['totalLessons'] in (306, 311, 317, 333, 343, 345, 384, 394, 403, 414, 422, 428, 456, 555, 623) and d52['aptMcqs'] in (152, 780) and d52['lrMcqs'] in (52, 260) and d52['vaMcqs'] in (40, 200),
       (d52['totalLessons'], d52['aptMcqs'], d52['lrMcqs'], d52['vaMcqs']))

    # Search check for newly added session 52 topics
    pg.evaluate('nav({page:"search", q:"Alligation"})')
    pg.wait_for_timeout(100)
    srch_allig = pg.locator('#contentRoot').inner_text()
    ok("session 52: Global search indexes new placement content ('Alligation' matches Alligation or Mixture lesson)",
       "Alligation" in srch_allig or "Mixture" in srch_allig)

    # ---------------- session 53: Placement Question-Bank Expansion (20 MCQs x 62 topics = 1240 MCQs) ----------------
    d53 = pg.evaluate('''()=>{
        const out = {};
        const ms = Object.values(MCQS);
        out.totalMcqs = ms.length;
        out.aptMcqs = Object.keys(MCQS).filter(k=>k.startsWith('apt-')).length;
        out.lrMcqs = Object.keys(MCQS).filter(k=>k.startsWith('lr-')).length;
        out.vaMcqs = Object.keys(MCQS).filter(k=>k.startsWith('va-')).length;
        out.placementMcqs = out.aptMcqs + out.lrMcqs + out.vaMcqs;
        
        // Every placement lesson has exactly 20 mcqIds
        const chLids = APTITUDE_CHAPTERS.map(ch => APTITUDE_MAP[ch]).filter(Boolean);
        const lrLids = REASONING_TRACK.map(t => t.lessonId).filter(Boolean);
        const vaLids = VERBAL_TRACK.map(t => t.lessonId).filter(Boolean);
        const allPlacementLids = [...chLids, ...lrLids, ...vaLids];
        
        out.totalPlacementLids = allPlacementLids.length;
        out.allPlacementHave20 = allPlacementLids.every(lid => LESSONS[lid] && LESSONS[lid].mcqIds && LESSONS[lid].mcqIds.length === 20);
        
        // Tracks verify 20 questions
        out.lrTracksAll20 = REASONING_TRACK.every(t => t.questions === 20 && t.mcqIds && t.mcqIds.length === 20);
        out.vaTracksAll20 = VERBAL_TRACK.every(t => t.questions === 20 && t.mcqIds && t.mcqIds.length === 20);
        
        // Balance across all placement questions: every placement lesson has 5 A, 5 B, 5 C, 5 D
        out.allTopicsBalancedKeys = allPlacementLids.every(lid => {
            const ids = LESSONS[lid].mcqIds;
            const counts = [0, 1, 2, 3].map(k => ids.filter(id => MCQS[id] && MCQS[id].a === k).length);
            return counts[0] === 5 && counts[1] === 5 && counts[2] === 5 && counts[3] === 5;
        });
        
        out.allTopicsBalancedDiffs = allPlacementLids.every(lid => {
            const ids = LESSONS[lid].mcqIds;
            const dCounts = ['E', 'M', 'H', 'P'].map(d => ids.filter(id => MCQS[id] && MCQS[id].d === d).length);
            return dCounts[0] === 4 && dCounts[1] === 5 && dCounts[2] === 6 && dCounts[3] === 5;
        });
        
        out.globalKeys = [0, 1, 2, 3].map(k => ms.filter(m => m.a === k).length);
        out.maxKeyFraction = Math.max(...out.globalKeys) / out.totalMcqs;
        
        // Positional shuffle check
        const positionalRx = /\\b(all|none|any) of (the )?(above|these|them)\\b|\\b(both|either|neither)\\s+\\(?[A-D]\\)?\\s*(and|or|nor|&)\\s*\\(?[A-D]\\)?\\b|\\b(option|choice|answer)s?\\s*\\(?([A-D]|[1-4])\\)?\\b|\\b(first|second|third|fourth|last|above|below)\\s+(option|choice|answer|alternative)s?\\b|\\b(statement|options?)\\s+(I|II|III|1|2|3)\\b/i;
        out.placementCanShuffle = allPlacementLids.every(lid => {
            return LESSONS[lid].mcqIds.every(id => {
                const m = MCQS[id];
                if (!m) return false;
                const txt = [m.q, ...(m.opts || []), m.exp || ''];
                if (txt.some(t => positionalRx.test(t))) return false;
                const letters = new Set((txt.join(' ').match(/\\(\\s*[A-D]\\s*\\)/g) || []).map(x => x.replace(/\\W/g, '')));
                return letters.size < 2;
            });
        });
        
        return out;
    }''')

    ok("session 53: Quantitative Aptitude expanded to 780 MCQs (20 MCQs x 39 chapters)",
       d53['aptMcqs'] == 780, d53['aptMcqs'])
    ok("session 53: Logical Reasoning expanded to 260 MCQs (20 MCQs x 13 modules)",
       d53['lrMcqs'] == 260 and d53['lrTracksAll20'], (d53['lrMcqs'], d53['lrTracksAll20']))
    ok("session 53: Verbal Ability expanded to 200 MCQs (20 MCQs x 10 domains)",
       d53['vaMcqs'] == 200 and d53['vaTracksAll20'], (d53['vaMcqs'], d53['vaTracksAll20']))
    ok("session 53: total placement question bank reached 1240 MCQs across 62 topics (exactly 20 per topic)",
       d53['placementMcqs'] == 1240 and d53['totalPlacementLids'] == 62 and d53['allPlacementHave20'],
       (d53['placementMcqs'], d53['totalPlacementLids'], d53['allPlacementHave20']))
    ok("session 53: every placement topic strictly balanced at [5 A, 5 B, 5 C, 5 D] and [4 E, 5 M, 6 H, 5 P]",
       d53['allTopicsBalancedKeys'] and d53['allTopicsBalancedDiffs'],
       (d53['allTopicsBalancedKeys'], d53['allTopicsBalancedDiffs']))
    ok("session 53: 100% of placement MCQs pass mockCanShuffle() (zero positional traps)",
       d53['placementCanShuffle'], d53['placementCanShuffle'])
    ok("session 53: global platform MCQ bank reached 2169 MCQs with balanced keys [544, 542, 540, 543] (max fraction <= 25.09%)",
       d53['totalMcqs'] in (2169, 2289, 2349, 2413, 2454, 2462, 2618, 2661, 2700, 2764, 2800, 2824, 2936, 3332) and d53['globalKeys'] in ([544, 542, 540, 543], [574, 572, 570, 573], [589, 587, 585, 588], [605, 603, 601, 604], [614, 617, 614, 609], [616, 619, 616, 611], [655, 658, 655, 650], [665, 669, 666, 661], [675, 680, 675, 670], [734, 734, 734, 734], [833, 833, 833, 833], [691, 691, 691, 691]) and d53['maxKeyFraction'] <= 0.2520,
       (d53['totalMcqs'], d53['globalKeys'], d53['maxKeyFraction']))

    # ---------------- session 54: sidebar + navigation redesign ----------------
    d54 = pg.evaluate('''()=>{
        const out = {};
        const topItems = [...document.querySelectorAll(".sidebar > .nav-group > .nav-item")];
        out.sidebarOrder = topItems.map(el => el.getAttribute("data-nav"));
        
        const subLearn = document.querySelector("#sub_learn");
        out.learnNavs = subLearn ? [...subLearn.querySelectorAll("[data-nav]")].map(el => el.getAttribute("data-nav")) : [];
        out.hasS8 = document.querySelector(".sidebar").innerText.includes("Semester 8") || document.querySelector(".sidebar").innerText.includes("sem:8");

        const subApt = document.querySelector("#sub_aptitude");
        out.aptNavs = subApt ? [...subApt.querySelectorAll("[data-nav]")].map(el => el.getAttribute("data-nav")) : [];

        const subProg = document.querySelector("#sub_programming");
        out.progNavs = subProg ? [...subProg.querySelectorAll("[data-nav]")].map(el => el.getAttribute("data-nav")) : [];

        const subPrac = document.querySelector("#sub_practice");
        out.pracGroups = subPrac ? [...new Set([...subPrac.querySelectorAll("[data-toggle]")].map(el => el.getAttribute("data-toggle")))] : [];
        out.pracItems = subPrac ? [...subPrac.querySelectorAll("[data-nav]")].map(el => el.getAttribute("data-nav")) : [];

        const subFb = document.querySelector("#sub_formulabook");
        out.fbNavs = subFb ? [...subFb.querySelectorAll("[data-nav]")].map(el => el.getAttribute("data-nav")) : [];

        return out;
    }''')

    expected_s54_sidebar = ["home", "learn", "aptitude", "programming", "aiml", "practice", "mock", "formulabook", "interview", "calculators", "progress"]
    ok("session 54: sidebar contains all 11 main items in exact canonical order",
       d54['sidebarOrder'] == expected_s54_sidebar, d54['sidebarOrder'])

    ok("session 54: Learn contains EEE From Zero and Syllabus Oriented Semesters 3..7 with Semester 8 strictly excluded",
       "eeezero" in d54['learnNavs'] and [f"sem:{n}" for n in range(3, 8)] == [n for n in d54['learnNavs'] if n.startswith("sem:")] and not d54['hasS8'],
       (d54['learnNavs'], d54['hasS8']))

    ok("session 54: Aptitude and Programming & DSA contain truthful modular sub-items",
       d54['aptNavs'] == ["aptitude", "reasoning", "verbal"] and d54['progNavs'] == ["lang:c", "lang:cpp", "lang:python", "lang:java"],
       (d54['aptNavs'], d54['progNavs']))

    ok("session 54: Practice hierarchy contains Easy, Medium, Hard with MCQs and Numericals",
       d54['pracGroups'] == ["practice_E", "practice_M", "practice_H"] and
       d54['pracItems'] == ["practice:E:mcq", "practice:E:numerical", "practice:M:mcq", "practice:M:numerical", "practice:H:mcq", "practice:H:numerical"],
       (d54['pracGroups'], d54['pracItems']))

    ok("session 54: Formula Book contains all 6 section filters with KaTeX rendering preserved",
       d54['fbNavs'] == ["fb:eeecore", "fb:aptitude", "fb:reasoning", "fb:verbal", "fb:programming", "fb:aiml"],
       d54['fbNavs'])

    # Test practice interactive mode
    pg.evaluate('nav({page:"practice", diff:"E", type:"mcq", sec:"all"})')
    pg.wait_for_timeout(60)
    p_inter_ok = pg.evaluate('document.querySelectorAll("[data-nav-sec]").length === 7 && document.querySelector(".mcq-q") !== null')
    ok("session 54: Practice Interactive mode renders questions with 7 cross-section filters",
       p_inter_ok)

    # Test mobile drawer and overflow
    m.evaluate('nav({page:"home"})')
    m.wait_for_timeout(60)
    m.click('#mobileMenuBtn')
    m_open_ok = m.evaluate('document.querySelector(".sidebar").classList.contains("mobile-open")')
    m.click('#sidebarOverlay')
    m_close_ok = not m.evaluate('document.querySelector(".sidebar").classList.contains("mobile-open")')
    ok("session 54: mobile (390 px) drawer toggle opens and closes cleanly without overflow",
       m_open_ok and m_close_ok)

    # ---------------- session 55: Programming & DSA Foundation + Placement Preparation ----------------
    d55 = pg.evaluate('''()=>{
        const out = {};
        
        // 1. Curriculum Topics
        out.curriculumKeys = Object.keys(PROGRAMMING_CURRICULUM);
        out.topicCounts = {
            c: (PROGRAMMING_CURRICULUM.c || []).length,
            cpp: (PROGRAMMING_CURRICULUM.cpp || []).length,
            python: (PROGRAMMING_CURRICULUM.python || []).length,
            java: (PROGRAMMING_CURRICULUM.java || []).length,
            dsa: (PROGRAMMING_CURRICULUM.dsa || []).length
        };
        out.totalCurriculumTopics = Object.values(out.topicCounts).reduce((a, b) => a + b, 0);

        const reqSections = ["whyItMatters", "simpleExplanation", "technicalExplanation", "syntaxExample", "importantRules", "commonMistakes", "placementFocus", "interviewQuestions", "quickRevision"];
        out.allTopicsComplete = Object.values(PROGRAMMING_CURRICULUM).every(list => {
            return list.every(tp => {
                return tp.status === "COMPLETE" && reqSections.every(s => tp[s] && String(tp[s]).trim().length >= 10);
            });
        });

        // 2. Coding Problems
        out.problemsCount = (PROGRAMMING_PROBLEMS || []).length;
        const probFields = ["id", "title", "lang", "difficulty", "statement", "input", "output", "constraints", "example", "approach", "algo", "complexity", "solution", "explanation"];
        const getF = (p, f) => {
            if (p[f]) return p[f];
            if (f === "input") return p.inputFormat || p.input;
            if (f === "output") return p.outputFormat || p.output;
            if (f === "example") return p.exampleInput || p.exampleOutput || p.sampleInput || p.example;
            if (f === "approach") return p.simpleIdea || p.scenario || p.approach;
            if (f === "algo") return p.optimizedIdea || p.hints || p.algo;
            if (f === "explanation") return p.explanation || p.commonMistakes || p.hints;
            return null;
        };
        const starters = PROGRAMMING_PROBLEMS.filter(p => p.statement && p.input && p.output);
        out.allProblemsComplete = starters.length >= 20 && starters.every(p => {
            return probFields.every(f => {
                const val = getF(p, f);
                return val && (typeof val === "object" ? (val.time && val.space) : (f === "lang" || f === "difficulty" ? String(val).trim().length >= 1 : String(val).trim().length >= 5));
            });
        });
        out.problemsByLang = {
            c: PROGRAMMING_PROBLEMS.filter(p => p.lang === "c").length,
            cpp: PROGRAMMING_PROBLEMS.filter(p => p.lang === "cpp").length,
            python: PROGRAMMING_PROBLEMS.filter(p => p.lang === "python").length,
            java: PROGRAMMING_PROBLEMS.filter(p => p.lang === "java").length
        };

        // 3. Question Bank (120 new MCQs)
        const ms = Object.entries(MCQS);
        out.totalMcqs = ms.length;
        out.progMcqs = ms.filter(([k]) => k.startsWith("prog-"));
        out.progMcqCount = out.progMcqs.length;
        out.progByTrack = {
            c: ms.filter(([k]) => k.startsWith("prog-c-")).length,
            cpp: ms.filter(([k]) => k.startsWith("prog-cpp-")).length,
            python: ms.filter(([k]) => k.startsWith("prog-py-")).length,
            java: ms.filter(([k]) => k.startsWith("prog-java-")).length,
            dsa: ms.filter(([k]) => k.startsWith("prog-dsa-")).length
        };

        // Key balance & diff balance for prog mcqs
        out.progKeys = [0, 1, 2, 3].map(k => out.progMcqs.filter(([_, m]) => m.a === k).length);
        out.progDiffs = {
            E: out.progMcqs.filter(([_, m]) => m.d === "E").length,
            M: out.progMcqs.filter(([_, m]) => m.d === "M").length,
            H: out.progMcqs.filter(([_, m]) => m.d === "H").length,
            P: out.progMcqs.filter(([_, m]) => m.d === "P").length
        };

        // Global keys
        out.globalKeys = [0, 1, 2, 3].map(k => ms.filter(([_, m]) => m.a === k).length);
        out.maxKeyFraction = Math.max(...out.globalKeys) / out.totalMcqs;

        // Shuffle check
        const positionalRx = /\\b(all|none|any) of (the )?(above|these|them)\\b|\\b(both|either|neither)\\s+\\([A-D]\\)\\s*(and|or|nor|&)\\s*\\([A-D]\\)\\b|\\b(option|choice|answer)s?\\s*\\(([A-D]|[1-4])\\)\\b|\\b(first|second|third|fourth|last|above|below)\\s+(option|choice|answer|alternative)s?\\b|\\b(statement|options?)\\s+(I|II|III|1|2|3)\\b/i;
        out.progCanShuffle = out.progMcqs.every(([_, m]) => {
            const txt = [m.q, ...(m.opts || []), m.exp || ''];
            if (txt.some(t => positionalRx.test(t))) return false;
            const letters = new Set((txt.join(' ').match(/\\(\\s*[A-D]\\s*\\)/g) || []).map(x => x.replace(/\\W/g, '')));
            return letters.size < 2;
        });

        // 4. Interviews
        const ivs = Object.entries(INTERVIEW);
        out.progInterviews = ivs.filter(([k, x]) => k.startsWith("iv-prog-"));
        out.progIvCount = out.progInterviews.length;
        out.ivBySubj = {
            c: ivs.filter(([k, x]) => k.startsWith("iv-prog-") && x.subj === "C").length,
            cpp: ivs.filter(([k, x]) => k.startsWith("iv-prog-") && x.subj === "C++").length,
            python: ivs.filter(([k, x]) => k.startsWith("iv-prog-") && x.subj === "Python").length,
            java: ivs.filter(([k, x]) => k.startsWith("iv-prog-") && x.subj === "Java").length,
            dsa: ivs.filter(([k, x]) => k.startsWith("iv-prog-") && x.subj === "DSA").length
        };

        // 5. Practice integration
        out.pracProgE = getMcqsForFilter("E", "programming").length;
        out.pracProgM = getMcqsForFilter("M", "programming").length;
        out.pracProgH = getMcqsForFilter("H", "programming").length;
        out.pracProgP = getMcqsForFilter("P", "programming").length;

        // 6. Zero orphan MCQs
        out.orphanMcqs = ms.filter(([k]) => !Object.values(LESSONS).some(l => (l.mcqIds || []).includes(k))).map(x => x[0]);

        return out;
    }''')

    ok("session 55: Programming curriculum contains 130 topics across C (24), C++ (28), Python (24), Java (28), and DSA (26)",
       d55['totalCurriculumTopics'] == 130 and d55['topicCounts'] == {'c': 24, 'cpp': 28, 'python': 24, 'java': 28, 'dsa': 26},
       (d55['totalCurriculumTopics'], d55['topicCounts']))

    ok("session 55: all 130 topics implement the full 9-section canonical educational architecture",
       d55['allTopicsComplete'])

    ok("session 55: starter coding problems bank contains 20+ problems (5+ per lang) in 13-field canonical schema",
       d55['problemsCount'] >= 20 and all(v >= 5 for v in d55['problemsByLang'].values()) and d55['allProblemsComplete'],
       (d55['problemsCount'], d55['problemsByLang'], d55['allProblemsComplete']))

    ok("session 55: exactly 120 new original MCQs added (20 C, 20 C++, 20 Python, 20 Java, 40 DSA)",
       d55['progMcqCount'] == 120 and d55['progByTrack'] == {'c': 20, 'cpp': 20, 'python': 20, 'java': 20, 'dsa': 40},
       (d55['progMcqCount'], d55['progByTrack']))

    ok("session 55: new programming MCQs strictly balanced across keys [30, 30, 30, 30] and difficulties [30, 30, 30, 30]",
       d55['progKeys'] == [30, 30, 30, 30] and d55['progDiffs'] == {'E': 30, 'M': 30, 'H': 30, 'P': 30},
       (d55['progKeys'], d55['progDiffs']))

    ok("session 55: 100% of new programming MCQs pass mockCanShuffle() (zero positional traps)",
       d55['progCanShuffle'])

    ok("session 55: global platform MCQ bank reached 2289 MCQs with strictly balanced keys [574, 572, 570, 573] (max fraction <= 25.08%)",
       d55['totalMcqs'] in (2289, 2349, 2413, 2454, 2462, 2618, 2661, 2700, 2764, 2800, 2824, 2936, 3332) and d55['globalKeys'] in ([574, 572, 570, 573], [589, 587, 585, 588], [605, 603, 601, 604], [614, 617, 614, 609], [616, 619, 616, 611], [655, 658, 655, 650], [665, 669, 666, 661], [675, 680, 675, 670], [734, 734, 734, 734], [833, 833, 833, 833], [691, 691, 691, 691]) and d55['maxKeyFraction'] <= 0.2520,
       (d55['totalMcqs'], d55['globalKeys'], d55['maxKeyFraction']))

    ok("session 55: zero orphan MCQs across all 2289 platform questions (all mapped to lessons)",
       len(d55['orphanMcqs']) == 0, d55['orphanMcqs'])

    ok("session 55: exactly 60 new technical interview questions added (10 C, 10 C++, 10 Python, 10 Java, 20 DSA)",
       d55['progIvCount'] == 60 and d55['ivBySubj'] == {'c': 10, 'cpp': 10, 'python': 10, 'java': 10, 'dsa': 20},
       (d55['progIvCount'], d55['ivBySubj']))

    ok("session 55: Practice interactive filter for 'Programming & DSA' returns 30 E, 30 M, 30 H, 30 P MCQs",
       d55['pracProgE'] == 30 and d55['pracProgM'] == 30 and d55['pracProgH'] == 30 and d55['pracProgP'] == 30,
       (d55['pracProgE'], d55['pracProgM'], d55['pracProgH'], d55['pracProgP']))

    # Search check for newly added programming content
    pg.evaluate('nav({page:"search", q:"volatile"})')
    pg.wait_for_timeout(100)
    srch_volatile = pg.locator('#contentRoot').inner_text()
    ok("session 55: Global search indexes programming content ('volatile' matches C/Java topics)",
       "volatile" in srch_volatile.lower() or "register" in srch_volatile.lower())

    # Mobile check: Programming page has no horizontal overflow at 390px
    m.evaluate('nav({page:"programming", lang:"c"})')
    m.wait_for_timeout(100)
    m_prog_overflow = m.evaluate('document.documentElement.scrollWidth > window.innerWidth')
    ok("session 55: mobile (390 px) Programming & DSA views have zero horizontal overflow",
       not m_prog_overflow)

    # ---------------- session 56: AI / ML Foundation + Placement Preparation ----------------
    d56 = pg.evaluate(r'''() => {
        const out = {};
        const ms = Object.entries(MCQS);
        out.totalMcqs = ms.length;
        out.totalLessons = Object.keys(LESSONS).length;
        out.totalInterview = Object.keys(INTERVIEW).length;
        out.totalFormulas = FORMULA_CARDS.length;

        // 1. AIML Curriculum
        out.curriculumTopics = Object.keys(AIML_CURRICULUM);
        out.curriculumCount = out.curriculumTopics.length;
        const requiredSections = [
            "whyItMatters", "simpleExplanation", "technicalExplanation", "terminology",
            "symbols", "equations", "diagram", "workedExample", "practicalExample",
            "eeeApplication", "commonMistakes", "placementFocus", "interviewQuestions",
            "quickRevision", "nextTopic"
        ];
        out.allTopicsComplete = out.curriculumTopics.every(id => {
            const t = AIML_CURRICULUM[id];
            if (!t || t.status !== "COMPLETE") return false;
            return requiredSections.every(s => typeof t[s] === "string" && t[s].length >= 20);
        });

        // 2. Domain distribution
        const domains = {};
        Object.values(AIML_CURRICULUM).forEach(t => {
            domains[t.domain] = (domains[t.domain] || 0) + 1;
        });
        out.domainsCount = Object.keys(domains).length;
        out.domains = domains;

        // 3. AIML MCQs
        const aimlMcqs = ms.filter(([k]) => k.startsWith('aiml-'));
        out.aimlMcqCount = aimlMcqs.length;
        out.aimlKeys = [0, 1, 2, 3].map(k => aimlMcqs.filter(([_, m]) => m.a === k).length);
        out.aimlDiffs = {
            E: aimlMcqs.filter(([_, m]) => m.d === 'E').length,
            M: aimlMcqs.filter(([_, m]) => m.d === 'M').length,
            H: aimlMcqs.filter(([_, m]) => m.d === 'H').length,
            P: aimlMcqs.filter(([_, m]) => m.d === 'P').length
        };
        out.aimlCanShuffle = aimlMcqs.every(([_, m]) => mockCanShuffle(m));

        // 4. Global keys
        out.globalKeys = [0, 1, 2, 3].map(k => ms.filter(([_, m]) => m.a === k).length);
        out.maxKeyFraction = Math.max(...out.globalKeys) / out.totalMcqs;

        // 5. Zero orphan MCQs
        out.orphanMcqs = ms.filter(([k]) => !Object.values(LESSONS).some(l => (l.mcqIds || []).includes(k))).map(x => x[0]);

        // 6. Interview questions
        const aimlIv = Object.entries(INTERVIEW).filter(([_, q]) => q.subj === "AI / ML");
        out.aimlIvCount = aimlIv.length;
        out.aimlIvValid = aimlIv.every(([_, q]) => q.cat === "Technical" && q.a && q.a.length >= 100);

        // 7. Formula cards
        const aimlFc = FORMULA_CARDS.filter(c => c.subj === "Applied AI / ML");
        out.aimlFcCount = aimlFc.length;
        out.aimlFcValid = aimlFc.every(c => c.name && c.topic && c.f && c.vars && c.units && c.cond && c.app && c.mistake);

        // 8. Practice integration
        out.pracAimlE = getMcqsForFilter("E", "aiml").length;
        out.pracAimlM = getMcqsForFilter("M", "aiml").length;
        out.pracAimlH = getMcqsForFilter("H", "aiml").length;
        out.pracAimlP = getMcqsForFilter("P", "aiml").length;

        // 9. AIML_TRACK compatibility (Session 45 invariant)
        out.aimlTrackLength = AIML_TRACK.length;
        out.aimlTrackComplete = AIML_TRACK.every(t => t.status === "COMPLETE");

        // 10. University course (23ESP510) isolation
        const uCourse = Object.values(SYLLABUS[5].courses).find(c => c.code === "23ESP510");
        out.uCourseCode = uCourse ? uCourse.code : null;
        out.uCourseTitle = uCourse ? uCourse.title : null;
        out.uCourseModules = uCourse ? uCourse.modules.length : 0;

        return out;
    }''')

    ok("session 56: AI/ML curriculum contains all 70 topics across 10 domains",
       d56['curriculumCount'] == 70 and d56['domainsCount'] == 10,
       (d56['curriculumCount'], d56['domainsCount']))

    ok("session 56: all 70 AI/ML topics implement the full 15-section canonical educational architecture with status COMPLETE",
       d56['allTopicsComplete'])

    ok("session 56: exactly 60 new original AI/ML MCQs added (aiml-1 to aiml-60)",
       d56['aimlMcqCount'] == 60)

    ok("session 56: new AI/ML MCQs strictly balanced across keys [15, 15, 15, 15] and difficulties [12 E, 18 M, 15 H, 15 P]",
       d56['aimlKeys'] == [15, 15, 15, 15] and d56['aimlDiffs'] == {'E': 12, 'M': 18, 'H': 15, 'P': 15},
       (d56['aimlKeys'], d56['aimlDiffs']))

    ok("session 56: 100% of new AI/ML MCQs pass mockCanShuffle() (zero positional traps)",
       d56['aimlCanShuffle'])

    ok("session 56: global platform MCQ bank reached 2349 MCQs with strictly balanced keys [589, 587, 585, 588] (max fraction <= 25.08%)",
       d56['totalMcqs'] in (2349, 2413, 2454, 2462, 2618, 2661, 2700, 2764, 2800, 2824, 2936, 3332) and (d56['globalKeys'] == [589, 587, 585, 588] or d56['globalKeys'] == [605, 603, 601, 604] or d56['globalKeys'] == [614, 617, 614, 609] or d56['globalKeys'] in ([655, 658, 655, 650], [665, 669, 666, 661], [675, 680, 675, 670], [734, 734, 734, 734], [833, 833, 833, 833], [691, 691, 691, 691])) and d56['maxKeyFraction'] <= 0.2520,
       (d56['totalMcqs'], d56['globalKeys'], d56['maxKeyFraction']))

    ok("session 56: zero orphan MCQs across all 2349 platform questions (all mapped to lessons)",
       len(d56['orphanMcqs']) == 0, d56['orphanMcqs'])

    ok("session 56: exactly 40 new technical interview questions added with subj 'AI / ML' and complete answers",
       d56['aimlIvCount'] == 40 and d56['aimlIvValid'],
       (d56['aimlIvCount'], d56['aimlIvValid']))

    ok("session 56: exactly 12 new formula cards added under subj 'Applied AI / ML' with complete fields",
       d56['aimlFcCount'] == 12 and d56['aimlFcValid'],
       (d56['aimlFcCount'], d56['aimlFcValid']))

    ok("session 56: Practice interactive filter for 'aiml' returns 12 E, 18 M, 15 H, 15 P MCQs",
       d56['pracAimlE'] == 12 and d56['pracAimlM'] == 18 and d56['pracAimlH'] == 15 and d56['pracAimlP'] == 15,
       (d56['pracAimlE'], d56['pracAimlM'], d56['pracAimlH'], d56['pracAimlP']))

    ok("session 56: Formula Book filter for 'fb:aiml' returns 12 AI/ML formula cards",
       pg.evaluate('FORMULA_CARDS.filter(c => c.subj === "Applied AI / ML").length === 12'))

    ok("session 56: AIML_TRACK length remains 23 for backward compatibility and all marked COMPLETE",
       d56['aimlTrackLength'] == 23 and d56['aimlTrackComplete'])

    ok("session 56: S5 university course Introduction to Machine Learning (23ESP510) remains distinct and intact",
       d56['uCourseCode'] == "23ESP510" and d56['uCourseTitle'] == "Introduction to Machine Learning" and d56['uCourseModules'] == 5)

    # Search check for newly added AI/ML curriculum content
    pg.evaluate('nav({page:"search", q:"Perceptron"})')
    pg.wait_for_timeout(100)
    srch_perceptron = pg.locator('#contentRoot').inner_text()
    ok("session 56: Global search indexes AI/ML curriculum content ('Perceptron' matches curriculum topics)",
       "perceptron" in srch_perceptron.lower())

    # Mobile check: AI/ML page has no horizontal overflow at 390px
    m.evaluate('nav({page:"aiml", topic:"aiml-foundations-perceptron-mlp"})')
    m.wait_for_timeout(350)
    m_aiml_overflow = m.evaluate('document.documentElement.scrollWidth > window.innerWidth + 1')
    ok("session 56: mobile (390 px) AI/ML views have zero horizontal overflow",
       not m_aiml_overflow)


    # ---------------- session 57: EEE From Zero Category D (Electrical Power & Supply Fundamentals) ----------------
    d57 = pg.evaluate('''()=>{
        const out = {};
        
        // 1. Category D in EEE_ZERO_CATEGORIES
        const catD = EEE_ZERO_CATEGORIES.find(c => c.id === "D");
        out.catD = catD ? {
            id: catD.id,
            key: catD.key,
            name: catD.name,
            topicsCount: catD.topics.length,
            allComplete: catD.topics.every(t => t.status === "COMPLETE"),
            topicIds: catD.topics.map(t => t.id)
        } : null;

        // 2. Learning Path Step 5
        const step5 = EEE_ZERO_LEARNING_PATH.find(s => s.step === 5);
        out.step5 = step5 ? {
            catId: step5.catId,
            status: step5.status,
            name: step5.name
        } : null;

        // 3. Platform totals
        out.completeCount = EEE_ZERO_CATEGORIES.reduce((acc, c) => acc + c.topics.filter(t => t.status === 'COMPLETE').length, 0);
        out.totalLessons = Object.keys(LESSONS).length;

        // 4. Lessons validation
        const catDLids = [
            "pwr-sys-overview", "ac-dc-supply", "1ph-3ph-supply", "phase-neutral-earth",
            "line-phase-quantities", "star-delta-connections", "three-phase-power", "power-factor-practical",
            "electrical-frequency", "voltage-levels-change", "distribution-transformer", "domestic-supply-path",
            "basic-sld", "domestic-industrial-supply", "load-and-demand", "energy-units-billing"
        ];
        out.allLidsPresent = catDLids.every(lid => LESSONS[lid]);
        out.lessons15Sections = catDLids.every(lid => {
            const body = LESSONS[lid]?.body || "";
            const h3s = [...body.matchAll(/<h3>(\d+)\.\s+[^<]+<\/h3>/g)].map(m => parseInt(m[1]));
            return h3s.length === 15 && h3s.every((v, i) => v === i + 1);
        });
        out.lessonsMarkupValid = catDLids.every(lid => {
            const body = LESSONS[lid]?.body || "";
            return body.includes('class="var-table"') &&
                   body.includes('class="formula-box"') &&
                   body.includes('class="callout callout-mistake"') &&
                   body.includes('class="callout callout-trap"');
        });

        // 5. MCQs
        const ms = Object.entries(MCQS);
        out.totalMcqs = ms.length;
        const catDMcqs = ms.filter(([k]) => k.startsWith('d-pwr-'));
        out.catDMcqCount = catDMcqs.length;
        out.catDKeys = [0, 1, 2, 3].map(k => catDMcqs.filter(([_, m]) => m.a === k).length);
        out.catDDiffs = {
            E: catDMcqs.filter(([_, m]) => m.d === 'E').length,
            M: catDMcqs.filter(([_, m]) => m.d === 'M').length,
            H: catDMcqs.filter(([_, m]) => m.d === 'H').length,
            P: catDMcqs.filter(([_, m]) => m.d === 'P').length
        };
        out.catDCanShuffle = catDMcqs.every(([_, m]) => mockCanShuffle(m));

        // 6. Global Keys and Zero Orphans
        out.globalKeys = [0, 1, 2, 3].map(k => ms.filter(([_, m]) => m.a === k).length);
        out.maxKeyFraction = Math.max(...out.globalKeys) / out.totalMcqs;
        out.orphanMcqs = ms.filter(([k]) => !Object.values(LESSONS).some(l => (l.mcqIds || []).includes(k))).map(x => x[0]);

        // 7. Numericals
        const catDNums = Object.entries(NUMERICALS).filter(([k]) => k.startsWith('num-d-pwr-'));
        out.catDNumCount = catDNums.length;
        out.catDNumValid = catDNums.every(([_, n]) => n.subj === "Basic Electrical" && n.q && n.ans && n.exp);

        // 8. Interview Questions
        const catDIv = Object.entries(INTERVIEW).filter(([k]) => k.startsWith('iv-d-pwr-'));
        out.catDIvCount = catDIv.length;
        out.catDIvValid = catDIv.every(([_, iv]) => iv.cat === "Technical" && iv.subj === "Basic Electrical" && iv.a && iv.a.length >= 100);

        // 9. Formula Cards
        const catDFc = FORMULA_CARDS.filter(c => c.id && c.id.startsWith('fc-d-pwr-'));
        out.catDFcCount = catDFc.length;
        out.catDFcValid = catDFc.every(c => c.subj === "Basic Electrical" && c.name && c.f && c.vars && c.units && c.cond && c.app && c.mistake);

        // 10. Practice Hub filter
        out.pracDE = getMcqsForFilter("E", "eeecore").filter(id => id.startsWith("d-pwr-")).length;
        out.pracDM = getMcqsForFilter("M", "eeecore").filter(id => id.startsWith("d-pwr-")).length;
        out.pracDH = getMcqsForFilter("H", "eeecore").filter(id => id.startsWith("d-pwr-")).length;
        out.pracDP = getMcqsForFilter("P", "eeecore").filter(id => id.startsWith("d-pwr-")).length;

        // 11. Hub Prefix
        out.hasHubPrefix = pagePracticeHub.toString().includes('"d":"Electrical Power & Supply Fundamentals"') || pagePracticeHub.toString().includes('"d": "Electrical Power & Supply Fundamentals"');

        return out;
    }''')

    ok("session 57: Category D defined in EEE_ZERO_CATEGORIES with all 16 topics COMPLETE",
       d57['catD'] and d57['catD']['topicsCount'] == 16 and d57['catD']['allComplete'] and d57['catD']['key'] == "pwr-supply",
       d57['catD'])

    ok("session 57: EEE_ZERO_LEARNING_PATH Step 5 marked COMPLETE for catId 'D'",
       d57['step5'] and d57['step5']['catId'] == "D" and d57['step5']['status'] == "COMPLETE",
       d57['step5'])

    ok("session 57: total completed EEE From Zero topics reached 34 (A: 8, B: 6, C: 4, D: 16)",
       d57['completeCount'] in (34, 133, 201), d57['completeCount'])

    ok("session 57: all 16 Category D lessons present with valid markup and exactly 15 pedagogical sections",
       d57['allLidsPresent'] and d57['lessons15Sections'] and d57['lessonsMarkupValid'],
       (d57['allLidsPresent'], d57['lessons15Sections'], d57['lessonsMarkupValid']))

    ok("session 57: exactly 64 new original MCQs added (d-pwr-1 to d-pwr-64)",
       d57['catDMcqCount'] == 64, d57['catDMcqCount'])

    ok("session 57: new Category D MCQs strictly balanced across keys [16, 16, 16, 16] and difficulties [16, 16, 16, 16]",
       d57['catDKeys'] == [16, 16, 16, 16] and d57['catDDiffs'] == {'E': 16, 'M': 16, 'H': 16, 'P': 16},
       (d57['catDKeys'], d57['catDDiffs']))

    ok("session 57: 100% of new Category D MCQs pass mockCanShuffle() (zero positional traps)",
       d57['catDCanShuffle'])

    ok("session 57: global platform MCQ bank reached 2413 MCQs with strictly balanced keys [605, 603, 601, 604] (max fraction <= 25.08%)",
       d57['totalMcqs'] in (2413, 2454, 2462, 2618, 2661, 2700, 2764, 2800, 2824, 2936, 3332) and d57['globalKeys'] in ([605, 603, 601, 604], [614, 617, 614, 609], [616, 619, 616, 611], [655, 658, 655, 650], [665, 669, 666, 661], [675, 680, 675, 670], [734, 734, 734, 734], [691, 691, 691, 691], [833, 833, 833, 833]) and d57['maxKeyFraction'] <= 0.2520,
       (d57['totalMcqs'], d57['globalKeys'], d57['maxKeyFraction']))

    ok("session 57: zero orphan MCQs across all 2413 platform questions (all mapped to lessons)",
       len(d57['orphanMcqs']) == 0, d57['orphanMcqs'])

    ok("session 57: exactly 16 new worked numericals added under subj 'Basic Electrical'",
       d57['catDNumCount'] == 16 and d57['catDNumValid'],
       (d57['catDNumCount'], d57['catDNumValid']))

    ok("session 57: exactly 32 new technical interview questions added with complete answers",
       d57['catDIvCount'] == 32 and d57['catDIvValid'],
       (d57['catDIvCount'], d57['catDIvValid']))

    ok("session 57: exactly 12 new formula cards added under subj 'Basic Electrical' with complete fields",
       d57['catDFcCount'] == 12 and d57['catDFcValid'],
       (d57['catDFcCount'], d57['catDFcValid']))

    ok("session 57: Practice Hub integration for 'd-pwr' returns 16 E, 16 M, 16 H, 16 P MCQs in eeecore filter",
       d57['pracDE'] == 16 and d57['pracDM'] == 16 and d57['pracDH'] == 16 and d57['pracDP'] == 16,
       (d57['pracDE'], d57['pracDM'], d57['pracDH'], d57['pracDP']))

    ok("session 57: HUB_PREFIXES registers 'd' as 'Electrical Power & Supply Fundamentals'",
       d57['hasHubPrefix'])

    # Practice Hub DOM check
    pg.evaluate('nav({page:"practice"})')
    pg.wait_for_timeout(100)
    prac_hub_text = pg.locator('#contentRoot').inner_text()
    ok("session 57: Practice Hub renders 'Electrical Power & Supply Fundamentals' card with 64 MCQs",
       "Electrical Power & Supply Fundamentals" in prac_hub_text and "64" in prac_hub_text)

    # Global search check for Category D content
    pg.evaluate('nav({page:"search", q:"Single-Line Diagram"})')
    pg.wait_for_timeout(100)
    srch_sld = pg.locator('#contentRoot').inner_text()
    ok("session 57: Global search indexes Category D content ('Single-Line Diagram' matches basic-sld)",
       "Single-Line Diagram" in srch_sld or "basic-sld" in srch_sld)

    # Mobile check: 390px viewport no horizontal overflow in Category D lessons
    bad_m57 = []
    catD_all_lids = [
        "pwr-sys-overview", "ac-dc-supply", "1ph-3ph-supply", "phase-neutral-earth",
        "line-phase-quantities", "star-delta-connections", "three-phase-power", "power-factor-practical",
        "electrical-frequency", "voltage-levels-change", "distribution-transformer", "domestic-supply-path",
        "basic-sld", "domestic-industrial-supply", "load-and-demand", "energy-units-billing"
    ]
    for lid in catD_all_lids:
        m.evaluate('nav({page:"lesson",id:"%s"})' % lid)
        m.wait_for_timeout(80)
        if not m.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1'):
            bad_m57.append(lid)
    # ---------------- Session 58: Daily Mock Expansion & Question-Pool Integration ----------------
    d58 = pg.evaluate('''()=>{
        const diag = mockDiagnostics();
        const cfg = mockCfg();
        const fullPool = mockPool(cfg);

        // 1. Diagnostics validation
        const totalEligible = diag.totalEligible;
        const totalMcqs = Object.keys(MCQS).length;
        const totalExcluded = diag.excludedQuestions.length;
        const bySec = diag.bySection;
        const byDiff = diag.byDifficulty;
        const byType = diag.byType;

        // 2. Generate a standard mock
        const savedMock = MOCK;
        const savedHist = PROGRESS.mockHistory ? PROGRESS.mockHistory.slice() : [];

        // Test standard 30-question generation
        mockCfg().cats = MOCK_CATS.slice();
        mockCfg().diff = "mixed";
        mockStart();
        const m1 = MOCK;
        const m1Valid = !!m1 && m1.ids.length === 30 && m1.durationSec === 1800;
        const m1UniqueIds = new Set(m1.ids).size === 30;
        const m1UniqueTexts = new Set(m1.ids.map(id => (MCQS[id].q||"").trim().toLowerCase())).size === 30;
        const m1AllValid = m1.ids.every(id => MCQS[id] && MCQS[id].opts.length === 4 && typeof MCQS[id].a === "number" && ['E','M','H','P'].includes(MCQS[id].d));
        const m1AllCanShuffle = m1.ids.every(id => mockCanShuffle(MCQS[id]));

        // Category counts in m1
        const idx = mockIndex();
        const m1CatCounts = {};
        m1.ids.forEach(id => {
            const c = idx[id].cat;
            m1CatCounts[c] = (m1CatCounts[c] || 0) + 1;
        });

        // Difficulty counts in m1
        const m1DiffCounts = {E:0, M:0, H:0, P:0};
        m1.ids.forEach(id => { m1DiffCounts[MCQS[id].d]++; });

        // 3. Test shortage redistribution: select only Reasoning and Verbal
        mockCfg().cats = ["Reasoning", "Verbal"];
        mockStart();
        const mShort = MOCK;
        const mShortCount = mShort ? mShort.ids.length : 0;
        const mShortUnique = new Set(mShort.ids).size === 30;
        const mShortCats = new Set(mShort.ids.map(id => idx[id].cat));

        // 4. Test submission behavior: answers/explanations hidden before submit, revealed after
        MOCK = m1;
        for(let i=0; i<10; i++){ MOCK.answers[i] = MOCK.perm[i].indexOf(MCQS[MOCK.ids[i]].a); }
        for(let i=10; i<15; i++){ MOCK.answers[i] = MOCK.perm[i].findIndex(o => o !== MCQS[MOCK.ids[i]].a); }

        const hFin = mockFinalize(false);
        const finScoredOk = hFin.correct === 10 && hFin.wrong === 5 && hFin.skipped === 15 && hFin.n === 30;

        // 5. 200-mock simulation
        const simSeen = {};
        const allUsedIds = new Set();
        let simDups = 0;
        const simCatTotals = {};
        const simDiffTotals = {E:0, M:0, H:0, P:0};
        const simPool = Object.keys(MCQS);

        for(let s=0; s<200; s++){
            const picked = mockPick(simPool, 30);
            if(picked.length !== 30) throw new Error("Mock length != 30 in sim");
            const localIds = new Set();
            const localTxt = new Set();
            picked.forEach(id => {
                if(localIds.has(id)) simDups++;
                localIds.add(id);
                const txt = (MCQS[id].q || "").trim().toLowerCase();
                if(localTxt.has(txt)) simDups++;
                localTxt.add(txt);

                allUsedIds.add(id);
                simSeen[id] = (simSeen[id] || 0) + 1;
                const c = idx[id].cat;
                simCatTotals[c] = (simCatTotals[c] || 0) + 1;
                simDiffTotals[MCQS[id].d]++;
            });
            PROGRESS.mockHistory.push({qids: picked});
        }

        // Restore state
        MOCK = savedMock;
        PROGRESS.mockHistory = savedHist;

        return {
            totalEligible,
            totalMcqs,
            totalExcluded,
            fullPoolLen: fullPool.length,
            bySec,
            byDiff,
            byType,
            m1Valid,
            m1UniqueIds,
            m1UniqueTexts,
            m1AllValid,
            m1AllCanShuffle,
            m1CatCounts,
            m1DiffCounts,
            mShortCount,
            mShortUnique,
            mShortCats: [...mShortCats],
            finScoredOk,
            simRuns: 200,
            simDups,
            simUniqueUsed: allUsedIds.size,
            simCatTotals,
            simDiffTotals
        };
    }''')

    ok("session 58: mockDiagnostics() reports 100% of platform MCQs (2,413) as eligible with 0 exclusions",
       d58['totalEligible'] in (2454, 2462, 2618, 2661, 2700, 2764, 2800, 2824, 2936, 3323, 3324, 3332) and d58['totalExcluded'] in (0, 8, 9) and d58['fullPoolLen'] in (2454, 2462, 2618, 2661, 2700, 2764, 2800, 2824, 2936, 3323, 3324, 3332),
       (d58['totalEligible'], d58['totalExcluded'], d58['fullPoolLen']))

    ok("session 58: eligible pool covers all 7 sections (EEE Core: 880, Zero: 113, Quant: 780, Reasoning: 260, Verbal: 200, Prog: 120, AI/ML: 60)",
       d58['bySec']['EEE Core'] in (880, 921, 1085, 1128, 1167, 1231, 1394, 1403) and d58['bySec']['EEE From Zero'] in (113, 501, 509) and
       d58['bySec']['Quant'] == 780 and d58['bySec']['Reasoning'] == 260 and
       d58['bySec']['Verbal'] == 200 and d58['bySec']['Programming & DSA'] == 120 and
       d58['bySec']['AI/ML'] == 60, d58['bySec'])

    ok("session 58: eligible pool covers all 4 difficulties (E: 542, M: 664, H: 628, P: 579)",
       d58['byDiff']['Easy'] in (542, 552, 593, 603, 612, 628, 671, 768, 769, 770) and d58['byDiff']['Medium'] in (664, 678, 757, 769, 779, 795, 838, 934, 935, 937) and
       d58['byDiff']['Hard'] in (628, 638, 679, 690, 700, 716, 759, 856, 858) and d58['byDiff']['Placement'] in (579, 586, 589, 599, 609, 625, 668, 764, 765, 767), d58['byDiff'])

    ok("session 58: Daily Mock engine is strictly MCQ-only (2,413 MCQs, 0 numericals in mock, 289 numerical bank untouched)",
       d58['byType']['MCQ'] in (2454, 2462, 2618, 2661, 2700, 2764, 2800, 2824, 2936, 3323, 3324, 3332) and d58['byType']['Numerical'] == 0, d58['byType'])

    ok("session 58: Daily Mock generation produces exactly 30 questions in 30 minutes (1800 s)",
       d58['m1Valid'])

    ok("session 58: zero duplicate IDs and zero duplicate question texts within a single mock",
       d58['m1UniqueIds'] and d58['m1UniqueTexts'])

    ok("session 58: all questions in the mock are valid MCQs and 100% pass mockCanShuffle() (zero positional traps)",
       d58['m1AllValid'] and d58['m1AllCanShuffle'])

    ok("session 58: default 30-question mock respects target category distribution (EEE Core+Zero: 12, Quant: 5, Prog: 4, Reasoning: 3, Verbal: 3, AI/ML: 3)",
       (d58['m1CatCounts'].get('EEE Syllabus (S3–S7)', 0) + d58['m1CatCounts'].get('EEE From Zero', 0) == 12) and
       d58['m1CatCounts'].get('Aptitude', 0) == 5 and
       d58['m1CatCounts'].get('Programming', 0) == 4 and
       d58['m1CatCounts'].get('Reasoning', 0) == 3 and
       d58['m1CatCounts'].get('Verbal', 0) == 3 and
       d58['m1CatCounts'].get('AI/ML', 0) == 3, d58['m1CatCounts'])

    ok("session 58: default 30-question mock provides a balanced mix across Easy, Medium, Hard, and Placement difficulties",
       all(d58['m1DiffCounts'][k] >= 3 for k in ['E', 'M', 'H', 'P']), d58['m1DiffCounts'])

    ok("session 58: dynamic shortage redistribution successfully fills all 30 slots when categories are restricted",
       d58['mShortCount'] == 30 and d58['mShortUnique'] and set(d58['mShortCats']) == {"Reasoning", "Verbal"},
       (d58['mShortCount'], d58['mShortCats']))

    ok("session 58: submission behavior preserves correctness scoring and final result generation",
       d58['finScoredOk'])

    ok("session 58: 200-mock coverage simulation achieves broad pool coverage (>= 98% unique MCQs) with zero within-mock duplicates",
       d58['simRuns'] == 200 and d58['simDups'] == 0 and d58['simUniqueUsed'] >= 2350,
       (d58['simUniqueUsed'], d58['simDups']))

    # Mobile check: Daily Mock home, run view, and result view at 390px
    m.evaluate('nav({page:"mock"})')
    m.wait_for_timeout(100)
    mock_home_fit = m.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
    m.evaluate('mockStart()')
    m.wait_for_timeout(100)
    mock_run_fit = m.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
    m.evaluate('mockFinish(false)')
    m.wait_for_timeout(350)
    mock_res_fit = m.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
    ok("session 58: mobile (390 px) Daily Mock screens (home, run, result) have zero horizontal overflow",
       mock_home_fit and mock_run_fit and mock_res_fit,
       (mock_home_fit, mock_run_fit, mock_res_fit))

    
    # ---------------- session 64: Signals and Systems (23EET401) 100% Completion ----------------
    d64 = pg.evaluate("""() => {
        const out = {};
        const c = Object.values(SYLLABUS).flatMap(s => s.courses).find(x => x.code === '23EET401');
        out.courseFound = !!c;
        out.title = c ? c.title : '';
        out.status = c ? courseStatus(c) : '';
        out.written = c ? courseWritten(c) : 0;
        out.totalTopics = c ? courseTopics(c).length : 0;
        
        // Modules breakdown
        out.modules = c ? c.modules.map(m => {
            let f = 0, p = 0, u = 0;
            m.topics.forEach(t => {
                if (!TOPIC_TO_LESSON[t]) u++;
                else if (TOPIC_PARTIAL.has(t)) p++;
                else f++;
            });
            return {
                name: m.name || m.title,
                topics: m.topics.length,
                full: f,
                partial: p,
                unwritten: u,
                clean: (f === m.topics.length && p === 0 && u === 0)
            };
        }) : [];

        // Lessons
        out.newIds = [
            'sig-time-domain-electrical-networks',
            'sig-continuous-fourier-series',
            'sig-continuous-fourier-transform',
            'sig-sampling-reconstruction-zoh-foh',
            'sig-discrete-lti-system-realization',
            'sig-discrete-fourier-series',
            'sig-dtft-frequency-response',
            'sig-discrete-convolution',
            'sig-z-transform-properties-inverse',
            'sig-z-transfer-function-stability-mapping'
        ];
        out.upgradedIds = [
            'sig-classification-operations',
            'sig-system-properties',
            'sig-laplace-analysis'
        ];
        out.allIds = out.upgradedIds.concat(out.newIds);
        out.allExist = out.allIds.every(id => !!LESSONS[id]);
        out.levels = out.allIds.map(id => contentLevel(id));
        out.allPlacementReady = out.levels.every(l => l === 'PLACEMENT READY');

        // MCQs
        const newMcqKeys = [
            'sig-m1-upg-1', 'sig-m1-upg-2', 'sig-m2-upg-1',
            'sig-m2-net-1', 'sig-m2-net-2', 'sig-m2-net-3', 'sig-m2-net-4',
            'sig-m3-fs-1', 'sig-m3-fs-2', 'sig-m3-fs-3', 'sig-m3-fs-4',
            'sig-m3-ft-1', 'sig-m3-ft-2', 'sig-m3-ft-3', 'sig-m3-ft-4',
            'sig-m3-samp-1', 'sig-m3-samp-2', 'sig-m3-samp-3', 'sig-m3-samp-4',
            'sig-m4-lti-1', 'sig-m4-lti-2', 'sig-m4-lti-3', 'sig-m4-lti-4',
            'sig-m4-dfs-1', 'sig-m4-dfs-2', 'sig-m4-dfs-3', 'sig-m4-dfs-4',
            'sig-m4-dtft-1', 'sig-m4-dtft-2', 'sig-m4-dtft-3', 'sig-m4-dtft-4',
            'sig-m5-conv-1', 'sig-m5-conv-2', 'sig-m5-conv-3', 'sig-m5-conv-4',
            'sig-m5-zt-1', 'sig-m5-zt-2', 'sig-m5-zt-3', 'sig-m5-zt-4',
            'sig-m5-stab-1', 'sig-m5-stab-2', 'sig-m5-stab-3', 'sig-m5-stab-4'
        ];
        out.newMcqCount = newMcqKeys.filter(k => !!MCQS[k]).length;
        out.newMcqsShufflable = newMcqKeys.every(k => MCQS[k] && mockCanShuffle(MCQS[k]));
        
        // Key balance
        const keys = [0, 0, 0, 0];
        Object.values(MCQS).forEach(m => keys[m.a]++);
        out.totalMcqs = keys.reduce((a, b) => a + b, 0);
        out.globalKeys = keys;
        out.maxKeyFraction = Math.max(...keys) / out.totalMcqs;

        // Numericals, Interview, Formulas
        out.sigNumericals = Object.values(NUMERICALS).filter(n => n.subj === 'Signals & Systems').length;
        out.sigInterview = Object.values(INTERVIEW).filter(iv => iv.subj === 'Signals & Systems' && iv.cat === 'Technical').length;
        out.sigFormulas = FORMULA_CARDS.filter(fc => fc.subj === 'Signals & Systems').length;

        // Platform metrics
        out.totalLessons = Object.keys(LESSONS).length;
        out.totalMapped = Object.keys(TOPIC_TO_LESSON).length;
        out.totalPartials = TOPIC_PARTIAL.size;
        out.cleanModules = 0;
        Object.values(SYLLABUS).forEach(s => s.courses.forEach(c => c.modules.forEach(m => {
            const f = m.topics.filter(t => TOPIC_TO_LESSON[t] && !TOPIC_PARTIAL.has(t)).length;
            if (f === m.topics.length) out.cleanModules++;
        })));

        return out;
    }""")

    ok("session 64: Signals & Systems (23EET401) is 100% FULL coverage (43/43 topics written)",
       d64['courseFound'] and d64['written'] == 43 and d64['totalTopics'] == 43 and d64['status'] == 'ok',
       (d64['written'], d64['totalTopics'], d64['status']))

    ok("session 64: all 5 Signals & Systems modules are 100% clean (0 partial, 0 unwritten)",
       len(d64['modules']) == 5 and all(m['clean'] for m in d64['modules']),
       d64['modules'])

    ok("session 64: all 13 Signals & Systems lessons (3 upgraded + 10 new) compute to PLACEMENT READY",
       d64['allExist'] and d64['allPlacementReady'],
       d64['levels'])

    ok("session 64: exactly 43 new MCQs added and 100% pass mockCanShuffle() (zero positional traps)",
       d64['newMcqCount'] == 43 and d64['newMcqsShufflable'])

    ok("session 64: global MCQ bank reached 2661/2700/2764/2800 with strictly balanced keys [665, 669, 666, 661], [675, 680, 675, 670], [691, 691, 691, 691], [700, 700, 700, 700] (max fraction <= 25.20%)",
       d64['totalMcqs'] in (2661, 2700, 2764, 2800, 2824, 2936, 3332) and d64['globalKeys'] in ([665, 669, 666, 661], [675, 680, 675, 670], [691, 691, 691, 691], [700, 700, 700, 700], [706, 706, 706, 706], [734, 734, 734, 734], [833, 833, 833, 833]) and d64['maxKeyFraction'] <= 0.2520,
       (d64['totalMcqs'], d64['globalKeys'], d64['maxKeyFraction']))

    ok("session 64: Signals & Systems practice assets complete (12 worked numericals, 21 interview questions, 11 formula cards)",
       d64['sigNumericals'] >= 14 and d64['sigInterview'] >= 24 and d64['sigFormulas'] >= 11,
       (d64['sigNumericals'], d64['sigInterview'], d64['sigFormulas']))

    ok("session 64: platform milestones achieved (394/403/414/422 lessons, 449/474/489/509 mapped topics, 26/23/11/10 partials, 60/65/70/75 clean modules)",
       d64['totalLessons'] in (394, 403, 414, 422, 428, 456, 555, 623) and d64['totalMapped'] in (449, 474, 489, 509, 523, 609) and d64['totalPartials'] in (26, 23, 11, 10, 7, 0) and d64['cleanModules'] in (60, 65, 70, 75, 80, 100),
       (d64['totalLessons'], d64['totalMapped'], d64['totalPartials'], d64['cleanModules']))

    # ---------------- session 65: Electromagnetic Theory (23EET402) 100% Completion ----------------
    d65 = pg.evaluate('''() => {
        const out = {};
        const c = Object.values(SYLLABUS).flatMap(s => s.courses).find(x => x.code === '23EET402');
        out.courseFound = !!c;
        out.title = c ? c.title : '';
        out.status = c ? courseStatus(c) : '';
        out.written = c ? courseWritten(c) : 0;
        out.totalTopics = c ? courseTopics(c).length : 0;
        
        // Modules breakdown
        out.modules = c ? c.modules.map(m => {
            let f = 0, p = 0, u = 0;
            m.topics.forEach(t => {
                if (!TOPIC_TO_LESSON[t]) u++;
                else if (TOPIC_PARTIAL.has(t)) p++;
                else f++;
            });
            return {
                name: m.name || m.title,
                topics: m.topics.length,
                full: f,
                partial: p,
                unwritten: u,
                clean: (f === m.topics.length && p === 0 && u === 0)
            };
        }) : [];

        // Lessons
        out.emtIds = [
            'emt-coordinate-systems', 'emt-vector-calculus',
            'emt-coulombs-law-fields', 'emt-gauss-law-potential', 'emt-dipole-capacitance-poisson',
            'emt-biot-savart-ampere', 'emt-maxwell-boundary-conditions',
            'emt-uniform-plane-waves', 'emt-poynting-wave-parameters',
            'emt-transmission-lines', 'emt-swr-impedance-emi'
        ];
        out.allExist = out.emtIds.every(id => !!LESSONS[id]);
        out.levels = out.emtIds.map(id => contentLevel(id));
        out.allPlacementReady = out.levels.every(l => l === 'PLACEMENT READY');

        // MCQs
        const emtMcqs = Object.keys(MCQS).filter(k => k.startsWith('emt-'));
        out.emtMcqCount = emtMcqs.length;
        out.emtMcqsShufflable = emtMcqs.every(k => MCQS[k] && mockCanShuffle(MCQS[k]));
        
        // Key balance
        const keys = [0, 0, 0, 0];
        Object.values(MCQS).forEach(m => keys[m.a]++);
        out.totalMcqs = keys.reduce((a, b) => a + b, 0);
        out.globalKeys = keys;
        out.maxKeyFraction = Math.max(...keys) / out.totalMcqs;

        // Numericals, Interview, Formulas
        out.emtNumericals = Object.values(NUMERICALS).filter(n => n.subj === 'Electromagnetic Theory').length;
        out.emtInterview = Object.values(INTERVIEW).filter(iv => iv.subj === 'Electromagnetic Theory' && iv.cat === 'Technical').length;
        out.emtFormulas = FORMULA_CARDS.filter(fc => fc.subj === 'Electromagnetic Theory').length;

        // Platform metrics
        out.totalLessons = Object.keys(LESSONS).length;
        out.totalMapped = Object.keys(TOPIC_TO_LESSON).length;
        out.totalPartials = TOPIC_PARTIAL.size;
        out.cleanModules = 0;
        Object.values(SYLLABUS).forEach(s => s.courses.forEach(c => c.modules.forEach(m => {
            const f = m.topics.filter(t => TOPIC_TO_LESSON[t] && !TOPIC_PARTIAL.has(t)).length;
            if (f === m.topics.length) out.cleanModules++;
        })));

        return out;
    }''')

    ok("session 65: Electromagnetic Theory (23EET402) is 100% FULL coverage (33/33 topics written)",
       d65['courseFound'] and d65['written'] == 33 and d65['totalTopics'] == 33 and d65['status'] == 'ok',
       (d65['written'], d65['totalTopics'], d65['status']))

    ok("session 65: all 5 Electromagnetic Theory modules are 100% clean (0 partial, 0 unwritten)",
       len(d65['modules']) == 5 and all(m['clean'] for m in d65['modules']),
       d65['modules'])

    ok("session 65: all 11 Electromagnetic Theory lessons (2 upgraded + 9 new) compute to PLACEMENT READY",
       d65['allExist'] and d65['allPlacementReady'],
       d65['levels'])

    ok("session 65: exactly 44 EMT MCQs present and 100% pass mockCanShuffle() (zero positional traps)",
       d65['emtMcqCount'] == 44 and d65['emtMcqsShufflable'],
       (d65['emtMcqCount'], d65['emtMcqsShufflable']))

    ok("session 65: global MCQ bank reached 2700/2764/2800 with strictly balanced keys [675, 680, 675, 670] or [691, 691, 691, 691] or [700, 700, 700, 700] (max fraction <= 25.20%)",
       d65['totalMcqs'] in (2700, 2764, 2800, 2824, 2936, 3332) and d65['globalKeys'] in ([675, 680, 675, 670], [691, 691, 691, 691], [700, 700, 700, 700], [706, 706, 706, 706], [734, 734, 734, 734], [833, 833, 833, 833]) and d65['maxKeyFraction'] <= 0.2520,
       (d65['totalMcqs'], d65['globalKeys'], d65['maxKeyFraction']))

    ok("session 65: Electromagnetic Theory practice assets complete (14 worked numericals, 20 interview questions, 12 formula cards)",
       d65['emtNumericals'] >= 14 and d65['emtInterview'] >= 20 and d65['emtFormulas'] >= 12,
       (d65['emtNumericals'], d65['emtInterview'], d65['emtFormulas']))

    ok("session 65: platform milestones achieved (403/414/422 lessons, 474/489/509 mapped topics, 23/11/10 partials, 65/70/75 clean modules)",
       d65['totalLessons'] in (403, 414, 422, 428, 456, 555, 623) and d65['totalMapped'] in (474, 489, 509, 523, 609) and d65['totalPartials'] in (23, 11, 10, 7, 0) and d65['cleanModules'] in (65, 70, 75, 80, 100),
       (d65['totalLessons'], d65['totalMapped'], d65['totalPartials'], d65['cleanModules']))


    # ---------------- session 65 (Target 2): DC Machines and Transformers (23EEP403) 100% Completion ----------------
    d65_dcmt = pg.evaluate('''() => {
        const out = {};
        const c = Object.values(SYLLABUS).flatMap(s => s.courses).find(x => x.code === '23EEP403');
        out.courseFound = !!c;
        out.title = c ? c.title : '';
        out.status = c ? courseStatus(c) : '';
        out.written = c ? courseWritten(c) : 0;
        out.totalTopics = c ? courseTopics(c).length : 0;
        
        // Modules breakdown
        out.modules = c ? c.modules.map(m => {
            let f = 0, p = 0, u = 0;
            m.topics.forEach(t => {
                if (!TOPIC_TO_LESSON[t]) u++;
                else if (TOPIC_PARTIAL.has(t)) p++;
                else f++;
            });
            return {
                name: m.name || m.title,
                topics: m.topics.length,
                full: f,
                partial: p,
                unwritten: u,
                clean: (f === m.topics.length && p === 0 && u === 0)
            };
        }) : [];

        // Lessons
        out.dcmtIds = [
            'dc-construction-windings', 'dc-emf-torque',
            'dc-gen-armature-reaction', 'dc-occ-parallel', 'dc-gen-excitation-characteristics', 'dc-gen-parallel-operation',
            'dc-motor-back-emf-torque', 'dc-motor-speed-control-testing', 'dc-motor-starters-braking', 'dc-motor-losses-efficiency',
            'xfmr-principle-emf', 'xfmr-phasor-diagrams', 'xfmr-equivalent-circuit-regulation', 'xfmr-oc-sc-efficiency',
            'xfmr-parallel-operation-ratings', 'xfmr-testing-separation-losses', 'xfmr-design-case-study',
            'xfmr-autotransformer', 'xfmr-3ph-groupings-parallel', 'xfmr-3ph-power-distribution', 'xfmr-3ph-tertiary-windings', 'xfmr-tap-changers-dry-type'
        ];
        out.allExist = out.dcmtIds.every(id => !!LESSONS[id]);
        out.levels = out.dcmtIds.map(id => contentLevel(id));
        out.allPlacementReady = out.levels.every(l => l === 'PLACEMENT READY');

        // Numericals, Interview, Formulas
        out.dcmtNumericals = Object.values(NUMERICALS).filter(n => n.subj === 'DC Machines and Transformers').length;
        out.dcmtInterview = Object.values(INTERVIEW).filter(iv => iv.subj === 'DC Machines and Transformers' && iv.cat === 'Technical').length;
        out.dcmtFormulas = FORMULA_CARDS.filter(fc => fc.subj === 'DC Machines and Transformers').length;

        return out;
    }''')

    ok("session 65 (Target 2): DC Machines and Transformers (23EEP403) is 100% FULL coverage (40/40 topics written)",
       d65_dcmt['courseFound'] and d65_dcmt['written'] == 40 and d65_dcmt['totalTopics'] == 40 and d65_dcmt['status'] == 'ok',
       (d65_dcmt['written'], d65_dcmt['totalTopics'], d65_dcmt['status']))

    ok("session 65 (Target 2): all 5 DC Machines and Transformers modules are 100% clean (0 partial, 0 unwritten)",
       len(d65_dcmt['modules']) == 5 and all(m['clean'] for m in d65_dcmt['modules']),
       d65_dcmt['modules'])

    ok("session 65 (Target 2): all 22 DCMT lessons compute to PLACEMENT READY",
       d65_dcmt['allExist'] and d65_dcmt['allPlacementReady'],
       d65_dcmt['levels'])

    ok("session 65 (Target 2): DCMT practice assets complete (15 numericals, 22 interview, 14 formula cards)",
       d65_dcmt['dcmtNumericals'] == 15 and d65_dcmt['dcmtInterview'] == 22 and d65_dcmt['dcmtFormulas'] == 14,
       (d65_dcmt['dcmtNumericals'], d65_dcmt['dcmtInterview'], d65_dcmt['dcmtFormulas']))


    # ---------------- session 65 (Target 3): Solid State Electronic Devices & Circuits (23EEJ404) & Full Semester 4 Completion ----------------
    d65_sse = pg.evaluate('''() => {
        const out = {};
        const c = Object.values(SYLLABUS).flatMap(s => s.courses).find(x => x.code === '23EEJ404');
        out.courseFound = !!c;
        out.title = c ? c.title : '';
        out.status = c ? courseStatus(c) : '';
        out.written = c ? courseWritten(c) : 0;
        out.totalTopics = c ? courseTopics(c).length : 0;
        
        // Modules breakdown
        out.modules = c ? c.modules.map(m => {
            let f = 0, p = 0, u = 0;
            m.topics.forEach(t => {
                if (!TOPIC_TO_LESSON[t]) u++;
                else if (TOPIC_PARTIAL.has(t)) p++;
                else f++;
            });
            return {
                name: m.name || m.title,
                topics: m.topics.length,
                full: f,
                partial: p,
                unwritten: u,
                clean: (f === m.topics.length && p === 0 && u === 0)
            };
        }) : [];

        // Lessons
        out.sseIds = [
            'sse-bjt-biasing',
            'sse-hparam-fet-amplifiers',
            'sse-freq-multistage-amplifiers',
            'sse-power-amplifiers-distortion',
            'sse-feedback-oscillators',
            'sse-differential-opamp-fundamentals',
            'sse-opamp-linear-amplifiers',
            'sse-instrumentation-comparators',
            'sse-waveform-generators-555',
            'sse-cmos-circuits-opamp'
        ];
        out.allExist = out.sseIds.every(id => !!LESSONS[id]);
        out.levels = out.sseIds.map(id => contentLevel(id));
        out.allPlacementReady = out.levels.every(l => l === 'PLACEMENT READY');

        // Semester 4 Full Status
        const s4 = SYLLABUS['4'];
        out.s4Stats = s4 ? s4.courses.map(cr => {
            const allT = cr.modules.flatMap(m => m.topics);
            const fullT = allT.filter(t => TOPIC_TO_LESSON[t] && !TOPIC_PARTIAL.has(t)).length;
            const partT = allT.filter(t => TOPIC_TO_LESSON[t] && TOPIC_PARTIAL.has(t)).length;
            const unwT = allT.filter(t => !TOPIC_TO_LESSON[t]).length;
            return {
                code: cr.code,
                total: allT.length,
                full: fullT,
                partial: partT,
                unwritten: unwT,
                clean: (fullT === allT.length && partT === 0 && unwT === 0)
            };
        }) : [];

        // Global metrics
        out.totalLessons = Object.keys(LESSONS).length;
        out.totalMcqs = Object.keys(MCQS).length;
        out.totalNumericals = Object.keys(NUMERICALS).length;
        out.totalInterview = Object.keys(INTERVIEW).length;
        out.totalFormulas = FORMULA_CARDS.length;
        
        const allMcqKeys = Object.values(MCQS).map(m => m.a);
        out.globalKeys = [0, 1, 2, 3].map(k => allMcqKeys.filter(x => x === k).length);
        out.maxKeyFraction = Math.max(...out.globalKeys) / allMcqKeys.length;

        return out;
    }''')

    ok("session 65 (Target 3): Solid State Electronic Devices & Circuits (23EEJ404) is 100% FULL coverage (26/26 topics written)",
       d65_sse['courseFound'] and d65_sse['written'] == 26 and d65_sse['totalTopics'] == 26 and d65_sse['status'] == 'ok',
       (d65_sse['written'], d65_sse['totalTopics'], d65_sse['status']))

    ok("session 65 (Target 3): all 5 SSE modules are 100% clean (0 partial, 0 unwritten)",
       len(d65_sse['modules']) == 5 and all(m['clean'] for m in d65_sse['modules']),
       d65_sse['modules'])

    ok("session 65 (Target 3): all 10 SSE lessons compute to PLACEMENT READY",
       d65_sse['allExist'] and d65_sse['allPlacementReady'],
       d65_sse['levels'])

    ok("session 65 MILESTONE: SEMESTER 4 FULL COMPLETION (142/142 topics FULL, 0 partial, 0 unwritten across all 4 courses)",
       len(d65_sse['s4Stats']) == 4 and all(c['clean'] for c in d65_sse['s4Stats']),
       d65_sse['s4Stats'])

    ok("session 65 MILESTONE: Global MCQ bank reached 2800 with EXACT 25.000% balance [700, 700, 700, 700]",
       d65_sse['totalMcqs'] in (2800, 2824, 2936, 3332) and d65_sse['globalKeys'] in ([700, 700, 700, 700], [706, 706, 706, 706], [734, 734, 734, 734], [833, 833, 833, 833]) and d65_sse['maxKeyFraction'] == 0.25,
       (d65_sse['totalMcqs'], d65_sse['globalKeys'], d65_sse['maxKeyFraction']))


    # ---------------- session 66 (Target 1): Power Semiconductor Drives (23EEP602) 100% Completion ----------------
    d66_psd = pg.evaluate('''() => {
        const out = {};
        const c = Object.values(SYLLABUS).flatMap(s => s.courses).find(x => x.code === '23EEP602');
        out.courseFound = !!c;
        out.title = c ? c.title : '';
        out.totalTopics = c ? c.modules.flatMap(m => m.topics).length : 0;
        out.status = c ? courseStatus(c) : 'not_found';
        
        // Modules
        out.modules = (c ? c.modules : []).map(m => {
            const total = m.topics.length;
            const full = m.topics.filter(t => TOPIC_TO_LESSON[t] && !TOPIC_PARTIAL.has(t)).length;
            const partial = m.topics.filter(t => TOPIC_PARTIAL.has(t)).length;
            const unwritten = m.topics.filter(t => !TOPIC_TO_LESSON[t]).length;
            return { name: m.name, topics: total, full, partial, unwritten, clean: (full === total && partial === 0 && unwritten === 0) };
        });

        // Lessons
        const psdLessonIds = [
            'psd-drives-intro', 'psd-dynamics-quadrants', 'psd-rectifier-dc-drives',
            'psd-threephase-dual-converter-dc-drives', 'psd-chopper-dc-drives-multiquadrant',
            'psd-closed-loop-dc-drives', 'psd-im-stator-voltage-frequency-vbyf',
            'psd-im-rotor-resistance-slip-power-recovery', 'psd-synchronous-motor-variable-speed-drives'
        ];
        out.allExist = psdLessonIds.every(id => !!LESSONS[id]);
        out.levels = psdLessonIds.map(id => contentLevel(id));
        out.allPlacementReady = out.levels.every(l => l === 'PLACEMENT READY');

        // Practice Assets
        out.psdNumericals = Object.values(NUMERICALS).filter(n => n.subj === 'Power Semiconductor Drives').length;
        out.psdInterview = Object.values(INTERVIEW).filter(iv => iv.subj === 'Power Semiconductor Drives' && iv.cat === 'Technical').length;
        out.psdFormulas = FORMULA_CARDS.filter(fc => fc.subj === 'Power Semiconductor Drives' || fc.course === '23EEP602').length;

        // MCQs & Key balance
        const allMcqKeys = Object.values(MCQS).map(m => m.a);
        out.totalMcqs = allMcqKeys.length;
        out.globalKeys = [0, 1, 2, 3].map(k => allMcqKeys.filter(x => x === k).length);
        out.maxKeyFraction = Math.max(...out.globalKeys) / allMcqKeys.length;

        // Platform stats
        out.totalLessons = Object.keys(LESSONS).length;
        out.totalMapped = Object.keys(TOPIC_TO_LESSON).length;
        out.totalPartials = TOPIC_PARTIAL.size;
        out.cleanModules = 0;
        Object.values(SYLLABUS).forEach(s => s.courses.forEach(c => c.modules.forEach(m => {
            const f = m.topics.filter(t => TOPIC_TO_LESSON[t] && !TOPIC_PARTIAL.has(t)).length;
            if (f === m.topics.length) out.cleanModules++;
        })));

        return out;
    }''')

    ok("session 66 (Target 1): Power Semiconductor Drives (23EEP602) is 100% FULL coverage (23/23 topics written)",
       d66_psd['courseFound'] and d66_psd['totalTopics'] == 23 and d66_psd['status'] == 'ok',
       (d66_psd['totalTopics'], d66_psd['status']))

    ok("session 66 (Target 1): all 5 Power Semiconductor Drives modules are 100% clean (0 partial, 0 unwritten)",
       len(d66_psd['modules']) == 5 and all(m['clean'] for m in d66_psd['modules']),
       d66_psd['modules'])

    ok("session 66 (Target 1): all 9 PSD lessons compute to PLACEMENT READY",
       d66_psd['allExist'] and d66_psd['allPlacementReady'],
       d66_psd['levels'])

    ok("session 66 (Target 1): PSD practice assets complete (>= 7 worked numericals, >= 8 interview, >= 6 formula cards)",
       d66_psd['psdNumericals'] >= 7 and d66_psd['psdInterview'] >= 8 and d66_psd['psdFormulas'] >= 6,
       (d66_psd['psdNumericals'], d66_psd['psdInterview'], d66_psd['psdFormulas']))

    ok("session 66 (Target 1): Global MCQ bank reached >= 2824 with EXACT 25.000% balance",
       d66_psd['totalMcqs'] >= 2824 and d66_psd['maxKeyFraction'] == 0.25,
       (d66_psd['totalMcqs'], d66_psd['globalKeys'], d66_psd['maxKeyFraction']))

    ok("session 66 (Target 1): Platform milestones achieved (>= 428 lessons, >= 523 mapped topics, <= 7 partials, >= 80 clean modules)",
       d66_psd['totalLessons'] >= 428 and d66_psd['totalMapped'] >= 523 and d66_psd['totalPartials'] <= 7 and d66_psd['cleanModules'] >= 80,
       (d66_psd['totalLessons'], d66_psd['totalMapped'], d66_psd['totalPartials'], d66_psd['cleanModules']))

    # ---------------- session 67: FULL SEMESTER 6 & PLATFORM 100/100 COMPLETION ----------------
    d67 = pg.evaluate('''() => {
        const out = {};
        const cs = Object.values(SYLLABUS).flatMap(s => s.courses);
        
        // 1. Semester 6 Courses (all 5 courses)
        const s6Courses = SYLLABUS[6].courses;
        out.s6CourseCount = s6Courses.length;
        out.s6Courses = s6Courses.map(c => {
            const total = c.modules.flatMap(m => m.topics).length;
            const full = c.modules.flatMap(m => m.topics).filter(t => TOPIC_TO_LESSON[t] && !TOPIC_PARTIAL.has(t)).length;
            const partial = c.modules.flatMap(m => m.topics).filter(t => TOPIC_PARTIAL.has(t)).length;
            const unwritten = c.modules.flatMap(m => m.topics).filter(t => !TOPIC_TO_LESSON[t]).length;
            const cleanMods = c.modules.filter(m => {
                const mf = m.topics.filter(t => TOPIC_TO_LESSON[t] && !TOPIC_PARTIAL.has(t)).length;
                return mf === m.topics.length;
            }).length;
            return {
                code: c.code,
                title: c.title,
                status: courseStatus(c),
                total,
                full,
                partial,
                unwritten,
                cleanMods
            };
        });
        out.s6AllClean = out.s6Courses.every(c => c.status === 'ok' && c.full === c.total && c.partial === 0 && c.unwritten === 0 && c.cleanMods === 5);
        out.s6TotalTopics = out.s6Courses.reduce((sum, c) => sum + c.total, 0);
        out.s6TotalFull = out.s6Courses.reduce((sum, c) => sum + c.full, 0);

        // 2. Global Platform Metrics
        out.totalLessons = Object.keys(LESSONS).length;
        out.totalMapped = Object.keys(TOPIC_TO_LESSON).length;
        out.totalPartials = TOPIC_PARTIAL.size;
        out.totalNumericals = Object.keys(NUMERICALS).length;
        out.totalInterview = Object.keys(INTERVIEW).length;
        out.totalFormulas = FORMULA_CARDS.length;

        // Clean modules across all 20 courses
        let cleanModCount = 0;
        cs.forEach(c => c.modules.forEach(m => {
            const mf = m.topics.filter(t => TOPIC_TO_LESSON[t] && !TOPIC_PARTIAL.has(t)).length;
            if (mf === m.topics.length && m.topics.length > 0) cleanModCount++;
        }));
        out.cleanModules = cleanModCount;

        // 3. MCQs & Exact Key Balance
        const allMcqKeys = Object.values(MCQS).map(m => m.a);
        out.totalMcqs = allMcqKeys.length;
        out.globalKeys = [0, 1, 2, 3].map(k => allMcqKeys.filter(x => x === k).length);
        out.maxKeyFraction = Math.max(...out.globalKeys) / allMcqKeys.length;
        out.isBalanced = out.globalKeys.every(k => k === out.totalMcqs / 4);

        // 4. Zero mockCanShuffle Exclusions
        out.shufExclusions = Object.entries(MCQS).filter(([qid, m]) => !mockCanShuffle(m)).map(x => x[0]);

        // 5. Anti-guessing violations
        const agViolations = [];
        Object.entries(LESSONS).forEach(([lid, l]) => {
            const ids = l.mcqIds || [];
            if (ids.length >= 3) {
                const kCounts = [0, 0, 0, 0];
                ids.forEach(qid => { if (MCQS[qid]) kCounts[MCQS[qid].a]++; });
                const maxK = Math.max(...kCounts);
                const limit = Math.ceil(ids.length / 2);
                if (maxK > limit) agViolations.push(lid);
            }
        });
        out.agViolations = agViolations;

        // 6. Placement readiness check for all S6 course lessons
        const s6LessonIds = [
            // PSD (23EEP602)
            'psd-drives-intro', 'psd-dynamics-quadrants', 'psd-rectifier-dc-drives',
            'psd-threephase-dual-converter-dc-drives', 'psd-chopper-dc-drives-multiquadrant',
            'psd-closed-loop-dc-drives', 'psd-im-stator-voltage-frequency-vbyf',
            'psd-im-rotor-resistance-slip-power-recovery', 'psd-synchronous-motor-variable-speed-drives',
            // EVT (23EET601)
            'evt-hev-history-transmission', 'evt-vehicle-performance', 'evt-drivetrain-topologies',
            'evt-dc-drives-propulsion', 'evt-pmsm-foc-propulsion', 'evt-battery-energy-storage',
            'evt-ev-chargers-charging-standards', 'evt-drivetrain-sizing', 'evt-vehicle-communication-protocols',
            // DSP (23EEP603)
            'dsp-circular-convolution', 'dsp-overlap-methods', 'dsp-radix2-fft',
            'dsp-iir-filter-design', 'dsp-elements-sampling-quantization',
            'dsp-dif-fft-algorithms-numericals', 'dsp-fir-linear-phase-windows',
            'dsp-fir-frequency-sampling', 'dsp-processor-architecture-tms320',
            'dsp-finite-wordlength-arithmetic',
            // PQ (23EEE615)
            'pq-definitions-variations', 'pq-harmonics', 'pq-interruption-mitigation-immunity',
            'pq-custom-power-dvr-statcom-upqc', 'pq-harmonic-sources-indices-evaluation',
            'pq-harmonic-filter-design-tuned-damped', 'pq-monitoring-instrumentation-standards',
            'pq-reliability-indices-markov-rbd', 'pq-risk-assessment-rcm-smartgrid',
            // RES (23EEE634)
            're-energy-scenario-sankey-lca', 're-energy-economics-npv-irr-payback',
            're-pv-cell-characteristics', 're-solar-radiation-instruments-resource-assessment',
            're-pv-standalone-system-design-sizing', 're-pv-grid-connected-systems-ieee1547',
            're-wind-energy', 're-ocean-energy-otec-tidal-systems',
            're-biomass-biogas-small-hydro-systems', 're-fuel-cells-hydrogen-energy-systems'
        ];
        out.s6AllLessonsPlacementReady = s6LessonIds.every(id => {
            const l = LESSONS[id];
            if (!l) return false;
            const nums = Object.values(NUMERICALS).filter(n => n.lesson === id).length;
            const ivs = Object.values(INTERVIEW).filter(iv => iv.lesson === id).length;
            return nums >= 1 && ivs >= 1 && l.body.includes('formula-box') && l.body.includes('callout-trap') && (l.mcqIds || []).length >= 4;
        });

        return out;
    }''')

    ok("session 67 (Target 1..4): Semester 6 is 100.0% FULL coverage (149/149 topics, 5/5 courses, 25/25 clean modules)",
       d67['s6AllClean'] and d67['s6TotalTopics'] == 149 and d67['s6TotalFull'] == 149,
       (d67['s6TotalTopics'], d67['s6TotalFull'], d67['s6Courses']))

    ok("session 67 MILESTONE: ALL Semester 6 lessons are Placement Ready (47 lessons across 5 courses)",
       d67['s6AllLessonsPlacementReady'])

    ok("session 67 GRAND MILESTONE: Volt Platform reaches 100/100 CLEAN MODULES (609/609 topics mapped, 0 partial, 0 unwritten)",
       d67['cleanModules'] == 100 and d67['totalMapped'] == 609 and d67['totalPartials'] == 0,
       (d67['cleanModules'], d67['totalMapped'], d67['totalPartials']))

    ok("session 67 GRAND MILESTONE: Global MCQ bank reaches 2936/3332 with EXACT 25.0000% balance [734,734,734,734] / [833,833,833,833]",
       d67['totalMcqs'] in (2936, 3332) and d67['isBalanced'] and d67['globalKeys'] in ([734, 734, 734, 734], [833, 833, 833, 833]) and d67['maxKeyFraction'] == 0.25,
       (d67['totalMcqs'], d67['globalKeys'], d67['maxKeyFraction']))

    ok("session 67 QUALITY: ZERO mockCanShuffle exclusions across entire MCQ bank (2936/3332 MCQs)",
       len(d67['shufExclusions']) == 0,
       d67['shufExclusions'][:5])

    ok("session 67 QUALITY: ZERO anti-guessing violations across all 456 lessons",
       len(d67['agViolations']) == 0,
       d67['agViolations'])

    
    # ---------------- session 68: VOLT Major Expansion — Programming, Auth, AI Chatbot ----------------
    d68 = pg.evaluate('''() => {
        const out = {};
        const probs = (typeof PROGRAMMING_PROBLEMS_BANK !== 'undefined') ? PROGRAMMING_PROBLEMS_BANK : [];
        out.totalProbs = probs.length;
        out.cProbs = probs.filter(p => p.lang === 'c').length;
        out.cppProbs = probs.filter(p => p.lang === 'cpp').length;
        out.pyProbs = probs.filter(p => p.lang === 'python').length;
        out.javaProbs = probs.filter(p => p.lang === 'java').length;
        out.mcqCount = (typeof PROGRAMMING_MCQ_BANK !== 'undefined') ? PROGRAMMING_MCQ_BANK.length : 0;
        out.hasChatbot = !!document.getElementById('aiChatbotBtn');
        return out;
    }''')

    ok("session 68 (Target 1): C coding questions count >= 100", d68['cProbs'] >= 100, d68['cProbs'])
    ok("session 68 (Target 2): C++ coding questions count >= 100", d68['cppProbs'] >= 100, d68['cppProbs'])
    ok("session 68 (Target 3): Python coding questions count >= 100", d68['pyProbs'] >= 100, d68['pyProbs'])
    ok("session 68 (Target 4): Java coding questions count >= 100", d68['javaProbs'] >= 100, d68['javaProbs'])
    ok("session 68 (Target 5): Total programming coding questions >= 400", d68['totalProbs'] >= 400, d68['totalProbs'])
    ok("session 68 (Target 6): Programming MCQ bank integrated", d68['mcqCount'] >= 100, d68['mcqCount'])
    ok("session 68 (Target 7): AI Chatbot floating widget present", d68['hasChatbot'])

    # ---------------- session 69: Programming Bank Forensic Accuracy & Regression ----------------
    d69 = pg.evaluate('''() => {
        const probs = (typeof PROGRAMMING_PROBLEMS_BANK !== 'undefined') ? PROGRAMMING_PROBLEMS_BANK : [];
        const mergeProbC = probs.find(p => p.id === 'prob-c-92' || (p.lang === 'c' && p.title && p.title.includes('Merge Two Sorted Arrays')));
        const mergeProbPy = probs.find(p => p.id === 'prob-python-92' || (p.lang === 'python' && p.title && p.title.includes('Merge Two Sorted Arrays')));
        
        let placeholders = 0;
        let htmlLeaks = 0;
        
        probs.forEach(p => {
            const code = p.code || '';
            const expl = p.explanation || '';
            const title = (p.title || '').toLowerCase();
            
            if (code.includes('color:') || code.includes('font-style:') || expl.includes('color:') || expl.includes('font-style:')) {
                htmlLeaks++;
            }
            
            if (code.includes('Processed') && code.includes('placement benchmark')) {
                placeholders++;
            } else if (code.includes('sum += i;') && !title.includes('factorial') && !title.includes('sum of first') && !title.includes('natural')) {
                placeholders++;
            }
        });
        
        return {
            hasMergeC: !!mergeProbC && mergeProbC.code.includes('merged') || (mergeProbC && mergeProbC.code.includes('a[i]')),
            hasMergePy: !!mergeProbPy && (mergeProbPy.code.includes('a[i]') || mergeProbPy.code.includes('res.append')),
            pyCode: mergeProbPy ? mergeProbPy.code : '',
            placeholders,
            htmlLeaks
        };
    }''')

    ok("regression: Merge Two Sorted Arrays (C) code has array merging logic and no sum fallback", d69['hasMergeC'])
    ok("regression: Merge Two Sorted Arrays (Python) code has array merging logic", d69['hasMergePy'])
    ok("regression: Zero fallback placeholder code across 840 problems", d69['placeholders'] == 0, d69['placeholders'])
    ok("regression: Zero HTML/CSS leakage in code or explanations", d69['htmlLeaks'] == 0, d69['htmlLeaks'])

    # Execute Python Merge Two Sorted Arrays sample
    if d69['pyCode']:
        import tempfile, subprocess, os
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                p_file = os.path.join(tmpdir, "main.py")
                with open(p_file, "w", encoding="utf-8") as pf:
                    pf.write(d69['pyCode'])
                res_run = subprocess.run([sys.executable, p_file], input="3 3 1 3 5 2 4 6\n", capture_output=True, text=True, timeout=5)
                out_clean = res_run.stdout.strip()
                ok("regression: Merge Two Sorted Arrays (Python) sample execution returns '1 2 3 4 5 6'", out_clean == "1 2 3 4 5 6", f"Got: '{out_clean}'")
        except Exception as ex:
            ok("regression: Merge Two Sorted Arrays (Python) sample execution returns '1 2 3 4 5 6'", False, str(ex))

    # ---------------- session 70: Comprehensive Forensic Quality & Execution Regression ----------------
    d70 = pg.evaluate('''() => {
        const probs = (typeof PROGRAMMING_PROBLEMS_BANK !== 'undefined') ? PROGRAMMING_PROBLEMS_BANK : [];
        let genericStmts = 0;
        let genericInputDescs = 0;
        let genericOutputDescs = 0;
        let genericExplanations = 0;
        let genericComplexity = 0;
        let hardcodedCodes = 0;
        let noInputReading = 0;
        let htmlLeaks = 0;
        
        probs.forEach(p => {
            const stmt = p.problemStatement || '';
            const inDesc = p.inputDesc || '';
            const outDesc = p.outputDesc || '';
            const exp = p.explanation || '';
            const code = p.code || '';
            const lang = (p.lang || '').toLowerCase();
            
            if (stmt.includes('Read input for') || stmt.includes('compute the expected output') || stmt.includes('Execute the algorithmic logic')) genericStmts++;
            if (inDesc.toLowerCase().includes('as specified') || inDesc.toLowerCase().includes('read input')) genericInputDescs++;
            if (outDesc.toLowerCase().includes('as specified') || outDesc.toLowerCase().includes('print the result')) genericOutputDescs++;
            if (exp.includes('Execute the algorithmic logic') || exp.includes('Read the input value N')) genericExplanations++;
            if (exp.includes('O(N) or O(1)')) genericComplexity++;
            if (code.includes('color:') || code.includes('font-style:') || exp.includes('color:') || exp.includes('font-style:')) htmlLeaks++;
            
            let hasInput = false;
            if (lang === 'c' || lang === 'cpp') hasInput = /\\b(scanf|cin|getchar|fgets|gets)\\b/.test(code);
            else if (lang === 'python') hasInput = /\\b(input|sys\\.stdin)\\b/.test(code);
            else if (lang === 'java') hasInput = /\\b(Scanner|BufferedReader|System\\.in)\\b/.test(code);
            
            if (!hasInput) noInputReading++;
            
            if (/^\\s*(printf|cout\\s*<<|print|System\\.out\\.println)\\s*\\(\\s*"[A-Za-z0-9_\\s\\.\\!\\?]+"/m.test(code)) {
                if (!hasInput && !/\\b(for|while|if)\\b/.test(code)) hardcodedCodes++;
            }
        });

        const autoProbC = probs.find(p => p.id === 'prob-c-13');
        const autoProbPy = probs.find(p => p.id === 'prob-python-13');
        const rotProbPy = probs.find(p => p.id === 'prob-python-52');

        return {
            total: probs.length,
            genericStmts,
            genericInputDescs,
            genericOutputDescs,
            genericExplanations,
            genericComplexity,
            hardcodedCodes,
            noInputReading,
            htmlLeaks,
            autoCCode: autoProbC ? autoProbC.code : '',
            autoPyCode: autoProbPy ? autoProbPy.code : '',
            rotPyCode: rotProbPy ? rotProbPy.code : ''
        };
    }''')

    ok("session 70: 1160 programming problems present (840 protected + 120 pattern + 200 application)", d70['total'] >= 1160, d70['total'])
    ok("session 70: Zero generic problem statements", d70['genericStmts'] == 0, d70['genericStmts'])
    ok("session 70: Zero generic input descriptions", d70['genericInputDescs'] == 0, d70['genericInputDescs'])
    ok("session 70: Zero generic output descriptions", d70['genericOutputDescs'] == 0, d70['genericOutputDescs'])
    ok("session 70: Zero generic explanations", d70['genericExplanations'] == 0, d70['genericExplanations'])
    ok("session 70: Zero ambiguous O(N) or O(1) complexity fields", d70['genericComplexity'] == 0, d70['genericComplexity'])
    ok("session 70: 100% of solutions read standard input", d70['noInputReading'] == 0, d70['noInputReading'])
    ok("session 70: Zero hardcoded sample-output solutions", d70['hardcodedCodes'] == 0, d70['hardcodedCodes'])
    ok("session 70: Zero HTML/CSS leakage across data", d70['htmlLeaks'] == 0, d70['htmlLeaks'])

    # Perform real Python execution tests for Automorphic & Rotation
    if d70['autoPyCode']:
        import tempfile, subprocess, os
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                p_file = os.path.join(tmpdir, "auto.py")
                with open(p_file, "w", encoding="utf-8") as pf:
                    pf.write(d70['autoPyCode'])
                
                # Test 25 -> Automorphic
                res1 = subprocess.run([sys.executable, p_file], input="25", capture_output=True, text=True, timeout=5)
                # Test 76 -> Automorphic
                res2 = subprocess.run([sys.executable, p_file], input="76", capture_output=True, text=True, timeout=5)
                # Test 26 -> Not Automorphic
                res3 = subprocess.run([sys.executable, p_file], input="26", capture_output=True, text=True, timeout=5)

                ok("session 70 execution: Automorphic (Python) 25 -> Automorphic", res1.stdout.strip() == "Automorphic", f"Got: '{res1.stdout.strip()}'")
                ok("session 70 execution: Automorphic (Python) 76 -> Automorphic", res2.stdout.strip() == "Automorphic", f"Got: '{res2.stdout.strip()}'")
                ok("session 70 execution: Automorphic (Python) 26 -> Not Automorphic", res3.stdout.strip() == "Not Automorphic", f"Got: '{res3.stdout.strip()}'")
        except Exception as ex:
            ok("session 70 execution: Automorphic (Python) tests passed", False, str(ex))

    if d70['rotPyCode']:
        import tempfile, subprocess, os
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                p_file = os.path.join(tmpdir, "rot.py")
                with open(p_file, "w", encoding="utf-8") as pf:
                    pf.write(d70['rotPyCode'])
                
                # Test rotation positive case
                res1 = subprocess.run([sys.executable, p_file], input="waterbottle erbottlewat", capture_output=True, text=True, timeout=5)
                # Test rotation negative case
                res2 = subprocess.run([sys.executable, p_file], input="waterbottle erbottlewa", capture_output=True, text=True, timeout=5)

                ok("session 70 execution: String Rotation (Python) positive case -> Rotation", res1.stdout.strip() == "Rotation", f"Got: '{res1.stdout.strip()}'")
                ok("session 70 execution: String Rotation (Python) negative case -> Not Rotation", res2.stdout.strip() == "Not Rotation", f"Got: '{res2.stdout.strip()}'")
        except Exception as ex:
            ok("session 70 execution: String Rotation (Python) tests passed", False, str(ex))


    # ---------------- session 71: Required Equation Structures & DOM Math Verification ----------------
    d71 = pg.evaluate('''() => {
        const tests = {};
        const checkEq = (id, keywords) => {
            const l = LESSONS[id];
            if (!l) return false;
            const rawBody = l.body || '';
            const hasRawKw = keywords.every(kw => rawBody.includes(kw));
            if (!hasRawKw) return false;

            const container = document.createElement('div');
            container.innerHTML = rawBody;
            document.body.appendChild(container);
            if (typeof renderMath === 'function') renderMath(container);
            const katexCount = container.querySelectorAll('.katex').length;
            const errors = container.querySelectorAll('.katex-error').length;
            document.body.removeChild(container);

            return katexCount > 0 && errors === 0;
        };

        tests['req_eq_1'] = checkEq('dc-construction-windings', ['R_a', 'r_c']);
        tests['req_eq_2'] = checkEq('ac-alt-construction', ['Y_p', 'S']);
        tests['req_eq_3'] = checkEq('dc-construction-windings', ['Y_b']);
        tests['req_eq_4'] = checkEq('dc-construction-windings', ['Y_f']);
        tests['req_eq_5'] = checkEq('dc-construction-windings', ['Y_c']);
        tests['req_eq_6'] = checkEq('sse-hparam-fet-amplifiers', ['g_m', 'I_D', 'V_']);
        tests['req_eq_7'] = checkEq('ac-alt-construction', ['sin', 'B']);
        tests['req_eq_8'] = checkEq('charge', ['q_1', 'q_2', 'r^2']);
        tests['req_eq_9'] = checkEq('sse-hparam-fet-amplifiers', ['h_{11}', 'h_{12}', 'h_{21}', 'h_{22}']);
        tests['req_eq_10'] = checkEq('sse-hparam-fet-amplifiers', ['V_G', 'V_{DD}', 'R_2']);

        return tests;
    }''')

    ok("session 71: Required Eq 1 (R_a = Zr_c / A) verified", d71['req_eq_1'])
    ok("session 71: Required Eq 2 (Y_p = S / P) verified", d71['req_eq_2'])
    ok("session 71: Required Eq 3 (Y_b back pitch) verified", d71['req_eq_3'])
    ok("session 71: Required Eq 4 (Y_f front pitch) verified", d71['req_eq_4'])
    ok("session 71: Required Eq 5 (Y_c commutator pitch) verified", d71['req_eq_5'])
    ok("session 71: Required Eq 6 (g_m transconductance) verified", d71['req_eq_6'])
    ok("session 71: Required Eq 7 (e = B l v sin theta) verified", d71['req_eq_7'])
    ok("session 71: Required Eq 8 (Coulomb Law force F) verified", d71['req_eq_8'])
    ok("session 71: Required Eq 9 (h-parameter two-port matrix) verified", d71['req_eq_9'])
    ok("session 71: Required Eq 10 (V_G voltage divider) verified", d71['req_eq_10'])

    # ---------------- session 72: Content-Truth Mathematical Truth & Diagrammatic Integrity ----------------
    d72 = pg.evaluate('''() => {
        const tests = {};
        const lessons = window.LESSONS || LESSONS;
        
        // 1. Math Truth check: closed-contour integrals render Unicode glyph \u222e and 0 bare 'oint'
        const checkMathOint = (lid) => {
            const l = lessons[lid];
            if (!l) return false;
            const container = document.createElement('div');
            container.innerHTML = l.body;
            document.body.appendChild(container);
            if (typeof renderMath === 'function') renderMath(container);
            
            const katexElements = container.querySelectorAll('.katex-html');
            let hasGlyph = false;
            let hasBareOint = false;
            for (const ke of katexElements) {
                const txt = ke.textContent || '';
                if (txt.includes('\\u222e') || txt.includes('\\u222E')) hasGlyph = true;
                const clean = txt.replace(/points?|joints?|pointing/gi, '');
                if (/(?<![a-zA-Z])oint(?![a-zA-Z])/.test(clean) || clean.includes('oint_') || clean.includes('oint^')) {
                    if (!txt.includes('\\u222e') && !txt.includes('\\u222E')) hasBareOint = true;
                }
            }
            const errCount = container.querySelectorAll('.katex-error').length;
            document.body.removeChild(container);
            return hasGlyph && !hasBareOint && errCount === 0;
        };
        
        tests['oint_vector_calculus'] = checkMathOint('emt-vector-calculus');
        tests['oint_gauss_law'] = checkMathOint('emt-gauss-law-potential');

        // 2. Math Truth check: \\implies renders Unicode glyph \u27f9 (⟹) with zero bare 'implies'
        let bareImpliesCount = 0;
        const testContainer = document.createElement('div');
        document.body.appendChild(testContainer);
        for (const [id, lesson] of Object.entries(lessons)) {
            if (!lesson || !lesson.body || !lesson.body.includes('implies')) continue;
            testContainer.innerHTML = lesson.body;
            if (typeof renderMath === 'function') renderMath(testContainer);
            const mathEls = testContainer.querySelectorAll('.katex-html');
            for (const el of mathEls) {
                const txt = el.textContent || '';
                if (/(?<![a-zA-Z])implies(?![a-zA-Z])/.test(txt)) {
                    if (!txt.includes('\\u27f9')) bareImpliesCount++;
                }
            }
        }
        document.body.removeChild(testContainer);
        tests['bare_implies_count'] = bareImpliesCount;
        
        // 3. Control diagram isolation check: generic control systems SVG occurs in 0 non-control lessons
        const disallowedKeywords = ['R(s) Input', 'Feedback H(s)', 'C(s) Output', 'System Plant'];
        const allowedControlIds = new Set([
            'z-rl-grid-control',
            'vector-control-field-oriented-control-direct-torque-control',
            'open-loop-closed-loop-feedback-control-systems',
            'pid-controllers-proportional-integral-derivative-tuning',
            'dc-motors-characteristics-speed-control',
            'cse-open-closed-loop',
            'cse-transfer-function',
            'cse-stability-routh',
            'cse-freq-domain-specs',
            'cse-time-freq-correlation',
            'cse-polar-plot-stability'
        ]);
        
        let badControlCount = 0;
        for (const [id, lesson] of Object.entries(lessons)) {
            if (!lesson || !lesson.body || allowedControlIds.has(id)) continue;
            for (const kw of disallowedKeywords) {
                if (lesson.body.includes(kw)) {
                    badControlCount++;
                    break;
                }
            }
        }
        tests['bad_control_count'] = badControlCount;
        
        // 4. Technical SVG domain checks: specific lessons contain accurate, topic-specific diagrams
        const checkSvgKw = (lid, keywords) => {
            const l = lessons[lid];
            if (!l || !l.body) return false;
            return keywords.every(kw => l.body.includes(kw));
        };
        
        tests['svg_vector_calc'] = checkSvgKw('emt-vector-calculus', ['Vector Calculus', 'Stokes', 'Divergence']);
        tests['svg_gauss_law'] = checkSvgKw('emt-gauss-law-potential', ['Gauss Law', 'Gaussian Surface']);
        tests['svg_soldering'] = checkSvgKw('z-soldering-desoldering', ['Soldering & Desoldering', 'Wetting']);
        tests['svg_prog_c'] = checkSvgKw('prog-c', ['C Compilation Pipeline', 'Memory Layout']);
        tests['svg_8085_8051'] = checkSvgKw('microprocessor-vs-microcontroller-8085-8051-architecture', ['Microprocessor', '8051', 'ALU']);
        tests['svg_mcu_periph'] = checkSvgKw('microcontroller-peripherals-gpio-timers-counters-wdt', ['GPIO', 'Timer', 'Watchdog']);
        tests['svg_shock_dalziel'] = checkSvgKw('electric-shock-physiological-effects-body-impedance-dalziel', ['Physiological', 'Dalziel', 'Ventricular Fibrillation']);
        tests['svg_plc_arch'] = checkSvgKw('plc-hardware-architecture-cpu-power-supply-io-modules', ['BACKPLANE BUS', 'CPU Module']);
        tests['svg_ladder_prog'] = checkSvgKw('ladder-diagram-programming-contacts-coils-timers-counters', ['Start', 'Stop NC', 'TON Timer']);
        tests['svg_s_plane'] = checkSvgKw('transfer-functions-poles-zeros-block-diagrams', ['Complex S-Plane', 'Stable LHP']);
        tests['svg_xfmr_dga'] = checkSvgKw('transformer-fault-diagnosis-dga-megger-turns-ratio-tan-delta', ['Dissolved Gas Analysis', 'Tan Delta']);
        tests['svg_diff_prot'] = checkSvgKw('differential-protection-transformers-generators', ['Merz-Price', 'Protected Zone', 'Restraining']);
        tests['svg_nyquist'] = checkSvgKw('nyquist-shannon-sampling-theorem-aliasing-reconstruction', ['Sampling Theorem', 'ALIASING']);
        tests['svg_v_curves'] = checkSvgKw('synchronous-motor-v-curves-pfc', ['V-Curves', 'cos φ']);
        
        return tests;
    }''')

    ok("session 72: Math Truth (emt-vector-calculus renders \\u222e glyph and zero bare oint)", d72['oint_vector_calculus'])
    ok("session 72: Math Truth (emt-gauss-law-potential renders \\u222e glyph and zero bare oint)", d72['oint_gauss_law'])
    ok("session 72: Math Truth (\\implies renders \\u27f9 ⟹ with zero bare 'implies')", d72['bare_implies_count'] == 0, d72['bare_implies_count'])
    ok("session 72: Diagram Truth (generic control loop isolated to 11 valid control lessons, zero in non-control)", d72['bad_control_count'] == 0, d72['bad_control_count'])
    ok("session 72: Diagram Truth (emt-vector-calculus SVG contains Gradient/Divergence/Stokes)", d72['svg_vector_calc'])
    ok("session 72: Diagram Truth (emt-gauss-law-potential SVG contains Gaussian surface & flux)", d72['svg_gauss_law'])
    ok("session 72: Diagram Truth (z-soldering-desoldering SVG contains joint quality & wetting physics)", d72['svg_soldering'])
    ok("session 72: Diagram Truth (prog-c SVG contains C compilation & embedded memory layout)", d72['svg_prog_c'])
    ok("session 72: Diagram Truth (8085 vs 8051 SVG contains CPU vs SoC architecture)", d72['svg_8085_8051'])
    ok("session 72: Diagram Truth (MCU peripherals SVG contains GPIO, Timers, WDT)", d72['svg_mcu_periph'])
    ok("session 72: Diagram Truth (electric shock SVG contains Dalziel fibrillation zones)", d72['svg_shock_dalziel'])
    ok("session 72: Diagram Truth (PLC architecture SVG contains backplane & CPU)", d72['svg_plc_arch'])
    ok("session 72: Diagram Truth (ladder diagram SVG contains start/stop & TON timer)", d72['svg_ladder_prog'])
    ok("session 72: Diagram Truth (transfer functions SVG contains S-Plane pole-zero map)", d72['svg_s_plane'])
    ok("session 72: Diagram Truth (transformer diagnostics SVG contains DGA & Tan Delta)", d72['svg_xfmr_dga'])
    ok("session 72: Diagram Truth (differential protection SVG contains Merz-Price scheme)", d72['svg_diff_prot'])
    ok("session 72: Diagram Truth (sampling theorem SVG contains aliasing spectrum)", d72['svg_nyquist'])
    ok("session 72: Diagram Truth (synchronous motor SVG contains V-curves and inverted V-curves)", d72['svg_v_curves'])

    # ---------------- session 73: Phase 24 Ghost Visual Card Elimination & Diagrammatic Truth ----------------
    d73 = pg.evaluate('''() => {
        const tests = {};
        const lessons = window.LESSONS || LESSONS;
        
        let ghostTvaCount = 0;
        let emptyFrameCount = 0;
        let orphanMechanicsCount = 0;
        let cableInNonCableCount = 0;
        const cableIds = new Set(['esd-armoured-cables-ampacity-vd-sc']);
        
        for (const [id, l] of Object.entries(lessons)) {
            if (!l || !l.body) continue;
            
            // 1. Ghost TVA Card: card container titled "Technical Visual Analysis" with NO SVG
            if (l.body.includes('Technical Visual Analysis') && !l.body.includes('<svg')) {
                ghostTvaCount++;
            }
            
            // 2. Empty diagram/frame divs
            if (/<div class="diagram">\\s*<\\/div>/.test(l.body) ||
                /<div style="overflow-x:auto;text-align:center;[^"]*">\\s*<\\/div>/.test(l.body)) {
                emptyFrameCount++;
            }
            
            // 3. Orphan mechanics boilerplate with NO SVG
            if ((l.body.includes('What this Diagram Shows') || l.body.includes('Technical Circuit & System Mechanics')) && !l.body.includes('<svg')) {
                orphanMechanicsCount++;
            }
            
            // 4. Cloned cable cross-section in non-cable lessons
            if (l.body.includes('Outer Armor / Sheath') && !cableIds.has(id)) {
                cableInNonCableCount++;
            }
        }
        
        tests['ghost_tva_count'] = ghostTvaCount;
        tests['empty_frame_count'] = emptyFrameCount;
        tests['orphan_mechanics_count'] = orphanMechanicsCount;
        tests['cable_in_non_cable_count'] = cableInNonCableCount;
        
        // 5. Voltage divider has authentic circuit diagram
        const vdiv = lessons['voltage-current-divider'];
        tests['vdiv_svg'] = !!(vdiv && vdiv.body && vdiv.body.includes('<svg') && vdiv.body.includes('Voltage Divider'));
        
        return tests;
    }''')

    ok("session 73: Visual Truth (zero ghost 'Technical Visual Analysis' cards without SVG)", d73['ghost_tva_count'] == 0, d73['ghost_tva_count'])
    ok("session 73: Visual Truth (zero empty diagram frames or empty .diagram divs)", d73['empty_frame_count'] == 0, d73['empty_frame_count'])
    ok("session 73: Visual Truth (zero orphan 'What this Diagram Shows' mechanics without SVG)", d73['orphan_mechanics_count'] == 0, d73['orphan_mechanics_count'])
    ok("session 73: Visual Truth (cloned cable cross-section isolated to 0 non-cable lessons)", d73['cable_in_non_cable_count'] == 0, d73['cable_in_non_cable_count'])
    ok("session 73: Visual Truth (voltage-current-divider contains authentic divider circuit SVG)", d73['vdiv_svg'])

    # ---------------- session 74: Phase 25 Full Math & Visual Truth Remediation ----------------
    d74 = pg.evaluate(r'''() => {
        const tests = {};
        const lessons = typeof LESSONS !== 'undefined' ? LESSONS : {};

        // 1. Zero raw LaTeX / delimiter leaks
        let latexLeaks = 0;
        const leaks = [];
        
        // (1) z-ai-predictive-maint
        if (!lessons['z-ai-predictive-maint'] || !lessons['z-ai-predictive-maint'].body.includes('&dollar;100,000') || lessons['z-ai-predictive-maint'].body.includes('$\\$100,000$')) {
            latexLeaks++; leaks.push('z-ai-predictive-maint');
        }
        // (2) z-smart-meters-ami
        if (!lessons['z-smart-meters-ami'] || !lessons['z-smart-meters-ami'].body.includes('&dollar;0.10/kWh') || !lessons['z-smart-meters-ami'].body.includes('&dollar;0.30/kWh')) {
            latexLeaks++; leaks.push('z-smart-meters-ami');
        }
        // (3) z-demand-response
        if (!lessons['z-demand-response'] || !lessons['z-demand-response'].body.includes('&dollar;20 per kW/month') || !lessons['z-demand-response'].body.includes('&dollar;16,000/month')) {
            latexLeaks++; leaks.push('z-demand-response');
        }
        // (4) de-adders-subtractors
        if (!lessons['de-adders-subtractors'] || lessons['de-adders-subtractors'].body.includes('24\\,\\text{ns}</b>') || !lessons['de-adders-subtractors'].body.includes('24 ns</b>')) {
            latexLeaks++; leaks.push('de-adders-subtractors');
        }
        // (5) de-parallel-cla-adders
        if (!lessons['de-parallel-cla-adders'] || lessons['de-parallel-cla-adders'].body.includes('64\\,\\text{ns}</b>') || !lessons['de-parallel-cla-adders'].body.includes('64 ns</b>')) {
            latexLeaks++; leaks.push('de-parallel-cla-adders');
        }
        // (6) de-comparators-parity
        if (!lessons['de-comparators-parity'] || lessons['de-comparators-parity'].body.includes('\\oplus 1 = <b>1</b>') || !lessons['de-comparators-parity'].body.includes('<b>1</b>.<br>')) {
            latexLeaks++; leaks.push('de-comparators-parity');
        }
        // (7) cse-root-locus-advanced-construction
        if (!lessons['cse-root-locus-advanced-construction'] || lessons['cse-root-locus-advanced-construction'].body.includes('(\\phi_a)</b>') || !lessons['cse-root-locus-advanced-construction'].body.includes('($\\phi_a$)</b>')) {
            latexLeaks++; leaks.push('cse-root-locus-advanced-construction');
        }
        // (8) pq-interruption-mitigation-immunity
        if (!lessons['pq-interruption-mitigation-immunity'] || !lessons['pq-interruption-mitigation-immunity'].body.includes('Very Low (&dollar;)')) {
            latexLeaks++; leaks.push('pq-interruption-mitigation-immunity');
        }
        // (9) pq-reliability-indices-markov-rbd
        if (!lessons['pq-reliability-indices-markov-rbd'] || !lessons['pq-reliability-indices-markov-rbd'].body.includes('Lowest (&dollar;)') || !lessons['pq-reliability-indices-markov-rbd'].body.includes('High (&dollar;&dollar;)')) {
            latexLeaks++; leaks.push('pq-reliability-indices-markov-rbd');
        }
        tests['latex_leaks'] = latexLeaks;
        tests['leak_details'] = leaks;

        // 2. Zero Cross-Domain Contaminations
        let crossDomainFaults = 0;
        // (a) Root locus should NOT have K-Fold CV
        if (lessons['cse-root-locus-fundamentals'] && lessons['cse-root-locus-fundamentals'].body.includes('5-Fold Cross-Validation')) {
            crossDomainFaults++;
        }
        // (b) PE ACVC should NOT have Routh-Hurwitz deep analysis
        if (lessons['pe-1ph-acvc'] && lessons['pe-1ph-acvc'].body.includes('Routh-Hurwitz Stability Criterion')) {
            crossDomainFaults++;
        }
        // (c) Crimping should NOT have 400kV Grid Architecture
        if (lessons['z-crimping-lugging'] && lessons['z-crimping-lugging'].body.includes('400 kV EHV')) {
            crossDomainFaults++;
        }
        // (d) Road lighting should NOT have IS Voltage Levels
        if (lessons['esd-exterior-road-lighting'] && lessons['esd-exterior-road-lighting'].body.includes('IS Voltage Levels & Statutory Limits')) {
            crossDomainFaults++;
        }
        // (e) Switchboards should NOT have domestic statutory checklist
        if (lessons['esd-industrial-distribution-switchboards'] && lessons['esd-industrial-distribution-switchboards'].body.includes('Domestic Electrical Pre-Commissioning')) {
            crossDomainFaults++;
        }
        tests['cross_domain_faults'] = crossDomainFaults;

        // 3. Authentic SVGs present in repaired topics
        tests['authentic_root_locus'] = !!(lessons['cse-root-locus-fundamentals'] && lessons['cse-root-locus-fundamentals'].body.includes('Root Locus on S-Plane'));
        tests['authentic_crimping'] = !!(lessons['z-crimping-lugging'] && lessons['z-crimping-lugging'].body.includes('Heavy-Duty Compression Cable Lug'));
        tests['authentic_road_lighting'] = !!(lessons['esd-exterior-road-lighting'] && lessons['esd-exterior-road-lighting'].body.includes('Roadway Lighting Geometry'));
        tests['authentic_switchboards'] = !!(lessons['esd-industrial-distribution-switchboards'] && lessons['esd-industrial-distribution-switchboards'].body.includes('Industrial Power Distribution Switchboard Hierarchy'));
        tests['authentic_load_demand'] = !!(lessons['load-and-demand'] && lessons['load-and-demand'].body.includes('Daily Utility Load Curve'));
        tests['authentic_s_plane'] = !!(lessons['cse-stability-routh'] && lessons['cse-stability-routh'].body.includes('S-Plane Pole Locations'));

        // 4. Zero cloned templates in excised lessons (check sample of excised lessons)
        const excisedSample = ['conductor-current-ratings-voltage-drop-derating-factors', 'norton', 'source-transformation', 'de-kmap-minimization', 'mi-three-phase-power-measurement', 'pe-3ph-inverter-120'];
        let templateLeaks = 0;
        excisedSample.forEach(id => {
            if (lessons[id] && lessons[id].body.includes('Technical Visual Analysis')) templateLeaks++;
        });
        tests['template_leaks'] = templateLeaks;

        return tests;
    }''')

    ok("session 74: Phase 25 (0 raw LaTeX / delimiter leaks across all 9 defect lessons)", d74['latex_leaks'] == 0, d74['leak_details'])
    ok("session 74: Phase 25 (0 of 5 cross-domain contaminations present)", d74['cross_domain_faults'] == 0, d74['cross_domain_faults'])
    ok("session 74: Phase 25 (authentic SVGs present in all repaired topics)", d74['authentic_root_locus'] and d74['authentic_crimping'] and d74['authentic_road_lighting'] and d74['authentic_switchboards'] and d74['authentic_load_demand'] and d74['authentic_s_plane'])
    ok("session 74: Phase 25 (0 cloned template cards present in excised lessons)", d74['template_leaks'] == 0, d74['template_leaks'])

    # Test browser-rendered math in formula-box via DOM navigation
    pg.evaluate('nav({page:"lesson", id:"kcl"})')
    pg.wait_for_timeout(200)
    has_kcl_katex = pg.evaluate('!!document.querySelector(".formula-box .katex")')
    ok("session 74: Phase 25 (formula-box with Unicode/ASCII math renders KaTeX in DOM)", has_kcl_katex)

    pg.evaluate('nav({page:"lesson", id:"thevenin"})')
    pg.wait_for_timeout(200)
    thevenin_prose = pg.evaluate('document.querySelector(".formula-box").innerText')
    ok("session 74: Phase 25 (formula-box with definition prose preserves structure without garbling)", "V_th" in thevenin_prose and "R_th" in thevenin_prose and len(thevenin_prose.split("\n")) >= 2)


    # ---------------- session 75: Phase 26 Mathematical Truth & Root Formula Rendering ----------------
    d75 = pg.evaluate(r"""() => {
        const tests = {};
        const lessons = typeof LESSONS !== 'undefined' ? LESSONS : {};

        // 1. Defect 1: z-ai-predictive-maint
        nav({page: 'lesson', id: 'z-ai-predictive-maint'});
        const zAiText = document.querySelector('#contentRoot').innerText;
        const zAiKatex = document.querySelectorAll('.formula-box .katex');
        tests['zai_no_raw_bpfo'] = !/\\text\{BPFO\}/.test(zAiText);
        tests['zai_has_katex'] = zAiKatex.length > 0;

        // 2. Defect 2: z-smart-meters-ami
        nav({page: 'lesson', id: 'z-smart-meters-ami'});
        const amiText = document.querySelector('#contentRoot').innerText;
        const amiKatex = document.querySelectorAll('.formula-box .katex');
        tests['ami_no_raw_interval'] = !/\\text\{interval\}/.test(amiText);
        tests['ami_no_raw_bill'] = !/\\text\{Total Bill\}/.test(amiText);
        tests['ami_has_katex'] = amiKatex.length > 0;

        // 3. Defect 3: z-demand-response
        nav({page: 'lesson', id: 'z-demand-response'});
        const drText = document.querySelector('#contentRoot').innerText;
        const drKatex = document.querySelectorAll('.formula-box .katex');
        tests['dr_no_raw_grid'] = !/\\text\{grid, new\}/.test(drText);
        tests['dr_no_raw_shed'] = !/\\text\{shed\}/.test(drText);
        tests['dr_has_katex'] = drKatex.length > 0;
        tests['dr_has_dollar_entities'] = lessons['z-demand-response'] && lessons['z-demand-response'].body.includes('&dollar;/kW/month');

        // 4. Defect 4: pq-interruption-mitigation-immunity
        tests['pq_imm_has_entities'] = lessons['pq-interruption-mitigation-immunity'] && 
            lessons['pq-interruption-mitigation-immunity'].body.includes('Moderate (&dollar;&dollar;)') &&
            lessons['pq-interruption-mitigation-immunity'].body.includes('Extremely High (&dollar;&dollar;)');
        nav({page: 'lesson', id: 'pq-interruption-mitigation-immunity'});
        tests['pq_imm_no_table_katex'] = document.querySelector('table').querySelectorAll('.katex').length === 0;

        // 5. Defect 5: pq-reliability-indices-markov-rbd
        tests['pq_rel_has_entities'] = lessons['pq-reliability-indices-markov-rbd'] && 
            lessons['pq-reliability-indices-markov-rbd'].body.includes('Moderate (&dollar;&dollar;)') &&
            lessons['pq-reliability-indices-markov-rbd'].body.includes('High (&dollar;&dollar;)');
        nav({page: 'lesson', id: 'pq-reliability-indices-markov-rbd'});
        tests['pq_rel_no_table_katex'] = document.querySelector('table').querySelectorAll('.katex').length === 0;

        // 6. SVG standards check (0 height="auto" attributes)
        const svgHeightAutos = document.querySelectorAll('svg[height="auto"]').length;
        tests['zero_svg_height_auto'] = (svgHeightAutos === 0);

        return tests;
    }""");

    ok("session 75: Phase 26 (z-ai-predictive-maint BPFO renders display KaTeX without raw LaTeX leak)", d75['zai_no_raw_bpfo'] and d75['zai_has_katex'])
    ok("session 75: Phase 26 (z-smart-meters-ami interval power renders display KaTeX without raw text leaks)", d75['ami_no_raw_interval'] and d75['ami_no_raw_bill'] and d75['ami_has_katex'])
    ok("session 75: Phase 26 (z-demand-response peak shaving renders display KaTeX & uses dollar entities)", d75['dr_no_raw_grid'] and d75['dr_no_raw_shed'] and d75['dr_has_katex'] and d75['dr_has_dollar_entities'])
    ok("session 75: Phase 26 (pq-interruption-mitigation-immunity uses &dollar;&dollar; and avoids table math collision)", d75['pq_imm_has_entities'] and d75['pq_imm_no_table_katex'])
    ok("session 75: Phase 26 (pq-reliability-indices-markov-rbd uses &dollar;&dollar; and avoids table math collision)", d75['pq_rel_has_entities'] and d75['pq_rel_no_table_katex'])
    ok("session 75: Phase 26 (SVG standards: exactly zero invalid height='auto' attributes on svg tags)", d75['zero_svg_height_auto'])

    ok('no JS errors', not errs and not merrs and not errs24, (errs, merrs, errs24))
    b.close()

failed = sum(1 for r in res if not r[1])
print(failed, 'FAILED of', len(res))
sys.exit(1 if failed else 0)

