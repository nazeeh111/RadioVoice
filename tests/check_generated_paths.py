"""Check actual grcc output, rather than a source-field spelling assertion."""
import ast
from pathlib import Path
import sys

for graph in ('laser_mf_demod', 'saleae_demod', 'usrp_laser_demod2', 'laser_zmod'):
    path = Path(sys.argv[1]) / (graph + '.py')
    tree = ast.parse(path.read_text())
    assert ast.dump(tree) == ast.dump(ast.parse(Path(graph + '.py').read_text())), (graph, 'shipped Python differs from GRC regeneration')
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute)]
    sinks = [call for call in calls if call.func.attr == 'wavfile_sink']
    if graph == 'laser_zmod':
        assert not sinks, (graph, 'disabled writer unexpectedly generated')
        continue
    assert len(sinks) == 1, (graph, 'writer missing')
    assert isinstance(sinks[0].args[0], ast.Name) and sinks[0].args[0].id == 'output_path', (graph, ast.dump(sinks[0]))
    if graph == 'saleae_demod':
        sources = [call for call in calls if call.func.attr == 'file_source']
        assert len(sources) == 1
        assert isinstance(sources[0].args[1], ast.Name) and sources[0].args[1].id == 'input_path', ast.dump(sources[0])
print('PASS regenerated GNU Radio path arguments are variables, not literal filenames')
