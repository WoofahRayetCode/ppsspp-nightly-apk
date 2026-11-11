"""Run with python3 tests/verify_workflow.py (requires PyYAML).

Exercises the actual workflow shell with a fake Gradle process; no downloads.
"""
import os, pathlib, subprocess, tempfile, yaml
root = pathlib.Path(__file__).resolve().parents[1]
workflow = yaml.safe_load((root / '.github/workflows/build-apk.yml').read_text())
assert workflow['concurrency']['cancel-in-progress'] is False
steps = workflow['jobs']['build']['steps']
for step in steps:
    if 'run' in step:
        import re
        script = re.sub(r'\$\{\{.*?\}\}', 'test', step['run'])
        subprocess.run(['bash', '-n'], input=script, text=True, check=True)
script = next(s['run'] for s in steps if s['name'] == 'Assemble normalOptimized APK')
script = script.replace('${{ steps.ver.outputs.desc }}', 'v1.19.3-1-gtest').replace('${{ steps.ver.outputs.code }}', '119030001')
cases = [
 ('success', ['ok'], 0, 1),
 ('timeout_success', ['java.net.SocketTimeoutException: Read timed out','ok'], 0, 2),
 ('plugin_success', ["could not resolve plugin artifact 'com.google.protobuf:0.10.1'",'ok'], 0, 2),
 ('exhausted', ['Could not resolve dependency'] * 3, 42, 3),
 ('compiler', ['file.cpp:7: error: missing symbol'], 42, 1),
 ('compiler_and_network', ['Could not resolve dependency\nfile.cpp:7: error: missing symbol'], 42, 1),
 ('unknown', ['Unexpected internal failure'], 42, 1),
]
for name, outputs, expected_code, attempts in cases:
    with tempfile.TemporaryDirectory() as tmp:
        p = pathlib.Path(tmp)
        (p/'gradle/wrapper').mkdir(parents=True)
        prop = p/'gradle/wrapper/gradle-wrapper.properties'
        original = 'distributionUrl=https\\://services.gradle.org/distributions/gradle-9.9.0-bin.zip\ndistributionSha256Sum=unchanged\n'
        prop.write_text(original + 'networkTimeout=10000\nnetworkTimeout:20000\n')
        for i, output in enumerate(outputs, 1):
            (p/f'output-{i}').write_text(output+'\n')
        (p/'gradlew').write_text('''#!/bin/bash
n=0
[ ! -f count ] || read -r n < count
n=$((n+1))
echo "$n" > count
printf '%s\\n' "$@" >> args
cat "output-$n"
grep -qx ok "output-$n" && exit 0
exit 42
''')
        (p/'bin').mkdir()
        (p/'bin/sleep').write_text('#!/bin/bash\necho "$1" >> delays\n')
        (p/'bin/sleep').chmod(0o755)
        env = dict(os.environ, RUNNER_TEMP=tmp, PATH=str(p/'bin')+':'+os.environ['PATH'])
        result = subprocess.run(['bash','-c',script], cwd=p, env=env, capture_output=True, text=True)
        assert result.returncode == expected_code, (name,result.stdout,result.stderr)
        assert int((p/'count').read_text()) == attempts
        assert prop.read_text() == original+'networkTimeout=60000\n'
        assert len(list(p.glob('ppsspp-assemble-*.log'))) == attempts
        assert (p/'args').read_text().splitlines() == ['assembleNormalOptimized','--stacktrace','-PANDROID_VERSION_NAME=v1.19.3-1-gtest','-PANDROID_VERSION_CODE=119030001']*attempts
        if attempts > 1:
            assert (p/'delays').read_text().splitlines() == ['15','30'][:attempts-1]
        # Re-running must not accumulate timeout properties.
        (p/'count').write_text('0\n')
        subprocess.run(['bash','-c',script], cwd=p, env=env, capture_output=True)
        assert prop.read_text() == original+'networkTimeout=60000\n'
        print('PASS', name)
print('PASS workflow YAML, concurrency, all embedded shell syntax, arguments, logs, delays, exit codes, timeout idempotence')
