#!/usr/bin/env python3
"""
PSN Username Database — generator
Builds a self-contained index.html with an embedded, scored username database.

Run:  python3 build.py
Output: index.html (open in any browser, no server needed)

Availability is SIMULATED (deterministic demo data). Sony exposes no public
endpoint to check PSN Online ID availability; a real checker can be wired in later.
"""
import json, sys, datetime, re, os, base64

# ---------------------------------------------------------------- word lists
# 3-letter dictionary words
W3 = """ace act add age ago aid aim air ale amp ant ape apt arc ark arm art ash ask asp ate awe axe
bad bag ban bar bat bay bed bee bet bid bin bit boa bog bow box boy bud bug bun bus but buy
cab can cap car cat cob cod cog con cop cow coy cry cue cup cut
dab dam day den dew did die dig dim din dip doe dog don dot dry dub dud due dug duo dye
ear eat ebb eel egg ego elm elk elf end era eve ewe eye
fad fan far fat fax fay fee fen few fie fig fin fir fit fix flu fly fob foe fog fop fox fry fun fur
gab gag gal gap gas gem get gig gin gnu gob god goo got gum gun gut guy gym
had hag ham has hat hay hem hen her hew hex hey hid him hip hit hoe hog hop hot how hub hue hug hum hut
ice icy ill imp ink inn ion ire ivy
jab jag jam jar jaw jay jet jig job jog jot joy jug jut
keg ken key kid kin kit kip koi
lab lac lad lag lam lap law lax lay lea leg lei let lid lie lip lit log loo lot low lug lye
mad man map mar mat maw may men mew mid mil mix mob mod mom mop mow mud mug mum
nab nag nap nay net new nib nil nip nit nod nor not now nub nun nut
oaf oak oar oat ode odd off oil old one orb ore our out owl own
pad pal pan par pat paw pay pea peg pen pep per pet pew pie pig pin pip pit ply pod pop pot pox pry pub pug pun pup put
qua rad rag ram ran rap rat raw ray red rev rex rib rid rig rim rip rob rod roe rot row rub rue rug rum run rut rye
sac sad sag sap sat saw say sea see set sew shy sib sic sin sip sir sis sit six ski sky sly sob sod son sop sot sow soy spa spy sty sub sue sum sun sup
tab tad tag tan tap tar tau tax tea ten the thy tic tie til tin tip toe tom ton too top tor tot tow toy try tub tug tun tux two
ufo ump urn use
van vat vet vex via vie vim vow vox
wad wag wan war was wax way web wed wee wen wet who why wig win wit woe wok won woo wow wry
yak yam yap yaw yea yen yep yes yet yew yin yon you
zag zap zed zee zen zig zip zit zoo"""

# 4-letter dictionary words
W4 = """able ache acid acme acre aged airy aloe alto amen amok apex arch area army atom aunt aura auto away axis axle
baby back bail bait bake bald bale ball balm band bane bang bank bard bare bark barn base bash bask bath bead beak beam bean bear beat beau beck been beer bell belt bend bent berg best beta bike bile bill bind bird bite blab blip blob bloc blog blot blow blue blur boar boat bode body boil bold bolt bomb bond bone bong book boom boon boot bore born boss both bout bowl brad brag bran brat bray bred brew brig brim brow buck buff bulb bulk bull bump bunk buoy burn bury bush bust busy buzz byte
cafe cage cake calf call calm came camp cane cape card care carp cart case cash cast cave cede cell cent chap char chat chef chew chic chin chip chop chow chug cite city clad clam clan clap claw clay clew clip clod clog clot club clue coal coat coax coca coco code coil coin coke cola cold colt coma comb come cone conk cook cool coop coot cope copy cord core cork corn cost cove cosy crab cram crew crib crop crow crux cube cuff cult curb cure curl cusp cute cyan cyst
dame damn dank dare dark darn dart dash data date dawn daze dead deaf deal dean dear deck deed deem deep deer deft defy deli dell demo dent deny desk dial dice died diet dike dill dime dine ding dink dire dirt disc dish disk diva dive dock doer dole doll dome done doom door dope dork dorm dose dote dove down doze drab drag draw dray drew drip drop drum dual duck duct dude duel duet duke dull duly dumb dump dune dunk dusk dust duty dyer
each earl earn ease east easy eats echo eddy edge edgy edit else emit envy eons epic ergo etch even ever evil exam exec exit expo eyed eyes
face fact fade fail fair fake fall fame fang fare farm fast fate fawn fear feat feed feel feet fell felt fend fern fete feud fiat fief fife file fill film find fine fink fire firm fish fist five fizz flag flak flan flap flat flaw flay flea fled flee flew flex flip flit floe flog flop flow flue foal foam foil fold folk fond font food fool foot ford fore fork form fort foul four fowl frat fray free fret frog from fuel full fume fund funk fuse fuss fuzz
gain gait gale gall game gape garb gash gate gave gaze gear geek geld gems gene gent germ gift gild gill gilt girl gist give glad glam glee glen glib glow glue glum glut gnaw gnat goad goal goat goes gold golf gone gong good goon gore gory gown grab grad gram gray grew grid grim grin grit grog grow grub gulf gull gulp gunk guru gush gust guts guys gyro
hack hail hair hale half hall halo halt hand hang hank hard hare hark harm harp hash hast hate haul have hawk hays haze head heal heap hear heat heed heel heft heir held hell helm help hems hens herb herd here hero hers hewn hick hide high hike hill hilt hind hint hips hire hiss hive hobo hock hoes hogs hold hole holy home hone honk hood hoof hook hoop hoot hope hops horn hose host hour howl hubs hues huff huge hulk hull hums hung hunk hunt hurl hurt hush husk hype hypo
ibex iced ices icon idea idle idol ilks inch inky inns into ions iota iris iron isle itch item
jade jags jail jams jars jaws jazz jean jeep jeer jest jets jibe jilt jinx jobs joey jogs join joke jolt josh jots jowl joys judo jugs juke jump junk jury just jute juts
kale keel keen keep kept khan kick kids kiln kilt kind king kink kips kiss kite kith kiwi knee knew knit knob knot koan kudo
lace lack lacy lade lady laid lain lair lake lamb lame lamp land lane lank lard lark lash lass last late laud lava lawn laws lays laze lazy lead leaf leak lean leap leek leer lees left leis lend lens lent less lest levy lewd liar lice lick lido lids lied lien lies lieu life lift like lily limb lime limn limo limp line ling link lino lint lion lips lisp list lite live load loaf loam loan lobe loci lock lode loft logo logs loin loll lone long look loom loon loop loot lope lord lore lorn lose loss lost lots loud lout love lows luau lube luck lugs lull lump luna lung lunk lure lurk lush lust lute luxe lynx lyre
mace made mage magi maid mail maim main make male mall malt mama mane many maps mare mark mars mart mash mask mass mast mate math mats maul maze mead meal mean meat meek meet mega melt memo mend menu meow mere mesh mess meta mete mewl mica mice midi mike mild mile milk mill milo mime mind mine mini mink mint minx mire miry miss mist mite mitt moan moat mobs mock mode mods mold mole moll molt monk mono mood moon moor moot mope mops more moss most mote moth move mows much muck muff mugs mule mull murk muse mush musk must mute mutt myth
nabs nada nail name nape naps nasa navy nays near neat neck need neon nerd nest nets news newt next nibs nice nick nigh nine nips nods noel noir none noon nope norm nose nosh nosy note noun nova nubs nude nuke null numb nuns nuts
oaks oars oath oats obey obit odds odor ogle ogre oily okay olde omen omit once ones only onto onus onyx oops ooze opal open opus oral orbs oryx oust oval oven over ovum owed owes owls owns
pace pack pact pads page paid pail pain pair pale pall palm pals pane pang pans pant papa pare park part pass past pate path pats pave pawn paws pays peak peal pear peas peat peck peek peel peep peer pegs pelt pens peon perk pert peso pest pets pews phew pica pick pics pied pier pies pike pile pill pimp pine ping pink pins pint pipe pita pith pits pity plan play plea plod plop plot ploy plum plus pods poet poke poky pole poll polo pond pong pony pool poop poor pope pore pork porn port pose posh post posy pots pout pram pray prep prey prig prim prod prof prom prop pros prow pubs puck puff pugs puke pull pulp puma pump punk puns punt puny pups pure purr push puts putt pyre
quad quay quid quip quit quiz
race rack racy rads raft raga rage rags raid rail rain rake ramp rang rank rant rape raps rapt rare rash rasp rate rats rave rays raze razz read real ream reap rear redo reed reef reek reel refs rein rely rend rent rest rice rich ride rids rife riff rift rigs rile rill rime rims rind ring rink riot ripe rips rise risk rite road roam roan roar robe robs rock rode rods roes roil role roll romp roof rook room root rope rose rosy rote rots rout rove rows rubs ruby rude rues ruff rugs ruin rule rump rums rune rung runs runt ruse rush rust ruts ryes
sack safe saga sage sago said sail sake sale salt same sand sane sang sank sari sate save saws says scab scam scan scar scat scow scud scum seal seam sear seas seat sect seed seek seem seen seep seer self sell semi send sent serf sets sewn shad shah sham shay shea shed shin ship shiv shod shoe shoo shop shot show shun shut sibs sick side sift sigh sign sike silk sill silo silt sine sing sink sins sips sire sirs site sits size skew skid skim skin skip skit slab slam slap slat slaw slay sled slew slid slim slip slit slob sloe slog slop slot slow slug slum slur smog smug snag snap snip snit snob snot snow snub snug soak soap soar sobs sock soda sofa soft soil sold sole solo soma some song sons soot sops sore sort soul soup sour sown soya spar spat spay sped spew spin spit spot spry spud spun spur stab stag star stay stem step stew stir stop stow stub stud stun subs such suck suds sued sues suet suit sulk sump sums sung sunk suns surd sure surf swab swag swam swan swap swat sway swim swum
tabs tack taco tact tads tags tail take talc tale talk tall tame tamp tang tank tans tape taps tare tarn taro tarp tars tart task taut taxi teak teal team tear teas tech teed teem teen tees tell temp tend tens tent term tern test text than that thaw thee then they thin this thud thug thus tick tide tidy tied tier ties tiff tile till tilt time tine ting tins tint tiny tips tire toad toes tofu toil toke told toll tomb tome tone tong tons tony took tool toon toot topi tops tore torn tors toss tote tots tout town tows toys tram trap tray tree trek trey trig trim trio trip trod trot trow troy true tsar tubs tuck tuft tugs tuna tune turd turf turn tush tusk tutu twig twin twit twos tyke type typo tyre tzar
udon ugly ulna undo unit upon urea urge urns used user uses
vain vale vamp vane vans vary vase vast vats veal veep veer veil vein veld vend vent verb very vest veto vets vial vibe vice vids vied vies vile vine vino viny viol visa vise vita viva void vole volt vote vows
wade wads waft wage wags waif wail wait wake walk wall wand wane wans want ward ware warm warn warp wars wart wary wash wasp watt wave wavy waxy ways weak weal wean wear webs weds weed week ween weep weft weir weld well welt wend went wept were west wets wham what whee when whet whew whey whig whim whip whir whit whiz whoa whom wick wide wife wild wile will wilt wily wimp wind wine wing wink wino wins winy wipe wire wiry wise wish wisp wist with wits wive woad woes woke woks wold wolf womb wont wood woof wool word wore work worm worn wort wove wows wrap wren writ
xmas xray
yaks yams yang yank yaps yard yarn yawl yawn yeah year yeas yell yelp yens yeps yeti yews yoga yogi yoke yolk yore your yowl yuck yule
zags zany zaps zeal zebu zeds zees zein zero zest zeta zigs zinc zing zins zips ziti zits zone zoom"""

