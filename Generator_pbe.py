import os, json
from pprint import pprint
import sys, urllib.request, re, time, os
import aiohttp
import asyncio
import re
from aiofiles import open as aio_open

champions = [
	"annie", "olaf", "galio", "twistedfate", "xinzhao", "urgot", "leblanc", "vladimir", "fiddlesticks", "kayle",
	"masteryi", "alistar", "ryze", "sion", "sivir", "soraka", "teemo", "tristana", "warwick", "nunu", "missfortune",
	"ashe", "tryndamere", "jax", "morgana", "zilean", "singed", "evelynn", "twitch", "karthus", "chogath", "amumu",
	"rammus", "anivia", "shaco", "drmundo", "sona", "kassadin", "irelia", "janna", "gangplank", "corki", "karma",
	"taric", "veigar", "trundle", "swain", "caitlyn", "blitzcrank", "malphite", "katarina", "nocturne", "maokai",
	"renekton", "jarvaniv", "elise", "orianna", "monkeyking", "brand", "leesin", "vayne", "rumble", "cassiopeia",
	"skarner", "heimerdinger", "nasus", "nidalee", "udyr", "poppy", "gragas", "pantheon", "ezreal", "mordekaiser",
	"yorick", "akali", "kennen", "garen", "leona", "malzahar", "talon", "riven", "kogmaw", "shen", "lux", "xerath",
	"shyvana", "ahri", "graves", "fizz", "volibear", "rengar", "varus", "nautilus", "viktor", "sejuani", "fiora",
	"ziggs", "lulu", "draven", "hecarim", "khazix", "darius", "jayce", "lissandra", "diana", "quinn", "syndra",
	"aurelionsol", "kayn", "zoe", "zyra", "kaisa", "seraphine", "gnar", "zac", "yasuo", "velkoz", "taliyah",
	"camille", "akshan", "belveth", "braum", "jhin", "kindred", "zeri", "jinx", "tahmkench", "viego", "senna",
	"lucian", "zed", "kled", "ekko", "qiyana", "vi", "aatrox", "nami", "azir", "yuumi", "samira", "thresh", "illaoi",
	"reksai", "ivern", "kalista", "bard", "rakan", "xayah", "ornn", "sylas", "neeko", "aphelios", "rell", "pyke",
	"vex", "yone", "sett", "lillia", "gwen", "renata", "nilah", "ksante", "milio", "naafiri", "briar",
]

async def find_key_ending_with_async(dictionary, partial_key):
	for key, val in dictionary.items():
		if key.endswith(partial_key):
			return val
	return None

async def find_key_by_full_name(dictionary, full_name):
	current_dict = dictionary  # Initialize current_dict with the input dictionary
	for key, val in current_dict.items():
		if key == full_name:
			return val
		elif isinstance(val, dict):
			result = await find_key_by_full_name(val, full_name)
			if result is not None:
				return result
	return None
    
async def get_latest_version():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://sieve.services.riotcdn.net/api/v1/products/lol/version-sets/PBE1?q[platform]=windows&q[published]=true") as response:
            if response.status == 200:
                data = await response.json()
                releases = data.get("releases", [])
                if releases:
                    version = releases[0]["release"]["labels"].get("riot:artifact_version_id", {}).get("values", [])[0]
                    # Separar la versión por "+" y tomar los primeros cuatro segmentos
                    version_parts = version.split('+')[0].split('.')
                    formatted_version = '.'.join(version_parts[:4])
                    return formatted_version
                else:
                    print('No se encontraron datos de versiones en la respuesta.')
                    return None
            else:
                print('Error al obtener la lista de versiones: {}'.format(response.status))
                return None

async def download_unit_data():
	result_folder = 'unit_data_pbe'
	pattern_url_list = 'https://raw.communitydragon.org/pbe/game/data/characters/'
	pattern_url_unit_data = 'https://raw.communitydragon.org/pbe/game/data/characters/{}/{}.bin.json'

	url = pattern_url_list

	if not os.path.isdir(result_folder):
		os.mkdir(result_folder)

	print('Requesting: ' + url)
	headers = {
		'User-Agent': "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"
	}

	async with aiohttp.ClientSession() as session:
		async with session.get(url) as response:
			if response.status == 200:
				page = await response.text()
			else:
				print('Failed to fetch the list of champions: {}'.format(response.status))
				return

		async def fetch_and_save(champion):
			url = pattern_url_unit_data.format(champion, champion)
			#print('Requesting: ' + url)

			try:
				async with session.get(url) as response:
					if response.status == 200:
						json = await response.read()
						if champion == "monkeyking":
							champion = "wukong"
						file_path = os.path.join(result_folder, champion)
						async with aio_open(file_path, 'wb') as file:
							await file.write(json)
							print(f'Saved data for {champion}')
					else:
						print('Failed to retrieve data for {}: {}'.format(champion, response.status))
			except Exception as e:
				print('Failed to retrieve data for {}. ({})'.format(champion, str(e)))

		
		tasks = [fetch_and_save(champion) for champion in champions]
		await asyncio.gather(*tasks)

