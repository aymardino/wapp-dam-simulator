import os, sys, json, tempfile, subprocess
ROOT = os.path.join(os.path.dirname(__file__), '..')


def test_cli_reference_run():
    out = os.path.join(tempfile.mkdtemp(), 'r.json'); prices = out.replace('.json', '.csv')
    env = dict(os.environ, WAPP_DB_PATH=os.path.join(tempfile.mkdtemp(), 'x.db'))
    r = subprocess.run([sys.executable, '-m', 'engine.cli', '--reference', '--hours', '19', '--out', out, '--prices-csv', prices],
                       cwd=ROOT, env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    res = json.load(open(out))
    assert res['summary']['hours'] == [19] and res['welfare'] > 0
    assert open(prices).read().splitlines()[0].startswith('hour,NGA')
