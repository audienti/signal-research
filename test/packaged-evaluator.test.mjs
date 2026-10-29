import test from 'node:test';
import assert from 'node:assert/strict';
import {evaluate, resolveFilter, qualifyPerson, countNew} from '../skills/signal-prospect-research/scripts/evaluator.mjs';

const now = '2026-10-29T12:00:00Z';
const signals = ['a','b'].map(id => ({id, scope:'company', question:`Is ${id} true?`, matchRule:'Explicit proof',maxObservationAgeDays:30}));
const config = (logic='AND') => ({topic:'Test',scope:'company', logic, signals, filters:[]});
const company = {id:'company:example.com', scope:'company'};
const proof = (questionId, answer, extra={}) => ({questionId, answer, evidenceKind:answer===false?'explicit_negative':'explicit_positive',sourceRelation:'first_party',quote:'Explicit statement',coverage:'Complete stated scope', targetId:company.id, scope:'company', sourceUrl:'https://example.com/evidence', summary:'Explicit evidence for the exact question.', access:'opened', observedAt:now, ...extra});

test('S1/S2: complete Boolean truth tables including unknown', () => {
  for (const a of [true,false,null]) for (const b of [true,false,null]) {
    const evidence = [proof('a',a),proof('b',b)];
    const and = a===false||b===false ? false : a===true&&b===true ? true : null;
    const or = a===true||b===true ? true : a===false&&b===false ? false : null;
    assert.equal(evaluate(config(),company,evidence,now).answer,and);
    assert.equal(evaluate(config('OR'),company,evidence,now).answer,or);
  }
});
test('S2: empty, duplicate, mixed-scope, unknown logic and freshness configs rejected', () => {
  for (const patch of [{signals:[]},{signals:[signals[0],signals[0]]},{signals:[{...signals[0],scope:'person'}]},{logic:'xor'},{signals:[{id:'a',scope:'company'}]}])
    assert.throws(()=>evaluate({...config(),...patch},company,[],now));
});
test('S2: cross-company and cross-person evidence never completes an AND', () => {
  assert.equal(evaluate(config(),company,[proof('a',true),proof('b',true,{targetId:'company:other.com'})],now).answer,null);
  const c={topic:'Test',scope:'person',logic:'AND',signals:signals.map(s=>({...s,scope:'person'}))};
  const p={id:'https://example.com/people/1',scope:'person'};
  const e=[proof('a',true,{scope:'person',targetId:p.id}),proof('b',true,{scope:'person',targetId:'https://example.com/people/2'})];
  assert.equal(evaluate(c,p,e,now).answer,null);
});
test('S4: unavailable, stale, future, malformed and snippet evidence are unknown, not false', () => {
  for(const patch of [{access:'blocked'},{access:'snippet'},{sourceUrl:''},{summary:''},{sourceUrl:'javascript:alert(1)'},{observedAt:'2020-01-01'},{observedAt:'2027-01-01'},{answer:'true'},{observedAt:'bad'}]) {
    assert.equal(evaluate(config('OR'),company,[proof('a',true,patch)],now).answer,null);
  }
  assert.equal(evaluate(config(),company,[proof('a',true),proof('b',false,{access:'blocked'})],now).answer,null);
});
test('S4: conflict is unresolved; dated event required separately from observation', () => {
  assert.equal(evaluate(config('OR'),company,[proof('a',true),proof('a',false)],now).answer,null);
  const c={...config('OR'),signals:[{...signals[0],eventSince:'2025-01-01',eventUntil:'2026-10-29'}]};
  for(const eventAt of [null,'bad','2024-12-31','2027-01-01']) assert.equal(evaluate(c,company,[proof('a',true,{eventAt})],now).answer,null);
  assert.equal(evaluate(c,company,[proof('a',true,{eventAt:'2025-02-01'})],now).answer,true);
});
test('S3: names require evidence-backed resolution; domain and LinkedIn normalize safely', () => {
  const evidence={companyId:company.id, status:'resolved', matchedNames:['Example'],linkedinUrls:['https://www.linkedin.com/company/example'],websiteDomain:'example.com',sources:[{url:'https://example.com/about',access:'opened',observedAt:now,summary:'Official identity'}]};
  for(const [kind,value] of [['company_name','Example'],['company_url','https://www.example.com/about'],['linkedin_company_url','https://uk.linkedin.com/company/example/?trk=x']]) {
    assert.equal(resolveFilter({kind,value,resolution:evidence},now).companyId,company.id);
  }
  assert.equal(resolveFilter({kind:'company_name',value:'Acme'},now).status,'unresolved');
  assert.throws(()=>resolveFilter({kind:'linkedin_company_url',value:'https://linkedin.com/in/somebody'},now));
  assert.throws(()=>resolveFilter({kind:'linkedin_company_url',value:'https://linkedin.com.evil.com/company/example'},now));
  assert.throws(()=>resolveFilter({kind:'company_url',value:'https://example.com@evil.com'},now));
});
test('S3: filters restrict, union entries, preserve unresolved and never grant a signal', () => {
  const f={kind:'company_name',value:'Example',resolution:{status:'resolved',companyId:company.id,matchedNames:['Example'],sources:[{url:'https://example.com',access:'opened',observedAt:now,summary:'Official identity'}]}};
  const other={...f,value:'Other',resolution:{...f.resolution,matchedNames:['Other'],companyId:'company:other.com',sources:[{url:'https://other.com',access:'opened',observedAt:now,summary:'Other identity'}]}};
  assert.equal(evaluate({...config('OR'),filters:[f]},company,[],now).answer,null);
  assert.equal(evaluate({...config('OR'),filters:[other]},company,[proof('a',true)],now).answer,false);
  assert.equal(evaluate({...config('OR'),filters:[other,{kind:'company_name',value:'Unclear'}]},company,[proof('a',true)],now).answer,null);
  assert.equal(evaluate({...config('OR'),filters:[other,f]},company,[proof('a',true)],now).answer,true);
});
test('S5: signal does not override missing company fit, person role or wrong employer', () => {
  const criterion=(id,targetId)=>({id,status:'met',targetId,companyId:company.id,sources:[{url:'https://example.com/bio',sourceKind:'current_page',access:'opened',observedAt:now}],reason:'Verified'});
  const p={id:'https://example.com/people/1',companyId:company.id};
  const req={companyCriteria:['industry','geography'],roleCriteria:['employment','function','seniority']};
  const cf=req.companyCriteria.map(id=>criterion(id,company.id)); const rf=req.roleCriteria.map(id=>criterion(id,p.id));
  const result=evaluate(config('OR'),company,[proof('a',true)],now);
  assert.equal(qualifyPerson(req,company,p,result,cf,rf,now).status,'qualified');
  assert.equal(qualifyPerson(req,company,p,result,[],rf,now).status,'needs_evidence');
  assert.equal(qualifyPerson(req,company,p,result,cf,rf.slice(1),now).status,'needs_evidence');
  assert.equal(qualifyPerson(req,company,{...p,companyId:'other'},result,cf,rf,now).status,'needs_evidence');
  assert.equal(qualifyPerson(req,company,p,result,cf,[...rf.slice(1),{...rf[0],status:'not_met'}],now).status,'not_fit');
});
test('S4: repeat runs and verified aliases do not inflate new-person counts', () => {
  const p={id:'https://example.com/bio',aliases:[{id:'https://linkedin.com/in/verified',evidenceUrl:'https://example.com/bio',access:'opened',reason:'Bio links exact profile'}],status:'qualified'};
  assert.equal(countNew([p,p],[]).newCount,1);
  assert.equal(countNew([p],['https://linkedin.com/in/verified']).newCount,0);
  assert.equal(countNew([{...p,status:'needs_evidence'}],[]).newCount,0);
});

