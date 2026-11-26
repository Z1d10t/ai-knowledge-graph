import json,re,html,hashlib,collections
from pathlib import Path
ROOT=Path.cwd(); MD=ROOT.parent/'材料论文/全部_285篇/md'; OUT=ROOT/'evaluation/terminology_review_20261125'; OUT.mkdir(exist_ok=True)
# Reference entries authored from source passages before looking at prediction endpoints.
# term format: canonical | category | aliases separated by semicolon
DATA=[
('001',53,87,'research',[
'4-chlorobenzenesulfonate|material|4Cl-BZS;4- chlorobenzenesulfonate','benzenesulfonate|material|BZS','undercoordinated Pb2+|defect|undercoordinated Pb;Pb2+ defect sites','density functional theory|method|DFT','electron transport layer|component|ETL','nonradiative recombination|mechanism|non-radiative recombination','fill factor|property|FF','inverted perovskite solar cells|device|pin PSCs'],[
('4-chlorobenzenesulfonate','enables','dual-site Pb2+ passivation',87),('undercoordinated Pb2+ ions','results in','nonradiative recombination',77),('nonradiative recombination','limits','fill factor',77)]),
('011',25,39,'research',[
'Ga2O3|material|gallium oxide','NiOx|material|p-NiOx','GaN|material|gallium nitride','SiC|material|silicon carbide','heterojunction PN diodes|device|HJ PN diodes;PN hetero-junction','conductivity modulation|mechanism|','specific on-resistance|property|Ron,sp','breakdown voltage|property|BV'],[
('holes injection','induces','conductivity modulation',25),('Ga2O3','used in','power electronics',25),('p-NiOx','combined with','n-Ga2O3',39)]),
('021',27,55,'review',[
'quasi-2D perovskites|material_class|quasi-two-dimensional perovskites;quasi2D perovskites','quantum-well structure|structure|quantum-well structures','dielectric confinement|mechanism|dielectric-confinement','quantum confinement|mechanism|quantum-confinement','exciton binding energy|property|','energy transfer|mechanism|','photoluminescence quantum yield|property|PLQY;PLQYs','perovskite LEDs|device|PeLEDs'],[
('quasi-2D perovskites','has structure','quantum-well structures',55),('quantum-well structures','induces','quantum-confinement effects',55),('quasi-2D perovskites','used in','LEDs',27)]),
('023',27,39,'review',[
'AlGaN|material|AlGaN alloys','III-nitride|material_class|III-nitride material','solar-blind ultraviolet photodetectors|device|solar-blind UV PDs','focal plane arrays|device|FPAs','metal-semiconductor-metal photodetectors|device|MSM','avalanche photodiodes|device|APDs','epitaxy|process|','p-type doping|process|'],[
('AlGaN','used in','solar-blind UV photodetectors',27),('AlGaN-based focal plane arrays','enables','solar-blind imaging',27),('avalanche photodiodes','is a','photodetectors',27)]),
('038',35,39,'review',[
'metal oxide semiconductors|material_class|MOS','flexible room-temperature gas sensors|device|FRT gas sensors','noble metal nanoparticles|material_class|','organic polymers|material_class|','carbon nanotubes|material_class|','graphene derivatives|material_class|','transition metal dichalcogenides|material_class|','operating temperature|property|'],[
('metal oxide semiconductors','used in','gas sensors',39),('noble metal nanoparticles','modifies','metal oxide semiconductors',39),('organic polymers','modifies','metal oxide semiconductors',39)]),
('043',190,194,'research',[
'HfO2|material|','ZrO2|material|','SiO2|material|','HfO2-ZrO2 superlattice|structure|','atomic layer deposition|process|ALD','ferroelectric order|structure|FE;ferroelectric','antiferroelectric order|structure|AFE;antiferroelectric','effective oxide thickness|property|EOT'],[
('HfO2','used as','high-k dielectric layer',192),('doped-HfO2','grown by','atomic layer deposition',190),('HfO2-ZrO2 superlattice gate stack','exploits','mixed ferroelectric-antiferroelectric order',194)]),
('052',23,31,'review',[
'MXenes|material_class|MXene','transition metal carbides|material_class|carbides','transition metal nitrides|material_class|nitrides','graphene|material|','transition metal dichalcogenides|material_class|TMDCs','exfoliation|process|exfoliating','solid solutions|structure|solid solution','Mo2TiC2Tx|material|'],[
('MXenes','is a','2D materials',23),('transition metal dichalcogenides','prepared by','exfoliation',29),('Mo2TiC2Tx','has structure','ordered transition metal atomic sandwiches',31)]),
('065',31,31,'research',[
'phosphonic acids|material_class|phosphonic','carboxylic acids|material_class|carboxylic','indium tin oxide|material|ITO','self-assembled monolayer|structure|SAM','hole-selective contact|component|','perovskite light absorber|component|','one-step solution-coating|process|one-step solution-coating procedure','wettability|property|'],[
('phosphonic or carboxylic acids','self-assemble on','indium tin oxide substrate',31),('self-assembled monolayer','used as','hole-selective contact',31),('one-step solution-coating','forms','perovskite light absorber',31)]),
('095',62,72,'research',[
'Sb2O3|material|','Sb4O6|material|','MoS2|material|','inorganic molecular crystal|material_class|IMC;IMCs','van der Waals dielectrics|material_class|vdW dielectrics;vdW dielectric','standard thermal evaporation deposition|process|STED;standard thermal evaporation','electron mobility|property|','transfer-curve hysteresis|property|hysteresis'],[
('Sb2O3 dielectric film','fabricated via','standard thermal evaporation deposition',66),('Sb2O3 powder','consists of','Sb4O6 molecules',72),('Sb4O6 molecules','bonded via','van der Waals interaction',72)]),
('153',40,64,'review',[
'wide-bandgap perovskites|material_class|WBG perovskites','tandem solar cells|device|TSCs','front absorber|component|','photo-induced phase separation|mechanism|','open-circuit voltage deficit|property|VOC deficit;V OC deficit','thermalization losses|mechanism|thermalization loss','charge transport layers|component|','bandgap complementarity|mechanism|'],[
('wide-bandgap perovskites','acts as','front absorber',40),('front cell with WBG absorber','reduces','thermalization loss',62),('wide-bandgap perovskite solar cells','has issue','photo-induced phase separation',40)]),
('201',21,31,'research',[
'alpha-FAPbI3|material|α-FAPbI3;α-phase of formamidinium lead triiodide','delta-FAPbI3|material|δ-phase','formamidinium lead triiodide|material|FAPbI3','formate|material|HCOO−;HCOO-','anion-vacancy defects|defect|anion vacancy','grain boundaries|structure|grain boundary','anion engineering|process|','crystallinity|property|'],[
('formate','suppresses','anion-vacancy defects',21),('formate','improves','crystallinity',21),('FAPbI3 films','undergo phase transition','black alpha-phase to yellow delta-phase below 150 C',29)]),
('250',26,42,'research',[
'AgBiS2|material|','colloidal nanocrystals|material_class|NCs','cation disorder|structure|','cation segregation|structure|','optical transition matrix elements|property|','absorption coefficient|property|','valence band maximum|property|VBM','conduction band minimum|property|CBM'],[
('cation disorder engineering','enhances','optical transition matrix elements',26),('cation-disorder-engineered AgBiS2 colloidal nanocrystals','enables','extremely thin absorber photovoltaic devices',26),('AgBiS2 valence band maximum','derives from','Ag d and S p states',42)])]
def norm(s):
 s=html.unescape(re.sub('<[^>]+>','',str(s))).lower().replace('α','alpha').replace('δ','delta')
 return re.sub(r'[^a-z0-9]+','',s)
