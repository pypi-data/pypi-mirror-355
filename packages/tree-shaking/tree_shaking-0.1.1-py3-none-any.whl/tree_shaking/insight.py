if __name__ == '__main__':
    __package__ = 'tree_shaking'

from collections import defaultdict

from lk_utils import fs
from pyecharts.charts import Graph

from .config import parse_config
from .finder import Finder
from .graph import T


def main(config_file: T.AnyPath) -> None:
    cfg = parse_config(config_file)
    finder = Finder(cfg['ignores'])
    
    weights = defaultdict(int)
    for path0 in cfg['entries'].keys():
        sources = []
        target = None
        for module, path1 in finder.get_direct_imports(
            path0, include_self=True
        ):
            if target is None:
                target = module.full_name
                weights[module.full_name] += 10
            else:
                sources.append(module.full_name)
                weights[module.full_name] += 2
        
    # DELETE
    refs = finder.references
    
    all_names = defaultdict(int)
    for k, v in refs.items():
        all_names[k] += 10
        for w in v:
            all_names[w] += 2
    nodes = [{'name': k, 'symbolSize': v} for k, v in all_names.items()]
    
    links = []
    for k, v in refs.items():
        for w in v:
            links.append({'source': w, 'target': k})
    print(len(nodes), len(links), ':v2')
    
    (
        Graph()
        .add('Dependency Network', nodes, links, repulsion=100)
        .render()
    )


if __name__ == '__main__':
    from argsense import cli
    cli.add_cmd(main)
    cli.run(main)