test('H1/M1: no-result cannot be false; explicit window-wide negative needs coverage, not invented event',()=>{
  const c={...config(),signals:[{...signals[0],eventSince:'2025-01-01',eventUntil:'2026-10-28'}]};
  assert.equal(evaluate(c,company,[proof('a',false,{evidenceKind:'search_absence',summary:'No results found'})],now).answer,null);
  assert.equal(evaluate(c,company,[proof('a',false,{eventAt:null,coverageSince:'2025-01-01',coverageUntil:'2026-10-28'})],now).answer,false);
  assert.equal(evaluate(c,company,[proof('a',false,{coverageSince:'2025-02-01',coverageUntil:'2026-10-28'})],now).answer,null);
});
test('H4/H5: filter resolution binds actual domain and fresh identity sources; namespace variants agree',()=>{
  const resolution={status:'resolved',companyId:'company:example.com',sources:[{url:'https://example.com/about',access:'opened',observedAt:now,summary:'Official identity'}]};
  assert.equal(resolveFilter({kind:'company_url',value:'dbs.com',resolution},now).status,'unresolved');
  assert.equal(resolveFilter({kind:'company_url',value:'example.com',resolution:{...resolution,sources:[{...resolution.sources[0],access:'snippet'}]}},now).status,'unresolved');
  const f={kind:'company_url',value:'example.com',resolution:{...resolution,companyId:'example.com'}};
  assert.equal(evaluate({...config('OR'),filters:[f]},company,[proof('a',true)],now).answer,true);
});
test('H2/H3/M2/M4: sourced current employment mandatory, stale counterevidence visible, forged result refused',()=>{
  const req={companyCriteria:['industry'],roleCriteria:['function']};
  const p={id:'https://example.com/person',companyId:company.id};
  const row=(id,targetId)=>({id,targetId,companyId:company.id,status:'met',reason:'Explicit current role',sources:[{url:'https://example.com/bio',observedAt:now,access:'opened',sourceKind:'current_page'}]});
  const cf=[row('industry',company.id)],rf=[row('function',p.id)],result=evaluate(config('OR'),company,[proof('a',true)],now);
  assert.equal(qualifyPerson(req,company,p,result,cf,rf,now).status,'needs_evidence');
  rf.push(row('employment',p.id));
  assert.equal(qualifyPerson(req,company,p,result,cf,rf,now).status,'qualified');
  const counter={...row('function',p.id),status:'not_met',sources:[{...row('function',p.id).sources[0],access:'snippet'}]};
  assert.equal(qualifyPerson(req,company,p,result,cf,[...rf,counter],now).status,'needs_evidence');
  const old={...row('employment',p.id),sources:[{...row('employment',p.id).sources[0],sourceKind:'dated_statement',publishedAt:'2020-01-01'}]};
  assert.equal(qualifyPerson(req,company,p,result,cf,[rf[0],old],now).status,'needs_evidence');
  assert.throws(()=>qualifyPerson(req,company,p,{...result},cf,rf,now));
});
test('M5/M6: canonical IDs, independent duplicate counts, timezone-required datetimes',()=>{
  const people=['https://www.linkedin.com/in/Foo/','https://linkedin.com/in/foo?utm_source=x'].map(id=>({id,status:'qualified'}));
  assert.deepEqual([countNew(people,[]).newCount,countNew(people,[]).alreadySeenCount,countNew(people,[]).duplicateInRun],[1,0,1]);
  assert.equal(countNew([people[0]],['https://linkedin.com/in/foo']).alreadySeenCount,1);
  assert.equal(countNew([{...people[0],aliases:['https://linkedin.com/in/bar']}],['https://linkedin.com/in/bar']).newCount,1);
  assert.equal(evaluate(config('OR'),company,[proof('a',true,{observedAt:'2026-10-29T10:00:00'})],now).answer,null);
});

