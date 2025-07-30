import os


def get_prompt_template(prompt_name: str) -> str:
    try:
        with open(
            os.path.join(os.path.dirname(__file__), f"{prompt_name}.md"),
            "r",
            encoding="utf-8",
        ) as f:
            template = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"경고: '{prompt_name}.md' 파일을 찾을 수 없습니다.")
    return template
