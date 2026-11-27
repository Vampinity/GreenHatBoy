#!/usr/bin/env python3
"""Make the capture card fill the OBS canvas, whatever size it delivers (9 Nov: since 8 Nov ~22:25 the card sent
1280x720 and OBS showed it unscaled in the top-left 2/3 of the 1920x1080 recording, so the flash meter's grid saw
half the picture). Sets the capture source's scene item (settings: capture.source) to 'fit to screen' (bounds = canvas, scale inner,
centred) and reports the source size. --check only reports; exit 1 if the capture does not fill the canvas."""
import importlib.util, json, sys, os
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
import runner_config
cfg = runner_config.load()['capture']
spec = importlib.util.spec_from_file_location('ar', os.path.join(here, 'auto-run.py')); ar = importlib.util.module_from_spec(spec); spec.loader.exec_module(ar)
o = ar.Obs(cfg['obs_host'], cfg['obs_port'])
v = o.request('GetVideoSettings')['responseData']; W, H = v['baseWidth'], v['baseHeight']
items = o.request('GetSceneItemList', {'sceneName': o.scene})['responseData']['sceneItems']
it = next(i for i in items if i['sourceName'] == cfg['source'])
t = o.request('GetSceneItemTransform', {'sceneName': o.scene, 'sceneItemId': it['sceneItemId']})['responseData']['sceneItemTransform']
fills = abs(t['width'] - W) < 2 or abs(t['height'] - H) < 2
print(f"capture source {t['sourceWidth']:.0f}x{t['sourceHeight']:.0f}, shown {t['width']:.0f}x{t['height']:.0f} on a {W}x{H} canvas, bounds {t['boundsType']}: {'fills' if fills else 'DOES NOT FILL'}")
if '--check' in sys.argv:
    o.close(); sys.exit(0 if fills else 1)
if t['boundsType'] != 'OBS_BOUNDS_SCALE_INNER' or not fills:
    o.request('SetSceneItemTransform', {'sceneName': o.scene, 'sceneItemId': it['sceneItemId'], 'sceneItemTransform': {
        'boundsType': 'OBS_BOUNDS_SCALE_INNER', 'boundsWidth': float(W), 'boundsHeight': float(H), 'boundsAlignment': 0,
        'positionX': 0.0, 'positionY': 0.0, 'alignment': 5, 'cropLeft': 0, 'cropRight': 0, 'cropTop': 0, 'cropBottom': 0}})
    t = o.request('GetSceneItemTransform', {'sceneName': o.scene, 'sceneItemId': it['sceneItemId']})['responseData']['sceneItemTransform']
    print(f"set fit-to-canvas: shown {t['width']:.0f}x{t['height']:.0f} at {t['positionX']:.0f},{t['positionY']:.0f}, bounds {t['boundsType']}")
o.close()