test('R1: invalid employer IDs do not match each other in person-scope qualification',()=>{
  const p={id:'https://example.com/person',scope:'person',companyId:'junk-a'},c={id:'junk-b',scope:'company'};
  const cfg={...config('OR'),scope:'person',signals:signals.map(s=>({...s,scope:'person'}))};
  const result=evaluate(cfg,p,[proof('a',true,{scope:'person',targetId:p.id})],now);
  const row=(id,targetId)=>({id,targetId,companyId:'junk-c',status:'met',reason:'Claimed fit',sources:[{url:'https://example.com',observedAt:now,access:'opened',sourceKind:'current_page'}]});
  assert.equal(qualifyPerson({companyCriteria:['industry'],roleCriteria:['function']},c,p,result,[row('industry',c.id)],[row('employment',p.id),row('function',p.id)],now).status,'needs_evidence');
});
test('R2/R3/R7: sourced domain alias maps to canonical company, LinkedIn website binding required, null source unresolved',()=>{
  const source={url:'https://example.com/about',access:'opened',observedAt:now,summary:'Official page links regional example.com.au service'};
  const filter={kind:'company_url',value:'https://www.example.com.au',resolution:{status:'resolved',companyId:company.id,sources:[source],aliasDomains:[{domain:'example.com.au',canonicalDomain:'example.com',sources:[source]}]}};
  assert.equal(evaluate({...config('OR'),filters:[filter]},company,[proof('a',true)],now).answer,true);
  assert.equal(resolveFilter({...filter,resolution:{...filter.resolution,aliasDomains:[]}},now).status,'unresolved');
  assert.equal(resolveFilter({...filter,resolution:{...filter.resolution,sources:[null]}},now).status,'unresolved');
  const linkedin={kind:'linkedin_company_url',value:'https://linkedin.com/company/example',resolution:{status:'resolved',companyId:company.id,linkedinUrls:['https://www.linkedin.com/company/example'],websiteDomain:'other.com',sources:[source]}};
  assert.equal(resolveFilter(linkedin,now).status,'unresolved');
});
