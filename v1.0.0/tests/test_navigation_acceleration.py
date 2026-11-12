import random
from math import hypot,ceil
from engine.map import Terrain


def sampled(terrain,start,end,vehicle):
    n=max(1,ceil(hypot(end[0]-start[0],end[1]-start[1])/50))
    return all(terrain.passable(round(start[0]+(end[0]-start[0])*i/n),round(start[1]+(end[1]-start[1])*i/n),vehicle) for i in range(n+1))


def test_fast_segments_match_original_sampling_for_edges_corners_and_random_terrain():
    rng=random.Random(301);terrain=Terrain(64,64)
    terrain.cells=[[rng.randrange(11) for _ in range(16)] for _ in range(16)]
    points=[(x,y) for x in (-1,0,1,399,400,401,6399,6400) for y in (0,399,400,401,6399)]
    pairs=[(a,b) for a in points for b in points]
    pairs.extend(((rng.randrange(6400),rng.randrange(6400)),(rng.randrange(6400),rng.randrange(6400))) for _ in range(4000))
    for a,b in pairs:
        for vehicle in (False,True):assert terrain.segment_clear(a,b,vehicle)==sampled(terrain,a,b,vehicle),(a,b,vehicle)


def test_vehicle_footprint_and_dynamic_obstacles_cannot_be_bypassed_by_center_cell():
    from engine.transport import FootprintTerrain
    terrain=Terrain(64,64);terrain.cells[3][3]=3
    footprint=FootprintTerrain(terrain,[800,800]);footprint.obstacles=[(4000,4000,800,800)]
    for a in ((1000,1000),(1800,1800),(3500,3500),(4000,3600)):
        for b in ((1000,1000),(2000,1000),(1800,1800),(4200,4200)):
            assert footprint.segment_clear(a,b,True)==sampled(footprint,a,b,True)


def test_optimized_team_views_keep_mapping_order_membership_and_live_view_contract():
    from engine.orders import TeamMap
    m=TeamMap();m['1:2']=7;m['0:1']=3
    items=m.items();values=m.values()
    assert list(items)==[('0:1',3),('1:2',7)] and len(items)==2 and ('0:1',3) in items
    m['0:3']=4
    assert len(values)==3 and list(values)==[3,4,7]