async def generate_unit_data():
	version = await get_latest_version() # Get version
    
    
	data, units, spells, stats, skins = {}, {}, {}, {}, {}
	failed = []
	add_failed_appended = True

	data["version"] = version # Add version
	print(f'Obteniendo la versión: {version}')
    
	infos = ''
	unit_tags = set()
	script_directory = os.path.dirname(os.path.abspath(__file__))
	unit_data_folder = os.path.join(script_directory, "unit_data_pbe")
	for champion in champions:
		abilitycounter = -1
		
		print("Processing: " + champion.strip())  # Use strip() to remove extra spaces
		
		if champion == "monkeyking":
			champion = "wukong"

		props = {}
		with open(os.path.join(unit_data_folder, champion)) as file:
				props = json.loads(file.read())

		champion_data = {}
		
		for key, val in props.items():
			
			# Main nodes objects
			root = await find_key_ending_with_async(props, '/Root')
			spellnamestemp = root['spellNames']  
			champNameToUpper = root.get('mCharacterName', '')
			
			
			if not root:
				print('[Fail] No root found for: ' + champion)
				continue
			
			if len(champion) == 0:
				print('[Fail] No character name found for: ' + champion)
				continue
							

			# Get abilities data
			champion_data["baseStats"]  = {
				"baseHP":  root.get("baseHP", 0),
				"hpPerLevel":  root.get("hpPerLevel", 0),
				"baseStaticHPRegen":  root.get("baseStaticHPRegen", 0),
				"hpRegenPerLevel":  root.get("hpRegenPerLevel", 0),
				"healthBarHeight":  root.get("healthBarHeight", 0),
				"baseDamage":  root.get("baseDamage", 0),
				"baseArmor":  root.get("baseArmor", 0),
				"armorPerLevel":  root.get("armorPerLevel", 0),
				"baseMoveSpeed":    root.get("baseMoveSpeed", 0),
				"baseSpellBlock":      root.get("baseSpellBlock", 0),
				"spellBlockPerLevel":      root.get("spellBlockPerLevel", 0), 
				"attackRange": root.get("attackRange", 0), 
				"attackSpeed": root.get("attackSpeed", 0),
				"attackSpeedRatio":  root.get("attackSpeedRatio", 0),
				"attackSpeedPerLevel":    float(root.get("attackSpeedPerLevel", 0)),
				"passiveSpell":   root.get("passiveSpell",''),
				#"tags": list(tags)

				}        
			champion_data["basicAttack"]  = {
				
				"mAttackTotalTime":  root.get("mAttackTotalTime", 100),
				"mAttackCastTime":  root.get("mAttackCastTime", 100),
				"mAttackProbability":  root.get("mAttackProbability", 100),
			}


		# Get stats
		for ability in ["Q", "W", "E", "R"]:
			abilitycounter += 1
			
			#ability_key = await find_key_by_full_name(props, f'Characters/{champNameToUpper}/Spells/{champNameToUpper}{ability}Ability/{champNameToUpper}{ability}')
			ability_key = await find_key_by_full_name(props, f'Characters/{champNameToUpper}/Spells/{spellnamestemp[abilitycounter]}')
			if ability_key is None:
				# Handle the case when ability_key is None (e.g., print a message)
				print(f'none for {champion} : Characters/{champNameToUpper}/Spells/{spellnamestemp[abilitycounter]}')
				# if champion == "twistedfate":
				# 	print(champNameToUpper)
				# 	current_dict = props  # Initialize current_dict with the input dictionary
				# 	for key, val in current_dict.items():
				# 		if key == f'Characters/{champNameToUpper}/Spells/WildCardsAbility/WildCards':
				# 			print(key)
						# 	return val
						# elif isinstance(val, dict):
						# 	result = await find_key_by_full_name(val, full_name)
						# 	if result is not None:
						# 		return result


					#print(ability_key["mScriptName"])
				continue
			# if champion == "zac":
			#     print(ability_key)
			if champion == "twistedfate" and abilitycounter == 1:
				print(spellnamestemp[1])

			# if "mBuff" not in ability_key:
			# 		#print(f"no spell {ability} for {champion}")
			# 		if add_failed_appended:
			# 			failed.append(f'{champion} : {ability} : no missile name found')
			# 			add_failed_appended = False
			# 		#continue
			
			
			# inside mBuff
			#mBuff = ability_key.get('mBuff', None)
			
			if "mSpell" not in ability_key:
					#print(f"no spell {ability} for {champion}")
					if add_failed_appended:
						failed.append(f'{champion}: no abilities')
						add_failed_appended = False
					#continue
			
			# inside mSpell
			mSpell = ability_key.get('mSpell', None)
			mSpellTags = mSpell.get('mSpellTags', None)
			mEffectAmount = mSpell.get('mEffectAmount', None)
			mChannelDuration = mSpell.get('mChannelDuration', None)
			mCastRangeGrowthMax = mSpell.get('mCastRangeGrowthMax', None)
			castRadius = mSpell.get('castRadius', None)
			mCastRangeGrowthDuration = mSpell.get('mCastRangeGrowthDuration', None)
			cooldownTime = mSpell.get('cooldownTime', None)
			castRange = mSpell.get('castRange', None)
			mTargetingTypeData = mSpell.get('mTargetingTypeData', None)
			mMissileSpec = mSpell.get('mMissileSpec', None)
			if "mDataValues" in mSpell:
				mDataValues = mSpell.get('mDataValues', None)

			if "mSpellCalculations" in mSpell:
				mSpellCalculations = mSpell.get('mSpellCalculations', None)
				DamageTooltip = mSpellCalculations.get('DamageTooltip', None)
				MaxDamageTooltip = mSpellCalculations.get('MaxDamageTooltip', None)
				HealthCostTooltip = mSpellCalculations.get('HealthCostTooltip', None)
				MaxStun = mSpellCalculations.get('MaxStun', None)

			if "mClientData" in mSpell:
				mClientData = mSpell.get('mClientData', None)
				mTooltipData = mClientData.get('mTooltipData', None)
				mLists = mTooltipData.get('mLists', None)
				if "mLists" in mTooltipData:
					LevelUp = mLists.get('LevelUp', None)
			
			stunDuration = 0
			targetingType = ''
			
			if targetingType == '':
				if "mTargetingTypeData" in mSpell:
					tt_first = mTargetingTypeData['__type']
					targetingType = tt_first
				#tt_two = mTargetingTypeData['__type']

				# if tt_first is not None:
				#     targetingType = tt_first
				#if tt_two is not None:
				#print(mSpell.get("mMissileWidth", ''))
				#targetingType = ''



			for key, value in mSpellCalculations.items():
				if key == "MaxStun":
					stunDuration = value['mFormulaParts'][0]['mPart1']['mEffectIndex'] / 10
			
			spell_tags = set()
			if mSpellTags is not None:
				spell_tags = [tag.replace("Trait_", '').replace("PositiveEffect_", '') for tag in mSpellTags]
			
			#print(mCastRangeGrowthMax)
			damageList= []
			#if champion == "sett":
			for key, value in mSpell.items():
				if key == "mDataValues":
					cvlist = list(value)
					for item in cvlist:
						damageList.append(item)
						#print("Item Key:", item)
							
			#for key, value in mEffectAmount:
				#print(f'{key} : {value}')
			
			#custum castRange for some champions
			#mCastRangeGrowthMaxCustom = []
			# if champion == 'Zac':
			#     if mCastRangeGrowthMax is not None:
			#         #mCastRangeGrowthMaxCustom.insert(0, mCastRangeGrowthMax[0])
			#         #mCastRangeGrowthMaxCustom.extend(mCastRangeGrowthMax[1:])

			#         castRange = mSpell.get('castRange', None)


			
			champion_data[ability]  = {
			"missileName":   ability_key["mScriptName"],
			"mCoefficient":  mSpell.get("mCoefficient", 0),
			"mCoefficient2":  mSpell.get("mCoefficient2", 0),
			"mAnimationName":  mSpell.get("mAnimationName", ''),
			"mCantCancelWhileWindingUp":  bool(mSpell.get("mCantCancelWhileWindingUp", 0)),
			"alwaysSnapFacing":  bool(mSpell.get("alwaysSnapFacing", 0)),
			"mLineWidth":  mSpell.get("mLineWidth", 0),
			"missileSpeed":  mSpell.get("missileSpeed", 0),
			"totalLevels":  LevelUp.get("levelCount", 0),
			"mTargetingType":  targetingType,
			"stunDuration":  stunDuration,

			
			
			"mCastTime":  mSpell.get("mCastTime", 0),

			"castRange":   castRange,
			"castRange":   castRange,
			"cooldownTime":   cooldownTime,
			"damages":   damageList,
			"channelingDuration":   mChannelDuration,
			"mCastRangeGrowthMax":   mCastRangeGrowthMax,
			"mCastRangeGrowthDuration":   mCastRangeGrowthDuration,
			"castRadius":   castRadius,
			"mSpellCalculations":   mSpellCalculations,

			"tags": list(spell_tags)
			}

				



			# # Get basic attack info
			# missile_speed = 0
			# windup = 0
			# basic_attack = await find_key_ending_with_async(props, champion + "BasicAttack")
			# if basic_attack != None:
			#     spell = basic_attack.get('mSpell', None)
			#     if spell:
			#         missile_speed = spell.get("missileSpeed", 0)
			# if 'basicAttack' in root:
			#     basic_attack = root['basicAttack']
			#     if 'mAttackTotalTime' in basic_attack and 'mAttackCastTime' in basic_attack:
			#         windup = basic_attack['mAttackCastTime']/basic_attack['mAttackTotalTime']
			#     else:
			#         windup = 0.3 + basic_attack.get('mAttackDelayCastOffsetPercent', 0)

			# tags = set(['Unit_' + x.strip().replace('=', '_') for x in root.get("unitTagsString", "").split('|')])
			# sdsdsqdsq  = {
			#     "name":             champion,
			#     "healthBarHeight":  root.get("healthBarHeight", 100),
			#     "baseMoveSpeed":    root.get("baseMoveSpeed", 0),
			#     "attackRange":      root.get("attackRange", 0),
			#     "attackSpeed":      root.get("attackSpeed", 0), 
			#     "attackSpeedRatio": root.get("attackSpeedRatio", 0), 
			#     "acquisitionRange": root.get("acquisitionRange", 0),
			#     "selectionRadius":  root.get("selectionRadius", 0),
			#     "pathingRadius":    root.get("pathfindingCollisionRadius", 0),
			#     "gameplayRadius":   root.get("overrideGameplayCollisionRadius", 65.0),
			#     "basicAtkMissileSpeed": missile_speed,
			#     "basicAtkWindup": windup,
			#     "tags": list(tags)
			# }
			

			 

		# # Read spells
		for key, val in props.items():
			if "mSpell" not in val:
				continue
			
			s = val["mSpell"]
			if s:
				icon_name = os.path.basename(s.get("mImgIconName", [""])[0]).replace(".dds", "")
				spell = {
					"name":               os.path.basename(key),
					"icon":               f'https://raw.communitydragon.org/pbe/game/assets/characters/{champion}/hud/icons2d/{icon_name.lower()}.png',
					"flags":              s.get("mAffectsTypeFlags", 0),
					"delay":              s.get("mCastTime", 0.5 + 0.5*s.get("delayCastOffsetPercent", 0)),
					"castRange":          s.get("castRangeDisplayOverride", s.get("castRange", [s.get("castConeDistance", 0)]))[0],
					"castRadius":         s.get("castRadiusSecondary", s.get("castRadius", [0]))[0],
					"width":              s.get("mLineWidth", 0),
					"height":             0,
					"speed":              s.get("missileSpeed", 0),
					"travelTime":         0,
					"projectDestination": False
				}
				
				if 'mCastRangeGrowthMax' in s:
					spell['castRange'] = s['mCastRangeGrowthMax'][4]
				
				missile = s.get("mMissileSpec", None)
				if missile:
					movcomp = missile.get("movementComponent", None)
					if movcomp:
						if spell["speed"] == 0:
							spell["speed"] =          movcomp.get("mSpeed", 0)
						spell["height"] =             movcomp.get("mOffsetInitialTargetHeight", 100)
						spell["projectDestination"] = movcomp.get("mProjectTargetToCastRange", False)
						spell["travelTime"] =         movcomp.get("mTravelTime", 0)
						
				spells[spell["name"]] = spell
		
		data["allSpellsFromChampions"] = spells 
		data[champion] = champion_data 

	print(f'Found {len(champions)} units and {len(spells)} spells')
	print('Error retrieving following units:')
	pprint(failed)
	async with aio_open("championDataPBE.json", 'w') as f:
		await f.write(json.dumps(data, indent=4))

	# async with aio_open("SpellData.json", 'w') as f:
	#     await f.write(json.dumps(list(spells.values()), indent=4))

async def main():
    await download_unit_data()  # Descarga los datos primero
    await generate_unit_data()  # Genera los datos después
    
if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())