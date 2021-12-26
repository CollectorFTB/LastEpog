from collections import Counter, OrderedDict
from dataclasses import dataclass
from item import Item
import math

ALL_STATS = ['strength', 'dexterity', 'intelligence', 'attunement', 'vitality']
ELEMENTAL_RESISTANCES = ['fire_resistance', 'lightning_resistance', 'cold_resistance']
ALL_RESISTANCES = OrderedDict({'Fire': 'fire_resistance', 'Lightning': 'lightning_resistance', 'Cold': 'cold_resistance', 'Physical': 'physical_resistance', 'Poison': 'poison_resistance', 'Necrotic': 'necrotic_resistance', 'Void': 'void_resistance'})

BASE_STATS = {
    'health': 100,
    'health_per_level': 8,
    'health_regeneration': 20,
    'mana': 51,
    'mana_per_level': 0.5,
    'mana_regeneration': 8,
    'all_attributes': 1,
    'block_chance': 0,
    'endurance': 20,
    'strength': 2,
    'vitality': 1,
    'base_crit': 5
}

TAG_TO_STATS = {
    'increased_spell_damage': ['spell'],
    'increased_void_damage': ['void'],
    'added_adaptive_spell_damage': ['spell'],
    'added_void_damage': ['spell', 'attack'],
    'added_void_spell_damage': ['spell'],
    'critical_strike_chance': ['spell', 'attack'],
    'critical_strike_multiplier': ['spell', 'attack'],
    'cast_speed': ['spell'],
    'spell_critical_chance': ['spell'],
    'increased_smite_damage': ['smite'],
    'void_penetration': ['void'],
    'smite_damage_per_vitality': ['smite']
}