# 5-9 letter dictionary words
W5_9 = """about above abuse actor acute admit adopt adore after again agent agile agony agree ahead alarm album alert alias alibi alien align alike alive alley allow alloy aloft alone aloud alpha altar alter amber amend amiss among ample amuse angel anger angle angry ankle annex annoy anvil apart apple apply apron area arena argue arise armor aroma arose array arrow ashen aside asset atoll attic audio audit avoid await awake award aware awful axiom azure
bacon badge badly bagel baker balmy banal banjo baron basic basil basin basis baton bayou beach beard beast began begin begun being below bench berry birth black blade blame blank blast blaze bleak bleed blend bless blind blink bliss blitz bloat block bloke blond blood bloom blown blues bluff blunt blurt blush board boast bonus boost booth bound brain brand brash brass brave bravo brawl bread break breed bribe brick bride brief bring brink brisk broad broke brood brook broom broth brown brush brute budge buggy build built bunch bunny burst buyer bylaw
cabin cable cache camel canal candy canoe caper cargo carol carry carve caste catch cater cause cedar chain chair chalk champ chant chaos charm chart chase cheap cheat check cheek cheer chess chest chief child chill chime china choir choke chord chore chose chunk churn cider cigar circa civic civil claim clamp clash clasp class clean clear clerk click cliff climb cling cloak clock close cloth cloud clout clown coach coast cobra colon color comet comic comma coral corny cough could count court cover coven crack craft cramp crane crank crash crate crave crawl craze crazy creak cream credo creed creek creep crepe crest crime crimp crisp croak crock crook croon cross crowd crown crude cruel crumb crush crust crypt cubic curve cycle
daily dairy daisy dance datum dealt death debit debug debut decay decor decoy defer deity delay delta delve demon denim dense depot depth derby deter devil diary dicey digit dimly diner dingy diode dirge dirty disco ditch ditto ditty dizzy dodge dogma doing dolly donor donut dozen draft drain drake drama drank drape drawl drawn dread dream dress dried drift drill drink drive droll drone drool droop drove drown druid drunk dryer ducat duchy dwarf dwell dwelt dying
eager eagle early earth easel eaten eater ebony edict edify eight eject elate elbow elder elect elegy elite elope elude email embed ember emcee empty enact ended enjoy ensue enter entry envoy epoch equal equip erase erode error erupt essay ether ethic ethos evade event every exact exalt excel exert exile exist expel extra exult
fable facet faint fairy faith false fancy farce fatal fatty fault fauna favor feast fiber field fiend fiery fifth fifty fight filly final finch finer first fitly fixed fjord flair flake flame flank flare flash flask fleet flesh flick fling flint flirt float flock flood floor flora floss flour flute foamy focal focus foggy folio force forge forth forty forum frame frank fraud fresh friar fried front frost froth frown froze fruit fudge fully funny furor furry fussy
gable gamma gauge gaunt gauze gavel gawky gecko genie genre ghost ghoul giant giddy gland glare glass glaze gleam glean glide glint gloat globe gloom glory gloss glove gnome going golem goofy goose gorge gouge gourd grace grade grain grand grant grape graph grasp grass grate grave gravy graze great greed green greet grief grill grimy grind gripe groan groin groom grope gross group grove growl grown grunt guard guess guest guide guild guilt guise gulch gully gusty gypsy
habit hairy handy happy hardy harem harsh haste hasty hatch haunt haven havoc hazel heart heavy hedge hefty heist helix hello hence heron hinge hippo hobby hoist holly honey honor horse hotel hound house hover human humid humor hunch hurry hutch hydro hyena hyper
icing ideal idiom idiot igloo image imbue impel imply inane inbox incur index inept inert infer inlet inner input inset inter intro irony issue itchy ivory
jazzy jelly jerky jewel jiffy joint joker jolly joust judge juice juicy jumpy juror
kappa karma kayak kebab kiosk kitty knack knead kneel knife knock known koala kudos krill
label labor laden ladle lager lance latch later lathe laugh layer leach leafy learn lease leash least leave ledge legal lemon lemur level lever light lilac limbo limit linen liner liver llama lobby local lodge lofty logic login loyal lucid lucky lunar lunch lunge lurch lurid lyric
macaw macro madam magic magma maize major maker mango manor maple march marry match maybe mayor mecca medal media melee melon mercy merge merit merry metal meter metro micro midst might mimic mince minor minus mirth miser modal model modem mogul moist molar money month moral motel motif motor motto mound mount mourn mouse mouth movie mulch mural mushy music musty myrrh myth
nacho naive naked nanny nasal nasty natal naval navel needy nerve never newly nexus nicer niche niece night ninja noble noise nomad north notch novel nudge nurse nylon nymph
oasis occur ocean octet offer often older olive omega onion onset opera opine optic orbit order organ other otter ounce outer ovary overt owner oxide ozone
paddy pagan paint panel panic pansy paper party pasta paste patch patio pause peace peach pearl pecan pedal penny perch peril petty phase phone photo piano piece pilot pinch piper pivot pixel pizza place plaid plain plane plank plant plate plaza plead pluck plumb plume plump plush poem point polar poppy porch poser posit posse pouch pound power prank prawn preen press price prick pride prime print prior prism prize probe prone proof prose proud prove prowl proxy prune psalm pudgy pulse punch pupil puppy purge purse pushy putty pygmy
quail quake qualm quark quart quash queen quell query quest queue quick quiet quill quilt quirk quite quota quote
rabbi racer radar radio rainy raise rally ranch range rapid ratio ratty raven razor reach react ready realm recap rebel refer reign relax relay relic remit renal renew repay repel reply reset resin retro revel revue rhino rhyme rider ridge rifle right rigid rinse risen river rivet roach roast robin robot rocky rodeo rogue roman roomy roost rotor rouge rough round rouse route rover rowdy royal rugby ruler rumba rumor rupee rural rusty
saber sadly safer saint salad salvo sandy sassy satin sauce sauna savor savvy scale scalp scamp scant scare scarf scene scent scone scoop scope score scout scowl scrap screw scrub sedan seize sense sepia serif serum serve setup seven sever shade shady shaft shake shaky shale shall shame shank shape shard share shark sharp shave sheaf shear sheen sheep sheet shelf shell shift shine shiny shirt shock shoot shore short shout shove shown shred shrew shrub shrug siege sigh sigma sight silky silly since singe sinus siren sissy sitar sixth sixty skate skier skill skimp skirt skulk skull skunk slain slang slant slate slave sleek sleep sleet slice slick slide slime slimy sling slink slope sloth slump smack small smart smash smear smell smile smirk smite smith smoke smoky snack snail snake snare snarl sneak sneer snide sniff snipe snore snort snout snowy soapy sober soggy solar solid solve sonar sonic sooty sorry sound south space spade spank spare spark spasm spawn speak spear speed spell spelt spend spice spicy spike spill spine spire spite split spoil spoke spoof spook spool spoon spore sport spout spray spree sprig squad squid stack stage stain stair stake stalk stall stamp stare stark start stash state stave stead steak steal steam steed steel steep steer stein stern stick stiff still sting stink stint stock stoic stoke stole stomp stone stony stool stoop store storm story stout stove strap straw stray strip strum stuck study stuff stump stung stunt style suave suede sugar suite sulky sunny super surge sushi swamp swarm sweat sweep sweet swell swept swift swine swing swirl swish swoon swoop sword sworn syrup
table taboo tacit taffy taken taker talon tango tangy taper tapir tardy tarot taste tasty taunt tawny teach tease teary tempo tenet tenor tenth terse thank theft their theme there theta thigh thing think thorn those three threw throw thumb tiara tidal tiger tight timer timid tinge tipsy titan title toast today token tonic tooth topic torch torus total totem touch tough tower toxic toxin trace track tract trade trail train trait tramp trap tread treat trend triad trial tribe trick tried trill troll troop trout truce truck truly trunk trust truth tudor tulip tuner tunic turbo tutor twang tweak tweet twice twine twirl twist
umbra uncle under undue unfit unify union unite unity until upset urban urine usage usher usual utter
vague valid valor value valve vapor vault vegan venom venue verge verse video vigor villa vinyl viola viper viral virus visit vista vital vivid vocal vodka vogue voice vomit voter vouch vowel
wagon waist waltz waste watch water weary weave wedge weigh weird whale wharf wheat wheel where while whine whirl whisk white whole wield wince winch witch witty woven wrath wreck wrist write wrong wrote
xenia xenon xerox
yahoo yacht yearn yeast yield young youth yummy
zebra zesty zilch zippy
anchor breeze castle dragon ember falcon fjord glacier harbor island jungle kelp lagoon meadow nebula obsidian panther quartz raptor summit timber utopia valley willow
gamble hammer kettle ladder magnet needle orange pencil rocket saddle trumpet velvet wizard yellow zigzag banner butter copper dinner effort forest gossip heaven jacket karma laptop marble napkin origin pocket ribbon silver tunnel unicorn victory window crystal dynamo elegant freedom gravity harmony iceberg justice knight legend memory neutral oceanic phantom rainbow shadow thunder unique viking warrior
sniper hunter slayer ranger wizard sorcerer paladin rogue druid monk bard cleric warlock knight samurai ninja viking pirate bandit outlaw sheriff cowboy knight? assassin hacker gamer streamer? tryhard camper lobby clutch frag respawn levelup powerup hitpoint mana exp lootbox raidboss endgame newgame gameover joystick gamepad arcade console pixel retro voxel sprite shader texture polygon vector sprite bitmap codec server client modem router signal cipher crypto token wallet avatar profile ranked ladder season battle arena stadium victory defeat triumph legacy destiny fortune glory honor prestige renown infamous legendary mythical immortal eternal divine celestial radiant luminous blazing frozen burning raging prime apex ultra hyper mega giga turbo nitro omega alpha sigma delta gamma theta lambda"""

NAMES = """al alex alfa? alice allen alma amos amy andy andre ann anna annie archie arlo arnold art arthur ash asher ava axel barnaby? basil baxter bea becky ben benny bert bess? beth bill billy bobby bonnie boris brad brenda brett bruce bryan bud byron callum carl carla carlos carmen carol carrie casey cecil celia chad charlie chelsea cheryl chester chris cindy clara clare claude cliff clint clive clyde cody colin colin connie cora corey craig curtis cyril dale damon dan dana daniel danny daphne darcy daria darla darren dave dawn dean debra denise dennis derek diana diane dirk dolly dominic don donald donna dora doris doug duane? duke duncan dwight dylan earl ed eddie edgar edith edmund edna edwin eileen elaine elena eli elias ellen ellis elmer elsa elsie emily emma eric erika erin ernest esther ethan eugene eva evan eve evelyn ezra faith fannie felix fern fiona flora floyd frances francis frank frankie fred freda gabriel gail garrett garry garth gary gavin gail gene geoff george gerald gilbert gina giselle glenn gloria gordon grace grant greg greta guy gwen hank hannah harold harriet harry harvey hazel heath hector heidi helen henry herbert herman hilary hollis homer hope horace howard hubert hugh ian ida ignatius? imogen ingrid ira irene iris irma irvin irving isaac isabel ivan ivy jack jacob jade james jamie jane janet janice jared jasmine jason jay jean jeff jenny jeremy jerome jess jill jim joan joanna joel john jonas jordan jorge jose josephine josh joyce juan judith judy jules julia julie julius june justin kai karen karl kate katherine katie kay keith kelly kelvin ken kendra kenneth kevin kim kirk kirsten kurt kyle lamar lance lara larry laura lauren laurie leah lee lena leo leon leonard leroy leslie lester levi lewis liam lillian lily linda lindsay lionel lisa lloyd logan lois lola lonnie loren lori lou louie louis louise lucas lucy luis luke luther lydia lyle lynn mabel mack mara marc marcella? marcus margaret maria marian marie marilyn mario marion marjorie mark marlene marsh? marshall martha martin marvin mary mathew matt maureen maurice max maxine may maya megan melanie melvin meredith merle michael michel michelle mildred miles milton mimi mindy miriam mitch mitchell molly mona monica morris morton muriel myra myrtle nancy naomi natalie natasha nathan nathaniel neal neil nicholas nick nicolas nina noah noel nolan nora norman oliver olivia ollie omar oscar owen pablo pam pamela patricia patrick paul paula pearl peggy penny percy peter philip phillip phoebe phyllis preston priscilla piers quentin quincy quinn rachel ralph randall randy raquel ray raymond rebecca regina reginald renee rex rhonda richard rick rita robert roberta roberto robin rodney roger roland ron ronald rosa rosie ross roxanne roy ruben ruby rudolph rudy russell ruth ryan sadie sally salvador sam samantha samuel sandy sanford? sara sarah scott sean sebastian serena seth seymour shane shannon sharon sharon sheila shelley shelly sherman shirley sidney silas simon sonia sophie spencer stacy stanley stella stephen stephanie steve stewart stuart sue susan sylvester sylvia tamara tanya tara terence teresa terrence terri thelma theo theodore theresa thomas tiffany tim timothy tina tobias? toby todd tom tommy tony tonya tracey tracy travis trevor tricia troy tyler valerie vanessa vera verna vernon veronica vic victor victoria vincent viola violet virgil virginia vivian wade wallace wally walter wanda warren wayne wendell wendy wesley whitney wilbur willard william willie willis wilma winifred winston wyatt xavier yolanda yvette yvonne zach zachary zack zane zara zelda zoe"""

