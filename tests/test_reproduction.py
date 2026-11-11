import io
import json
import os
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

os.environ['PBE_ROOT'] = str(Path(__file__).resolve().parents[1])
from pbe.runtime_images import import_archive, _digest, _verified_local
from pbe.systems.hysynth import runtime
from pbe.systems.hysynth.common import AdapterError
from pbe_artifact.common import read, write, sha
from pbe_artifact.programs import collect, validate_index, check_source


class RuntimeTests(unittest.TestCase):
    def test_config_pin_is_exposed_without_changing_any_image_blob(self):
        layer = b'a layer'
        layer_digest = _digest(layer.decode())
        config = json.dumps(dict(os='linux', architecture='amd64', rootfs=dict(diff_ids=[layer_digest])))
        pin = _digest(config)
        config_name = 'blobs/sha256/' + pin.split(':')[1]
        layer_name = 'blobs/sha256/' + layer_digest.split(':')[1]
        files = {config_name: config.encode(), layer_name: layer,
                 'manifest.json': json.dumps([dict(Config=config_name, Layers=[layer_name], RepoTags=None)]).encode(),
                 'index.json': b'{"schemaVersion":2,"manifests":[]}'}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'images.tar'
            with tarfile.open(path, 'w') as archive:
                for name, content in files.items():
                    member = tarfile.TarInfo(name)
                    member.size = len(content)
                    archive.addfile(member, io.BytesIO(content))
            before = path.read_bytes()
            with import_archive(path, {pin: [config]}) as (adapted, aliases):
                with tarfile.open(adapted) as archive:
                    self.assertEqual(archive.extractfile(layer_name).read(), layer)
                    self.assertEqual(archive.extractfile(config_name).read(), config.encode())
                    index = json.load(archive.extractfile('index.json'))
                    self.assertEqual(len(index['manifests']), 1)
                    candidate = index['manifests'][0]['digest']
                inspected = dict(Id=candidate, Os='linux', Architecture='amd64', RootFS=dict(Layers=[layer_digest]))
                with patch('pbe.runtime_images._inspect', side_effect=lambda image: inspected if image == candidate else None):
                    self.assertEqual(_verified_local(pin, [config], aliases[pin]), candidate)
                wrong = config.replace('amd64', 'arm64')
                with patch('pbe.runtime_images._inspect', return_value=None):
                    with self.assertRaisesRegex(ValueError, 'changes the pinned configuration'):
                        _verified_local(pin, [config], [[wrong]])
            self.assertEqual(path.read_bytes(), before)

    def test_only_search_memory_failures_are_recoverable(self):
        record = dict(returncode=1, container_state={}, timeout=False)
        error = 'Exception in thread "main" java.lang.OutOfMemoryError: Java heap space'
        self.assertEqual(runtime.search_resource_failure('search', record, error), 'out_of_memory')
        self.assertIsNone(runtime.search_resource_failure('inspect', record, error))
        self.assertIsNone(runtime.search_resource_failure('search', record, 'Unexpected parse error'))
        self.assertIsNone(runtime.search_resource_failure('search', dict(record, returncode=125), error))
        self.assertIsNone(runtime.search_resource_failure('search', dict(record, container_state={'inspection_error': True}), error))
        self.assertEqual(runtime.search_resource_failure('search', dict(record, container_state={'OOMKilled': True}), ''), 'out_of_memory')

    def test_failed_search_checkpoint_is_not_retried(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            (folder/'task.sl').write_text('task')
            (folder/'completions.json').write_text('{}')
            logs = folder/'search'
            def failure(case, attempt, action, seconds, images):
                attempt.mkdir(parents=True)
                (attempt/'stdout.txt').write_text('')
                (attempt/'stderr.txt').write_text('java.lang.OutOfMemoryError')
                return dict(returncode=1, timeout=False, resource_failure='out_of_memory'), None
            with patch.object(runtime, '_call', side_effect=failure) as called:
                first = runtime.search(folder, logs, images={'search': 'test'})
                second = runtime.search(folder, logs, images={'search': 'test'}, resume=True)
                self.assertEqual(first, dict(status='out_of_memory', frozen=False))
                self.assertEqual(first, second)
                self.assertEqual(called.call_count, 1)
                (logs/'attempts/000/stderr.txt').write_text('changed evidence')
                with self.assertRaisesRegex(AdapterError, 'checkpoint changed'):
                    runtime.search(folder, logs, images={'search': 'test'}, resume=True)

    def test_unknown_native_failure_still_stops_the_run(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            (folder/'task.sl').write_text('task')
            (folder/'completions.json').write_text('{}')
            with patch.object(runtime, '_call', return_value=(dict(returncode=1, timeout=False), None)):
                with self.assertRaisesRegex(AdapterError, 'Native stage failed'):
                    runtime.search(folder, folder/'logs', images={'search': 'test'})


class CollectionTests(unittest.TestCase):
    def test_failed_attempt_counts_toward_complete_design(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            batch = folder/'batch'
            protocol = dict(suite='main', condition='synthphonia', repeat=1, examples=2, task_ids=['T001','T002'])
            program = dict(id='p2', condition='synthphonia', system='synthphonia', repeat=1, examples=2, task_id='T002')
            write(batch/'protocol.json', protocol)
            write(batch/'programs.json', [program])
            outcomes = [dict(task_id='T001', frozen=False, status='out_of_memory'), dict(task_id='T002', frozen=True, status='frozen')]
            write(batch/'outcomes.json', outcomes)
            original = read
            def definitions(path):
                return {'selected_tasks':['T001','T002']} if str(path).endswith('data/selection.json') else original(path)
            with patch('pbe_artifact.programs.design', return_value={('synthphonia',1,2)}), patch('pbe_artifact.programs.read', side_effect=definitions):
                programs, summary = collect(folder, 'main')
                self.assertEqual(programs, [program])
                self.assertEqual(summary['attempts'], 2)
                write(batch/'outcomes.json', outcomes[:1])
                with self.assertRaisesRegex(ValueError, 'Unfinished synthesis batch'):
                    collect(folder, 'main')

    def test_duplicate_candidate_slots_are_rejected(self):
        p = dict(id='a', condition='merlin', system='merlin', repeat=1, examples=2, task_id='T002')
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            validate_index([p, dict(p, id='b')])

    def test_sensitivity_index_is_not_treated_as_main_synthesis(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'programs.json'
            p = dict(id='a', condition='merlin', system='merlin', repeat=1, examples=5, task_id='T002')
            write(path,[p])
            with self.assertRaisesRegex(ValueError, 'different experiment design'):
                collect(path,'selection')

    def test_analysis_rejects_changed_observations_or_different_selection_programs(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            p = dict(id='a',condition='merlin',system='merlin',repeat=1,examples=2,task_id='T002',sha256='a'*64)
            def save(suite, program):
                write(folder/(suite+'_programs.json'),[program])
                write(folder/(suite+'_execution.json'),dict(mode='new',programs=[program['id']],program_hashes={program['id']:program['sha256']},program_index=[program]))
                write(folder/(suite+'_validation.json'),dict(observations_sha256=sha(folder/(suite+'.jsonl.gz')),
                      program_index_sha256=sha(folder/(suite+'_programs.json'))))
            for suite in ['main','random','selection','sensitivity']:
                (folder/(suite+'.jsonl.gz')).write_bytes(b'fixed observations')
                save(suite,p)
            check_source(folder)
            (folder/'selection.jsonl.gz').write_bytes(b'changed observations')
            with self.assertRaisesRegex(ValueError, 'Changed execution observations'):
                check_source(folder)
            save('selection',dict(p,sha256='b'*64))
            with self.assertRaisesRegex(ValueError, 'same new main programs'):
                check_source(folder)


if __name__ == '__main__':
    unittest.main()