class Build:    
    def __init__(self, level, idols, items, tree, blessings):
        self.level = level
        self.idols = idols
        self.items = items
        self.tree = tree
        self.blessings = blessings
        self.stats = Counter(BASE_STATS)

        self.calc_stats()

    def __getattribute__(self, name):
        try:
            return object.__getattribute__(self, name)
        except:
            return self.stats[name]

        
    def calc_stats(self):
        for item in self.idols+self.items:
            self.stats.update(item.prefixes)
            self.stats.update(item.suffixes)
            self.stats.update(item.implicits)

        self.stats.update(self.tree.stats)
        self.stats.update(self.blessings.stats)
        
        self.unpack_stats()


    def unpack_stats(self):
        # all attributes
        for stat in ALL_STATS:
            self.stats[stat] += self.all_attributes
        del self.stats['all_attributes']

        # all res
        for stat in ELEMENTAL_RESISTANCES:
            self.stats[stat] += self.elemental_resistance
        del self.stats['elemental_resistance']
        
        from pprint import pprint as pp
        pp(self.stats)


    def show_mods(self, skills):        
        self.print_stats()
        self.show_generic_mods()
        self.print_resistances()


        smite = skills['smite']

        mods = set()
        for skill_tag in smite:
            mods.update(set([mod for mod, tags in TAG_TO_STATS.items() if skill_tag in tags]))
        

        base = 30 + 1.5*(self.added_adaptive_spell_damage + self.added_void_spell_damage+self.added_void_damage + self.smite_damage_per_vitality * self.vitality)
        # self.stats['increased_void_damage'] *= 1.15
        increases = sum([v for k,v in self.stats.items() if k in mods and 'increased' in k])
        
        chance = 1+(self.critical_strike_chance + self.spell_critical_chance)/100
        final_crit_chance = min(1,self.base_crit*chance/100)
        multi = 2 + (self.critical_strike_multiplier)/100
        
        final_damage = base * ((increases/100) + 1) * (1+self.more_damage/100) * (1+self.void_penetration/100)
        after_crit_damage = final_crit_chance * multi * final_damage + (1-final_crit_chance) * final_damage
        after_echo = after_crit_damage * (1 + self.echo_chance/100)
        after_repeat = after_echo * (1+self.repeat_chance/100)
        print(self.cast_speed)
        after_cast_speed = after_repeat * (1+self.cast_speed/100)
        magic_number = 0.7703253494 # ALWAYS WORKS FOR SMITE DONT ASK
        final = after_cast_speed * magic_number 

        print('FINAL_DAMAGE:', int(final))

        
        


    def print_stats(self):
        print('~~~~~~~~~~~~~~~~ STATS ~~~~~~~~~~~~~~~~')
        for stat in ALL_STATS:
            print(f'{stat.capitalize()}: {self.stats[stat]}') 


    def show_generic_mods(self):
        print('~~~~~~~~~~~~~~~~ GENERIC ~~~~~~~~~~~~~~~~')
        # effective hp/mana, hp/mana regen and ms
        ehp = round((self.health + self.health_per_level * self.level + self.vitality * 10) * (1 + self.increased_health * 0.01))
        emp = round(self.mana + self.mana_per_level * self.level + self.attunement * 2) * (1 + self.increased_mana * 0.01)
        ehr = round(self.health_regeneration * (1 + 0.01 * (self.increased_health_regeneration + 2 * self.vitality)))
        emr = round(self.mana_regeneration * (1 + (self.increased_mana_regeneration) * 0.01))

        print('HP:', ehp)
        print('MP:', emp)
        print('Health Regen:', ehr)
        print('Mana Regen:', emr)
        print('MS:', self.movement_speed)

    def print_resistances(self):
        print('~~~~~~~~~~~~~~~~ RESISTANCES ~~~~~~~~~~~~~~~~')
        adjust = 9
        names = [name.rjust(adjust, " ") for name in ALL_RESISTANCES.keys()]
        values = [str(self.stats[value]).rjust(adjust, " ") for value in ALL_RESISTANCES.values()]
        print('|'.join(names))
        print('|'.join(values))

    def print_stats(self):
        print('~~~~~~~~~~~~~~~~ STATS ~~~~~~~~~~~~~~~~')
        for stat in ALL_STATS:
            print(f'{stat.capitalize()}: {self.stats[stat]}') 


    def print_additional_stats(self):
        block_chance = self.block_chance * 0.01
        block_effectiveness = self.block_effectiveness
        armor = round(self.armor * self.increased_armour * 0.01)

@dataclass
class Tree:
    def __init__(self, mods: list[dict]):
        self.mods = mods
        self.stats = Counter()
        for mod in self.mods:
            self.stats.update(mod)

@dataclass
class Blessings:
    mods: list[dict]

    def __init__(self, mods):
        self.mods = mods
        self.stats = Counter()

        for mod in self.mods:
            self.stats.update(mod)


idols = [ 
    # 1x1
    Item(
        {'healing_effectiveness': 9},
        {'increased_void_damage': 7},
    ),
    Item(
        {'dodge_rating': 11},
        {'increased_void_damage': 8},
    ),  
    Item(
        {'damage_over_time': 8},
        {'increased_void_damage': 7},
    ),
    # 2x1
    Item(
        {'vitality': 3},
        {'increased_void_damage': 10},
    ),
    Item(
        {'vitality': 3},
        {'necrotic_resistance': 10},
    ),
    Item(
        {'vitality': 3},
        {'poison_damage': 15},
    ),
    # 4x1
    Item(
        {'vitality': 4},
        {'armor_shred_chance': 0.51},
    ),
    # 1x3
    Item( 
        # {'increased_smite_damage': 52},
        {'fire_resistance': 29},
    ),
    # 2x2
    Item(
        {'increased_void_damage_if_echo': 75},
        {'block_effectiveness': 433},
    ),
]