ACRONYMS = """fbi cia nsa nasa sas kgb mi5 mi6 un eu nba nfl fifa ufc wwe psn ps2 ps3 ps4 ps5 sony mtv cnn bbc abc nbc hbo espn vip ceo cfo cto coo diy aka lol lmao rofl omg wtf smh brb tbh ngl idk imo iirc gg wp ez op afk irl tba tbd eta atm bae fam lit rizz goat npc pvp pve rpg fps rts mmo moba tcg ccg hud dps dmg aggro meta bmw amg jdm dtm gt3 gt4 wrc gtr x-ray ascii malware spyware trojan adware bitcoin ethereum blockchain defi nft dao web3 opensource"""

OG_WORDS = """ace bad bit boss cat ceo cry dad day dog dry duo ego elk era eve eye fan fbi fly fox gap gas gem gg gig gnu gob god goo gym hex hip hop hub hug ice icy imp ink ion ivy jab jag jam jar jaw jay jet jig job joy jug keg key kid kin kit koi lab leg lit loo lot low mad map max mom mop mud mug nab nap nba net new nil nit nod now nub nun nut oaf oak oat ode oil old orb ore owl own pad pal pan pat paw pay pea peg pen pep pet pew pie pig pin pip pit pod pop pot pro pry pub pug pup put rad rag ram rap rat raw ray red rev rex rid rig rim rip rob rod rot row rub rue rug rum run rut rye sad sag sat saw say sea see set sew shy sip sir six ski sky sly sob son sow spy sub sue sum sun sup tab tag tap tar tax tea ten the tie til tin tip toe ton too top tot toy try tub tug two ufo ump urn use van vat vet vex via vie vim vow war was wax way web wet who wig win wit woe wok won wow yak yap yen yes yet yin you zap zen zig zip zit zoo
bomb cash clan doom epic fire flux gang goat grim hero high hype icon idol joke king kiss liar lion loot luck meta myth nerd noob omen play pwn raid rank real rich riot rock rush sage shot sick trap trip true vibe void wave wild wing wish wolf zero zone alpha apex ash atom chief elite prime ultra edge core fade flux nexus onyx storm nova echo"""

WORDS = set((W3 + " " + W4 + " " + W5_9 + " alpha apex omega sigma delta").split())
WORD_SET = {w.replace('?', '').strip() for w in WORDS if w.replace('?', '').strip().isalpha()}
NAME_SET = {w.replace('?', '') for w in NAMES.split() if w.replace('?', '').isalpha()}
ACR_SET = {w.replace('?', '').replace('-', '') for w in ACRONYMS.split() if w.replace('?', '').replace('-', '').isalnum()}
OG_SET = {w for w in OG_WORDS.split() if w}

# word-form facets: FINAL = whole word / name as-is (lonely, ace, maria)
# SEMI = stem + prefix/suffix form (loneliness, replay, aces, gamer…)
# note: underived base forms ONLY — derived forms (loneliness, stormy) are SEMI by design
EXTRA_WORDS = set("""lonely alone solitude empty hollow quiet silence spirit ghost mist fog frost dream
sleep shadow reverie twilight midnight dusk dawn echo void ember rain snow wind storm curse bless haunt
prequel preview prelude outbreak outlaw outcast outsider underdog undertow misfit nonzero antisocial
heroine villain wanderer drifter pilgrim oracle prophet phantom specter wraith golem leviathan behemoth""".split())
WORD_SET |= {w for w in EXTRA_WORDS if w.isalpha()}
WORD_BASE = WORD_SET | NAME_SET

AFFIX_PRE = ('un','re','pre','dis','mis','over','under','out','non','super','ultra','anti','auto',
             'neo','hyper','multi','semi','pseudo','omni','ex')
AFFIX_SUF = ('s','es','ing','ed','er','ers','est','ness','tion','ism','ist','ful','less','able',
             'ible','ous','ive','ic','al','ology','ify','ies','ier','hood','ship','dom','ish','y')

def is_semi(s):
    """stem-with-affix check (strict: whole stem must be a dictionary word or name)"""
    if not s.isalpha() or len(s) < 4:
        return False
    for p in AFFIX_PRE:
        if s.startswith(p) and len(s) - len(p) >= 3 and s[len(p):] in WORD_BASE:
            return True
    for af in AFFIX_SUF:
        if not s.endswith(af) or len(s) - len(af) < 3:
            continue
        stem = s[:-len(af)]
        if stem in WORD_BASE:                                   # game+s, storm+y, lonely+ness
            return True
        if af[:1] in ('i', 'e') and (stem + 'e') in WORD_BASE:  # make+ing, share+er
            return True
        if af[:1] in ('i', 'e') and len(stem) >= 2 and stem[-1] == stem[-2] and stem[:-1] in WORD_BASE:
            return True                                         # run+ing, sad+est (doubled consonant)
        if stem.endswith('i') and len(stem) >= 2 and (stem[:-1] + 'y') in WORD_BASE:
            return True                                         # y->i spelling: loneli+ness -> lonely, happi+est -> happy
    return False

# ---------------------------------------------------------------- language model
VOWELS = set('aeiou')
RARE_LETTERS = set('qzxj')
OK3 = {'str','spr','sch','scr','spl','shr','thr','chr','tch','nch','ght','ght','xts','ngs','cks','sts','sks','rks','nds','nts','lts','lps','rms','rns','mps','pth','nth','lth','dge','nge','nce','nse'}
QWERTY_ROWS = ['qwertyuiop', 'asdfghjkl', 'zxcvbnm']
ALPHA = 'abcdefghijklmnopqrstuvwxyz'

def has_run(s, n=3):
    for src in (ALPHA, ALPHA[::-1], *QWERTY_ROWS):
        for i in range(len(src) - n + 1):
            if src[i:i+n] in s:
                return True
    return False

def has_repeat(s):
    if any(a == b for a, b in zip(s, s[1:])):
        return True
    if s == s[::-1] and len(s) >= 3:
        return True
    h = len(s) // 2
    if h >= 2 and s[:h] == s[h:h*2]:
        return True
    return False

def bad_cluster(s):
    for i in range(len(s) - 2):
        trio = s[i:i+3]
        if all(c not in VOWELS and c.isalpha() for c in trio) and trio not in OK3:
            return True
    for i, c in enumerate(s):
        if c == 'q' and (i + 1 >= len(s) or s[i+1] != 'u'):
            return True
    return False

def is_pronounceable(s):
    letters = [c for c in s if c.isalpha()]
    if len(letters) < 2:
        return False
    v = sum(c in VOWELS for c in letters)
    if v == 0 or v == len(letters):
        return False
    alt = sum((a in VOWELS) != (b in VOWELS) for a, b in zip(letters, letters[1:]))
    ratio = alt / (len(letters) - 1)
    return ratio >= 0.55 and not bad_cluster(''.join(letters))

def fnv(s):
    h = 0x811c9dc5
    for ch in s.encode():
        h ^= ch
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h

# categories:
# 0:3-letter 1:4-letter 2:5-letter 3:6+ 4:dict 5:name 6:acronym 7:pronounceable
# 8:numbers 9:repeating 10:pattern 11:OG style 12:random 13:pokemon
POKEMON = set()
PGEN = {}
_pk_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "pokemon.json")
if os.path.exists(_pk_path):
    POKEMON = {p for p in json.load(open(_pk_path)) if p.isalpha()}
_pg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "poke_gens.json")
if os.path.exists(_pg_path):
    PGEN = json.load(open(_pg_path))

def length_bit(n):
    return 0 if n == 3 else 1 if n == 4 else 2 if n == 5 else 3

def mask_for(s, random_flag=False):
    n = len(s)
    m = 1 << length_bit(n)
    if s in WORD_SET and s not in NAME_SET: m |= 1 << 4   # pure dictionary word
    if s in NAME_SET: m |= 1 << 5                          # name
    if s in ACR_SET or (n == 3 and sum(c in VOWELS for c in s) <= 1): m |= 1 << 6
    if is_pronounceable(s): m |= 1 << 7
    if any(c.isdigit() for c in s): m |= 1 << 8
    if has_repeat(s): m |= 1 << 9
    run = has_run(s)
    if run: m |= 1 << 10
    if (s in OG_SET or run
            or (n <= 3 and (m >> 4 & 1))                      # 3-letter dictionary word
            or (n <= 4 and (m >> 9 & 1) and is_pronounceable(s))):  # clean repeats like emma, ooo
        m |= 1 << 11
    if random_flag: m |= 1 << 12
    if s in POKEMON: m |= 1 << 13
    if n >= 4 and s.isalpha():
        if is_semi(s):                          # stem + productive affix -> Semi (loneliness, replay, gamer)
            m |= 1 << 23
        elif (m >> 4 & 1) or (m >> 5 & 1):      # else exact lexeme -> Final (lonely, ace, maria)
            m |= 1 << 24
    if s in PGEN: m |= 1 << (13 + PGEN[s])          # gen 1-9 -> bits 14-22
    return m

def score_of(s, mask):
    n = len(s)
    base = {3: 64, 4: 57, 5: 50, 6: 44, 7: 38, 8: 32, 9: 26, 10: 22, 11: 19, 12: 16,
            13: 13, 14: 11, 15: 10, 16: 9}.get(n, 9)
    sc = float(base)
    if mask & (1 << 4):  sc += 24 if n == 3 else 14 if n == 4 else 13 if n <= 6 else 9  # dictionary word
    if mask & (1 << 5):  sc += 18 if n == 3 else 12 if n == 4 else 12 if n == 5 else 11 if n <= 7 else 7  # name
    if mask & (1 << 13): sc += 10                                       # pokemon species
    if mask & (1 << 6):  sc += 8 if s in ACR_SET else 3                 # acronym
    if mask & (1 << 7):  sc += 8                                        # pronounceable
    if mask & (1 << 11): sc += 5                                        # OG style
    if s in OG_SET and len(s) <= 4 and is_pronounceable(s): sc += 4     # curated OG that sounds clean
    if mask & (1 << 9):  sc += 7 if n <= 4 else 3                       # repeating
    if mask & (1 << 10): sc += 5                                        # pattern
    # vowel balance bonus
    letters = [c for c in s if c.isalpha()]
    if letters:
        vr = sum(c in VOWELS for c in letters) / len(letters)
        if 0.30 <= vr <= 0.60:
            sc += 3
    # meaningful strings (real words/names/acronyms) and intentional keyboard
    # patterns are "clean by construction" — skip the ugliness penalties
    meaningful = mask & ((1 << 4) | (1 << 5)) or (s in ACR_SET)
    run = mask & (1 << 10)
    if not meaningful and not run:
        if not is_pronounceable(s):
            sc -= 10 if n == 3 else 14
        rare = sum(c in RARE_LETTERS for c in s)
        sc -= rare * 4
        if rare >= 2:
            sc -= 5
    digits = sum(c.isdigit() for c in s)
    if digits:
        sc -= 18 if digits == 1 else 12 + 2 * digits
    if '_' in s: sc -= 14
    if '-' in s: sc -= 12
    # deterministic jitter for variety
    j = ((fnv(s) >> 8) % 5) - 2
    sc += j
    return max(1, min(99, int(round(sc))))

def avail_for(name, score):
    """Deterministic simulated availability. Mirror in JS."""
    h = fnv(name)
    p = 0.10 + (score / 100) ** 2 * 0.85        # rarer -> more likely taken
    taken = (h % 1000) < p * 1000
    return 1 if taken else 0

# ---------------------------------------------------------------- generation
entries = {}  # name -> [score, mask]

def add(name, random_flag=False):
    name = name.strip().lower()
    if not (3 <= len(name) <= 16):
        return
    if not name[0].isalpha():
        return
    if any(c.isdigit() for c in name):   # catalogue is letters / _ / - only — no numbers
        return
    if not re.fullmatch(r'[a-z_\-]+', name):
        return
    m = mask_for(name, random_flag)
    if name in entries:
        entries[name][1] |= m
        return
    entries[name] = [0, m]

# 1) curations (incl. Pokemon species list -> category bit 13 via mask_for)
for w in WORD_SET | NAME_SET | ACR_SET | OG_SET | POKEMON:
    add(w)

# 2) ALL letter 3-char combos (26^3 = 17,576; class-verified reserved) + ALL 4-letter (26^4).
#    No digits — catalogue and scanner are letters / _ / - only.
import itertools, string
letters = string.ascii_lowercase
CH3 = letters + '_-'
for a in letters:
    for b in CH3:
        for c in CH3:
            add(a + b + c)
for a, b, c, d in itertools.product(letters, repeat=4):
    add(a + b + c + d)
# legacy prioritised pools now redundant for 3/4 letters, but keep the generation calls
# for 5-8 letter coverage below (syllables, repeats, patterns, numbers).
tri_all = []
for a, b, c in itertools.product(letters, repeat=3):
    s = a + b + c
    m = mask_for(s)
    sc = score_of(s, m)
    tri_all.append((sc, s, m))
# ^ kept for reporting only; the full 3-char space was already added above

