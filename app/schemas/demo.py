from pydantic import BaseModel


class DemoScenario(BaseModel):
    id: str
    title: str
    description: str
    text: str


class DemoScenariosResponse(BaseModel):
    scenarios: list[DemoScenario]
