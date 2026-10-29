// Local prototype: validates supplied research; does not manufacture factual judgments.
const DAY = 86400000;
const nonempty = x => typeof x === 'string' && x.trim().length > 0;
const time = x => typeof x === 'string' && /^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2}))?$/.test(x) ? Date.parse(x) : NaN;
const evaluated = new WeakSet();
const assert = (ok, message) => { if (!ok) throw new Error(message); };
function webUrl(value) {
  try { const u = new URL(value); return ['http:','https:'].includes(u.protocol) && !u.username && !u.password && u.hostname.includes('.') ? u : null; }
  catch { return null; }
}
function fresh(value, now, days) {
  const t = time(value); return Number.isFinite(t) && t <= now && now-t <= days*DAY;
}
export function combine(values, logic) {
  assert(values.length > 0 && ['AND','OR'].includes(logic), 'Nonempty AND/OR required');
  return logic === 'AND' ? (values.includes(false) ? false : values.every(x=>x===true) ? true : null)
    : (values.includes(true) ? true : values.every(x=>x===false) ? false : null);
}
export function canonicalCompanyId(value) {
  if (!nonempty(value)) return null;
  const raw=value.replace(/^company:/,'');
  const u=webUrl(raw.includes('://')?raw:`https://${raw}`);
  if(!u || !['','/'].includes(u.pathname) || u.search || u.hash) return null;
  const host=u.hostname.toLowerCase().replace(/^www\./,'');
  if(['linkedin.com','facebook.com','twitter.com','x.com','google.com'].some(d=>host===d||host.endsWith(`.${d}`))) return null;
  return `company:${host}`;
}
export function resolveFilter(filter, asOf) {
  const now=time(asOf); assert(Number.isFinite(now),'Filter resolution requires as-of timestamp');
  assert(filter && ['company_name','company_url','linkedin_company_url'].includes(filter.kind) && nonempty(filter.value), 'Invalid company filter');
  let normalized = filter.value.trim();
  if (filter.kind === 'company_name') normalized = normalized.toLowerCase().replace(/\s+/g,' ');
  else {
    const u = webUrl(normalized.includes('://') ? normalized : `https://${normalized}`);
    assert(u, 'Invalid company URL');
    if (filter.kind === 'linkedin_company_url') {
      assert((u.hostname==='linkedin.com'||u.hostname.endsWith('.linkedin.com')) && /^\/company\/[^/]+(?:\/(?:about|posts|life))?\/?$/.test(u.pathname), 'LinkedIn company page required');
      normalized = `https://www.linkedin.com/company/${u.pathname.split('/')[2].toLowerCase()}`;
    } else {
      assert(u.hostname!=='linkedin.com' && !u.hostname.endsWith('.linkedin.com'), 'Use LinkedIn company filter type');
      normalized = u.hostname.toLowerCase().replace(/^www\./,'');
    }
  }
  // A normalized spelling is not proof of company identity. Research resolves it.
  const r = filter.resolution;
  const companyId=canonicalCompanyId(r?.companyId);
  const domain=companyId?.slice(8);
  const alias=(Array.isArray(r?.aliasDomains)?r.aliasDomains:[]).find(a=>a?.domain===normalized&&a.canonicalDomain===domain&&Array.isArray(a.sources)&&a.sources.some(s=>s&&webUrl(s.url)&&s.access==='opened'&&fresh(s.observedAt,now,30)&&nonempty(s.summary)&&[domain,normalized].includes(webUrl(s.url).hostname.replace(/^www\./,''))));
  const sources=(Array.isArray(r?.sources)?r.sources:[]).filter(s=>{
    if(!s||typeof s!=='object') return false;
    const u=webUrl(s.url);
    const host=u?.hostname.toLowerCase().replace(/^www\./,'');
    const relevant=host===domain||host?.endsWith(`.${domain}`)||(alias&&host===normalized)||(filter.kind==='linkedin_company_url'&&s.url.replace(/\/$/,'')===normalized);
    return relevant && s.access==='opened' && fresh(s.observedAt,now,30) && nonempty(s.summary);
  });
  const valueMatches=filter.kind==='company_url'?(companyId===canonicalCompanyId(normalized)||Boolean(alias))
    :filter.kind==='company_name'?r?.matchedNames?.some(n=>n.trim().toLowerCase().replace(/\s+/g,' ')===normalized)
    :r?.linkedinUrls?.includes(normalized)&&canonicalCompanyId(r.websiteDomain)===companyId;
  const resolved=r?.status==='resolved'&&companyId&&sources.length>0&&valueMatches;
  return {kind:filter.kind,value:filter.value,normalized,status:resolved?'resolved':'unresolved',companyId:resolved?companyId:null,sources};
}
function validate(config, subject, now) {
  assert(Number.isFinite(now), 'Invalid as-of date');
  assert(['company','person'].includes(config.scope) && config.scope===subject.scope && nonempty(subject.id), 'Target scope/identity required');
  if(subject.scope==='company') assert(canonicalCompanyId(subject.id),'Canonical company domain identity required');
  assert(['AND','OR'].includes(config.logic), 'Explicit AND/OR required');
  assert(nonempty(config.topic),'Topic required');
  assert(Array.isArray(config.signals) && config.signals.length>0, 'At least one signal required');
  const ids = new Set();
  for (const s of config.signals) {
    assert(nonempty(s.id)&&!ids.has(s.id)&&s.scope===config.scope, 'Unique, same-scope signals required'); ids.add(s.id);
    assert(nonempty(s.question)&&nonempty(s.matchRule),'Question and match rule required');
    assert(Number.isFinite(s.maxObservationAgeDays)&&s.maxObservationAgeDays>=0, 'Explicit observation freshness required');
    if(s.eventSince!==undefined) assert(Number.isFinite(time(s.eventSince)), 'Invalid event start');
    if(s.eventUntil!==undefined) assert(Number.isFinite(time(s.eventUntil)), 'Invalid event end');
    if(s.eventSince&&s.eventUntil) assert(time(s.eventSince)<=time(s.eventUntil),'Reversed event interval');
  }
  assert(config.filters===undefined||Array.isArray(config.filters),'Filters must be an array');
}
function answerFor(signal, subject, records, now) {
  const rows = records.filter(r=>r.questionId===signal.id && (subject.scope==='company'?canonicalCompanyId(r.targetId)===canonicalCompanyId(subject.id):r.targetId===subject.id) && r.scope===subject.scope);
  const valid = rows.filter(r=>{
    if(!['first_party','filing','third_party'].includes(r.sourceRelation)||!nonempty(r.quote)||r.evidenceKind!==(r.answer===true?'explicit_positive':'explicit_negative')) return false;
    if(r.answer===false && !nonempty(r.coverage)) return false;
    if(typeof r.answer!=='boolean'||r.access!=='opened'||!webUrl(r.sourceUrl)||!nonempty(r.summary)||!fresh(r.observedAt,now,signal.maxObservationAgeDays)) return false;
    if(r.eventAt!=null && (!Number.isFinite(time(r.eventAt))||time(r.eventAt)>now)) return false;
    if(signal.eventSince||signal.eventUntil) {
      if(r.answer===false) return Number.isFinite(time(r.coverageSince))&&Number.isFinite(time(r.coverageUntil))&&time(r.coverageSince)<=time(signal.eventSince??r.coverageSince)&&time(r.coverageUntil)>=time(signal.eventUntil??r.coverageUntil)&&time(r.coverageUntil)<=now;
      const event = time(r.eventAt);
      if(!Number.isFinite(event)) return false;
      if(signal.eventSince && event<time(signal.eventSince)) return false;
      const end = signal.eventUntil && time(signal.eventUntil)+(signal.eventUntil.length===10?DAY-1:0);
      if(end && event>end) return false;
    }
    return true;
  });
  const answers = new Set(valid.map(r=>r.answer));
  const unresolvedCounterevidence=rows.some(r=>typeof r.answer==='boolean'&&!valid.includes(r)&&valid.some(v=>v.answer!==r.answer));
  if(unresolvedCounterevidence) return {id:signal.id,answer:null,reason:'unresolved_counterevidence',evidence:valid,rejectedCount:rows.length-valid.length};
  return {id:signal.id, answer:answers.size===1?[...answers][0]:null, reason:answers.size>1?'conflicting_evidence':valid.length?'supported':'needs_evidence', evidence:valid, rejectedCount:rows.length-valid.length};
}
export function evaluate(config, subject, records, asOf) {
  const now = time(asOf); validate(config,subject,now);
  assert(Array.isArray(records),'Evidence array required');
  const signals = config.signals.map(s=>answerFor(s,subject,records,now));
  const filters = (config.filters??[]).map(f=>resolveFilter(f,asOf));
  const conflicting=new Set(filters.filter(f=>filters.some(g=>g.kind===f.kind&&g.normalized===f.normalized&&g.companyId&&f.companyId&&g.companyId!==f.companyId)).map(f=>`${f.kind}:${f.normalized}`));
  for(const f of filters) if(conflicting.has(`${f.kind}:${f.normalized}`)) {f.status='unresolved'; f.companyId=null;}
  const companyId = canonicalCompanyId(subject.scope==='company'?subject.id:subject.companyId);
  const filterAnswer = !filters.length?true:filters.some(f=>f.status==='resolved'&&f.companyId===companyId)?true:filters.some(f=>f.status==='unresolved')||!companyId?null:false;
  const signalAnswer = combine(signals.map(s=>s.answer),config.logic);
  const result={subjectId:subject.id, scope:subject.scope, asOf, logic:config.logic, answer:combine([signalAnswer,filterAnswer],'AND'), signalAnswer, filterAnswer, signals, filters};
  evaluated.add(result); return Object.freeze(result);
}
function fit(required, records, targetId, now, employerId=null) {
  assert(Array.isArray(required)&&required.length>0&&new Set(required).size===required.length, 'Explicit unique fit criteria required');
  const criteria=required.map(id=>{
    const rows=records.filter(r=>r.id===id&&r.targetId===targetId);
    const valid=rows.filter(r=>nonempty(r.reason)&&Array.isArray(r.sources)&&r.sources.length>0&&r.sources.every(s=>s&&webUrl(s.url)&&s.access==='opened'&&fresh(s.observedAt,now,30)&&(s.sourceKind==='current_page'||fresh(s.publishedAt,now,30)))&&(id!=='employment'||(canonicalCompanyId(employerId)&&canonicalCompanyId(r.companyId)===canonicalCompanyId(employerId))));
    const statuses=new Set(valid.map(r=>r.status));
    const rejected=rows.filter(r=>!valid.includes(r));
    const conflict=rejected.some(r=>r.status==='not_met');
    const answer=conflict||statuses.size!==1?null:statuses.has('met')?true:statuses.has('not_met')?false:null;
    return {id,answer,rejectedCount:rejected.length,reason:conflict?'unresolved_counterevidence':answer===null?'needs_evidence':'supported'};
  });
  return {answer:combine(criteria.map(r=>r.answer),'AND'),criteria};
}
export function qualifyPerson(requirements, company, person, signalResult, companyFit, roleFit, asOf) {
  const now=time(asOf); assert(Number.isFinite(now),'Invalid as-of date');
  assert(evaluated.has(signalResult),'Recompute signal result through evaluate before qualification');
  const companyResult=fit(requirements.companyCriteria,companyFit,company.id,now);
  const roleResult=fit([...new Set(['employment',...requirements.roleCriteria])],roleFit,person.id,now,company.id);
  const binding=canonicalCompanyId(company.id)&&canonicalCompanyId(person.companyId)===canonicalCompanyId(company.id) && signalResult.subjectId===(signalResult.scope==='company'?company.id:person.id) && signalResult.asOf===asOf;
  const answer=combine([binding?true:null, signalResult.answer, companyResult.answer, roleResult.answer],'AND');
  return {id:person.id,status:answer===true?'qualified':answer===false?'not_fit':'needs_evidence',companyAnswer:companyResult.answer,roleAnswer:roleResult.answer,signalAnswer:signalResult.answer,companyCriteria:companyResult.criteria,roleCriteria:roleResult.criteria};
}
export function canonicalPersonId(id) {
  if(typeof id==='string'&&/^linkedin:profile:[A-Za-z0-9_-]+$/.test(id)) return id;
  const u=webUrl(id); assert(u,'Stable URL/provider person ID required');
  u.hash='';
  for(const k of [...u.searchParams.keys()]) if(/^(utm_|trk|trackingId)/i.test(k)) u.searchParams.delete(k);
  if(u.hostname==='linkedin.com'||u.hostname.endsWith('.linkedin.com')) {
    assert(/^\/in\/[^/]+\/?$/.test(u.pathname),'LinkedIn person URL required');
    const id=u.pathname.split('/')[2];
    return `https://www.linkedin.com/in/${/^AC[ow][A-Za-z0-9_-]{10,}$/.test(id)?id:id.toLowerCase()}`;
  }
  u.hostname=u.hostname.toLowerCase().replace(/^www\./,'');
  u.pathname=u.pathname.replace(/\/$/,'');
  return u.toString().replace(/\/$/,'');
}
export function countNew(people, priorIds) {
  const prior=new Set(priorIds.map(canonicalPersonId)); const inRun=new Set(); let newCount=0, alreadySeenCount=0,duplicateInRun=0;
  for(const p of people.filter(p=>p.status==='qualified')) {
    const aliases=(p.aliases??[]).filter(a=>a && typeof a==='object' && a.access==='opened'&&webUrl(a.evidenceUrl)&&nonempty(a.reason));
    const ids=[canonicalPersonId(p.id),...aliases.map(a=>canonicalPersonId(a.id))];
    if(ids.some(id=>inRun.has(id))) duplicateInRun++;
    else if(ids.some(id=>prior.has(id))) alreadySeenCount++;
    else newCount++;
    ids.forEach(id=>inRun.add(id));
  }
  return {newCount,alreadySeenCount,duplicateInRun,seenIds:[...new Set([...prior,...inRun])].sort()};
}
