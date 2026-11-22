"""Calidad de los artefactos, participación por rol, técnicas de I3 y hitos del ciclo (caso Tomatera)."""
import json, sys, io, collections

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

MESAS = {('11/11', 1): 'A', ('11/11', 2): 'B', ('13/11', 1): 'C', ('13/11', 2): 'D'}
# Eventos que no son trabajo sobre los artefactos: conexión, ingreso, lectura de la carta,
# medición, cuestionario y cronómetro.
NO_TRABAJO = {'conexion', 'participante.unido', 'carta.leida', 'medicion.respondida',
              'cuestionario.respondido', 'cronometro.pausado', 'cronometro.reanudado',
              'tramo.iniciado', 'sesion.creada', 'inscripcion.cerrada', 'sesion.cerrada'}
STK = {'PO', 'SD', 'SD2'}

for et, p in [('11/11', sys.argv[1]), ('13/11', sys.argv[2])]:
    d = json.load(open(p, encoding='utf-8'))
    rol = {x['id']: x['roles'][0] for x in d['participantes']}
    mesa_de = {x['id']: x['mesa'] for x in d['participantes']}
    print('=' * 90)
    print('SESIÓN', et, '| tipos de evento:', dict(collections.Counter(e['tipo'] for e in d['eventos'])))
    # participación
    acc = collections.defaultdict(collections.Counter)
    tipos = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for e in d['eventos']:
        if e['tipo'] in NO_TRABAJO:
            continue
        por = e.get('por') or {}
        i = por.get('id') if isinstance(por, dict) else None
        if i in rol:
            m = mesa_de[i]
            acc[m][rol[i]] += 1
            tipos[m][rol[i]][e['tipo']] += 1
    for m in d['mesas']:
        n = m['numero']; L = MESAS[(et, n)]
        print('\n' + '-' * 30, 'MESA', L, '(', et, 'mesa', n, ')')
        miembros = {i: r[0] for i, r in m['miembros'].items()}
        a = acc[n]; tot = sum(a.values())
        stk = sum(v for r, v in a.items() if r in STK)
        print(f'  PARTICIPACIÓN: acciones de trabajo {tot}; stakeholders {stk} ({stk/tot:.0%}), equipo {tot-stk} ({(tot-stk)/tot:.0%})')
        for r in ['PO', 'SD', 'SD2', 'FR', 'AN', 'QA', 'RT']:
            if r in a or r in miembros.values():
                print(f'     {r:3s} {a.get(r,0):3d} ({a.get(r,0)/tot:.0%})  {dict(tipos[n][r])}')
        # respuestas a las rondas
        for rd in m['rondas']:
            for it in rd['items']:
                resp = rd.get('respuestas', {}).get(it['id'], {})
                print(f"  RONDA {rd['numero']} {it['id']:12s} ({it['tecnica']}): respondieron {len(resp)} de {len(miembros)}")
        marcas = [e['datos'] for e in d['eventos'] if e['tipo'] == 'ronda.marcada' and (e.get('por') or {}).get('id') in miembros]
        ult = {}
        for x in marcas:
            ult[(x['numero'], x['itemId'])] = x['resultado']
        print('  MARCAS FINALES DEL FR EN LAS RONDAS:', ult, '| quién marcó:', collections.Counter(rol[(e.get('por') or {}).get('id')] for e in d['eventos'] if e['tipo'] == 'ronda.marcada' and (e.get('por') or {}).get('id') in miembros))
        # hitos del ciclo
        ap = m['apertura'].get('versiones', {})
        print('  EC-1 versiones del problema:', len(ap), list(ap.keys()), '| equivalencia:', m['apertura'].get('equivalencia'))
        print('  chequeos del bloque:', m['chequeosBloque'])
        print('  I2a:', m['i2a'])
        print('  I2b:', m['i2b'])
        print('  línea base congelada:', bool(m['lineaBase'].get('congeladaEn')), 'por', m['lineaBase'].get('congeladaPor'))
        print('  lecturas:', {k: v['valor'] for k, v in m['lecturas'].items() if isinstance(v, dict)})
        # divergencias por técnica
        div = collections.Counter((x['detectadaEn'], x['estado']) for x in m['divergencias'])
        print('  DIVERGENCIAS 06:', dict(div))
        for x in m['divergencias']:
            print(f"     {x['id']} [{x['detectadaEn']}] {x['afectaA']} {x['estado']} :: {x['descripcion'][:150]}")
        # calidad de los artefactos
        nec = {x['id']: x for x in m['necesidades']}
        esp = m.get('esperadosPorNecesidad', {})
        tj = m['tarjetas']
        print(f'  NECESIDADES {len(nec)}: ' + '; '.join(f"{k} prioridad={v.get('prioridad')} estado={v.get('estado')} esperado={'sí' if esp.get(k, '').strip() else 'no'} tarjetas={sum(1 for t in tj if t.get('necesidadId') == k)}" for k, v in nec.items()))
        for k, v in nec.items():
            print(f"     {k}: {v.get('necesidad','')[:160]} || esperado: {esp.get(k,'')[:160]}")
        crit = [t for t in tj if t['critico'] == 'Sí']
        print(f'  TARJETAS {len(tj)} (críticas {len(crit)}); con necesidad válida {sum(1 for t in tj if t.get("necesidadId") in nec)}; con criterio {sum(1 for t in tj if str(t.get("criterioEjemplo","")).strip())}')
        for t in tj:
            c = m['i2c'].get(t['id'], {})
            marcas_c = {k: c.get(k, '—') for k in ('C1', 'C2', 'C3')}
            acept = all(c.get(k) == 'Sí' for k in ('C1', 'C2', 'C3'))
            print(f"     {t['id']} crit={t['critico']} nec={t.get('necesidadId')} tipo={t.get('tipo')} I2a={m['i2a'].get(t['id'],{}).get('revision','—')} I2c={marcas_c} aceptado={acept}")
            print(f"        enunciado: {t['enunciado']}")
            print(f"        criterio : {t['criterioEjemplo']}")
        print('  GLOSARIO:', [(g.get('termino'), g.get('estado')) for g in m['glosario']])
