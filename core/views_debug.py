import os, hashlib, time, io
from django.http import HttpResponse, JsonResponse

def healthcheck_view(request):
    return HttpResponse("OK", content_type="text/plain")

def whoami_view(request):
    # Read store/views.py directly from disk (no import)
    p = os.path.expanduser('~/apps/auditshield/store/views.py')
    info = {"file": p}
    try:
        with io.open(p, 'rb') as f:
            b = f.read()
        info.update({
            "lines": b.count(b'\n') + 1,
            "sha256": hashlib.sha256(b).hexdigest(),
            "mtime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.stat(p).st_mtime)),
        })
    except Exception as e:
        info["error"] = str(e)
    return JsonResponse(info)
