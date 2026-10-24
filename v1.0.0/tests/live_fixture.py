"""Small real-engine scenario for browser streaming/reconnection verification."""
import uvicorn,os
from engine.runtime import Engine
from engine.state import WorldState
from engine.types import Soldier,Team,WorldPos
from server.live import LiveRunner,serve

world=WorldState(15);world.soldiers.clear()
for team in Team:
    for index in range(3):
        id=1+int(team)*10+index
        world.soldiers[id]=Soldier(id,team,WorldPos(5000+int(team)*1000,6200+index*120),hp=11)
runner=LiveRunner(Engine(world))
serve(runner,port=int(os.environ.get("MW_NV_TEST_PORT","8010")),log_level='warning')