# 3) 4-letter space: fully enumerated above (all 26^4). Nothing left to prioritise.

# 4) syllable-built pronounceables (5-8 chars)
SYL = """ba be bi bo bu ca ce ci co cu da de di do du fa fe fi fo fu ga ge gi go gu ha he hi ho hu
ja je ji jo ju ka ke ki ko ku la le li lo lu ma me mi mo mu na ne ni no nu pa pe pi po pu
ra re ri ro ru sa se si so su ta te ti to tu va ve vi vo vu wa we wi wo ya ye yi yo yu za ze zi zo zu
xa xe xi xo bra bre bri bro cru cre dri dra flo fla fro gla glo gra gri kla kle kri kra pra pre pri pro
sha she shi sho ska ske ski sla sle slo sma sne sni spa spe spi spo sta ste sti sto stra stry swa swe
tha the thi tho tra tre tri tro twa twe twi vra wre zan zen zar zel vex lux nix rax xel xar qua qui kai ky"""

SYL = SYL.split()
import random
rng = random.Random(7331)
def syllable_words(count, nsyl):
    seen = set()
    attempts = 0
    while len(seen) < count and attempts < count * 30:
        attempts += 1
        w = ''.join(rng.choice(SYL) for _ in range(nsyl))
        if len(w) < 5 or len(w) > 8 or bad_cluster(w):
            continue
        seen.add(w)
    return seen

for w in syllable_words(900, 2):
    add(w)
for w in syllable_words(650, 3):
    add(w)

# 5) numbers category — skipped. Catalogue does not include digits.

# 6) repeating characters / palindromes / doubled syllables
for ch in letters:
    add(ch * 3)           # aaa, bbb...
rep2 = """dodo coco kiki mimi tata gaga bubu jojo zaza sasa lulu nana papa fifi gigi hihi lala mamu nono popo rara titi vovo wewe yaya zuzu
baba bebe bibi bobo caca dede fafa hoho juju kaka lele lili momo pepe pipi roro tete tutu xoxo yoyo zozo"""
for t in rep2.split():
    add(t)
PALS = """aba aca ada afa aga aha aka ala ama ana apa ara asa ata ava awa axa aya aza
bob cac? dad dud eke eme ere eve ewe gag gig huh mem mim mum nan non nun oho pap pep pip pop pup rad? sis tat tat tit tot tut wow yay"""
for t in PALS.split():
    if '?' not in t:
        add(t)
for a in letters:
    for b in letters:
        if a != b and (a in VOWELS) != (b in VOWELS):
            s = a + b + a + b
            if rng.random() < 0.18:
                add(s)

# 7) letter patterns (qwerty runs, alphabet runs)
for src in QWERTY_ROWS + [ALPHA, ALPHA[::-1]]:
    for i in range(len(src) - 2):
        add(src[i:i+3])
    for i in range(len(src) - 3):
        add(src[i:i+4])
PAT_WORDS = """poi iuy asd asdf sdf dfg zxc xcv cvb qwe qwer wert erty fgh ghj jkl poi iop lkj jhg ghj? fds fdsa ghjk"""
for t in PAT_WORDS.split():
    if '?' not in t:
        add(t)

# 8) underscore / hyphen variants (heavily penalised, but realistic)
for w in sorted(WORD_SET)[:400]:
    if 3 <= len(w) <= 5:
        add("x_" + w)
        add("the_" + w[:5])
for w in sorted(WORD_SET)[:200]:
    if len(w) <= 4:
        add(w + "_x")

# 8b) SEMI forms: dictionary/name stems with a prefix or suffix (loneliness, replay, gamer…)
#     deterministic fnv-ordered sample: up to 6 forms per stem, first 6000 stems
_stems = sorted((w for w in WORD_BASE if 3 <= len(w) <= 10 and w.isalpha()),
                key=lambda w: fnv('semi' + w))[:6000]
for w in _stems:
    cands = []
    for af in AFFIX_PRE:
        t = af + w
        if len(t) <= 16:
            cands.append(t)
    for af in AFFIX_SUF:
        t = w + af
        if w.endswith('e') and af[:1] in ('i', 'e'):
            t = w[:-1] + af                                 # make+ing -> making
        if w.endswith('y') and af[:1] == 'i':
            t = w[:-1] + af                                 # lonely+ier -> lonelier
        if len(t) <= 16:
            cands.append(t)
    cands = [t for t in dict.fromkeys(cands)
             if t not in entries and re.fullmatch(r'[a-z][a-z0-9_\-]{2,15}', t)]
    for t in sorted(cands, key=fnv)[:6]:
        add(t)
# canonical showcase forms — always present (fnv sampling above may skip them)
for t in ("loneliness","lonelier","loneliest","lonelies","darkness","darkly","stormy","stormier",
          "replay","replays","gamer","ghostly","shadowless","dreamless","voidechoes?","misty","frosty"):
    if '?' not in t and t not in entries:
        add(t)

# 9) random combinations (the realistic bulk / low tier)
rng2 = random.Random(4242)
weighted = 'eeaaiioorrsttnnllccdduummppggbbfyhkvwxzqj'
made = 0
tries = 0
while made < 800 and tries < 20000:
    tries += 1
    n = rng2.randint(5, 9)
    w = ''.join(rng2.choice(weighted) for _ in range(n))
    if w in entries or is_pronounceable(w):
        continue
    if sum(c in VOWELS for c in w) == 0:
        continue
    entries[w] = [0, mask_for(w, True)]
    made += 1

# ---------------------------------------------------------------- finalise
HERE = os.path.dirname(os.path.abspath(__file__))
VERIFIED = {}
import glob as _glob
for _vf in sorted(_glob.glob(os.path.join(HERE, "data", "verified*.json"))):
    for _k, _v in json.load(open(_vf)).items():
        if _k not in VERIFIED or _v.get("ts", 0) > VERIFIED[_k].get("ts", 0):
            VERIFIED[_k] = _v          # latest timestamp wins across shards
CLASS3 = {}
_c3 = os.path.join(HERE, "data", "class3.json")
if os.path.exists(_c3):
    CLASS3 = json.load(open(_c3))
WHY = ["-", "available", "taken", "blocked", "reserved3", "reserved"]

# 10) live-checked names (via server.py /api/check) that aren't in the base pools
#     become permanent, fully-scored DB rows in the next build.
_added_live = 0
for _n in list(VERIFIED.keys()):
    if _n not in entries and re.fullmatch(r'[a-z][a-z0-9_\-]{2,15}', _n):
        add(_n)
        _added_live += 1
if _added_live:
    print(f"live-added {_added_live} new names from verified pools")

rows = []
taken_rows = []                 # verified-unavailable: kept on record (name, why-idx, ts), never listed
tier_dist = {t: 0 for t in 'SABC?'}
n_verified = n_taken = 0
for name, (sc, m) in entries.items():
    assert re.fullmatch(r'[a-z][a-z0-9_\-]{2,15}', name), name
    sc = score_of(name, m)
    h = fnv(name)
    if name in VERIFIED:
        # verified against Sony's account endpoint — real status + epoch ts
        v = VERIFIED[name]
        if v.get("a") is None:
            a, d5, ver, why, nck = 2, None, 0, 0, 0  # inconclusive -> leave unverified
        else:
            a = 0 if v["a"] == 0 else 1
            d5, ver, why = v["ts"], 1, WHY.index(v["why"]) if v["why"] in WHY else 0
            nck = 2 if v.get("n") == 2 else 1
            n_verified += 1
    elif CLASS3 and len(name) == 3:
        # class-verified: every 3-char ID returns 406/reserved on Sony's endpoint
        a, d5, ver, why, nck = 1, CLASS3["ts"], 1, WHY.index("reserved3"), 1
        n_verified += 1
    else:
        # unverified -> shown as Unknown; the background scan (server.py) works through these
        # and they flip to verified on the next rebuild (or instantly via /api/updates sync)
        a, d5, ver, why, nck = 2, None, 0, 0, 0
    # verified-unavailable (taken / blocked / reserved): leave the browsable catalogue,
    # stay on record in TAKENDATA so searches still answer instantly without re-checking Sony
    if ver == 1 and a == 1:
        taken_rows.append([name, why, d5 if isinstance(d5, int) else 0])
        n_taken += 1
        continue
    # compact rows: unverified & never-checked entries emit just [name, score, mask]
    if ver == 0 and a == 2:
        rows.append([name, sc, m])
    else:
        rows.append([name, sc, m, a, d5, ver, why, nck])
    t = 'S' if sc >= 90 else 'A' if sc >= 80 else 'B' if sc >= 70 else 'C' if sc >= 60 else '?'
    tier_dist[t] += 1

rows.sort(key=lambda r: (-r[1], r[0]))
taken_rows.sort(key=lambda r: r[0])
TAKEN_DATA = json.dumps(taken_rows, separators=(',', ':'))
# extras for the systematic scanner: non-letter names (digits/_/-), length then a-z.
# Letter-only ids are generated by server.py (aaaa, aaab, … then 5-char, up to 16).
# 3-char is class-answered and never queued.
queue = sorted((r[0] for r in rows
                if len(r[0]) >= 4 and not r[0].isalpha() and not any(c.isdigit() for c in r[0])),
               key=lambda n: (len(n), n))
with open(os.path.join(HERE, "data", "sweep_queue.txt"), "w") as _q:
    _q.write("\n".join(queue))
DATA = json.dumps(rows, separators=(',', ':'))
GEN_DATE = datetime.date.today().isoformat()
print(f"entries={len(rows)} taken-on-record={n_taken} tiers={tier_dist} verified={n_verified} data_kb={len(DATA)//1024}+{len(TAKEN_DATA)//1024}taken queue={len(queue)}")

