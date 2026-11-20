"""jobs/<nome>.json: {"lines": [...], "edge": ["pt-BR-AntonioNeural"], "rate": "+0%", "chatterbox": false, "exaggeration": 0.5}
Each line is split at commas; each part becomes out/<nome>/<voz>/NN.mp3|wav. Jobs that already have output are skipped."""
import sys, os, re, json, glob, asyncio
mode = sys.argv[1]
def jobs():
    for p in sorted(glob.glob('jobs/*.json')):
        name = os.path.basename(p)[:-5]; j = json.load(open(p, encoding='utf-8'))
        parts = [x.strip() for l in j['lines'] for x in re.split(r'(?<=,)\s+', l) if x.strip()]
        yield name, j, parts
def todo(name, voice): return not os.path.exists(f'out/{name}/{voice}/done')
if mode == 'need':
    sys.exit(0 if any(j.get(sys.argv[2]) and todo(n, sys.argv[2]) for n, j, _ in jobs()) else 1)
if mode == 'edge':
    import edge_tts
    async def run():
        for name, j, parts in jobs():
            for v in j.get('edge', []):
                if not todo(name, v): continue
                d = f'out/{name}/{v}'; os.makedirs(d, exist_ok=True)
                for i, t in enumerate(parts):
                    for k in range(4):
                        try: await edge_tts.Communicate(t, v, rate=j.get('rate', '+0%'), pitch=j.get('pitch', '+0Hz')).save(f'{d}/{i:02d}.mp3'); break
                        except Exception as e: print('retry', e); await asyncio.sleep(3)
                open(f'{d}/done', 'w').write('\n'.join(parts)); print('ok', d)
    asyncio.run(run())
if mode == 'chatterbox':
    import torchaudio
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    m = ChatterboxMultilingualTTS.from_pretrained(device='cpu')
    for name, j, parts in jobs():
        if not (j.get('chatterbox') and todo(name, 'chatterbox')): continue
        d = f'out/{name}/chatterbox'; os.makedirs(d, exist_ok=True)
        ref = j.get('ref'); kw = {'audio_prompt_path': ref} if ref else {}
        for i, t in enumerate(parts):
            w = m.generate(t, language_id='pt', exaggeration=j.get('exaggeration', 0.5), cfg_weight=j.get('cfg', 0.5), **kw)
            torchaudio.save(f'{d}/{i:02d}.wav', w, m.sr); print(i, t, flush=True)
        open(f'{d}/done', 'w').write('\n'.join(parts)); print('ok', d)