allrefs=[]; manifest=[]
for pid,start,end,kind,terms,relations in DATA:
 src=next(MD.glob(pid+'*')); lines=src.read_text(encoding='utf-8').splitlines()
 ref={'paper':src.stem,'kind':kind,'source_path':str(src.resolve()),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'scope_lines':[start,end],'terms':[],'relations':[]}
 for x in terms:
  name,cat,aliases=x.split('|'); ref['terms'].append({'canonical':name,'category':cat,'aliases':[a for a in aliases.split(';') if a]})
 for sub,pred,obj,line in relations:
  assert line<=len(lines)
  ref['relations'].append({'subject':sub,'predicate':pred,'object':obj,'line':line,'evidence':lines[line-1],'verdict':'source_supported','qualifier':'paper-local claim; preserve source wording and context'})
 allrefs.append(ref)
# Only after reference construction, inspect predictions. Exact labels first; substring is candidate, not semantic confirmation.
for ref in allrefs:
 f=ROOT/'evaluation/full_v2/kg_output/enriched'/f"{ref['paper']}.json"; ts=json.loads(f.read_text(encoding='utf-8'))
 endpoints=collections.defaultdict(set)
 for t in ts:
  for side in ('subject','object'):
   label=str(t.get(side,''))
   if label.startswith('obs-'):continue
   endpoints[label].add(str(t.get(side+'_type')))
 for term in ref['terms']:
  names=[term['canonical']]+term['aliases']; keys={norm(s) for s in names}
  exact=[s for s in endpoints if norm(s) in keys]
  near=[s for s in endpoints if any(len(k)>=5 and (k in norm(s) or norm(s) in k and len(norm(s))>=5) for k in keys)] if not exact else []
  term['v2_status']='label_match' if exact else 'candidate_only' if near else 'not_located_by_labels'
  term['v2_matches']=[{'label':s,'types':sorted(endpoints[s])} for s in (exact or near)[:5]]
 ref['v2_edges']=len(ts)
# Save inspectable references and deterministic comparison.
(OUT/'reference_and_comparison.json').write_text(json.dumps(allrefs,ensure_ascii=False,indent=2),encoding='utf-8')
stats=collections.Counter(t['v2_status'] for r in allrefs for t in r['terms'])
print(json.dumps({'papers':len(allrefs),'terms':sum(len(r['terms']) for r in allrefs),'relations':sum(len(r['relations']) for r in allrefs),'status':dict(stats),'kinds':dict(collections.Counter(r['kind'] for r in allrefs))},ensure_ascii=False))
for r in allrefs:
 print(r['paper'][:45],dict(collections.Counter(t['v2_status'] for t in r['terms'])))