# ---------------------------------------------------------------- template
TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PSN Username Database</title>
<style>
:root{
  --panel:rgba(15,19,15,.78); --panel2:rgba(22,27,21,.66); --border:rgba(216,212,196,.16); --ink:#e9e6d9;
  --text:#c7c4b6; --muted:#8f8d80; --accent:#9dbf9a; --accent2:#3f6b4b;
  --s:#e0b25e; --sbg:rgba(224,178,94,.12); --b:#8fb5d9; --c:#8aa896; --common:#6f7268;
  --green:#7cc896; --red:#e0816f; --gray:#6e7365;
}
*{box-sizing:border-box;margin:0;padding:0}
html{color-scheme:dark}
body{background:#0b0e0b url("data:image/jpeg;base64,__WALLPAPER__") center/cover fixed no-repeat;color:var(--text);font-family:ui-sans-serif,system-ui,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;font-size:14px;line-height:1.5}
body::before{content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;background:linear-gradient(180deg,rgba(7,10,8,.66) 0%,rgba(7,10,8,.44) 26%,rgba(7,10,8,.74) 100%)}
.mono{font-family:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,monospace}
a{color:var(--accent)}
header{background:linear-gradient(180deg,rgba(7,10,8,.55),rgba(7,10,8,.16));border-bottom:3px double rgba(233,230,217,.28);padding:26px 24px 18px;backdrop-filter:blur(3px)}
header .kicker{font-size:10px;letter-spacing:.24em;text-transform:uppercase;color:var(--accent);font-weight:700;margin-bottom:6px}
header h1{font-size:30px;letter-spacing:-.6px;font-weight:800;color:var(--ink);display:flex;gap:12px;align-items:baseline;flex-wrap:wrap}
header h1 .ps{background:var(--accent);color:#0d110d;border-radius:2px;padding:2px 7px;font-size:11px;font-weight:800;letter-spacing:.18em;transform:translateY(-3px)}
header p{color:#a9a69a;font-size:12.5px;margin-top:8px;max-width:920px}
header p b{color:var(--ink)}
header p code{color:var(--accent)}
.stats{display:flex;gap:0;flex-wrap:wrap;margin-top:14px;border:1px solid rgba(233,230,217,.24);border-radius:3px;overflow:hidden;background:var(--panel);backdrop-filter:blur(8px);width:fit-content;max-width:100%}
.stat{border-right:1px solid var(--border);padding:7px 13px;font-size:10.5px;color:var(--muted);display:flex;gap:7px;align-items:baseline;text-transform:uppercase;letter-spacing:.08em}
.stat:last-child{border-right:0}
.stat b{color:var(--ink);font-size:15px;font-weight:800;letter-spacing:0}
.toolbar{position:sticky;top:0;z-index:20;background:rgba(9,12,9,.82);backdrop-filter:blur(10px);border-bottom:2px solid rgba(233,230,217,.5);padding:9px 24px;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.livebar{display:none;margin:12px 24px 0;padding:10px 14px;border:1px solid rgba(124,200,150,.4);border-left:5px solid var(--green);border-radius:3px;background:rgba(18,28,20,.88);backdrop-filter:blur(8px);font-size:13px;align-items:center;gap:10px;flex-wrap:wrap}
.livebar.show{display:flex}
.livebar code{color:var(--accent)}
.livebar .btn{padding:4px 10px;font-size:12px}
.livebar .mono{font-size:15px}
.livebar b{color:var(--ink)}
.syncstat{font-size:11px;color:var(--muted);white-space:nowrap;margin-left:2px;max-width:260px;overflow:hidden;text-overflow:ellipsis}
.toolbar input[type=search]{background:var(--panel);border:1.5px solid rgba(233,230,217,.55);color:var(--ink);border-radius:3px;padding:8px 12px;min-width:250px;font-size:14px;outline:none;box-shadow:3px 3px 0 rgba(0,0,0,.3)}
.toolbar input[type=search]:focus{border-color:var(--accent);box-shadow:3px 3px 0 rgba(157,191,154,.2)}
.toolbar select{background:var(--panel);border:1.5px solid rgba(233,230,217,.25);color:var(--text);border-radius:3px;padding:8px;font-size:12.5px}
.btn{background:var(--panel);border:1.5px solid rgba(233,230,217,.6);color:var(--ink);border-radius:3px;padding:8px 12px;font-size:12px;cursor:pointer;font-weight:600;letter-spacing:.02em;box-shadow:2px 2px 0 rgba(0,0,0,.35);transition:transform .04s}
.btn:hover{box-shadow:1px 1px 0 rgba(0,0,0,.5);transform:translate(1px,1px)}
.btn.on{background:var(--ink);color:#14150e;border-color:var(--ink)}
.btn.warn:hover{border-color:var(--red);color:var(--red)}
main{display:grid;grid-template-columns:252px 1fr;gap:18px;padding:18px 24px;max-width:1480px;margin:0 auto}
@media(max-width:900px){main{grid-template-columns:1fr}}
aside .card, #validator{background:var(--panel);backdrop-filter:blur(8px);border:1px solid var(--border);border-radius:3px;padding:14px;margin-bottom:14px}
aside h3, #validator h3{font-size:10px;text-transform:uppercase;letter-spacing:.16em;color:var(--muted);margin-bottom:10px;border-bottom:1px solid var(--border);padding-bottom:6px}
.chips{display:flex;flex-wrap:wrap;gap:5px}
.chip{border:1px solid rgba(233,230,217,.2);background:var(--panel2);color:var(--muted);border-radius:3px;padding:4px 9px;font-size:10.5px;cursor:pointer;user-select:none;text-transform:uppercase;letter-spacing:.06em;font-weight:600}
.chip:hover{border-color:rgba(233,230,217,.55);color:var(--ink)}
.chip.on{border-color:var(--ink);background:var(--ink);color:#14150e}
.checkrow{display:flex;gap:10px;flex-wrap:wrap}
label.ck{display:flex;align-items:center;gap:6px;font-size:13px;color:var(--muted);cursor:pointer;padding:2px 0}
label.ck input{accent-color:var(--accent)}
.lenrow{display:flex;gap:8px;align-items:center}
.lenrow input{width:64px;background:var(--panel);border:1.5px solid rgba(233,230,217,.3);color:var(--ink);border-radius:3px;padding:5px 8px;font-size:13px}
#count{color:var(--muted);font-size:11.5px;margin-bottom:8px;text-transform:uppercase;letter-spacing:.07em}
table{width:100%;border-collapse:collapse;font-size:13px;background:var(--panel);backdrop-filter:blur(8px);border:1px solid var(--border)}
thead th{position:sticky;top:var(--thtop,52px);background:#0c0f0c;text-align:left;color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.14em;padding:9px 10px;border-bottom:2px solid rgba(233,230,217,.5);z-index:5}
tbody td{padding:8px 10px;border-bottom:1px solid rgba(233,230,217,.12);vertical-align:middle}
tbody tr{cursor:pointer}
tbody tr:hover{background:rgba(233,230,217,.06)}
.uname{font-weight:700;font-size:14px;letter-spacing:.4px;color:var(--ink)}
.badge{display:inline-flex;align-items:center;gap:6px;font-size:11px;border-radius:3px;padding:2px 8px;border:1px solid rgba(233,230,217,.25);color:var(--muted);white-space:nowrap;font-weight:600;text-transform:uppercase;letter-spacing:.05em}
.badge .dot{width:7px;height:7px;border-radius:50%;display:inline-block}
.b-avail .dot{background:var(--green)} .b-avail{color:#8fd3a5;border-color:rgba(124,200,150,.4)}
.b-taken .dot{background:var(--red)} .b-taken{color:#e38f7d;border-color:rgba(224,129,111,.4)}
.b-unknown .dot{background:var(--gray)}
.badge.simline{border-style:dashed}
.srctag{font-size:8.5px;margin-left:5px;border:1px solid rgba(124,200,150,.4);border-radius:2px;padding:0 4px;color:var(--green);vertical-align:2px;letter-spacing:.1em;text-transform:uppercase;font-weight:700}
.srctag.live{color:#8fd3a5;border-color:rgba(124,200,150,.4)}
.tier{display:inline-block;min-width:27px;text-align:center;font-weight:800;border-radius:3px;padding:2px 6px;font-size:11.5px;border:1.5px solid rgba(233,230,217,.25)}
.tS{color:var(--s);border-color:rgba(224,178,94,.55);background:var(--sbg)}
.tA{color:#0d110d;border-color:var(--accent);background:var(--accent)}
.tB{color:var(--b);border-color:rgba(143,181,217,.5)}
.tC{color:var(--c);border-color:rgba(138,168,150,.35)}
.tCom{color:var(--common);font-weight:600}
.scorebar{position:relative;height:5px;background:rgba(233,230,217,.12);border-radius:2px;width:70px;display:inline-block;vertical-align:middle;margin-left:8px}
.scorebar i{position:absolute;inset:0;right:auto;background:var(--accent);border-radius:2px}
.catpill{display:inline-block;font-size:10px;color:var(--muted);border:1px solid rgba(233,230,217,.18);border-radius:2px;padding:1px 6px;margin:1px 2px 1px 0;background:var(--panel2);letter-spacing:.03em}
.iconbtn{background:none;border:1.5px solid rgba(233,230,217,.3);color:var(--muted);border-radius:3px;width:30px;height:30px;cursor:pointer;font-size:14px;line-height:1}
.iconbtn:hover{border-color:rgba(233,230,217,.7);color:var(--ink)}
.iconbtn.fav{color:var(--s);border-color:rgba(224,178,94,.55)}
#loadmore{display:block;margin:22px auto;padding:10px 26px}
footer{border-top:3px double rgba(233,230,217,.28);padding:18px 24px;color:var(--muted);font-size:12px;max-width:1480px;margin:0 auto}
footer details{margin-top:8px}
footer summary{cursor:pointer;color:var(--accent);font-weight:700}
footer li{margin:3px 0 3px 18px}
#overlay{position:fixed;inset:0;background:rgba(5,8,6,.55);backdrop-filter:blur(3px);display:none;z-index:50;align-items:center;justify-content:center;padding:18px}
#overlay.show{display:flex}
#modal{background:rgba(17,21,17,.93);backdrop-filter:blur(12px);border:2px solid rgba(233,230,217,.4);border-radius:3px;box-shadow:7px 7px 0 rgba(0,0,0,.45);padding:22px;width:min(560px,96vw);max-height:88vh;overflow:auto}
#modal .mname{font-size:27px;letter-spacing:.5px;color:var(--ink)}
.mrow{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid rgba(233,230,217,.14);font-size:13px}
.mrow .k{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.08em}
.mbtns{display:flex;gap:8px;margin-top:14px;flex-wrap:wrap}
.note{font-size:11px;color:var(--muted);margin-top:12px;border:1px dashed rgba(233,230,217,.25);border-radius:3px;padding:8px 10px}
#validator .vinput{width:100%;background:var(--panel);border:1.5px solid rgba(233,230,217,.55);color:var(--ink);border-radius:3px;padding:8px 10px;font-size:14px;margin-bottom:10px}
#validator ul{list-style:none}
#validator li{font-size:12.5px;color:var(--muted);padding:3px 0;display:flex;gap:8px;align-items:center}
#validator li.ok{color:#8fd3a5}#validator li.bad{color:#e38f7d}
.vverdict{margin-top:8px;font-size:12.5px;font-weight:700}
.vverdict.ok{color:var(--green)}.vverdict.bad{color:var(--red)}
.toast{position:fixed;bottom:18px;left:50%;transform:translateX(-50%);background:var(--ink);border:1px solid var(--ink);color:#14150e;border-radius:3px;padding:9px 16px;font-size:13px;display:none;z-index:99;box-shadow:4px 4px 0 rgba(0,0,0,.4)}
</style>
</head>
<body>
<header>
  <div class="kicker">Checked live against Sony's own endpoint · scanning continuously</div>
  <h1><span class="ps">PSN</span> Username Database</h1>
  <p>A Spell-style catalogue of PSN Online ID candidates — browse, search and filter every handle, each scored with a 0–99 rarity rating.
     Availability is checked against <b>Sony's own account endpoint</b>; verified entries carry a <b>✓ live</b> tag, everything else is <b>Unknown</b>
     until the background scan reaches it. <b>Search any valid ID</b> — if it isn't verified yet, the hosted app (run <code>python3 server.py</code>)
     checks Sony on the spot and adds it to the database. The list <b>auto-refreshes</b> with new verifications (Sync menu, default 1 min).
     Catalogue is <b>letters only</b> (plus <span class="mono">_</span>/<span class="mono">-</span>) — no numbers. Any valid 3–16-character ID is still searchable. Word forms are tagged <b>Final</b> (whole word — <span class="mono">lonely</span>) or
     <b>Semi</b> (stem + prefix/suffix — <span class="mono">loneliness</span>, <span class="mono">replay</span>, <span class="mono">gamer</span>).
     Verified <b>taken/reserved</b> IDs are removed from this catalogue but stay on record — search one to see its status instantly.</p>
  <div class="stats" id="stats"></div>
</header>

<div class="toolbar">
  <input type="search" id="search" placeholder="Search usernames…  ( / )" autocomplete="off">
  <select id="sort">
    <option value="score_desc">Sort: Rarity ↓</option>
    <option value="score_asc">Sort: Rarity ↑</option>
    <option value="az">Sort: A → Z</option>
    <option value="za">Sort: Z → A</option>
    <option value="len_asc">Sort: Shortest</option>
    <option value="len_desc">Sort: Longest</option>
    <option value="recent">Sort: Recently checked</option>
  </select>
  <button class="btn" id="pokebtn">Pokémon</button>
  <button class="btn" id="favbtn">★ Favourites <span id="favcount"></span></button>
  <button class="btn" id="dice">Random pick</button>
  <button class="btn" id="export">Export CSV</button>
  <select id="refresh" title="Background sync — how often the list refreshes with new Sony verifications">
    <option value="0">Sync: Off</option>
    <option value="30000">Sync: 30s</option>
    <option value="60000">Sync: 1 min</option>
    <option value="300000">Sync: 5 min</option>
  </select>
  <span id="syncstat" class="syncstat"></span>
  <button class="btn warn" id="reset">Reset filters</button>
</div>
<div class="livebar" id="livebar"></div>

<main>
  <aside>
    <div class="card"><h3>Rarity tier</h3><div class="chips" id="tierchips"></div></div>
    <div class="card"><h3>Availability</h3><div class="chips" id="availchips"></div>
      <div class="chips" style="margin-top:8px"><span class="chip" id="verchip">✓ verified only</span></div></div>
    <div class="card"><h3>Categories <span style="text-transform:none;font-size:10px">(all selected must match)</span></h3><div class="chips" id="catchips"></div></div>
    <div class="card"><h3>Pokémon generation <span style="text-transform:none;font-size:10px">(any match)</span></h3><div class="chips" id="genchips"></div></div>
    <div class="card"><h3>Character count</h3>
      <div class="lenrow"><input id="lenmin" type="number" min="3" max="16" value="3"> to <input id="lenmax" type="number" min="3" max="16" value="16"></div>
    </div>
    <div class="card"><h3>Character types</h3><div class="chips" id="charchips"></div></div>
    <div id="validator">
      <h3>PSN format validator</h3>
      <input class="vinput mono" id="vinput" placeholder="Type any Online ID…" maxlength="16" autocomplete="off">
      <ul id="vrules"></ul>
      <div class="vverdict" id="vverdict"></div>
      <div class="note" style="margin-top:8px">Format rules only — doesn’t check if the ID is registered.</div>
    </div>
  </aside>

  <section>
    <div id="count"></div>
    <table>
      <thead><tr>
        <th>Username</th><th>Availability</th><th>Len</th><th>Categories</th><th>Rarity</th><th>Checked</th><th></th>
      </tr></thead>
      <tbody id="rows"></tbody>
    </table>
    <button class="btn" id="loadmore">Load more</button>
  </section>
</main>

<footer>
  <div><b>PSN Username Database</b> · generated __GENDATE__ · <span id="ftotal"></span> entries · statuses tagged <b>✓ live</b> were verified against Sony's account endpoint; everything else is Unknown until the background scan reaches it.</div>
  <details>
    <summary>How rarity scoring works (0–99)</summary>
    <ul>
      <li><b>Base score by length</b> — 3 chars = 64 down to 16 chars = 9. Short IDs are the rarest commodity.</li>
      <li><b>Bonuses</b>: 3-letter dictionary word +24, longer words +9/+13/+14, real first name +7…+18, meaningful acronym +8, pronounceable +8, OG style +5, notable repeats +3…+7, letter patterns +5, balanced vowels +3.</li>
      <li><b>Penalties</b>: digits −18, underscores −14, hyphens −12, hard to pronounce −10/−14, rare-letter clusters (q/z/x/j) −4 each (waived for real words, names and intentional keyboard patterns).</li>
      <li><b>Tiers</b>: 90–99 S, 80–89 A, 70–79 B, 60–69 C, below 60 Common.</li>
    </ul>
  </details>
  <details>
    <summary>How availability is verified</summary>
    <div style="margin:6px 0 0 0">Verification posts to Sony's account-creation service (<code>accounts.api.playstation.com</code>) with <code>reserveIfAvailable:false</code>, which never claims or reserves the ID: 201 = claimable (double-confirmed on separate requests), 400/3101 = account exists, 400/3208 = Sony-blocked word, 406 = reserved class (empirically all 3-character IDs — Sony no longer issues them). <b>Scope note:</b> this is the validator the <i>web account-signup</i> uses; the PS App / console <i>rename</i> flow applies an additional stricter word-policy layer and can reject an API-available ID. Entries not yet verified show <b>Unknown</b> — no guesswork — and the server's background scan works the queue automatically (≈1 per 0.5s plus live search; 60s cooldowns on any throttle). New verifications stream into the open page via the Sync menu, and rebuild with <code>python3 build.py</code> to bake them into the portable file.</div>
    <div style="margin:6px 0 0 0"><b>Live search:</b> serve the app with <code>python3 server.py</code> and search any valid ID — if it isn't verified, the app asks the included server, which checks Sony exactly like the sweep (browsers can't call Sony's endpoint directly: it rejects any request carrying an <code>Origin</code> header) and writes the result to <code>data/verified_live.json</code>, so the name becomes a permanent database row on the next rebuild. Sony calls are rate-limited (≈1 per 1.6s) and share headroom with the running sweep.</div>
  </details>
</footer>

<div id="overlay"><div id="modal"></div></div>
<div class="toast" id="toast"></div>

<script>
const ROWS = __DATA__;
const TAKENDATA = __TAKEN__;
const CATS = ["3 letter","4 letter","5 letter","6+ letter","Dictionary word","Name","Acronym","Pronounceable","Numbers","Repeating chars","Letter pattern","OG style","Random combo","Pokémon","","","","","","","","","","Semi (word + prefix/suffix)","Final (whole word/name)"];
const TIERS = [
  {k:"S", min:90, cls:"tS"}, {k:"A", min:80, cls:"tA"}, {k:"B", min:70, cls:"tB"},
  {k:"C", min:60, cls:"tC"}, {k:"Common", min:0, cls:"tCom"}
];
const AVAIL = ["Available","Taken","Unknown"];
</script>
<script>
/* ---------------- data ---------------- */
function fnv(s){let h=0x811c9dc5;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,0x01000193)>>>0;}return h>>>0;}
const tierIdx = s => s>=90?0:s>=80?1:s>=70?2:s>=60?3:4;
const relDays = d => d===null? "never" : d===0 ? "just now" : d===1 ? "1d ago" : d+"d ago";
const lettersOnly = n => /^[a-z]+$/.test(n);

const WHY = ["-", "Available", "Taken (account exists)", "Blocked word (Sony)", "Reserved — 3-char IDs are no longer issued", "Reserved by Sony (policy, trademark or a previous holder)"];
const ALL = ROWS.map(r=>{
  const full = r.length >= 7;            // compact rows are [name,score,mask] = unchecked (Unknown)
  const ver = full && r[5] === 1;
  return {
    n:r[0], s:r[1], m:r[2],
    a: full ? r[3] : 2,
    d: ver ? Math.max(0, Math.floor((Date.now()/1000 - r[4]) / 86400)) : null,
    v: ver ? 1 : 0,
    w: full ? (r[6]||0) : 0,
    ck: full ? (r[7]||0) : 0,
    len:r[0].length,
    dig:/\d/.test(r[0]), us:r[0].includes("_"), hy:r[0].includes("-")
  };
});
const NAMEIDX = new Map(ALL.map(r=>[r.n, r]));
const nameFind = n => NAMEIDX.get(n);
/* verified-unavailable registry — not listed on the site, but searchable. name -> {w, ts} */
const TAKENIDX = new Map(TAKENDATA.map(r=>[r[0], {w:r[1], ts:r[2]}]));
const takenDays = t => !t.ts ? "a while ago" : relDays(Math.max(0, Math.floor((Date.now()/1000 - t.ts)/86400)));
let favs = new Set();
try{ favs = new Set(JSON.parse(localStorage.getItem("psnfavs")||"[]")); }catch(e){}
const saveFavs = ()=>{ try{ localStorage.setItem("psnfavs", JSON.stringify([...favs])); }catch(e){} };

/* ---------------- state ---------------- */
const state = { q:"", tiers:new Set(), avails:new Set(), cats:new Set(), chars:new Set(), gens:new Set(),
                lenMin:3, lenMax:16, favOnly:false, verifiedOnly:false, sort:"score_desc", shown:60 };
const PAGE = 60;

/* ---------------- filtering / sorting ---------------- */
function filtered(){
  const q = state.q.toLowerCase();
  return ALL.filter(r=>{
    if(r.dropped) return false;
    if(/\d/.test(r.n)) return false;          // never list names with numbers
    if(q && !r.n.includes(q)) return false;
    if(state.favOnly && !favs.has(r.n)) return false;
    if(state.verifiedOnly && !r.v) return false;
    if(state.tiers.size && !state.tiers.has(tierIdx(r.s))) return false;
    if(state.avails.size && !state.avails.has(r.a)) return false;
    if(r.len < state.lenMin || r.len > state.lenMax) return false;
    for(const c of state.cats) if(!(r.m & (1<<c))) return false;
    if(state.gens.size && ![...state.gens].some(g => r.m & (1 << (13+g)))) return false;
    for(const ch of state.chars){
      if(ch==="letters" && !lettersOnly(r.n)) return false;
      if(ch==="digits" && !r.dig) return false;
      if(ch==="underscore" && !r.us) return false;
      if(ch==="hyphen" && !r.hy) return false;
    }
    return true;
  });
}
function sortList(list){
  const L = list.slice();
  const s = state.sort;
  if(s==="score_desc") L.sort((a,b)=>b.s-a.s || a.n.localeCompare(b.n));
  else if(s==="score_asc") L.sort((a,b)=>a.s-b.s || a.n.localeCompare(b.n));
  else if(s==="az") L.sort((a,b)=>a.n.localeCompare(b.n));
  else if(s==="za") L.sort((a,b)=>b.n.localeCompare(a.n));
  else if(s==="len_asc") L.sort((a,b)=>a.len-b.len || b.s-a.s);
  else if(s==="len_desc") L.sort((a,b)=>b.len-a.len || b.s-a.s);
  else if(s==="recent") L.sort((a,b)=> (a.d===null?99:a.d)-(b.d===null?99:b.d) || b.s-a.s);
  return L;
}

/* ---------------- rendering ---------------- */
const $ = id => document.getElementById(id);
function catPills(m){
  const out=[]; for(let i=0;i<CATS.length;i++) if((m&(1<<i)) && CATS[i]) out.push(i);
  const show = out.slice(0,3).map(i=>`<span class="catpill">${CATS[i]}</span>`).join("");
  return show + (out.length>3? `<span class="catpill">+${out.length-3}</span>`:"");
}
function availBadge(r){
  const tag = r.v ? `<span class="srctag live">✓ live</span>` : "";
  const b = r.a===0? `<span class="badge b-avail"><span class="dot"></span>Available</span>`
          : r.a===1? `<span class="badge b-taken"><span class="dot"></span>Taken</span>`
          : `<span class="badge b-unknown"><span class="dot"></span>Unknown</span>`;
  return b + tag;
}
function rowHTML(r){
  const t = TIERS[tierIdx(r.s)];
  const av = availBadge(r);
  const fav = favs.has(r.n) ? "★" : "☆";
  const fc  = favs.has(r.n) ? "fav" : "";
  return `<tr data-n="${r.n}">
    <td class="mono uname">${r.n}</td>
    <td>${av}</td>
    <td>${r.len}</td>
    <td>${catPills(r.m)}</td>
    <td><span class="tier ${t.cls}">${t.k==="Common"?"Com":t.k}</span> ${r.s}<span class="scorebar"><i style="width:${r.s}%"></i></span></td>
    <td style="color:var(--muted)">${relDays(r.d)}</td>
    <td><button class="iconbtn ${fc}" data-act="fav" title="Favourite">${fav}</button></td>
  </tr>`;
}
function emptyRow(){
  const name = state.q.trim().toLowerCase().replace(/^@+/,"").replace(/\s+/g,"");
  const tk = /^[a-z][a-z0-9_\-]{2,15}$/.test(name) ? TAKENIDX.get(name) : null;
  if(tk){
    const lbl = WHY[(tk.w===4&&name.length>3)?5:tk.w]||"Taken";
    return `<tr><td colspan="7" style="text-align:center;color:var(--muted);padding:30px">“${name}” is <b style="color:var(--red)">taken</b> — live-verified against Sony ${takenDays(tk)} (${lbl}).<br>It's removed from the catalogue but kept on record, so no re-check was needed.</td></tr>`;
  }
  if(/^[a-z][a-z0-9_\-]{2,15}$/.test(name) && !nameFind(name)){
    const msg = (LIVE && NET_OK)
      ? `“${name}” isn't in the offline index — ${liveAsked.has(name)?"checking Sony right now…":"it will be live-checked against Sony in a moment…"}`
      : `“${name}” isn't in the offline index — open the hosted app (python3 server.py or the live preview) to check Sony live and add it here.`;
    return `<tr><td colspan="7" style="text-align:center;color:var(--muted);padding:30px">${msg}</td></tr>`;
  }
  return `<tr><td colspan="7" style="text-align:center;color:var(--muted);padding:30px">No usernames match these filters.</td></tr>`;
}
function render(){
  const list = sortList(filtered());
  const slice = list.slice(0, state.shown);
  $("rows").innerHTML = slice.map(rowHTML).join("") || emptyRow();
  $("count").textContent = `Showing ${slice.length.toLocaleString()} of ${list.length.toLocaleString()} matches · ${ALL.length.toLocaleString()} total entries`;
  $("loadmore").style.display = list.length>state.shown ? "block":"none";
  $("favcount").textContent = favs.size? `(${favs.size})`:"";
  renderStats();
}
function renderStats(){
  const t=[0,0,0,0,0]; let av=0, ver=0, verAv=0, listed=0;
  for(const r of ALL){ if(r.dropped || /\d/.test(r.n)) continue; listed++; t[tierIdx(r.s)]++; if(r.a===0)av++; if(r.v){ver++; if(r.a===0)verAv++;} }
  $("stats").innerHTML =
    `<div class="stat">Listed <b>${listed.toLocaleString()}</b></div>`+
    TIERS.map((x,i)=>`<div class="stat"><span class="tier ${x.cls}">${x.k==="Common"?"Common":x.k}</span> <b>${t[i].toLocaleString()}</b></div>`).join("")+
    `<div class="stat">Available (verified) <b>${verAv.toLocaleString()}</b></div>`+
    `<div class="stat">Not yet checked <b>${(listed-ver).toLocaleString()}</b></div>`+
    `<div class="stat">Taken/reserved on record <b>${TAKENIDX.size.toLocaleString()}</b></div>`;
  $("ftotal").textContent = (listed + TAKENIDX.size).toLocaleString();
}

/* ---------------- modal ---------------- */
function openModal(r){
  const t = TIERS[tierIdx(r.s)];
  const cats=[]; for(let i=0;i<CATS.length;i++) if((r.m&(1<<i)) && CATS[i]) cats.push(CATS[i]);
  const types = [];
  types.push(/[a-z]/.test(r.n)?"letters":null, r.dig?"numbers":null, r.us?"underscores":null, r.hy?"hyphens":null);
  const src = r.v ? "Sony account endpoint ✓" : "not checked yet — queued for the background scan";
  const wIdx = (r.w === 4 && r.len > 3) ? 5 : r.w;   // legacy data: 406 on >3 chars shows as reserved3
  const reason = r.v && wIdx ? WHY[wIdx] : null;
  let gen = null;
  if(r.m & (1<<13)) for(let g=1; g<=9; g++){ if(r.m & (1<<(13+g))) { gen = g; break; } }
  $("modal").innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px">
      <div><div class="mname mono">${r.n}</div>
      <div style="margin-top:6px"><span class="tier ${t.cls}">${t.k}</span> <b style="font-size:16px">${r.s}</b>/99 <span class="scorebar" style="width:120px"><i style="width:${r.s}%"></i></span></div></div>
      <button class="iconbtn" id="mclose">✕</button>
    </div>
    <div style="margin-top:10px">
      <div class="mrow"><span class="k">Availability</span><span id="mav">${availBadge(r)}</span></div>
      ${reason?`<div class="mrow"><span class="k">Detail</span><span>${reason}</span></div>`:""}
      ${r.v && r.a===0?`<div class="mrow"><span class="k">Live checks</span><span>${r.ck>=2?"2 independent Sony checks ✓✓":"1 Sony check"}</span></div>`:""}
      <div class="mrow"><span class="k">Source</span><span>${src}</span></div>
      <div class="mrow"><span class="k">Last availability check</span><span id="mdays">${relDays(r.d)}</span></div>
      <div class="mrow"><span class="k">Character count</span><span>${r.len}</span></div>
      <div class="mrow"><span class="k">Character types</span><span>${types.filter(Boolean).join(", ")}</span></div>
      <div class="mrow"><span class="k">PSN format</span><span style="color:var(--green)">✓ valid (3–16, starts with a letter)</span></div>
      <div class="mrow"><span class="k">Categories</span><span style="text-align:right;max-width:65%">${cats.map(c=>`<span class="catpill">${c}</span>`).join("")}</span></div>
      ${gen!==null?`<div class="mrow"><span class="k">Pokémon generation</span><span>Gen ${gen}</span></div>`:""}
    </div>
    <div class="mbtns">
      <button class="btn" id="mcheck">⟳ Check availability</button>
      <button class="btn" id="mfav">${favs.has(r.n)?"★ Remove favourite":"☆ Add favourite"}</button>
      <button class="btn" id="mcopy">⧉ Copy</button>
    </div>
    <div class="note">Rarity is a desirability heuristic — independent of availability. A 99-score ID can be taken, a Common one can be free.</div>
    ${r.v && r.a===0?`<div class="note" style="border-color:rgba(124,200,150,.4)">Verified claimable via Sony's <b>account-creation</b> API (what the web signup uses). The PS App / console <b>rename</b> flow applies stricter word policies and may still reject it — if that happens, that's a policy block, not someone holding the name.</div>`:""}`;
  $("overlay").classList.add("show");
  $("mclose").onclick = closeModal;
  $("overlay").onclick = e => { if(e.target.id==="overlay") closeModal(); };
  $("mfav").onclick = ()=>{ toggleFav(r.n); $("modal").querySelector("#mfav").textContent = favs.has(r.n)?"★ Remove favourite":"☆ Add favourite"; render(); };
  $("mcopy").onclick = async ()=>{ try{ await navigator.clipboard.writeText(r.n); toast("Copied “"+r.n+"”"); }catch(e){ toast("Copy blocked here — select the name manually"); } };
  $("mcheck").onclick = async ()=>{
    if(r.v){
      $("mav").innerHTML = availBadge(r);
      $("mdays").textContent = relDays(r.d);
      toast(`“${r.n}” already verified via Sony (${WHY[(r.w===4&&r.len>3)?5:r.w]||"checked"})`);
      return;
    }
    $("mav").innerHTML = `<span class="badge b-unknown"><span class="dot"></span>Checking…</span>`;
    if(!LIVE){
      setTimeout(()=>{
        $("mav").innerHTML = availBadge(r);
        toast("Live checking works in the hosted app (python3 server.py)");
      }, 300);
      return;
    }
    $("mcheck").disabled = true;
    const j = await fetch("/api/check?onlineId=" + encodeURIComponent(r.n)).then(x=>x.json()).catch(()=>null);
    $("mcheck").disabled = false;
    if(j && j.ok){
      applyLive(r.n, j);
      $("mav").innerHTML = availBadge(r);
      $("mdays").textContent = "just now";
      const lbl = WHY[(WHYIDX[j.why]===4&&r.len>3)?5:WHYIDX[j.why]]||"checked";
      toast(j.a===0 ? `“${r.n}” is AVAILABLE on Sony's endpoint ✓` : `Sony says: ${lbl}`);
      render();
    } else if(j && j.error==="cooldown"){
      $("mav").innerHTML = availBadge(r);
      if(j.queued || (j.retry_after||0) >= 90){
        toast("Sony blocks Cloudflare — queued. Scanner will answer in ~2 min");
        pollQueued(r.n);
      } else {
        toast(`Rate-limited — try again in ~${j.retry_after||60}s`);
      }
    } else {
      $("mav").innerHTML = availBadge(r);
      toast("Live check failed — try again shortly");
    }
  };
  // opening an unverified name IS intent to know it — fire the live check automatically
  if(!r.v && LIVE && CHECK_OK){
    setTimeout(()=>{ const b=$("mcheck"); if(b && !b.disabled) b.click(); }, 80);
  }
}
function closeModal(){ $("overlay").classList.remove("show"); }
document.addEventListener("keydown", e=>{ if(e.key==="Escape") closeModal(); if(e.key==="/" && document.activeElement!==$("search")){ e.preventDefault(); $("search").focus(); } });

function toast(msg){ const t=$("toast"); t.textContent=msg; t.style.display="block"; clearTimeout(t._h); t._h=setTimeout(()=>t.style.display="none",2200); }

/* ---------------- favourites ---------------- */
function toggleFav(n){ favs.has(n)? favs.delete(n):favs.add(n); saveFavs(); }

/* ---------------- events ---------------- */
$("rows").addEventListener("click", e=>{
  const tr = e.target.closest("tr"); if(!tr) return;
  const r = nameFind(tr.dataset.n); if(!r) return;
  if(e.target.dataset.act==="fav"){ toggleFav(r.n); render(); return; }
  openModal(r);
});
$("search").addEventListener("input", e=>{
  state.q = e.target.value.replace(/^@+/,"");
  state.shown = PAGE; render();
  clearTimeout(liveDeb);
  liveDeb = setTimeout(maybeLive, 1200);
});
$("sort").addEventListener("change", e=>{ state.sort=e.target.value; render(); });
$("loadmore").onclick = ()=>{ state.shown+=PAGE; render(); };
$("favbtn").onclick = e=>{ state.favOnly=!state.favOnly; e.currentTarget.classList.toggle("on",state.favOnly); state.shown=PAGE; render(); };
$("pokebtn").onclick = e=>{
  const on = !(state.cats.size===1 && state.cats.has(13));
  state.cats = new Set(); if(on) state.cats.add(13);
  e.currentTarget.classList.toggle("on", on);
  buildChips(); state.shown=PAGE; render();
};
$("dice").onclick = ()=>{ const l=filtered(); if(!l.length) return toast("Nothing to pick from"); openModal(l[Math.floor(Math.random()*l.length)]); };
$("export").onclick = ()=>{
  const l = sortList(filtered()).slice(0,5000);
  const csv = "username,availability,char_count,char_types,categories,rarity_score,rarity_tier,last_check\n"+l.map(r=>{
    const types=["letters", r.dig?"numbers":"", r.us?"underscore":"", r.hy?"hyphen":""].filter(Boolean).join(" ");
    const cats=[]; for(let i=0;i<CATS.length;i++) if((r.m&(1<<i)) && CATS[i]) cats.push(CATS[i]);
    return [r.n, AVAIL[r.a]+(r.v?" (live)":""), r.len, '"'+types+'"', '"'+cats.join("; ")+'"', r.s, TIERS[tierIdx(r.s)].k, relDays(r.d)].join(",");
  }).join("\n");
  const a=document.createElement("a");
  a.href=URL.createObjectURL(new Blob([csv],{type:"text/csv"}));
  a.download="psn-usernames.csv"; a.click(); URL.revokeObjectURL(a.href);
};
$("reset").onclick = ()=>{
  state.q=""; state.tiers.clear(); state.avails.clear(); state.cats.clear(); state.chars.clear();
  state.lenMin=3; state.lenMax=16; state.favOnly=false; state.verifiedOnly=false; state.gens.clear(); state.sort="score_desc"; state.shown=PAGE;
  $("search").value=""; $("sort").value="score_desc"; $("lenmin").value=3; $("lenmax").value=16;
  $("favbtn").classList.remove("on"); $("pokebtn").classList.remove("on"); buildChips(); render();
};

/* length */
$("lenmin").addEventListener("change", e=>{ state.lenMin=Math.max(3,Math.min(16,+e.target.value||3)); state.shown=PAGE; render(); });
$("lenmax").addEventListener("change", e=>{ state.lenMax=Math.max(3,Math.min(16,+e.target.value||16)); state.shown=PAGE; render(); });

/* chips */
function buildChips(){
  const tc=$("tierchips"); tc.innerHTML = TIERS.map((t,i)=>`<span class="chip" data-i="${i}">${t.k==="Common"?"Common":t.k+" tier"}</span>`).join("");
  [...tc.children].forEach(c=>c.onclick=()=>{ const i=+c.dataset.i; state.tiers.has(i)?state.tiers.delete(i):state.tiers.add(i); c.classList.toggle("on"); state.shown=PAGE; render(); });
  const ac=$("availchips"); ac.innerHTML = [[0,"Available"],[2,"Unknown"]].map(([i,a])=>`<span class="chip" data-i="${i}">${a}</span>`).join("");
  [...ac.children].forEach(c=>c.onclick=()=>{ const i=+c.dataset.i; state.avails.has(i)?state.avails.delete(i):state.avails.add(i); c.classList.toggle("on"); state.shown=PAGE; render(); });
  const cc=$("catchips"); cc.innerHTML = CATS.map((a,i)=>a?`<span class="chip" data-i="${i}">${a}</span>`:"").join("");
  [...cc.children].forEach(c=>c.onclick=()=>{ const i=+c.dataset.i; state.cats.has(i)?state.cats.delete(i):state.cats.add(i); c.classList.toggle("on"); state.shown=PAGE; render(); });
  const hc=$("charchips"); const CL=["Letters only","Has underscore","Has hyphen"]; const CK=["letters","underscore","hyphen"];
  hc.innerHTML = CL.map((a,i)=>`<span class="chip" data-k="${CK[i]}">${a}</span>`).join("");
  [...hc.children].forEach(c=>c.onclick=()=>{ const k=c.dataset.k; state.chars.has(k)?state.chars.delete(k):state.chars.add(k); c.classList.toggle("on"); state.shown=PAGE; render(); });
  const vc=$("verchip");
  vc.classList.toggle("on", state.verifiedOnly);
  vc.onclick=()=>{ state.verifiedOnly=!state.verifiedOnly; vc.classList.toggle("on",state.verifiedOnly); state.shown=PAGE; render(); };
  const gc=$("genchips");
  gc.innerHTML = [1,2,3,4,5,6,7,8,9].map(g=>`<span class="chip" data-g="${g}">Gen ${g}</span>`).join("");
  [...gc.children].forEach(c=>c.onclick=()=>{ const g=+c.dataset.g; state.gens.has(g)?state.gens.delete(g):state.gens.add(g); c.classList.toggle("on"); state.shown=PAGE; render(); });
}

/* ---------------- validator ---------------- */
function validate(){
  const v = $("vinput").value;
  const rules = [
    ["3–16 characters", v.length>=3 && v.length<=16],
    ["Starts with a letter", /^[A-Za-z]/.test(v)],
    ["Only letters, numbers, underscores, hyphens", /^[A-Za-z0-9_-]*$/.test(v)],
    ["No spaces", !/\s/.test(v)]
  ];
  $("vrules").innerHTML = rules.map(([txt,ok])=>`<li class="${ok?"ok":"bad"}">${ok?"✓":"✗"} ${txt}</li>`).join("");
  const all = rules.every(r=>r[1]);
  const el = $("vverdict");
  el.className = "vverdict "+(v? (all?"ok":"bad"):"");
  el.textContent = v? (all? "Valid PSN Online ID format" : "Not valid — see failed rules") : "";
}
$("vinput").addEventListener("input", validate);

/* ---------------- live check (served mode via server.py) ---------------- */
const LIVE = location.protocol === "http:" || location.protocol === "https:";
let NET_OK = true, netFails = 0;            // sync/updates stream health
let CHECK_OK = true, checkFails = 0;        // live-check endpoint health (separate: hosted mirrors may have check but no scanner stream)
const WHYIDX = {available:1, taken:2, blocked:3, reserved3:4, reserved:5};
let liveStore = {};
try{ liveStore = JSON.parse(localStorage.getItem("psnlive")||"{}"); }catch(e){}
for(const k of Object.keys(liveStore)) if(/\d/.test(k)) delete liveStore[k];
const saveLive = ()=>{ try{ localStorage.setItem("psnlive", JSON.stringify(liveStore)); }catch(e){} };
const liveAsked = new Set();
let liveT = null, liveDeb = null, bulkSync = false;

function livebar(html, sticky){
  const b = $("livebar"); if(!b) return;
  b.innerHTML = html; b.classList.add("show");
  clearTimeout(liveT);
  if(!sticky) liveT = setTimeout(()=>b.classList.remove("show"), 9000);
}
/* provisional score/mask for names the DB never had — build.py rescores properly on rebuild */
function quickScore(n){
  let s = {3:64,4:52,5:46,6:40,7:34,8:30,9:26,10:22,11:18,12:15,13:13,14:11,15:10,16:9}[n.length]||9;
  const vow = (n.match(/[aeiou]/g)||[]).length;
  if(lettersOnly(n) && vow>0 && vow/n.length>=0.2 && vow/n.length<=0.6) s += 8;
  if(/(.)\1\1/.test(n)) s += 5;
  for(const c of new Set(n)) if("qzxj".includes(c)) s -= 4;
  if(/\d/.test(n)) s -= 18; if(n.includes("_")) s -= 14; if(n.includes("-")) s -= 12;
  return Math.max(1, Math.min(99, s));
}
function quickMask(n){
  let m = n.length===3?1 : n.length===4?2 : n.length===5?4 : 8;
  if(/\d/.test(n)) m |= 1<<8;
  if(/(.)\1\1/.test(n) || /^(..+)\1+$/.test(n)) m |= 1<<9;
  const vow = (n.match(/[aeiou]/g)||[]).length;
  if(lettersOnly(n) && vow/n.length>=0.2 && vow/n.length<=0.6) m |= 1<<7; else m |= 1<<12;
  return m;
}
function applyLive(name, j){
  if(/\d/.test(name)){                        // never list / store numbered IDs
    delete liveStore[name];
    const ex = nameFind(name); if(ex) ex.dropped = 1;
    return null;
  }
  const w = WHYIDX[j.why]||0, d = Math.max(0, Math.floor((Date.now()/1000 - j.ts)/86400));
  let r = nameFind(name);
  if(j.a === 1){                                  // taken / blocked / reserved -> never listed
    if(r && !r.dropped){ r.dropped = 1; }         // corpse stays indexed so a flip can resurrect it
    TAKENIDX.set(name, {w, ts:j.ts});
    liveStore[name] = {a:1, w, ts:j.ts, ck:j.n||1};
    if(!bulkSync) saveLive();
    return null;
  }
  if(r){ if(r.dropped){ delete r.dropped; NAMEIDX.set(name, r); } r.a=0; r.v=1; r.w=w; r.ck=j.n||1; r.d=d; }
  else { r = {n:name, s:quickScore(name), m:quickMask(name), a:0, d, v:1, w, ck:j.n||1,
              len:name.length, dig:/\d/.test(name), us:name.includes("_"), hy:name.includes("-")};
         ALL.push(r); NAMEIDX.set(name, r); }
  TAKENIDX.delete(name);
  liveStore[name] = {a:0, w, ts:j.ts, ck:j.n||1, s:r.s, m:r.m};
  if(!bulkSync) saveLive();
  return r;
}
function rehydrateLive(){
  for(const name of Object.keys(liveStore)){
    if(/\d/.test(name)){ delete liveStore[name]; continue; }
    const rec = liveStore[name];
    if(!rec || rec.a===undefined || !rec.ts) continue;
    const d = Math.max(0, Math.floor((Date.now()/1000 - rec.ts)/86400));
    let r = nameFind(name);
    if(rec.a === 1){                              // taken -> registry only, drop any listed row
      if(r && !r.dropped){ r.dropped = 1; }
      TAKENIDX.set(name, {w: rec.w, ts: rec.ts});
      continue;
    }
    if(r){ if(!r.v){ if(r.dropped){ delete r.dropped; } r.a=rec.a; r.v=1; r.w=rec.w; r.ck=rec.ck; r.d=d; } }
    else { const nr = {n:name, s:rec.s||quickScore(name), m:rec.m||quickMask(name), a:rec.a, d,
                   v:1, w:rec.w, ck:rec.ck, len:name.length,
                   dig:/\d/.test(name), us:name.includes("_"), hy:name.includes("-")};
           ALL.push(nr); NAMEIDX.set(name, nr); }
  }
}
const _pollers = new Map();
function pollQueued(name){
  if(!name || _pollers.has(name)) return;
  let n = 0;
  const id = setInterval(async ()=>{
    n++;
    if(n > 18){ clearInterval(id); _pollers.delete(name); return; }
    try{
      const j = await fetch("/api/check?onlineId=" + encodeURIComponent(name)).then(x=>x.json());
      if(!(j && j.ok)) return;
      clearInterval(id); _pollers.delete(name);
      applyLive(name, j);
      const r = nameFind(name);
      const mav = $("mav"); if(mav && r) mav.innerHTML = availBadge(r);
      const md = $("mdays"); if(md) md.textContent = "just now";
      toast(j.a===0 ? `“${name}” is AVAILABLE on Sony's endpoint ✓` : `Sony says: ${j.why}`);
      render();
    }catch(e){}
  }, 10000);
  _pollers.set(name, id);
}
async function liveCheck(name){
  if(!LIVE || liveAsked.has(name)) return null;
  liveAsked.add(name);
  try{
    const resp = await fetch("/api/check?onlineId=" + encodeURIComponent(name));
    const j = await resp.json();
    if(!j.ok){
      liveAsked.delete(name);
      livebar(`<span>${j.error==="cooldown"
        ? ((j.queued || (j.retry_after||0) >= 90)
            ? `Sony blocks Cloudflare from this edge — queued for the off-CF scanner (usually under 2 min).`
            : `Rate-limited (~${j.retry_after||60}s) — try another name or wait a moment.`)
        : `Live check failed (${j.error||("http "+resp.status)}) — try again shortly.`}</span>`,
        !!(j && (j.queued || (j.retry_after||0) >= 90)));
      if(j && (j.queued || (j.retry_after||0) >= 90)) pollQueued(name);
      return null;
    }
    checkFails = 0; CHECK_OK = true;
    const r = applyLive(name, j);
    const wIdx = (WHYIDX[j.why]===4 && name.length>3) ? 5 : WHYIDX[j.why];
    const badge = j.a===0
      ? `<span class="badge b-avail"><span class="dot"></span>AVAILABLE ✓</span>`
      : `<span class="badge b-taken"><span class="dot"></span>${WHY[wIdx]||"Taken"}</span>`;
    livebar(`<span>⚡ <b class="mono">${name}</b> ${j.cached?"is already live-verified":"just checked against Sony"} —</span>${badge}${r?`<button class="btn" id="lbopen">Open details</button>`:""}`, true);
    const lb = $("lbopen"); if(lb && r) lb.onclick = ()=>openModal(r);
    render();
    return r;
  }catch(e){
    checkFails++; CHECK_OK = checkFails < 2;
    liveAsked.delete(name);
    livebar(`<span>Live check unreachable — this deployment has no check API (static mirror/preview), or the network blocked it. Run <code>python3 server.py</code> for the full app.</span>`);
    return null;
  }
}
function maybeLive(){
  const name = state.q.trim().toLowerCase().replace(/^@+/,"").replace(/\s+/g,"");
  if(!/^[a-z][a-z0-9_\-]{2,15}$/.test(name)) return;
  const r = nameFind(name);
  if(r && r.v && !r.dropped) return;
  const t = TAKENIDX.get(name);
  if(t){
    livebar(`<span>⚡ <b class="mono">${name}</b> was live-verified ${takenDays(t)}:</span><span class="badge b-taken"><span class="dot"></span>${WHY[(t.w===4&&name.length>3)?5:t.w]||"Taken"}</span><span style="color:var(--muted)">(removed from the catalogue, kept on record)</span>`, true);
    return;
  }
  if(!LIVE || !CHECK_OK){
    livebar(`<span>“${name}” isn't in the offline index, and this deployment has no live-check API to ask Sony. Run the full app (<code>python3 server.py</code>) or a mirror with <code>/api/check</code> (see deploy/HOSTING.md).</span>`);
    return;
  }
  liveCheck(name);
}

/* ---------------- background sync ---------------- */
const BUILT_AT = __BUILDTS__;
let refreshMs = 60000;
try{ refreshMs = JSON.parse(localStorage.getItem("psnrefresh")||"60000"); }catch(e){}
let lastSync = BUILT_AT;
for(const k in liveStore){ const t = liveStore[k] && liveStore[k].ts; if(t && t>lastSync) lastSync = t; }
let syncTimer = null, syncBusy = false;
function setSync(t){ const el = $("syncstat"); if(el) el.textContent = t; }
function trimLive(){
  const ks = Object.keys(liveStore);
  if(ks.length <= 20000) return;
  ks.sort((a,b)=>(liveStore[a].ts||0)-(liveStore[b].ts||0));
  for(let i=0;i<ks.length-20000;i++) delete liveStore[ks[i]];
}
async function syncNow(){
  if(!LIVE || syncBusy) return;
  syncBusy = true;
  let total = 0;
  try{
    bulkSync = true;
    for(let round=0; round<30; round++){
      const j = await fetch("/api/updates?since=" + lastSync).then(r=>r.json());
      if(!j || !j.ok) break;
      const rows = j.rows || [];
      for(const x of rows){ applyLive(x.nm, x); if(x.ts > lastSync) lastSync = x.ts; }
      total += rows.length;
      if(!j.more || !rows.length) break;
    }
    bulkSync = false; saveLive(); trimLive(); saveLive();
    let tail = "";
    try{
      const s = await fetch("/api/stats").then(r=>r.json());
      if(s && s.ok && s.scan_left != null) tail = ` · ${s.scan_left.toLocaleString()} left`;
    }catch(e){}
    if(total){ render(); setSync(`⟳ ${total.toLocaleString()} new verification${total>1?"s":""}${tail}`); }
    else setSync(`⟳ synced just now${tail}`);
  }catch(e){ bulkSync = false; netFails++; NET_OK = netFails < 2; setSync(NET_OK ? "⟳ sync offline" : "⟳ offline — open the hosted app for live sync"); }
  syncBusy = false;
}
function armSync(){
  clearInterval(syncTimer); syncTimer = null;
  if(LIVE && +refreshMs > 0) syncTimer = setInterval(syncNow, +refreshMs);
}

/* ---------------- init ---------------- */
function setHeadOffset(){
  const tb = document.querySelector(".toolbar");
  if(tb) document.documentElement.style.setProperty("--thtop", tb.offsetHeight + "px");
}
addEventListener("resize", setHeadOffset);
rehydrateLive(); buildChips(); render(); setHeadOffset(); setTimeout(setHeadOffset, 300);
const rsel = $("refresh");
if(rsel){
  const opts = [0, 30000, 60000, 300000];
  if(!opts.includes(+refreshMs)) refreshMs = 60000;
  rsel.value = String(refreshMs);
  rsel.onchange = ()=>{
    refreshMs = +rsel.value;
    try{ localStorage.setItem("psnrefresh", String(refreshMs)); }catch(e){}
    armSync();
    if(+refreshMs > 0) syncNow();
  };
}
armSync();
if(LIVE){ setSync("⟳ connecting…"); setTimeout(syncNow, 2000); }
else setSync("file mode — run server.py for live sync + checks");
</script>
</body>
</html>
"""

_wf = os.path.join(HERE, "assets", "field.jpg")
WALL64 = base64.b64encode(open(_wf, "rb").read()).decode() if os.path.exists(_wf) else ""
html = TEMPLATE.replace("__DATA__", DATA).replace("__TAKEN__", TAKEN_DATA).replace("__GENDATE__", GEN_DATE).replace("__BUILDTS__", str(int(datetime.datetime.now().timestamp()))).replace("__WALLPAPER__", WALL64)
with open("index.html", "w") as f:
    f.write(html)
print(f"wrote index.html ({len(html)//1024} KB)")
