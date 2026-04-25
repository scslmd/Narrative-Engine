import json
from pydantic import ValidationError

result = json.load(open("data/test_new_prompt_result.json", "r"))
try:
    from app.schemas.story_import import StoryImportAnalysis
    StoryImportAnalysis.model_validate(result)
    print("VALIDATION PASSED")
except ValidationError as e:
    print("VALIDATION FAILED:")
    for err in e.errors():
        loc = " -> ".join(str(x) for x in err["loc"])
        msg = err["msg"]
        print(f"  {loc}: {msg}")
