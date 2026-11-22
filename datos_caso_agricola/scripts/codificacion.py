"""Codificación de la medición antes y después del caso Tomatera con reglas escritas.

Categorías del anexo (Tabla tab:medicion_agricola) más dos que aparecieron en las
respuestas: «confusión con el tutor» (ítem 1) y «rango de 1 a 17» (ítem 2).
Convergencia = proporción de la mesa en la categoría más frecuente, sin contar
«no sabe» ni «otra» (coincidir en no saber, o en respuestas distintas entre sí, no
es entendimiento compartido).
"""
import json, sys, re, csv, io, collections, statistics as st

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def no_sabe(t):
    return bool(re.fullmatch(r'\s*(no\s*(lo\s*)?s[eé]\.?|ni idea|no tengo ni p idea)\s*', t.lower()))

def c1(t):  # ¿Qué es una guía?
    s = t.lower()
    if no_sabe(t): return 'no sabe'
    if re.search(r'\btutor\b|caña|palo|\batar\b', s): return 'confusión con el tutor'   # regla 1b
    if re.search(r'paso|manual|tutorial|instructivo|documento', s): return 'tutorial o instrucciones'  # regla 1a
    if 'tallo' in s: return 'tallo principal'
    return 'otra'

def c2(t):  # temperatura nocturna
    s = t.lower().replace('⁰', '').replace('°', '')
    if no_sabe(t): return 'no sabe'
    if re.search(r'\b1\s*([-–.,]|a)\s*17\b', s) or ('17' in s and 'menor a 1' in s): return 'rango de 1 a 17'  # regla 2a
    n = [int(x) for x in re.findall(r'\d+', s)]
    if not n: return 'otra'
    if n[0] == 10: return '10'
    if n[0] < 10: return 'menos de 10'
    if 11 <= n[0] <= 17: return 'de 11 a 17'
    return 'otra'

def c3(t):  # tierra seca
    s = t.lower()
    if no_sabe(t): return 'no sabe'
    if 'avisa para regar' in s: return 'avisa'  # regla 3a
    riega = bool(re.search(r'rieg|rega|irrig|regadera', s))
    avisa = bool(re.search(r'avis|notific', s))
    if riega and avisa: return 'las dos cosas'
    if riega: return 'riega sola'
    if avisa: return 'avisa'
    return 'otra'

def c4(t):  # mes de trasplante
    s = t.lower()
    if no_sabe(t): return 'no sabe'
    if re.search(r'hemisferio|país|pais|argentin', s): return 'según el país o el hemisferio'
    if re.search(r'septiembre|octubre', s): return 'septiembre u octubre'
    if re.search(r'marzo|abril', s): return 'marzo o abril'  # regla 4a: aunque agregue enero
    return 'otra'

COD = [c1, c2, c3, c4]
NO_CUENTAN = {'no sabe', 'otra'}

def convergencia(cats):
    c = collections.Counter(x for x in cats if x not in NO_CUENTAN)
    if not cats: return None, None
    if not c: return 0.0, '—'
    cat, k = c.most_common(1)[0]
    return k / len(cats), cat

MESAS = {('11/11', 1): 'A', ('11/11', 2): 'B', ('13/11', 1): 'C', ('13/11', 2): 'D'}
filas_csv, res = [], []
tot_ns = {'previa': [0, 0], 'posterior': [0, 0]}
for et, p in [('11/11', sys.argv[1]), ('13/11', sys.argv[2])]:
    d = json.load(open(p, encoding='utf-8'))
    rol = {x['id']: x['roles'][0] for x in d['participantes']}
    mesa = {x['id']: x['mesa'] for x in d['participantes']}
    med = d['medicion']
    for m in (1, 2):
        ids = [i for i in rol if mesa[i] == m]
        letra = MESAS[(et, m)]
        for q in range(4):
            fila = {'sesion': et, 'mesa': letra}
            for fase in ('previa', 'posterior'):
                cats = []
                for i in ids:
                    if i in med and fase in med[i]:
                        r = med[i][fase][q]
                        cat = COD[q](r)
                        cats.append(cat)
                        filas_csv.append([et, letra, rol[i], fase, f'ítem {q+1}', r, cat])
                pr, cat = convergencia(cats)
                ns = sum(1 for x in cats if x == 'no sabe')
                tot_ns[fase][0] += ns; tot_ns[fase][1] += len(cats)
                fila[fase] = (pr, cat, ns, len(cats), collections.Counter(cats))
            res.append((letra, q + 1, fila))

print('Convergencia por mesa e ítem (previa -> posterior), sin contar «no sabe» ni «otra»')
for letra, q, f in res:
    a, b = f['previa'], f['posterior']
    print(f'  {letra} ítem {q}: {a[0]:.2f} ({a[1]}) [no sabe {a[2]}/{a[3]}] -> {b[0]:.2f} ({b[1]}) [no sabe {b[2]}/{b[3]}]')
    print(f'        previa {dict(a[4])}')
    print(f'        posterior {dict(b[4])}')
pre = [f['previa'][0] for _, _, f in res]; post = [f['posterior'][0] for _, _, f in res]
print(f'\nMedia de las 16 celdas: {st.mean(pre):.2f} -> {st.mean(post):.2f}; celdas con 0,80 o más después: {sum(1 for x in post if x >= .8)} de 16')
print(f'No sabe: previa {tot_ns["previa"]}, posterior {tot_ns["posterior"]}')
for letra in 'ABCD':
    fs = [f for l, _, f in res if l == letra]
    print(f'  mesa {letra}: media previa {st.mean(f["previa"][0] for f in fs):.2f} -> posterior {st.mean(f["posterior"][0] for f in fs):.2f}')

with open(sys.argv[3], 'w', encoding='utf-8-sig', newline='') as fh:
    w = csv.writer(fh, delimiter=';')
    w.writerow(['sesion', 'mesa', 'rol', 'momento', 'item', 'respuesta', 'categoria'])
    w.writerows(filas_csv)
print('\nfilas en el CSV:', len(filas_csv))
