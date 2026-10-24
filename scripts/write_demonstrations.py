import json,pathlib
root=pathlib.Path(__file__).resolve().parents[1]
rows=[json.loads(s) for s in (root/'data/raw/train.jsonl').read_text().splitlines()]
specs=[
(0,'72','48 + 48 / 2','April sales are 48. May sales are 48 / 2 = 24. The total is 48 + 24 = 72.', 'april = 48\nmay = april / 2\nanswer = april + may', 'sold = 0\nsold += 48\nsold += 48 / 2\nanswer = sold', 'from sympy import Integer\napril = Integer(48)\nanswer = april + april / 2'),
(2,'5','100 - 100 / 2 - 15 - 2 * 15','Betty starts with 100 / 2 = 50 dollars. Gifts add 15 + 2 * 15 = 45 dollars. She still needs 100 - 50 - 45 = 5 dollars.', 'cost = 100\nsavings = cost / 2\ngifts = 15 + 2 * 15\nanswer = cost - savings - gifts','money = 100 / 2\nmoney += 15\nmoney += 2 * 15\nanswer = 100 - money','from sympy import symbols, Eq, solve, Integer\nx = symbols("x")\nanswer = solve(Eq(Integer(100) / 2 + 15 + 2 * 15 + x, 100), x)[0]'),
(3,'42','(120 - 12 - 2 * 12) / 2','She read 12 pages yesterday and 24 today, leaving 120 - 12 - 24 = 84 pages. Half of the remainder is 42.', 'read = 12 + 2 * 12\nanswer = (120 - read) / 2','remaining = 120\nremaining -= 12\nremaining -= 2 * 12\nanswer = remaining / 2','from sympy import Integer\nanswer = (Integer(120) - 12 - 2 * 12) / 2'),
(4,'624','3 * 2 * 2 * 52','Each week he writes 3 pages times 2 friends times 2 letters = 12 pages. In 52 weeks this is 624 pages.', 'pages_per_week = 3 * 2 * 2\nanswer = pages_per_week * 52','pages = 0\nfor week in range(52):\n    pages += 3 * 2 * 2\nanswer = pages','from sympy import Integer\nanswer = Integer(3) * 2 * 2 * 52'),
(7,'16','(2 * 3 + 2) * 2','The weight starts at 2 pounds, triples to 6, increases to 8, and then doubles to 16 pounds.', 'answer = (2 * 3 + 2) * 2','weight = 2\nweight *= 3\nweight += 2\nweight *= 2\nanswer = weight','from sympy import Integer\nanswer = (Integer(2) * 3 + 2) * 2'),
(8,'41','200 - 16 - 30 - 46 - 38 - 11 - 18','The known purchases cost 30 + 46 + 38 + 11 + 18 = 143 dollars. Total spending is 200 - 16 = 184, so shoes cost 184 - 143 = 41 dollars.', 'known = 30 + 46 + 38 + 11 + 18\nanswer = 200 - 16 - known','money = 200\nfor cost in [30, 46, 38, 11, 18]:\n    money -= cost\nanswer = money - 16','from sympy import symbols, Eq, solve\nx = symbols("x")\nanswer = solve(Eq(x + 30 + 46 + 38 + 11 + 18 + 16, 200), x)[0]')]
demos=[]
for i,answer,expr,cot,pal,sim,sym in specs:
 demos.append(dict(train_index=i,question=rows[i]['question'],answer=answer,solutions={'K2':cot+'\nFINAL: '+answer,'K3':expr,'K4':pal+'\nprint("FINAL:", answer)','K5':sim+'\nprint("FINAL:", answer)','K6':sym+'\nprint("FINAL:", answer)'}))
(root/'demonstrations/sets.json').write_text(json.dumps({'version':1,'primary_pair':'A','pairs':{'A':demos[:2],'B':demos[2:4],'C':demos[4:]}},indent=2)+'\n')
