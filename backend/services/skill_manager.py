"""SkillManager — 扫描 skills/ 目录，管理知识技能"""

import re
from typing import Optional
from pathlib import Path

SKILLS_DIR = Path(__file__).parent.parent.parent / "skills"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


class Skill:
    """一个知识技能"""
    def __init__(self, filename: str, name: str, description: str, always: bool, content: str):
        self.filename = filename
        self.name = name
        self.description = description
        self.always = always
        self.content = content


class SkillManager:
    """扫描、注册、加载技能文件"""

    def __init__(self):
        self._skills: list[Skill] = []
        self._reload()

    def _reload(self) -> None:
        """扫描 skills/ 目录"""
        self._skills = []
        if not SKILLS_DIR.exists():
            return
        for f in sorted(SKILLS_DIR.glob("*.md")):
            skill = self._parse(f)
            if skill:
                self._skills.append(skill)

    @staticmethod
    def _parse(filepath: Path) -> Optional[Skill]:
        text = filepath.read_text(encoding="utf-8")
        m = FRONTMATTER_RE.match(text)
        if not m:
            return None
        body = text[m.end():].strip()
        meta = {}
        for line in m.group(1).strip().split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        return Skill(
            filename=filepath.name,
            name=meta.get("name", filepath.stem),
            description=meta.get("description", ""),
            always=meta.get("always", "false").lower() == "true",
            content=body,
        )

    def get_registry(self) -> list[dict]:
        """返回可用技能列表（给 Function Call 用）"""
        on_demand = [
            {"name": s.name, "description": s.description}
            for s in self._skills if not s.always
        ]
        return on_demand

    def get_always_skills(self) -> list[str]:
        """返回 always=true 的技能名"""
        return [s.name for s in self._skills if s.always]

    def load(self, names: list[str]) -> str:
        """加载指定技能的内容，拼成 system prompt"""
        parts = []
        for name in names:
            for s in self._skills:
                if s.name == name:
                    parts.append(f"## {s.name}\n{s.content}")
                    break
        return "\n\n".join(parts)

    def get_source_files(self, names: list[str]) -> list[str]:
        """返回技能对应的源文件名"""
        result = []
        for name in names:
            for s in self._skills:
                if s.name == name:
                    result.append(s.filename)
                    break
        return result


skill_manager = SkillManager()
