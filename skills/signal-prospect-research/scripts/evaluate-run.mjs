#!/usr/bin/env node
import {readFileSync, realpathSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
import {dirname, resolve} from 'node:path';
import {auditSources} from './audit-sources.mjs';
import {evaluate, qualifyPerson, countNew, canonicalCompanyId, canonicalPersonId} from './evaluator.mjs';

export function evaluateRun(run) {
  if(run.version!==1 || !['native','credits','hybrid'].includes(run.mode)) throw new Error('Version 1 and explicit execution mode required');
  for(const key of ['companies','people','calls','queue']) if(!Array.isArray(run[key])) throw new Error(`${key} must be an array`);
  for(const item of run.queue) if(!item.targetId||!['identity','company_fit','signals','role_search','employment','qualification'].includes(item.stage)||!['pending','complete','exhausted','blocked'].includes(item.status)||typeof item.nextAction!=='string') throw new Error('Queue item requires target, stage, status and nextAction');
  for(const kind of ['companyCriteria','roleCriteria']) {
    const defined=Object.keys(run.brief?.[kind]??{}).sort();
    const required=[...(run.requirements?.[kind]??[])].sort();
    if(!defined.length||JSON.stringify(defined)!==JSON.stringify(required)) throw new Error(`All brief ${kind} must be checked`);
  }
  const companies=new Map();
  const personIds=new Set();
  for(const row of run.people) {
    const id=canonicalPersonId(row.person?.id);
    if(personIds.has(id)) throw new Error('Duplicate person identity in run; merge evidence first');
    personIds.add(id);
  }
  for(const row of run.companies) {
    const key=canonicalCompanyId(row.subject.id);
    if(!key||companies.has(key)||row.subject.id!==key) throw new Error('Unique canonical company IDs required');
    companies.set(key,row);
  }
  const matrices=run.config.scope==='company'?run.companies.map(c=>evaluate(run.config,c.subject,c.signals,run.asOf)):[];
  const people=run.people.map(row=>{
    const company=companies.get(canonicalCompanyId(row.person.companyId));
    if(!company) return {id:row.person.id,status:'needs_evidence',reason:'unresolved_employer'};
    const signal=run.config.scope==='company'?matrices.find(s=>s.subjectId===company.subject.id):evaluate(run.config,row.person,row.signals,run.asOf);
    return {...qualifyPerson(run.requirements,company.subject,row.person,signal,company.fit,row.fit,run.asOf), name:row.person.name, companyId:row.person.companyId, limitations:row.person.limitations??[], aliases:row.person.aliases??[], signal};
  });
  const seen=run.prior?.complete===true&&run.prior?.aliasesResolved===true?countNew(people,run.prior.personIds):{newCount:null,reason:'incomplete_prior_or_unresolved_aliases'};
  const qualifiedByEvidenceMode={native:0,credits:0,hybrid:0,unattributed:0};
  for(let i=0;i<people.length;i++) if(people[i].status==='qualified') {
    const row=run.people[i],company=companies.get(canonicalCompanyId(row.person.companyId));
    const evidence=[...(run.config.scope==='company'?company.signals:row.signals),...company.fit.flatMap(f=>f.sources??[]),...row.fit.flatMap(f=>f.sources??[]),...(run.config.filters??[]).flatMap(f=>f.resolution?.sources??[])];
    const modes=new Set(evidence.map(e=>e.acquisitionMode));
    const key=[...modes].some(m=>!['native','credits'].includes(m))?'unattributed':modes.size>1?'hybrid':modes.has('credits')?'credits':'native';
    qualifiedByEvidenceMode[key]++;
  }
  return {asOf:run.asOf,mode:run.mode,companies:matrices,people,qualifiedCount:people.filter(p=>p.status==='qualified').length,qualifiedByEvidenceMode,novelty:seen,pending:run.queue.filter(q=>!['complete','exhausted'].includes(q.status))};
}
if(process.argv[1] && import.meta.url===pathToFileURL(realpathSync(process.argv[1])).href) {
  try {
    const file=resolve(process.argv[2]), run=JSON.parse(readFileSync(file,'utf8'));
    const checks=auditSources(run,dirname(file));
    console.log(JSON.stringify({...evaluateRun(run),sourceAudit:checks},null,2));
  }
  catch(error) { console.error(error.message); process.exitCode=1; }
}