items = [
    Item( # helmet
        {'increased_void_damage': 57, 'level_of_anomaly': 2, 'vitality': 8},
        {'health': 62, 'increased_health': 10},
        {'armor': 210, 'critical_strike_avoidance': 23},
    ),
    Item( # amulet
        {'critical_strike_chance': 58, 'spell_critical_chance': 47, 'void_penetration': 8},
        {'health': 54, 'void_resistance': 23},
        {'necrotic_resistance': 22, 'physical_resistance': 34},
    ),
    Item( # staff
        {},
        {'added_adaptive_spell_damage': 87},
        {'increased_void_damage': 361, 'cast_speed': 46, 'increased_fire_damage': 64},
    ),
    Item( # armor
        {'armor': 350, 'critical_strike_avoidance': 19},
        {'vitality': 11},
        {'health': 104, 'increased_health': 15},
    ),
    Item( # ring1
        {'vitality': 6, 'health_regeneration': 5},
        {'increased_spell_damage': 90, 'critical_strike_chance': 48},
        {'physical_resistance': 8, 'poison_resistance': 26}
    ),
    Item( # ring2
        {'dodge_rating': 21},
        {'increased_spell_damage': 83, 'critical_strike_chance': 47},
        {'physical_resistance': 8, 'elemental_resistance': 14, 'void_resistance': 43}
    ),
    Item( # belt
        {'mana': 15},
        {'increased_void_damage': 59, 'increased_mana_regeneration': 34},
        {'increased_health': 11, 'cold_resistance': 44},
    ),
    Item( # boots
        {'movement_speed': 15, 'fire_resistance': 40, 'armor': 90},
        {'movement_speed': 16, 'vitality': 7},
        {'health': 100, 'critical_strike_avoidance': 20, 'elemental_resistance': 10},
    ),
    Item( # gloves
        {'armor': 80, 'vitality': 8},
        {'increased_health': 14, 'endurance_threshhold': 92},
        {},
    ),
    Item( # relic
        {'increased_void_damage': 62},
        {'spell_critical_chance': 71, 'increased_void_damage': 47},
        {'frailty_on_hit_chance': 49, 'physical_resistance': 44}
    ),
]

tree = Tree(
    [
        {'strength': 2},
        {'fire_resistance': 6},
        {'void_resistance': 6},
        {'vitality': 8},
        {'increased_health_regeneration': 80},
        {'armor': 75},
        {'less_damage_if_nearby': 10},
        # Time and Faith
        {'elemental_resistance': 15},
        {'attunement': 5},
        {'health': 150},
        {'healing_effectiveness': 50},
        {'blind_chance': 35},
        {'endurance': 14},
        {'health': 32},
        {'void_resistance': 16},
        {'physical_resistance': 16},
        {'added_void_damage': 12},
        {'critical_strike_multiplier': 71},
        {'added_void_spell_damage': 16},
        {'void_damage_leech': 0.06},
        {'smite_damage_per_vitality': 1},
        {'vitality': 5},
        {'echo_chance': 40},
        {'increased_health': 20},
        {'vitality': 10},
        {'increased_void_damage': 120},
        {'movement_speed': 15},
        {'increased_mana_cost': 10},
        # SMITE TREE,
        {'repeat_chance': 36},
        {'critical_strike_multiplier': 75},
        {'more_damage': 250},
        # {'cast_speed': -25},
        {'base_crit': 10}
]
)

blessings = Blessings([
        {'physical_resistance': 35},
        {'lightning_resistance': 61},
        {'armor': 266},
        {'critical_strike_avoidance': 56},
        {'void_resistance_shred_chance': 0.49},
])

sigil = Item(
    {'increased_void_damage': 24},
    {'added_adaptive_spell_damage': 7},
    {'increased_void_damage': 15, 'armor': 200},   
)

anomaly = Item(
    {'cast_speed': 10, 'critical_strike_chance': 150}
)

def main():
    global items
    items += 4*[sigil] + [anomaly]
    b = Build(level=100, idols=idols, items=items, tree=tree, blessings=blessings)
    skills = {'smite': ['smite', 'void', 'spell', 'vitality']}
    b.show_mods(skills)
    # b.damage_lolz()


if __name__ == '__main__':
    main()

