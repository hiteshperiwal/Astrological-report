from pathlib import Path
import json
import app.mundane as mundane

OUT=Path('data/mundane_backtest_report.json')
CASES=[
    dict(country='Israel',start='2020-01-01',end='2026-06-30',development_end='2023-12-31',holdout_start='2024-01-01'),
    dict(country='India',start='1971-01-01',end='1999-12-31',development_end='1989-12-31',holdout_start='1990-01-01'),
]
report={'version':'1.0.5','method':'chronological development tuning + frozen blind holdout','cases':[]}
for c in CASES:
    mundane._CORPUS_SIGNATURE_CACHE.clear()
    r=mundane.retrospective_event_forecast_backtest(c['country'],c['start'],c['end'],365,365,c['development_end'],c['holdout_start'],top_k=3)
    hits=[]
    for row in r.get('blind_holdout',{}).get('rows',[]):
        hits.extend(row.get('hits',[]))
    r['correct_blind_holdout_predictions']=hits
    report['cases'].append(r)
OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
for r in report['cases']:
    b=r['blind_holdout']
    print(f"{r['country']}: threshold={r['threshold']}; blind precision={b['precision_pct']}%; recall={b['recall_pct']}%; F1={b['f1_pct']}%; predictions={b['predicted']}; hits={b['hits']}; 80%-precision={r['meets_80_precision']}")
    for h in r['correct_blind_holdout_predictions']:
        print('  HIT:',h['actual']['date'],h['actual']['event'], '<-', h['prediction']['event_class'], h['prediction']['signal_score'])
