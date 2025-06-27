import os
from typing import Any, Dict, List, Optional
import uuid
import yaml
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# Вставим ту же логику из canvas
def load_scenarios(file_path: str, variables: Dict[str, Any]) -> List[Dict[str, Any]]:
    id_map: Dict[str, str] = {}

    def UUID(key: str) -> str:
        if key not in id_map:
            id_map[key] = str(uuid.uuid4())
        return id_map[key]

    env = Environment(
        loader=FileSystemLoader(searchpath=os.getcwd()),
        keep_trailing_newline=True,
        trim_blocks=False,
        lstrip_blocks=False,
    )
    def short_uuid(key: str) -> str:
        if key not in id_map:
            id_map[key] = str(uuid.uuid4())[:8]
        return id_map[key]

    env.globals['UUID'] = UUID
    env.globals['SHORT_UUID'] = short_uuid
    env.globals['now'] = lambda: datetime.now().isoformat()

    template = env.get_template(file_path)
    rendered = template.render(**variables)
    docs = list(yaml.safe_load_all(rendered))
    return docs

# Запуск проверки
vars_global = {
    'N_SLIDES': 3,
    'PROMPT': 'Напиши короткий текст про кота',
    'VIDEO_RESOLUTION': '1920x1080',
}
yaml_file = 'scenaries.yml'

all_scenarios = load_scenarios(yaml_file, vars_global)
print(f"Всего сценариев: {len(all_scenarios)}")
for s in all_scenarios:
    print(f"- {s.get('scenario_id')} (tasks: {len(s.get('tasks', []))})")
    for t in s.get('tasks', []):
        print("  ", t)
