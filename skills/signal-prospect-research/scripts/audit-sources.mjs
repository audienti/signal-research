import {readFileSync, realpathSync} from 'node:fs';
import {resolve, relative, isAbsolute} from 'node:path';

const normalized=s=>String(s).normalize('NFKC').replace(/\s+/g,' ').trim();
function strings(value) {
  if(typeof value==='string') return [value];
  if(Array.isArray(value)) return value.flatMap(strings);
  if(value&&typeof value==='object') return Object.values(value).flatMap(strings);
  return [];
}
// Presence/provenance checks, not a substitute for evaluating what a source means.
export function auditSources(run, directory) {
  const root=realpathSync(directory), calls=new Map();
  for(const call of run.calls??[]) {
    if(!call.id||calls.has(call.id)||!['native','credits'].includes(call.mode)) throw new Error('Unique call ID and native/credits call mode required');
    if(run.mode==='native'&&call.mode!=='native') throw new Error('Native run contains credit acquisition');
    calls.set(call.id,call);
  }
  let checked=0;
  function check(record) {
    if(!record||record.access!=='opened') return;
    if(!record.rawEvidenceFile||!record.quote?.trim()) throw new Error('Opened evidence needs rawEvidenceFile and exact quote');
    const file=realpathSync(resolve(root,record.rawEvidenceFile)), rel=relative(root,file);
    if(rel==='..'||rel.startsWith('../')||isAbsolute(rel)) throw new Error('Evidence must be within run directory');
    const raw=readFileSync(file,'utf8'); let haystack=raw, payload;
    try {payload=JSON.parse(raw);haystack=strings(payload).join('\n');} catch {}
    const url=record.sourceUrl??record.url;
    if(!url||(record.sourceUrl&&record.url&&record.sourceUrl!==record.url)) throw new Error('Consistent source URL required');
    if(payload?.sourceUrl ? payload.sourceUrl!==url : !haystack.includes(url)) throw new Error('Source URL is not bound to captured evidence');
    if(!normalized(haystack).includes(normalized(record.quote))) throw new Error(`Quote absent from ${record.rawEvidenceFile}`);
    const call=calls.get(record.callId);
    if(!call||record.acquisitionMode!==call.mode||!call.evidenceFiles?.includes(record.rawEvidenceFile)) throw new Error('Evidence must bind to a recorded acquisition call');
    const stamp=payload?.fetchedAt??call.observedAt??call.recordedAt;
    if(!stamp||!Number.isFinite(Date.parse(record.observedAt))||!Number.isFinite(Date.parse(stamp))||Math.abs(Date.parse(stamp)-Date.parse(record.observedAt))>60000) throw new Error('Observation must match capture/call receipt within one minute');
    if(record.eventAt && (!record.dateQuote||!normalized(haystack).includes(normalized(record.dateQuote)))) throw new Error('Dated event needs a raw source dateQuote; agent must verify its interpretation');
    checked++;
  }
  for(const c of run.companies??[]) {
    (c.signals??[]).forEach(check);
    for(const fit of c.fit??[]) (fit.sources??[]).forEach(check);
  }
  for(const p of run.people??[]) {
    (p.signals??[]).forEach(check);
    for(const fit of p.fit??[]) (fit.sources??[]).forEach(check);
  }
  for(const f of run.config?.filters??[]) {
    (f.resolution?.sources??[]).forEach(check);
    for(const alias of f.resolution?.aliasDomains??[]) (alias.sources??[]).forEach(check);
  }
  return {openedEvidenceChecked:checked,semanticJudgment:'agent_required'};
}
