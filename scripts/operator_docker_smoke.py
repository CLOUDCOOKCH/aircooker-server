"""Exercise installed offline maintenance using only disposable synthetic containers."""

import json
import subprocess
import time
from urllib.error import HTTPError, URLError
from uuid import uuid4

from docker_smoke import IMAGE, docker, mutation, request, setup_log_events

PTY_RUNNER = """
import errno,json,os,pty,select,subprocess,sys,time
master,slave=pty.openpty()
child=subprocess.Popen([sys.executable,'-m','aircooker.cli','delete-household']+json.loads(sys.argv[2]),stdin=slave,stdout=slave,stderr=slave,close_fds=True)
os.close(slave)
os.write(master,(sys.argv[1]+'\\n').encode())
output=bytearray()
deadline=time.monotonic()+20
try:
    while True:
        if time.monotonic()>deadline:
            child.kill();child.wait(timeout=3)
            raise RuntimeError('Synthetic operator terminal timed out')
        if not select.select([master],[],[],0.25)[0]: continue
        try: chunk=os.read(master,4096)
        except OSError as exc:
            if exc.errno==errno.EIO: break
            raise
        if not chunk: break
        output.extend(chunk)
finally: os.close(master)
print(json.dumps({'code':child.wait(timeout=10),'output':output.decode()}))
"""


def main():
    name = "aircooker-operator-test-" + str(uuid4())
    try:
        docker(
            "run",
            "-d",
            "--name",
            name,
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges:true",
            "--tmpfs",
            "/tmp:size=64m",
            "-p",
            "127.0.0.1::8080",
            IMAGE,
        )
        port = docker("port", name, "8080/tcp").rsplit(":", 1)[1]
        base = "http://127.0.0.1:" + port

        def ready():
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                try:
                    if request(base, "/api/v1/system/health")["status"] == "ok":
                        return
                except (URLError, TimeoutError, ConnectionError):
                    time.sleep(0.1)
            raise RuntimeError("Synthetic operator container not ready")

        def setup():
            device = str(uuid4())
            token = setup_log_events(name)[-1]["setup_token"]
            tokens = request(
                base,
                "/api/v1/setup",
                {
                    "name": "Synthetic operator household",
                    "username": "cook",
                    "password": "synthetic operator test password",
                    "device_id": device,
                },
                {"X-Setup-Token": token},
            )
            return device, {"Authorization": "Bearer " + tokens["access_token"]}

        def offline_delete(confirmation, arguments=None):
            return json.loads(
                docker(
                    "run",
                    "--rm",
                    "--read-only",
                    "--cap-drop",
                    "ALL",
                    "--security-opt",
                    "no-new-privileges:true",
                    "--tmpfs",
                    "/tmp:size=64m",
                    "--volumes-from",
                    name,
                    "--entrypoint",
                    "python",
                    IMAGE,
                    "-c",
                    PTY_RUNNER,
                    confirmation,
                    json.dumps(arguments or []),
                )
            )

        ready()
        device, headers = setup()
        identity = request(base, "/api/v1/system/info")["instance_id"]
        change = mutation(
            device,
            "recipe",
            {
                "title": "Retained synthetic recipe",
                "servings": "2",
                "ingredients": [],
                "steps": ["Cook"],
            },
        )
        request(base, "/api/v1/sync/push", {"mutations": [change]}, headers)
        docker(
            "exec",
            name,
            "python",
            "-m",
            "aircooker.cli",
            "backup",
            "--output",
            "/data/backups/operator.sqlite3",
        )
        proof = json.loads(
            docker(
                "exec",
                name,
                "python",
                "-c",
                "import json,sqlite3; d=sqlite3.connect('/data/backups/operator.sqlite3'); print(json.dumps({'health':d.execute('PRAGMA quick_check').fetchone()[0],'recipes':d.execute(\"SELECT COUNT(*) FROM entity WHERE kind='recipe'\").fetchone()[0]}))",
            )
        )
        assert proof == {"health": "ok", "recipes": 1}
        blocked = json.loads(
            docker("exec", name, "python", "-c", PTY_RUNNER, "DELETE " + identity, "[]")
        )
        assert blocked["code"] != 0 and "Stop the server" in blocked["output"]
        assert len(request(base, "/api/v1/recipes", headers=headers)["items"]) == 1
        docker("stop", name)
        denied = offline_delete("DELETE wrong-household")
        assert denied["code"] != 0 and "nothing was deleted" in denied["output"]
        erased = offline_delete("DELETE " + identity)
        assert erased["code"] == 0, erased
        docker("start", name)
        base = "http://127.0.0.1:" + docker("port", name, "8080/tcp").rsplit(":", 1)[1]
        ready()
        assert request(base, "/api/v1/system/info")["configured"] is False
        setup()
        replacement = request(base, "/api/v1/system/info")["instance_id"]
        assert replacement != identity
        try:
            request(base, "/api/v1/recipes", headers=headers)
            raise AssertionError("Old credentials survived deletion")
        except HTTPError as error:
            assert error.code == 401
        assert (
            docker(
                "exec",
                name,
                "python",
                "-c",
                "from pathlib import Path; print(Path('/data/backups/operator.sqlite3').exists())",
            )
            == "True"
        )
        docker("stop", name)
        erased = offline_delete("DELETE " + replacement, ["--include-backups"])
        assert erased["code"] == 0, erased
        exists = docker(
            "run",
            "--rm",
            "--volumes-from",
            name,
            "--entrypoint",
            "python",
            IMAGE,
            "-c",
            "from pathlib import Path; print(Path('/data/backups/operator.sqlite3').exists())",
        )
        assert exists == "False"
        print(
            "PASS: packaged verified backup, running-server deletion refusal, real terminal confirmation, stopped-volume erasure, retained/explicitly erased backups, fresh identity and old-session rejection"
        )
    finally:
        subprocess.run(
            ["docker", "--host=unix:///var/run/docker.sock", "rm", "-f", "-v", name],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


if __name__ == "__main__":
    main()
