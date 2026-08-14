declare module enums {
    export enum MessageType {
        Regular = 0,
        System = 1,
        Emote = 2,
        Limit3Spell = 3,// Sphere style shards use this to limit to 3 of these message types showing overhead.
        Label = 6,
        Focus = 7,
        Whisper = 8,
        Yell = 9,
        Spell = 10,
        Guild = 13,
        Alliance = 14,
        Command = 15,
        Encoded = 192,
        UOChat = 254,// web client related
        Party = 255
    }
}
declare module enums {
    export enum Abilities {
        Invalid = 255,
        None = 0,
        ArmorIgnore = 1,
        BleedAttack = 2,
        ConcussionBlow = 3,
        CrushingBlow = 4,
        Disarm = 5,
        Dismount = 6,
        DoubleStrike = 7,
        InfectiousStrike = 8,
        MortalStrike = 9,
        MovingShot = 10,
        ParalyzingBlow = 11,
        ShadowStrike = 12,
        WhirlwindAttack = 13,
        RidingSwipe = 14,
        FrenziedWhirlwind = 15,
        Block = 16,
        DefenseMastery = 17,
        NerveStrike = 18,
        TalonStrike = 19,
        Feint = 20,
        DualWield = 21,
        DoubleShot = 22,
        ArmorPierce = 23,
        Bladeweave = 24,
        ForceArrow = 25,
        LightningArrow = 26,
        PsychicAttack = 27,
        SerpentArrow = 28,
        ForceOfNature = 29,
        InfusedThrow = 30,
        MysticArc = 31
    }
    export enum Virtues {
        Honor = 1,
        Sacrifice = 2,
        Valor = 3
    }
}
declare module enums {
    export enum BuffDebuffs {
        DismountPrevention = 1001,
        NoRearm = 1002,
        NightSight = 1005,//*
        DeathStrike = 1006,
        EvilOmen = 1007,
        HonoredDebuff = 1008,
        AchievePerfection = 1009,
        DivineFury = 1010,//*
        EnemyOfOne = 1011,//*
        HidingAndOrStealth = 1012,//*
        ActiveMeditation = 1013,//*
        BloodOathCaster = 1014,//*
        BloodOathCurse = 1015,//*
        CorpseSkin = 1016,//*
        Mindrot = 1017,//*
        PainSpike = 1018,//*
        Strangle = 1019,
        GiftOfRenewal = 1020,//*
        AttuneWeapon = 1021,//*
        Thunderstorm = 1022,//*
        EssenceOfWind = 1023,//*
        EtherealVoyage = 1024,//*
        GiftOfLife = 1025,//*
        ArcaneEmpowerment = 1026,//*
        MortalStrike = 1027,
        ReactiveArmor = 1028,//*
        Protection = 1029,//*
        ArchProtection = 1030,
        MagicReflection = 1031,//*
        Incognito = 1032,//*
        Disguised = 1033,
        AnimalForm = 1034,
        Polymorph = 1035,
        Invisibility = 1036,//*
        Paralyze = 1037,//*
        Poison = 1038,
        Bleed = 1039,
        Clumsy = 1040,//*
        FeebleMind = 1041,//*
        Weaken = 1042,//*
        Curse = 1043,//*
        MassCurse = 1044,
        Agility = 1045,//*
        Cunning = 1046,//*
        Strength = 1047,//*
        Bless = 1048,//*
        Sleep = 1049,
        StoneForm = 1050,
        SpellPlague = 1051,
        Berserk = 1052,
        MassSleep = 1053,
        Fly = 1054,
        Inspire = 1055,
        Invigorate = 1056,
        Resilience = 1057,
        Perseverance = 1058,
        TribulationTarget = 1059,
        DespairTarget = 1060,
        FishPie = 1062,
        HitLowerAttack = 1063,
        HitLowerDefense = 1064,
        DualWield = 1065,
        Block = 1066,
        DefenseMastery = 1067,
        DespairCaster = 1068,
        Healing = 1069,
        SpellFocusingBuff = 1070,
        SpellFocusingDebuff = 1071,
        RageFocusingDebuff = 1072,
        RageFocusingBuff = 1073,
        Warding = 1074,
        TribulationCaster = 1075,
        ForceArrow = 1076,
        Disarm = 1077,
        Surge = 1078,
        Feint = 1079,
        TalonStrike = 1080,
        PsychicAttack = 1081,
        ConsecrateWeapon = 1082,
        GrapesOfWrath = 1083,
        EnemyOfOneDebuff = 1084,
        HorrificBeast = 1085,
        LichForm = 1086,
        VampiricEmbrace = 1087,
        CurseWeapon = 1088,
        ReaperForm = 1089,
        ImmolatingWeapon = 1090,
        Enchant = 1091,
        HonorableExecution = 1092,
        Confidence = 1093,
        Evasion = 1094,
        CounterAttack = 1095,
        LightningStrike = 1096,
        MomentumStrike = 1097,
        OrangePetals = 1098,
        RoseOfTrinsic = 1099,
        PoisonImmunity = 1100,
        Veterinary = 1101,
        Perfection = 1102,
        Honored = 1103,
        ManaPhase = 1104,
        FanDancerFanFire = 1105,
        Rage = 1106,
        Webbing = 1107,
        MedusaStone = 1108,
        TrueFear = 1109,
        AuraOfNausea = 1110,
        HowlOfCacophony = 1111,
        GazeDespair = 1112,
        HiryuPhysicalResistance = 1113,
        RuneBeetleCorruption = 1114,
        BloodwormAnemia = 1115,
        RotwormBloodDisease = 1116,
        SkillUseDelay = 1117,
        FactionStatLoss = 1118,
        HeatOfBattleStatus = 1119,
        CriminalStatus = 1120,
        ArmorPierce = 1121,
        SplinteringEffect = 1122,
        SwingSpeedDebuff = 1123,
        WraithForm = 1124,
        CityTradeDeal = 1126,
        HumilityDebuff = 1127,
        Spirituality = 1128,
        Humility = 1129,
        Rampage = 1130,
        Stagger = 1131,// Debuff
        Toughness = 1132,
        Thrust = 1133,
        Pierce = 1134,// Debuff
        PlayingTheOdds = 1135,
        FocusedEye = 1136,
        Onslaught = 1137,// Debuff
        ElementalFury = 1138,
        ElementalFuryDebuff = 1139,// Debuff
        CalledShot = 1140,
        Knockout = 1141,
        SavingThrow = 1142,
        Conduit = 1143,
        EtherealBurst = 1144,
        MysticWeapon = 1145,
        ManaShield = 1146,
        AnticipateHit = 1147,
        Warcry = 1148,
        Shadow = 1149,
        WhiteTigerForm = 1150,
        Bodyguard = 1151,
        HeightenedSenses = 1152,
        Tolerance = 1153,
        DeathRay = 1154,
        DeathRayDebuff = 1155,
        Intuition = 1156,
        EnchantedSummoning = 1157,
        ShieldBash = 1158,
        Whispering = 1159,
        CombatTraining = 1160,
        InjectedStrikeDebuff = 1161,
        InjectedStrike = 1162,
        UnknownTomato = 1163,
        PlayingTheOddsDebuff = 1164,
        DragonTurtleDebuff = 1165,
        Boarding = 1166,
        Potency = 1167,
        ThrustDebuff = 1168,
        FistsOfFury = 1169,// 1169
        BarrabHemolymphConcentrate = 1170,
        JukariBurnPoiltice = 1171,
        KurakAmbushersEssence = 1172,
        BarakoDraftOfMight = 1173,
        UraliTranceTonic = 1174,
        SakkhraProphylaxis = 1175,// 1175
        Sparks = 1176,
        Swarm = 1177,
        BoneBreaker = 1178,
        Unknown2 = 1179,
        SwarmImmune = 1180,
        BoneBreakerImmune = 1181,
        UnknownGoblin = 1182,
        UnknownRedDrop = 1183,
        UnknownStar = 1184,
        FeintDebuff = 1185,
        CaddelliteInfused = 1186,
        PotionGloriousFortune = 1187,
        MysticalPolymorphTotem = 1188,
        UnknownDebuff = 1189
    }
}
declare module enums {
    export enum Constant {
        WorldSerial = 4294967295
    }
}
declare module enums {
    export enum Directions {
        North = 0,
        Right = 1,
        East = 2,
        Down = 3,
        South = 4,
        Left = 5,
        West = 6,
        Up = 7
    }
}
declare module enums {
    export enum SearchEntityOptions {
        Any = 1,
        Enemy = 2,
        Murderer = 4,
        Criminal = 8,
        Gray = 16,
        Innocent = 32,
        Unfriendly = 64,
        Friend = 128,
        Invulnerable = 256
    }
    export enum SearchEntityRangeOptions {
        Next = 0,
        Previous = 1,
        Nearest = 2,
        Closest = 3
    }
    export enum SearchEntityTypeOptions {
        Any = 0,
        Human = 1,
        NonHuman = 2
    }
}
declare module enums {
    export enum Layers {
        Invalid = 0,
        OneHanded = 1,
        TwoHanded = 2,
        Shoes = 3,
        Pants = 4,
        Shirt = 5,
        Helmet = 6,
        Gloves = 7,
        Ring = 8,
        Talisman = 9,
        Necklace = 10,
        Hair = 11,
        Waist = 12,
        Torso = 13,
        Bracelet = 14,
        Face = 15,
        Beard = 16,
        Tunic = 17,
        Earrings = 18,
        Arms = 19,
        Cloak = 20,
        Backpack = 21,
        Robe = 22,
        Skirt = 23,
        Legs = 24,
        Mount = 25,
        ShopBuyRestock = 26,
        ShopBuy = 27,
        ShopSell = 28,
        Bank = 29
    }
}
declare module enums {
    export enum Notorieties {
        Unknown = 0,
        Innocent = 1,
        Ally = 2,
        Gray = 3,
        Criminal = 4,
        Enemy = 5,
        Murderer = 6,
        Invulnerable = 7
    }
}
declare module enums {
    export enum Skills {
        Alchemy = 0,
        Anatomy = 1,
        AnimalLore = 2,
        ItemID = 3,
        ArmsLore = 4,
        Parry = 5,
        Begging = 6,
        Blacksmith = 7,
        Fletching = 8,
        Peacemaking = 9,
        Camping = 10,
        Carpentry = 11,
        Cartography = 12,
        Cooking = 13,
        DetectHidden = 14,
        Discordance = 15,
        EvalInt = 16,
        Healing = 17,
        Fishing = 18,
        Forensics = 19,
        Herding = 20,
        Hiding = 21,
        Provocation = 22,
        Inscribe = 23,
        Lockpicking = 24,
        Magery = 25,
        MagicResist = 26,
        Tactics = 27,
        Snooping = 28,
        Musicianship = 29,
        Poisoning = 30,
        Archery = 31,
        SpiritSpeak = 32,
        Stealing = 33,
        Tailoring = 34,
        AnimalTaming = 35,
        TasteID = 36,
        Tinkering = 37,
        Tracking = 38,
        Veterinary = 39,
        Swords = 40,
        Macing = 41,
        Fencing = 42,
        Wrestling = 43,
        Lumberjacking = 44,
        Mining = 45,
        Meditation = 46,
        Stealth = 47,
        RemoveTrap = 48,
        Necromancy = 49,
        Focus = 50,
        Chivalry = 51,
        Bushido = 52,
        Ninjitsu = 53,
        Spellweaving = 54,
        Mysticism = 55,
        Imbuing = 56,
        Throwing = 57
    }
    export enum SkillLock {
        Up = 0,
        Down = 1,
        Locked = 2
    }
}
declare module enums {
    export enum Spells {
        Clumsy = 1,
        CreateFood = 2,
        Feeblemind = 3,
        Heal = 4,
        MagicArrow = 5,
        NightSight = 6,
        ReactiveArmor = 7,
        Weaken = 8,
        Agility = 9,
        Cunning = 10,
        Cure = 11,
        Harm = 12,
        MagicTrap = 13,
        RemoveTrap = 14,
        Protection = 15,
        Strength = 16,
        Bless = 17,
        Fireball = 18,
        MagicLock = 19,
        Poison = 20,
        Telekinesis = 21,
        Teleport = 22,
        Unlock = 23,
        WallOfStone = 24,
        ArchCure = 25,
        ArchProtection = 26,
        Curse = 27,
        FireField = 28,
        GreaterHeal = 29,
        Lightning = 30,
        ManaDrain = 31,
        Recall = 32,
        BladeSpirits = 33,
        DispelField = 34,
        Incognito = 35,
        MagicReflect = 36,
        MindBlast = 37,
        Paralyze = 38,
        PoisonField = 39,
        SummonCreature = 40,
        Dispel = 41,
        EnergyBolt = 42,
        Explosion = 43,
        Invisibility = 44,
        Mark = 45,
        MassCurse = 46,
        ParalyzeField = 47,
        Reveal = 48,
        ChainLightning = 49,
        EnergyField = 50,
        FlameStrike = 51,
        GateTravel = 52,
        ManaVampire = 53,
        MassDispel = 54,
        MeteorSwarm = 55,
        Polymorph = 56,
        Earthquake = 57,
        EnergyVortex = 58,
        Resurrection = 59,
        AirElemental = 60,
        SummonDaemon = 61,
        EarthElemental = 62,
        FireElemental = 63,
        WaterElemental = 64,
        AnimateDead = 101,
        BloodOath = 102,
        CorpseSkin = 103,
        CurseWeapon = 104,
        EvilOmen = 105,
        HorrificBeast = 106,
        LichForm = 107,
        MindRot = 108,
        PainSpike = 109,
        PoisonStrike = 110,
        Strangle = 111,
        SummonFamiliar = 112,
        VampiricEmbrace = 113,
        VengefulSpirit = 114,
        Wither = 115,
        WraithForm = 116,
        Exorcism = 117,
        CleanseByFire = 201,
        CloseWounds = 202,
        ConsecrateWeapon = 203,
        DispelEvil = 204,
        DivineFury = 205,
        EnemyOfOne = 206,
        HolyLight = 207,
        NobleSacrifice = 208,
        RemoveCurse = 209,
        SacredJourney = 210,
        HonorableExecution = 401,
        Confidence = 402,
        Evasion = 403,
        CounterAttack = 404,
        LightningStrike = 405,
        MomentumStrike = 406,
        FocusAttack = 501,
        DeathStrike = 502,
        AnimalForm = 503,
        KiAttack = 504,
        SurpriseAttack = 505,
        Backstab = 506,
        Shadowjump = 507,
        MirrorImage = 508,
        ArcaneCircle = 601,
        GiftOfRenewal = 602,
        ImmolatingWeapon = 603,
        Attunement = 604,
        Thunderstorm = 605,
        NaturesFury = 606,
        SummonFey = 607,
        SummonFiend = 608,
        ReaperForm = 609,
        Wildfire = 610,
        EssenceOfWind = 611,
        DryadAllure = 612,
        EtherealVoyage = 613,
        WordOfDeath = 614,
        GiftOfLife = 615,
        ArcaneEmpowerment = 616,
        NetherBolt = 678,
        HealingStone = 679,
        PurgeMagic = 680,
        Enchant = 681,
        Sleep = 682,
        EagleStrike = 683,
        AnimatedWeapon = 684,
        StoneForm = 685,
        SpellTrigger = 686,
        MassSleep = 687,
        CleansingWinds = 688,
        Bombard = 689,
        SpellPlague = 690,
        HailStorm = 691,
        NetherCyclone = 692,
        RisingColossus = 693,
        Inspire = 701,
        Invigorate = 702,
        Resilience = 703,
        Perseverance = 704,
        Tribulation = 705,
        Despair = 706,
        DeathRay = 707,
        EtherealBurst = 708,
        NetherBlast = 709,
        MysticWeapon = 710,
        CommandUndead = 711,
        Conduit = 712,
        ManaShield = 713,
        SummonReaper = 714,
        EnchantedSummoning = 715,
        AnticipateHit = 716,
        Warcry = 717,
        Intuition = 718,
        Rejuvenate = 719,
        HolyFist = 720,
        Shadow = 721,
        WhiteTigerForm = 722,
        FlamingShot = 723,
        PlayingTheOdds = 724,
        Thrust = 725,
        Pierce = 726,
        Stagger = 727,
        Toughness = 728,
        Onslaught = 729,
        FocusedEye = 730,
        ElementalFury = 731,
        CalledShot = 732,
        WarriorsGifts = 733,
        ShieldBash = 734,
        Bodyguard = 735,
        HeightenSenses = 736,
        Tolerance = 737,
        InjectedStrike = 738,
        Potency = 739,
        Rampage = 740,
        FistsOfFury = 741,
        Knockout = 742,
        Whispering = 743,
        CombatTraining = 744,
        Boarding = 745
    }
}
declare module enums {
    export * from enums;
    export * from enums;
    export * from enums;
    export * from enums;
    export * from enums;
    export * from enums;
    export * from enums;
    export * from enums;
    export * from enums;
    export * from enums;
}
declare module "GameObject" {
    import type { Client } from "Client";
    export interface SerialObject {
        readonly serial: number;
    }
    export type SerialOrEntity = number | GameObject | SerialObject;
    export class GameObject implements SerialObject {
        /** @ignore */
        constructor(client: Client, serial: number);
        serial: number;
    }
}
declare module "Entity" {
    import { Client } from "Client";
    import { GameObject } from "GameObject";
    export class Entity extends GameObject {
        /** @ignore */
        constructor(client: Client, serial: number);
        /**
         * Gets the graphic id of the entity.
         * Returns 0 if entity is no longer on screen.
         * @example
         *
         * ```ts
         * console.log(player.graphic); // e.g. 400
         * ```
         */
        graphic: number;
        /**
         * Gets the current X coordinate of the entity.
         * Returns 0 if entity is no longer on screen.
         * @example
         *
         * ```ts
         * const entity = client.findObject(player); // Replace with any other entity serial
         * console.log(entity.x)
         * ```
         */
        x: number;
        /**
         * Gets the current Y coordinate of the entity.
         * Returns 0 if entity is no longer on screen.
         * @example
         *
         * ```ts
         * const entity = client.findObject(player);
         * console.log(entity.y)
         * ```
         */
        y: number;
        /**
         * Gets the current Z coordinate of the entity.
         * Returns 0 if entity is no longer on screen.
         * @example
         *
         * ```ts
         * const entity = client.findObject(player);
         * console.log(entity.z)
         * ```
         */
        z: number;
        /**
         * Gets the name of the entity.
         * Returns an empty string if not known to the client yet.
         * @example
         *
         * ```ts
         * const entity = client.findObject(player.equippedItems.robe);
         * if(entity) {
         *  console.log(entity.name);
         * }
         * ```
         */
        name: string;
        /**
         * Gets the hue/color of the entity.
         * Returns 0 if entity is no longer on screen.
         * @example
         *
         * ```ts
         * const entity = client.findObject(player.equippedItems.robe);
         * if(entity) {
         *  console.log(entity.name);
         * }
         * ```
         */
        hue: number;
        /**
         * Gets the hits of the entity.
         * Returns 0 if the client does not know (e.g. item.hits) or the entity is no longer on screen.
         * @example
         *
         * ```ts
         * const entity = client.findObject(0x991);
         * if(entity) {
         *  console.log(entity.hits);
         * }
         * ```
         */
        hits: number;
        /**
         * Gets the maxHits of the entity.
         * Returns 0 if the client does not know (e.g. item.maxHits) or the entity is no longer on screen.
         * @example
         *
         * ```ts
         * const entity = client.findObject(0x991);
         * if(entity) {
         *  console.log(entity.maxHits);
         * }
         * ```
         */
        maxHits: number;
        /**
         * Gets the direction of the entity as a number, if it has one.
         * Returns 0 if the client does not know (e.g. item.maxHits) or the entity is no longer on screen.
         *
         * Compare using the [Directions enum](../enums/#directions).
         *
         * @example
         *
         * ```ts
         * const entity = client.findObject(0x991);
         * if(entity) {
         *   if(entity.direction === Directions.North) {
         *     console.log(`${entity.name} is facing North`);
         *   }
         *   else {
         *     console.log(Directions[entity.direction]); // Prints the directions name, e.g. East
         *   }
         * }
         * ```
         */
        direction: number;
        isHidden: boolean;
    }
}
declare module "Item" {
    import { Layers } from enums;
    import { Client } from "Client";
    import { Entity } from "Entity";
    export class Item extends Entity {
        _tag: 'Item';
        /** @ignore */
        constructor(client: Client, serial: number);
        /**
         * Get the item's parent container
         * @example
         *
         * ```ts
         * const item = client.findType(axeType);
         * if (item.container > 0) {
         *    client.sysMsg("the item is into a container");
         * }
         * ```
         */
        container: number;
        /**
         * Get the item's amount
         * @example
         *
         * ```ts
         * const item = client.findObject(0x40001234);
         * if (item.amount > 5) {
         *    client.sysMsg("amount of ${item.amount}");
         * }
         * ```
         */
        amount: number;
        /**
         * Get the item's layer if any
         * @example
         *
         * ```ts
         * const robe = client.findItemOnLayer(player, Layers.Robe);
         * console.log(robe.layer);
         * ```
         */
        layer: Layers;
        /**
         * Get the item's contents
         * @example
         *
         * ```ts
         * const itemList = player.backpack.contents;
         * for (const item of itemlist) {
         *   if (item.contents.length > 0)
         *     console.log("this item is a backpack's sub-container!");
         * }
         *
         * ```
         */
        contents: Item[] | undefined;
    }
}
declare module "Mobile" {
    import { Notorieties } from enums;
    import { Client } from "Client";
    import { Entity } from "Entity";
    import { Item } from "Item";
    /**
     * The `Mobile` class represents a mobile entity in the ClassicUO web client, such as players, NPCs, or creatures.
     * Each mobile entity has attributes such as health, position and stat attributes.
     * @class Mobile
     */
    export class Mobile extends Entity {
        _tag: 'Mobile';
        /** @ignore */
        constructor(client: Client, serial: number);
        /**
         * The mobiles current stamina.
         * For the player it returns the real value, for other mobiles it is a scale of 1 to 100
         */
        stamina: number;
        /**
         * The mobiles maximum stamina.
         * For the player it returns the real value, for other mobiles it is a scale of 1 to 100
         */
        maxStamina: number;
        /**
         * The mobiles current mana.
         * For the player it returns the real value, for other mobiles it is a scale of 1 to 100
         */
        mana: number;
        /**
         * The mobiles maximum mana.
         * For the player it returns the real value, for other mobiles it is a scale of 1 to 100
         */
        maxMana: number;
        /**
         * Whether the mobile is poisoned (green hued)
         */
        isPoisoned: boolean;
        /**
         * Whether the mobiles status is yellow (i.e. Invulnerable)
         */
        isYellowHits: boolean;
        /**
         * Whether the mobile is female, or otherwise male.
         */
        isFemale: boolean;
        /**
         * The mobiles Notoriety, i.e. Innocent, Gray, etc.
         */
        notoriety: Notorieties;
        /**
         * Whether the mobile is currently in War Mode (humanoid)
         */
        inWarMode: boolean;
        /**
         * Whether the mobile is currently paralyzed.
         */
        isParalyzed: boolean;
        /**
         * Whether the mobile is dead
         */
        isDead: boolean;
        /**
         * Whether this mobile is likely a player character (excludes NPCs, pets, guards).
         * Uses a heuristic based on body type, pet status, notoriety, and equipment.
         */
        isPlayer: boolean;
        /**
         * Whether this mobile has a human, elf, or gargoyle body graphic.
         */
        isHuman: boolean;
        /**
         * Whether this mobile can be renamed (true for pets/followers).
         */
        isRenamable: boolean;
        /**
         * The currently equipped items of the mobile (humanoid/players)
         */
        equippedItems: {
            shirt?: Item;
            pants?: Item;
            shoes?: Item;
            legs?: Item;
            torso?: Item;
            ring?: Item;
            talisman?: Item;
            bracelet?: Item;
            face?: Item;
            arms?: Item;
            gloves?: Item;
            skirt?: Item;
            tunic?: Item;
            robe?: Item;
            necklace?: Item;
            hair?: Item;
            waist?: Item;
            beard?: Item;
            earrings?: Item;
            oneHanded?: Item;
            helmet?: Item;
            twoHanded?: Item;
            cloak?: Item;
            mount?: Item;
        };
    }
}
declare module "Player" {
    import { Abilities, BuffDebuffs, Directions, Layers, SkillLock, Skills, Spells, Virtues } from enums;
    import { Client } from "Client";
    import { SerialOrEntity } from "GameObject";
    import { Item } from "Item";
    import { Mobile } from "Mobile";
    /**
     * This class references the current player whilst in-game and is accessible on the global scope as the `player` variable.
     *
     * @example A simple script which yells out when the player health is below a threshold
     *
     * ```ts
     * while(true) {
     *  if(player.hits < 50) {
     *    player.say('I need healing!');
     *  }
     *  sleep(500);
     * }
     * ```
     */
    export class Player extends Mobile {
        /** @ignore */
        constructor(client: Client);
        map: number;
        /**
         * Sends a chat message as your player, with an optional hue for the message.
         *
         * @example
         *
         * ```ts
         * player.say('Hello there!');
         * ```
         */
        say(message: string, hue?: number): void;
        /**
         * Casts a spell
         *
         * @example
         *
         * ```ts
         * player.cast(Spells.Agility);
         * target.wait();
         * target.entity(player);
         * ```
         */
        cast(spell: Spells | string): void;
        /**
         * Casts a spell and automatically targets the given serial on the next target
         *
         * @example
         *
         * ```ts
         * player.castTo(Spells.Heal, player);
         * ```
         */
        castTo(spell: Spells | keyof typeof Spells, serial: SerialOrEntity, timeout?: number): void;
        /**
         * Uses a skill
         *
         * @example Use skill without a target
         *
         * ```ts
         * player.useSkill(Skills.Meditation);
         *
         * @example Use skill and target yourself
         *
         * ```ts
         * player.useSkill(Skills.Anatomy);
         * ```
         */
        useSkill(skill: Skills | keyof typeof Skills, target?: SerialOrEntity, timeout?: number): void;
        /**
         * Uses a virtue
         *
         * @example Use virtue without a target
         *
         * ```ts
         * player.useVirtue(Virtues.Honor);
         *
         * @example Use virtue and target yourself
         *
         * ```ts
         * player.useVirtue(Virtues.Honor);
         * ```
         */
        useVirtue(virtue: Virtues | keyof typeof Virtues, target?: SerialOrEntity, timeout?: number): void;
        /**
         * Attempts to equip an item if possible
         *
         * @example
         *
         * ```ts
         * const axe = client.findType(0x0F49); // Axe graphic ID
         * player.equip(axe);
         * ```
         */
        equip(serial: SerialOrEntity): void;
        /**
         * Attacks a mobile
         *
         * @example
         *
         * ```ts
         * player.attack(target.lastSerial);
         * ```
         */
        attack(serial: SerialOrEntity): void;
        /**
         * Attempt to fly... if you can.
         *
         * @example
         *
         * ```ts
         * player.fly();
         * ```
         */
        fly(): void;
        /**
         * Turn off flying and land
         *
         * @example
         *
         * ```ts
         * player.land();
         * ```
         */
        land(): void;
        /**
         * Toggles flying, provided you are a Gargoyle.
         * @example
         *
         * ```ts
         * player.toggleFlying();
         * ```
         */
        toggleFlying(): void;
        /**
         * Uses the item currently in your left-hand first, otherwise it will try the right.
         * @example
         *
         * ```ts
         * player.useItemInHand();
         * ```
         */
        useItemInHand(): void;
        /**
         * Uses the last object you double-clicked
         * @example
         *
         * ```ts
         * player.useLastObject();
         * ```
         */
        useLastObject(): void;
        /**
         * Uses any door directly in-front of where the player is facing
         * @example
         *
         * ```ts
         * player.openDoor();
         * ```
         */
        openDoor(): void;
        /**
         * Triggers the `Bow` emote
         * @example
         *
         * ```ts
         * player.bow();
         * ```
         */
        bow(): void;
        /**
         * Triggers the `Salute` emote
         * @example
         *
         * ```ts
         * player.salute();
         * ```
         */
        salute(): void;
        /**
         * Toggle War Mode
         * @example
         *
         * ```ts
         * player.toggleWarMode();
         * ```
         */
        toggleWarMode(): void;
        /**
         * Attempts to use an object if possible
         *
         * @example
         *
         * ```ts
         * const dagger = client.findType(0x0F52); // Dagger graphic ID
         * player.use(dagger);
         * ```
         */
        use(serial: SerialOrEntity): void;
        /**
         * Simulates clicking an object
         *
         * @example
         *
         * ```ts
         * player.click(player);
         * ```
         */
        click(serial: SerialOrEntity): void;
        /**
         * Attempts to use an object of a certain type
         *
         * @example
         *
         * ```ts
         * const myFriend = 0x217DED;
         * player.useType(0xE21); // Bandage type
         * target.wait(5000);
         * target.entity(myFriend);
         * ```
         */
        useType(graphic: number, hue?: number, sourceSerial?: SerialOrEntity, range?: number): boolean;
        /**
         * Attempts to move an object between containers
         *
         * @example
         *
         * ```ts
         * if(player.equippedItems.robe) {
         *   player.moveItem(player.equippedItems.robe, player.backpack);
         * }
         * ```
         */
        moveItem(serial: SerialOrEntity, container: SerialOrEntity, x?: number, y?: number, z?: number, amount?: number): number;
        /**
         * Attempts to move an object around on the ground using an offset
         *
         * @example
         *
         * ```ts
         * const targetInfo = target.queryTarget();
         * if(targetInfo) {
         *   player.moveItemOnGroundOffset(targetInfo, 1, 0, 0); // Move item to the east
         * }
         * ```
         */
        moveItemOnGroundOffset(serial: SerialOrEntity, x?: number, y?: number, z?: number, amount?: number): number;
        /**
         * Attempts to move an object of a certain type between containers
         *
         * @example
         *
         * ```ts
         * player.moveType(0x0F52, player.backpack, bag);
         * ```
         */
        moveType(graphic: number, src: SerialOrEntity, dest: SerialOrEntity, x?: number, y?: number, z?: number, hue?: number, amount?: number, range?: number): number;
        /**
         * Attempts to move an object of a certain type onto the ground
         *
         * @example
         *
         * ```ts
         * player.moveType(0x0F52, player.backpack); // Move item to the east
         * ```
         */
        moveTypeOnGroundOffset(graphic: number, src: SerialOrEntity, x?: number, y?: number, z?: number, hue?: number, amount?: number, range?: number): number;
        /**
         * Toggle ability on/off
         *
         * @example
         *
         * ```ts
         * player.setAbility(true, false); // Turn primary ability off
         * player.setAbility(false, true); // Turn secondary ability on
         * ```
         */
        setAbility(primary: boolean, active: boolean): void;
        /**
         * Walk/turn a single step in a direction
         * @return `True` if character can walk
         *
         * @example
         *
         * ```ts
         * player.walk(Directions.North);
         * ```
         */
        walk(direction: Directions): boolean;
        /**
         * Run/turn a single step in a direction
         * @return `True` if character can run
         * @example
         *
         * ```ts
         * player.run(Directions.South);
         * ```
         */
        run(direction: Directions): boolean;
        /**
         * Set the status of a skill lock
         *
         * @example
         *
         * ```ts
         * player.setSkillLock(Skills.Anatomy, SkillLock.Down);
         * ```
         */
        setSkillLock(skill: Skills, lock: SkillLock): void;
        /**
         * Gets an object containing the values of a skill.
         * The actual `value` of the skill is represented as an integer value with no decimal.
         * e.g. 74.6 would be 746
         *
         * @example
         *
         * ```ts
         * const anatomySkill = player.getSkill(Skills.Anatomy).value;
         * ```
         */
        getSkill(skill: Skills): {
            value: number;
            index: number;
            name: string;
            lock: number;
            base: number;
            cap: number;
            canBeUsable: boolean;
        } | undefined;
        /**
         * Gets an array of all the skill values
         *
         * @example
         *
         * ```ts
         * const skills = player.getSkills();
         * console.log(skills[0].value); // Print Alchemy skill value
         * ```
         */
        getAllSkills(): {
            value: number;
            index: number;
            name: string;
            lock: number;
            base: number;
            cap: number;
            canBeUsable: boolean;
        }[] | undefined;
        serial: number;
        coldResistance: number;
        damageIncrease: number;
        damageMax: number;
        damageMin: number;
        defenseChanceIncrease: number;
        dexterity: number;
        energyResistance: number;
        fasterCasting: number;
        fasterCastRecovery: number;
        fireResistance: number;
        followers: number;
        maxFollowers: number;
        gold: number;
        hitChanceIncrease: number;
        intelligence: number;
        lowerManaCost: number;
        lowerReagentCost: number;
        luck: number;
        maxColdResistence: number;
        maxDefenseChanceIncrease: number;
        maxEnergyResistence: number;
        maxFireResistence: number;
        maxPhysicResistence: number;
        maxPoisonResistence: number;
        physicalResistance: number;
        poisonResistance: number;
        spellDamageIncrease: number;
        statsCap: number;
        strength: number;
        swingSpeedIncrease: number;
        tithingPoints: number;
        weight: number;
        weightMax: number;
        primaryAbility: Abilities;
        secondaryAbility: Abilities;
        hasBuffDebuff(buffID: BuffDebuffs): boolean;
        waitForBuffDebuff(buffId: BuffDebuffs, timeoutMs?: number): boolean | null;
        backpack: Item | undefined;
        dressKr(items: Array<Item | number>): void;
        undressKr(layers: Layers[]): void;
    }
}



declare module "Skill" {
    export interface Skill {
        index: number;
        name: string;
        lock: number;
        value: number;
        base: number;
        cap: number;
        canBeUsable: boolean;
    }
}

declare module "WorldMap" {
    export interface WorldMapMarker {
        /**
         * Name of the marker
         */
        name: string;
        /**
         * X coordinate
         */
        x: number;
        /**
         * Y coordinate
         */
        y: number;
        /**
         * Map Index/Id to place the marker on
         */
        mapId: number;
        /**
         * ZoomLevel at which the marker appears
         */
        zoomLevel: number;
        /**
         * Color of the marker, e.g. "blue"
         */
        color: string;
        /**
         * Icon name for the marker (must exist in MapIcons folder)
         */
        markerIconName?: string;
    }
    export interface WorldMapMarkerPartial {
        name: string;
        x: number;
        y: number;
        mapId?: number;
        zoomLevel?: number;
        color?: string;
        markerIconName?: string;
    }
}
declare module "index" {
    export * from "WorldMap";
}
declare module "Gump" {
    import { VendorItem } from "ItemSchema";
    import { Client } from "Client";
    import { GameObject } from "GameObject";
    import { Mobile } from "Mobile";
    /**
     * This class is for interacting with Gumps that are sent to the client by the server.
     * Server gumps have a unique serial per shard, and can only have one open at a time.
     *
     * An instance of Gump therefore interacts with any gump of that serial, and it may become "invalid" if the gump closes externally (e.g. by the shard or the user)
     * You should always to validate the gump is still open by using `gump.exists` periodically.
     *
     * @example A simple script that waits for a Runebook gump before pressing one of the buttons
     *
     * ```ts
     * player.use(0x4021C7B1); // Runebook object serial
     * const gump = Gump.findOrWait(0x59, 1000); // Wait 1 second for the gump to appear
     * if(!gump) {
     *   exit("There's no gump open, is the runebook missing?");
     * }
     *
     * player.say("I'm outta here!");
     * gump.reply(10) // Press the first rune
     * ```
     */
    export class Gump extends GameObject {
        /** @ignore */
        private client;
        /** @ignore */
        private fromServer;
        /** @ignore */
        constructor(client: Client, serial: number, fromServer?: boolean);
        /**
         * Check if the gump is still open, i.e. the server hasn't closed it or the player.
         * @example
         *
         * ```ts
         * const gump = Gump.findOrWait(0xBB1B5472, 100);
         * if(!gump) {
         *   exit("There's no gump open!");
         * }
         *
         * // ... somewhere further down the script
         *
         * if(gump.exists) {
         *   console.log("The gump closed, did you do it?");
         * }
         * ```
         */
        exists: boolean;
        /**
         * Replies to a gump by "pressing" one of the buttons
         * @example
         *
         * ```ts
         * const gump = Gump.findOrWait(0xBB1B5472, 100);
         * if(gump?.containsText("Alchemy")) { // If there's a gump open with that serial, check if it has `Alchemy` in it.
         *   gump.reply(1); // Craft something
         * }
         * ```
         */
        reply(buttonID: number): void;
        /**
         * Closes the gump
         * @example Closes the last open gump if it has the word Chat in it.
         * ```ts
         * if(Gump.last?.containsText("Chat")) {
         *   gump.last?.close();
         * }
         * ```
         */
        close(): void;
        /**
         * Checks if the gump contains a certain string, case-insensitive.
         *
         * @example
         *
         * ```ts
         * const gump = Gump.findOrWait(0xBB1B5472, 100);
         * if(gump.containsText("Tailoring")) {
         *   player.say("I hate tailors");
         *   gump.close();
         * }
         * ```
         */
        containsText(value: string): boolean;
        /**
         * Checks if a gump with the provided server serial is open without making a new instance of `Gump`
         *
         * @example
         *
         * ```ts
         * if(Gump.exists(0xBB1B5472)) {
         *   player.say("My lovely lady gumps, check it out")
         * }
         * ```
         * @param serial
         */
        static exists(serial: number): boolean;
        /**
         * The server serial of the last gump sent by the server.
         * May no longer be open, check with `exists` first.
         *
         */
        static lastSerial: number;
        /**
         * Get a reference to the last Gump sent by the server.
         * Returns `undefined` if the gump is no longer open.
         *
         * @example Closes the last sent gump, if it's open.
         * ```ts
         * Gump.last?.close();
         * ```
         */
        static last: Gump | null;
        /**
         * Find a gump by its serial or containing certain text, or wait for it to appear
         * @param serialOrText
         * @param timeoutMs
         * @param fromServer
         *
         * @example Waits for the gump with the serial 0xBB1B5472 to open, and then presses a button.
         * ```ts
         * const gump = Gump.findOrWait(0xBB1B5472, 100); // Wait 100 milliseconds (5,000 if unspecified) for the gump to appear
         * if(gump) {
         *   gump.reply(1); // Gump is open, simulate pressing a button
         * }
         * ```
         * @example Waits for a gump to exist that contains the text "Blacksmithing", and then presses a button.
         * ```ts
         * const gump = Gump.findOrWait("Blacksmithy Selection Menu");
         * if(gump) {
         *   gump.reply(1); // Gump is open, simulate pressing a button
         * }
         * ```
         * @example Open the gump associated to a container object
         * ```ts
         * const bag = client.findObject(0x4021C7B1);
         * if (bag) {
         *  player.use(bag);
         *  const gump = Gump.findOrWait(bag, 1000, false); // That 'false' means 'Search for local gumps'. Default is 'true'
         *  if(gump) {
         *    client.sysMsg("gump found");
         *  }
         * }
         * ```
         */
        static findOrWait(serialOrText: number | string, timeoutMs?: number, fromServer?: boolean): Gump | undefined;
        /**
         * Closes all gumps that aren't the Top Bar, Buff bar, or the World view (radar)
         * Same as the `Close Gumps` hotkey
         * @example
         *
         * ```ts
         * Gump.closeAll();
         * ```
         */
        static closeAll(): void;
        /**
         * Checks if the gump has the button id.
         * Useful if you want to prevent clicking a button that doesn't exist.
         * @param id
         *
         * @example
         *
         * ```ts
         * const gump = Gump.findOrWait(0x59);
         * if(gump && gump.hasButton(10)) {
         *   gump.reply(10); // gump is open and has a button with id 10
         * }
         * ```
         */
        hasButton(id: number): boolean;
        /**
         * Attempts to switch the page if possible.
         *
         * @param page
         * @example
         *
         * ```ts
         * const gump = Gump.findOrWait(0x59);
         * gump?.switchPage(2); // if gump is open, try changing to page 2
         * ```
         */
        switchPage(page: number): void;
        /**
         * Check or uncheck a checkbox/radio button
         * @param serial
         * @param value
         * @example
         *
         * ```ts
         * const gump = Gump.findOrWait(0x59);
         * gump?.gumpSetCheckbox(serial, true); // if the gump is open, check the checkbox/radio control
         * gump?.reply(1); // Press a button to reply
         * ```
         */
        setCheckbox(serial: number, value: boolean): void;
        /**
         * Set the contents of a text entry in a gump
         * @param localSerial
         * @param value
         * @example
         *
         * ```ts
         * const gump = Gump.findOrWait(0x59);
         * gump?.setTextEntry(0x01, "Hello there"); // if the gump is open, set the text entries content
         * gump?.reply(1); // Press a button to reply
         * ```
         */
        setTextEntry(localSerial: number, value: string): void;
        /**
         * Select an item in the old-school T2A horizontal menu gump.
         * @param graphic
         * @param hue
         * @example
         *
         * ```ts
         * const gump = Gump.findOrWait(0x59);
         * if(gump) {
         *   console.log('Gump exists.');
         *   gump.horizontalMenuSelect(gump, )
         * }
         * ```
         */
        horizontalMenuSelect(graphic: number, hue?: number): void;
        /**
         * Returns the data for the last vendor buy gump seen
         * @example
         *
         * ```ts
         * const data = Gump.lastVendorBuyData;
         * if (data && data.type === 'buy') {
         *   // Lets buy all his ingots
         *   const ingots = data.items.filter(i => i.name.toLowerCase().includes('ingot'));
         *   client.sendBuyRequest(data.vendor, ingots);
         *   console.log('Bought items', ingots);
         * }
         * ```
         */
        static lastVendorBuyData: {
            type: 'buy';
            vendor: Mobile;
            items: VendorItem[];
        } | undefined;
        /**
         * Returns the data for the last vendor buy gump seen
         * @example
         *
         * ```ts
         * player.say('vendor sell');
         *
         * const data = Gump.lastVendorSellData;
         *
         * if (data && data.type === 'sell') { // Make sure we don't try to sell on a buy gump
         *   // Lets sell all our Tongs
         *   const tongs = data.items.filter(i => i.name.toLowerCase() === 'tongs');
         *   client.sendSellRequest(data.vendor, tongs);
         *   console.log('Sold items', tongs.map(i => i.name));
         * }
         * ```
         */
        static lastVendorSellData: {
            type: 'sell';
            vendor: Mobile;
            items: VendorItem[];
        } | undefined;
        /**
         * Waits for a vendor buy or sell gump to appear and returns the data.
         * Or if no gump appears it will time out returning `undefined`
         * @example
         *
         * ```ts
         * // Caution! This sells everything!
         * player.say('vendor sell');
         * const data = Gump.waitForVendorGumpData();
         *
         * if (data && data.type === 'sell') { // Check the gump is a sell
         *   client.sendSellRequest(data.vendor, data.items); // Sell ALL the items the vendor will take
         *   console.log('Sold items', data.items.map(i => i.name)); // Print what we sold
         * }
         * ```
         */
        static waitForVendorGumpData(timeoutMs?: number): {
            type: 'buy' | 'sell';
            vendor: Mobile;
            items: VendorItem[];
        } | undefined;
    }
}
declare module "IgnoreList" {
    import type { Client } from "Client";
    import { SerialOrEntity } from "GameObject";
    /**
     * The `IgnoreList` class manages a list of ignored entities within the ClassicUO web client.
     * Use this class to ignore certain entities (Items/Mobiles) from various search functions like `searchEntity` or `findType`
     *
     * @example
     *
     * ```ts
     *
     * let entity: Item | Mobile;
     * while(entity = client.findType(0xEED)) {
     *  console.log(`Found item: ${entity.serial}`);
     *  ignoreList.add(entity); // Add it to the ignoreList so it won't get picked next
     * }
     *
     * ignoreList.clear(); // Clear the list when we're done, this is cross-script
     * ```
     */
    export class IgnoreList {
        /** @ignore */
        constructor(client: Client);
        /**
         * Adds an item to the ignore list, causing functions like `findType` to ignore them.
         * @param serial
         * @returns `true` if the value was added, `false` if it already exists
         */
        add(serial: SerialOrEntity): boolean;
        /**
         * Removes an item from ignore list, allowing them to be found again.
         * @param serial
         * @returns `true` if the value was removed, `false` if it didn't exist
         */
        remove(serial: SerialOrEntity): boolean;
        /**
         * Whether the entity exists in the ignore list.
         * @param serial
         * @returns `true` if in the list or `false`
         */
        contains(serial: SerialOrEntity): boolean;
        /**
         * @returns a cloned list of the ignored serials
         */
        values: number[];
        /**
         * Replaces the current list with a new one
         * @param values
         */
        replace(values: number[]): void;
        /**
         * Clears the list
         */
        clear(): void;
    }
}
declare module "Journal" {
    import { Client } from "Client";
    export interface JournalEntry {
        serial: number;
        text: string;
        name: string;
        hue: number;
        type: 'Regular' | 'System' | 'Emote' | 'Limit3Spell' | 'Label' | 'Focus' | 'Whisper' | 'Yell' | 'Spell' | 'Guild' | 'Alliance' | 'Command' | 'Encoded' | 'Party';
        font: number;
        textType: 'CLIENT' | 'SYSTEM' | 'OBJECT' | 'GUILD_ALLY';
        unicode: boolean;
        time: string;
        hueArgb: number;
    }
    /**
     * The `Journal` can be used to inspect the game journal contents to trigger parts of your script.
     *
     * Use it for:
     * - Checking if the Journal contains text
     * - Waiting for text to appear in the Journal
     * - Waiting for a collection of possible strings to exist
     */
    export class Journal {
        /** @ignore */
        constructor(client: Client);
        /**
         * Checks for the existence of text in the journal
         * @param text
         * @param author
         * @returns `true`/`false` if the text exists in the journal.
         */
        containsText(text: string, author?: string): boolean;
        /**
         * Waits for the text to appear in the journal.
         * - Use [clear()](#clear) to clear the journal text.
         * @param text
         * @param author
         * @param timeout
         *
         * @example Bandage self, waiting for the System message
         * ```ts
         * const healthBefore = player.hits;
         *
         * journal.clear();
         * player.useType(0xE21);
         * target.waitTargetSelf();
         *
         * if(journal.waitForText("You healed", "System", 8000)) {
         *   client.headMsg(`Bandaged +${player.hits - healthBefore}`, player, 66)
         * }
         * ```
         * @returns `true`/`false` if the text was found.
         */
        waitForText(text: string, author?: string, timeout?: number): boolean;
        /**
         * Waits for **EVERY** string in an array of strings to be found in the Journal, or for the timeout to be hit.
         * Returns all the strings that were found, may be less than the input if the timeout was hit.
         *
         * This method is useful if you're waiting for several strings to all appear.
         * If you want to wait for any string in the input array use `waitForTextAny`
         * @param text
         * @param author
         * @param timeout
         *
         * @example
         *
         * ```ts
         * const waitMessage = "You must wait";
         * const failMessage = "You cannot focus";
         * const successMessage = "You enter a meditative trance.";
         *
         * journal.clear();
         * const response = journal.waitForTextEvery([waitMessage, failMessage, successMessage]);
         *
         * if(response.includes(successMessage)) {
         *   client.headMsg(`Meditating...`, player, 66)
         * }
         * ```
         * @returns All the strings that were found within the timeout, or an empty array if none were found.
         */
        waitForTextEvery(text: string[], author?: string, timeout?: number): string[];
        /**
         * Waits for **ANY** string in an array of strings to be found in the Journal, or for the timeout to be hit.
         * Returns the first string to be found or `null` if the timeout was reached.
         *
         * This method is useful if you're waiting for any one of a list of strings to appear.
         * If you want all the strings to appear you should use `waitForTextEvery`
         * @param text
         * @param author
         * @param timeout
         *
         * @example
         *
         * ```typescript
         * const waitMessage = "You must wait";
         * const failMessage = "You cannot focus";
         * const successMessage = "You enter a meditative trance.";
         *
         * journal.clear();
         * const response = journal.waitForTextAny([waitMessage, failMessage, successMessage]);
         *
         * switch(response) {
         *   case waitMessage: {
         *     // sleep
         *     break;
         *   }
         *   case failMessage: {
         *     // retry
         *     break;
         *   }
         *   case successMessage: {
         *     // loop
         *     break;
         *   }
         * }
         * ```
         * @returns The string if it was found, or null if not.
         */
        waitForTextAny(text: string[], author?: string, timeout?: number): string | null;
        /**
         * Clears/forgets the journal history.
         * This is useful if you don't want to process older journal entries.
         * @param text
         * @param author
         * @param timeout
         *
         * @example
         *
         * ```ts
         * player.say("Hello there");
         * journal.waitForText("Hello there"); // This will succeed quickly as the text was just added
         * journal.clear();
         * journal.waitForText("Hello there"); // this will time out, as the string is now empty.
         * ```
         */
        clear(): void;
    }
}
declare module "PopupMenu" {
    import { MenuPopupData } from "index";
    import { Client } from "Client";
    /**
     * This class is for interacting with context menus (i.e. when you single click on an item or your self).
     * `PopupMenu` is available via the `popupMenu` variable on the global scope.
     * @example
     *
     * ```ts
     * popupMenu.request(player.serial);
     * popupMenu.waitUntilOpen(1000); // Wait 1 second for the menu to open
     * popupMenu.reply(0); // 0 is first item, second item is 1, etc.
     * ```
     */
    export class PopupMenu {
        /** @ignore */
        constructor(client: Client);
        /**
         * Replies to a popup menu. Index 0 is the first item.
         * @param index
         */
        reply(index: number): void;
        /**
         * Requests a popup menu for the given object
         * @param serial
         * @param waitMs
         */
        request(serial: number, waitMs?: number): boolean | undefined;
        /**
         * Checks if a popup currently exists
         */
        exists: boolean;
        /**
         * Wait until a popup context menu is open
         * @param timeoutMs
         */
        waitUntilOpen(timeoutMs?: number): boolean;
        /**
         * Wait until a popup context menu is open, and return its content or null
         * @param timeoutMs
         */
        waitForContent(timeoutMs?: number): {
            serial: number;
            items: {
                index: number;
                cliloc: number;
                hue: number;
                replacedHue: number;
                flags: number;
                text: string;
            }[];
        } | null;
        /**
         * Closes a popup menu if it exists
         */
        close(): void;
        /**
         * Get the menu content if it is open
         */
        content: MenuPopupData | null;
    }
}
declare module "Prompt" {
    import { Client } from "Client";
    /**
     * This class is for interacting with text prompts via the chat box.
     * `Prompt` is accessible in the global scope via the variable `prompt`.
     * @example
     *
     * ```ts
     * player.use(0x4021C7B1); // Runebook
     * const gump = Gump.findOrWait(0x59);
     * if (!gump) {
     *   exit("Coudln't open runebook")
     * }
     * gump.reply(1);
     * prompt.waitUntilOpen(1000); // wait up to 1 second for a prompt to show up
     * prompt.reply("My Awesome runebook");
     * ```
     */
    export class Prompt {
        /** @ignore */
        constructor(client: Client);
        /**
         * Reply to a currently waiting prompt, if one is open
         * @param value
         * @example
         *
         * ```ts
         * prompt.reply("House Rune");
         * ```
         */
        reply(value: string): void;
        /**
         * Checks if a prompt exists and is waiting for input
         * @example
         *
         * ```ts
         * if(prompt.exists) {
         *   prompt.reply("House Rune");
         * }
         * ```
         */
        exists: boolean;
        /**
         * Waits for a prompt to be open
         * @param timeoutMs time in milliseconds to wait
         * @example
         *
         * ```ts
         * prompt.waitUntilOpen(1000); // wait 1 second
         * prompt.reply("Yes");
         * ```
         */
        waitUntilOpen(timeoutMs?: number): boolean;
    }
}
declare module "Target" {
    import type { TargetInfo } from "index";
    import type { Client } from "Client";
    import { SerialOrEntity } from "GameObject";
    import { Item } from "Item";
    import { Mobile } from "Mobile";
    export class Target {
        /** @ignore */
        constructor(client: Client);
        /**
         * Target a Mobile or an Item with the currently open target
         *
         * @example
         *
         * ```ts
         * client.castSpell(Spells.Heal);
         * target.wait();
         * target.entity(player);
         * ```
         */
        entity(serial: SerialOrEntity): void;
        /**
         * Target self with the currently open target
         *
         * @example
         *
         * ```ts
         * client.castSpell(Spells.Heal);
         * target.wait();
         * target.self();
         * ```
         */
        self(): void;
        /**
         * Target a Tile or Static
         *
         * **When `graphic` is omitted it will target `LAND` by default.**
         *
         * @example This will target the tile
         *
         * ```ts
         * client.castSpell(Spells.Teleport);
         * target.wait();
         * target.terrain(1203, 222, 0);
         * ```
         * @example This will target the static graphic on a specific tile
         *
         * ```ts
         * client.castSpell(Spells.Teleport);
         * target.wait();
         * target.terrain(1203, 222, 0, 0x5a2);
         * ```
         */
        terrain(x: number, y: number, z: number, graphic?: number | undefined): void;
        /**
         * Target a Tile or Static where `{ x, y, z }` is the distance from the player.
         *
         * **When `graphic` is omitted it will target `LAND` by default.**
         *
         * @example This will target the tile at position `{ player.x - 1, player.y - 2, player.z - 0 }`
         * ```ts
         * client.castSpell(Spells.Teleport);
         * target.wait();
         * target.terrainWithOffset(-1, -2, 0);
         * ```
         *
         * @example This will target the static graphic on a specific tile at position `{ player.x - 1, player.y - 2, player.z - 0 }`
         * ```ts
         * client.castSpell(Spells.Teleport);
         * target.wait();
         * target.terrainWithOffset(-1, -2, 0, 0x5a2);
         * ```
         */
        terrainWithOffset(x: number, y: number, z: number, graphic?: number | undefined): void;
        /**
         * Target a Tile or Static from a specific Item or Mobile
         *
         * **When `graphic` is omitted it will target `LAND` by default.**
         *
         * @example This will target the file in front or behind the Mobile
         *
         * ```ts
         * client.castSpell(Spells.Teleport);
         * target.wait();
         * target.terrainRelativeToEntity(mob, 5, true);
         * ```
         *
         * @example This will target the static on a specific tile in front or behind the Mobile
         *
         * ```ts
         * client.castSpell(Spells.Teleport);
         * target.wait();
         * target.terrainRelativeToEntity(mob, 5, true, 0x5a2);
         * ```
         */
        terrainRelativeToEntity(entity: SerialOrEntity, range: number, forward: boolean, graphic?: number | undefined): void;
        /**
         * Check if target is open
         */
        open: boolean;
        /**
         * Serial of the last target
         */
        lastSerial: number;
        /**
         * Object of the last target, i.e. last Item/Mobile
         */
        last: Item | Mobile | undefined;
        /**
         * Serial of the last object used, i.e. double-clicked by the player
         */
        lastObjectSerial: number;
        /**
         * Last object used, i.e. double-clicked by the player
         */
        lastObject: Item | undefined;
        /**
         * Creates a target and returns information about the result
         */
        query(isGround?: boolean): TargetInfo;
        /**
         * Wait for the target to open within a specific amount of time.
         */
        wait(timeoutMs?: number): boolean;
        /**
         * Waits for the target to open, and then targets the desired entity
         */
        waitTargetEntity(entity: SerialOrEntity, timeoutMs?: number): boolean;
        /**
         * Wait for target with a specific amount of time, when open target self.
         * @example Use bandages, target self.
         *
         * ```ts
         * player.useType(0xE21);
         * target.waitTargetSelf();
         * ```
         */
        waitTargetSelf(timeoutMs?: number): boolean;
        /**
         * Wait for target, when open target the first object with a certain graphic/hue
         * @example Use a sewing kit, then target hides.
         *
         * ```ts
         * player.useType(0xF9D);
         * target.waitTargetType(0x1078);
         * ```
         */
        waitTargetType(graphic: number, hue?: number, timeoutMs?: number): boolean;
        /**
         * Clear target queue
         */
        clearQueue(): void;
        /**
         * Close the target
         */
        cancel(): void;
        /**
         * Repeats the last targeting information based on the cursor type, e.g. Entity/Position etc
         *
         * @example
         *
         * ```ts
         * client.castSpell(Spells.Heal);
         * target.wait();
         * target.repeatLast();
         * ```
         * @example
         *
         * ```ts
         * client.castSpell(Spells.Teleport);
         * target.wait();
         * target.repeatLast();
         * ```
         */
        repeatLast(): void;
    }
}
declare module "WorldMap" {
    import { WorldMapMarker, WorldMapMarkerPartial } from "index";
    import type { Client } from "Client";
    export class WorldMap {
        /** @ignore */
        constructor(client: Client);
        /**
         * Gets list of World Map markers.
         *
         * **Note:** this list is readonly, use `addMarker` or `removeMarker` to manage the World Map markers.
         */
        markers: readonly WorldMapMarker[];
        /**
         * Adds a marker to the World Map.
         * @param marker
         *
         * @example Adds a marker to the current player location
         * ```ts
         * const marker = worldMap.addMarker({ name: "Here", x: player.x, y: player.y, color: "green" });
         * ```
         */
        addMarker(marker: WorldMapMarker | WorldMapMarkerPartial): WorldMapMarker;
        /**
         * Remove a marker from the World Map.
         * @param marker
         *
         * @example Removes a marker by name if it exists
         * ```ts
         * worldMap.removeMarker("Here");
         * ```
         */
        removeMarker(marker: string | {
            name: string;
        }): boolean;
        /**
         * Closes the World Map gump.
         *
         * @example
         * ```ts
         * worldMap.close();
         * ```
         */
        close(): void;
        /**
         * Opens the World Map gump.
         *
         * @example
         * ```ts
         * worldMap.open();
         * ```
         */
        open(): void;
        /**
         * Attempts to parse a location string and convert into map coordinates.
         *
         * **Note:** Currently only supports Sextant coordinates, e.g. `100o25'S,40o04'E`
         * @param input
         *
         * @example
         * ```ts
         * const marker = worldMap.addMarker(
         *   {
         *     name: 'Sextant Loc',
         *     color: 'green',
         *     ...worldMap.parseLocation("100o25'S,40o04'E")
         *   }
         * )
         * ```
         */
        parseLocation(input: string): {
            x: number;
            y: number;
        } | undefined;
        /**
         * Changes the current location of the World Map, which also enables Free View.
         * @param coords
         *
         * @example Go To the current players coordinates
         * ```ts
         * worldMap.goTo({ x: player.x, y: player.y });
         * ```
         */
        goTo(coords: {
            x: number;
            y: number;
        }): void;
        /**
         * Removes all World Map markers.
         */
        removeAllMarkers(): void;
        /**
         * Import multiple markers at once from an array.
         * @param markers Array of markers to import
         * @returns Import result with success status, count, and any errors
         *
         * @example Import markers from an array
         * ```ts
         * const result = worldMap.importMarkers([
         *   { name: "Home", x: 1234, y: 5678, color: "blue" },
         *   { name: "Bank", x: 2345, y: 6789, color: "green" }
         * ]);
         * console.log(`Imported ${result.count} markers`);
         * ```
         */
        importMarkers(markers: (WorldMapMarker | WorldMapMarkerPartial)[]): {
            success: boolean;
            count: number;
            errors: string[];
        };
    }
}
declare module "config/types" {
    import { JournalEntry } from "Journal";
    import { Player } from "Player";
    export type KeyOfType<T, V> = keyof {
        [P in keyof T as T[P] extends V ? P : never]: any;
    };
    export type ScriptTriggerEvent<T extends string, A = unknown> = {
        name: T;
        data: A;
    };
    export type ScriptTriggerMap = {
        [K in KeyOfType<Player, string | number>]?: {
            action: (event: ScriptTriggerEvent<K, Player[K]>) => unknown;
        };
    } & Partial<{
        login: {
            action: (event: ScriptTriggerEvent<'login'>) => unknown;
        };
        journal: {
            action: (event: ScriptTriggerEvent<'journal', JournalEntry>) => unknown;
        };
    }>;
    export type ScriptConfig = {
        triggers: ScriptTriggerMap;
    };
    export type ScriptTriggerName = keyof ScriptTriggerMap;
    export type ScriptTriggerParameters<K extends ScriptTriggerName> = NonNullable<ScriptTriggerMap[K]> extends {
        action: (param: ScriptTriggerEvent<K, infer P>) => unknown;
    } ? P : never;
}


declare module "Client" {
    import { GameObject, SerialObject } from "GameObject";
    export class Client {
        /** @ignore */
        constructor(bindings?: any, withScriptDeferral?: any);
        /**
         * Gets the current ping to the server (as seen in the Connection gump)
         * @returns number
         */
        getPing: () => number;
        /**
         * Display a message in the text chat.
         *
         * @example Say a message in red/green over the players head.
         * ```ts
         * client.headMsg('A chat in Red', 33);
         * client.headMsg('A chat in Green', 66);
         * ```
         */
        sysMsg: (message: string, hue?: number | undefined) => void;
        /**
         * Display a message overhead of the target entity.
         *
         * @example Say a message in red/green over the players head.
         * ```ts
         * client.headMsg('A message in Red', player, 33);
         * client.headMsg('A message in Green', player, 66);
         * ```
         */
        headMsg: (message: string, serial: number | SerialObject | GameObject | "world", hue?: number | undefined) => void;
        /**
         * Open the paperdoll for a Mobile.
         *
         * @example
         *
         * ```ts
         * const nearestHuman = client.selectEntity(
         *  SearchEntityOptions.Any,
         *  SearchEntityRangeOptions.Nearest,
         *  SearchEntityTypeOptions.Human,
         *  false
         * );
         *
         * client.openPaperdoll(nearestHuman);
         * ```
         */
        openPaperdoll: (serial?: number | SerialObject | GameObject | "world" | undefined) => void;
        /**
         * Attempts to check whether a certain object can be found in the game.
         *
         * @example
         *
         * ```ts
         * const runebookSerial = 0x401C37FB;
         * const runebook = client.findObject(runebookSerial);
         *
         * if(runebook) {
         *   player.use(runebook);
         * } else {
         *   client.headMsg("Runbook missing!", player.serial);
         * }
         * ```
         */
        findObject: (serial: number | SerialObject | GameObject | "world", hue?: number | null | undefined, sourceSerial?: number | SerialObject | GameObject | "world" | null | undefined, amount?: number | null | undefined, range?: number | null | undefined) => Item | Mobile | undefined;
        /**
         * Attempts to find an object in the world with the specified search parameters, returning it if found.
         *
         * **Note:** The `range` parameter when combined with the `source` container parameter specifies the depth to search.
         *
         * @example
         * ```ts
         * // Print out all the gold in the players backpack, without iterating sub-containers.
         * const goldType = 0xEED;
         * ignoreList.clear();
         *
         * let gold: Item | undefined;
         * while (gold = client.findType(goldType, undefined, player.backpack, undefined, 0) as Item) {
         *   console.log(gold.name);
         *   ignoreList.add(gold);
         * }
         * ```
         *
         * @example
         * ```ts
         * //  Use any bandages that can be found
         * const bandageType = 0xE21;
         * const bandages = client.findType(bandageType);
         *
         * if(bandages) {
         *   player.use(bandages);
         *   target.waitTargetSelf();
         * } else {
         *   client.headMsg("Out of bandages", player.serial);
         * }
         * ```
         */
        findType: (graphic: number, hue?: number | null | undefined, sourceSerial?: number | SerialObject | GameObject | "world" | null | undefined, amount?: number | null | undefined, range?: number | null | undefined) => Item | Mobile | undefined;
        /**
         * Attempts to find all objects of a certain type (graphic), returning the matching Items/Mobiles.
         *
         * @example
         *
         * ```ts
         * const goldPile = 0xEED;
         * const piles = client.findAllOfType(goldPile, undefined, 'world');
         *
         * if(piles.length > 0) {
         *   client.headMsg(`Found ${piles.length} gold piles on the ground`, player);
         * } else {
         *   client.headMsg("No gold piles in range", player);
         * }
         * ```
         */
        findAllOfType: (graphic: number, hue?: number | null | undefined, sourceSerial?: number | SerialObject | GameObject | "world" | null | undefined, amount?: number | null | undefined, range?: number | null | undefined) => (Item | Mobile)[];
        /**
         * Attempts to find all **Items** of a certain type (graphic).
         *
         * @example
         *
         * ```ts
         * const goldPile = 0xEED;
         * const piles = client.findAllItemsOfType(goldPile, undefined, 'world');
         *
         * if (piles.length > 0) {
         *   const total = piles.reduce((sum, item) => sum + item.amount, 0);
         *   client.headMsg(`Found ${piles.length} piles, ${total} gold`, player);
         * } else {
         *   client.headMsg("No gold piles in range", player);
         * }
         * ```
         */
        findAllItemsOfType: (graphic: number, hue?: number | null | undefined, sourceSerial?: number | SerialObject | GameObject | "world" | null | undefined, amount?: number | null | undefined, range?: number | null | undefined) => Item[];
        /**
         * Attempts to find all **Mobiles** of a certain type (graphic).
         *
         * @example Count all the sheep on screen
         *
         * ```ts
         * const sheepGraphic = 0xCF;
         * const sheep = client.findAllMobilesOfType(sheepGraphic);
         *
         * if(sheep.length > 0) {
         *   client.headMsg(`I count ${sheep.length} sheep`, player);
         * } else {
         *   client.headMsg("No sheep here!", player);
         * }
         * ```
         */
        findAllMobilesOfType: (graphic: number, hue?: number | null | undefined, sourceSerial?: number | SerialObject | GameObject | "world" | null | undefined, amount?: number | null | undefined, range?: number | null | undefined) => Mobile[];
        /**
         * Attempts to find the object at the specified layer, if it exists.
         *
         * @example Try to remove the currently equipped helmet.
         *
         * ```ts
         * const helm = client.findItemOnLayer(player.serial, Layers.Helmet);
         *
         * if (helm) {
         *   client.headMsg(`Removing helm`, player);
         *   player.moveItem(helm, player.backpack);
         * } else {
         *   client.headMsg("Not wearing a helm", player.serial);
         * }
         * ```
         */
        findItemOnLayer: (serial: number | SerialObject | GameObject | "world", layer: Layers) => Item | undefined;
        /**
         * Returns the entity based on the search criteria
         *
         * @example Select nearest `Gray` or `Enemy` entity, with `Any` body type, and not as a friend
         *
         * ```ts
         *  client.selectEntity(
         *    SearchEntityOptions.Enemy | SearchEntityOptions.Gray,
         *    SearchEntityRangeOptions.Nearest,
         *    SearchEntityTypeOptions.Any,
         *    false
         *  )
         * ```
         * @example Select nearest `Innocent`  entity, with `Any` body type, and not as a friend
         *
         * ```ts
         *  client.selectEntity(
         *    SearchEntityOptions.Innocent,
         *    SearchEntityRangeOptions.Nearest,
         *    SearchEntityTypeOptions.Human,
         *    false
         *  )
         * ```
         */
        selectEntity: (searchOpt: number, searchRangeOpt: number, searchTypeOpt: number, asFriend: boolean) => Mobile | undefined;
        /** Whether the mobile is likely a player character (heuristic: human body, not a pet, not invulnerable NPC, not grey NPC). */
        mobileIsPlayer: (a_0: number, ...a: unknown[]) => boolean;
        /** Whether the mobile has a human, elf, or gargoyle body graphic (includes ghosts). */
        mobileIsHuman: (a_0: number, ...a: unknown[]) => boolean;
        /** Whether the mobile can be renamed (true for pets/followers). */
        mobileIsRenamable: (a_0: number, ...a: unknown[]) => boolean;
        /**
         * Triggers the `All Names` macro which shows name overheads for all entities on-screen.
         * @example
         *
         * ```ts
         * client.allNames();
         * ```
         */
        allNames: () => any;
        /**
         * Triggers the `Quit Game` dialogue
         * @example
         *
         * ```ts
         * client.quitGame();
         * ```
         */
        quitGame: () => any;
        /**
         * Toggles whether the player always runs despite the mouse distance from the player mobile.
         * @example
         *
         * ```ts
         * client.toggleAlwaysRun();
         * ```
         */
        toggleAlwaysRun: () => any;
        /**
         * Closes all gumps that aren't the Top Bar, Buff bar, or the World view (radar)
         * @example
         *
         * ```ts
         * client.closeAllGumps();
         * ```
         */
        closeAllGumps: () => any;
        /**
         * Closes all corpses on-screen
         * @example
         *
         * ```ts
         * client.closeCorpses();
         * ```
         */
        closeCorpses: () => any;
        /**
         * Closes all healthbars on-screen
         * @example
         *
         * ```ts
         * client.closeAllHealthBars();
         * ```
         */
        closeAllHealthBars: () => any;
        /**
         * Closes all inactive healthbars (i.e. dead or off-screen entities).
         * @example
         *
         * ```ts
         * client.closeInactiveHealthBars();
         * ```
         */
        closeInactiveHealthBars: () => any;
        /**
         * Reset the viewport zoom back to default (1.1)
         * @example
         *
         * ```ts
         * client.zoomReset();
         * ```
         */
        zoomReset: () => any;
        /**
         * Zooms in the viewport
         * @example
         *
         * ```ts
         * client.zoomIn();
         * ```
         */
        zoomIn: () => any;
        /**
         * Zooms out the viewport
         * @example
         *
         * ```ts
         * client.zoomIn();
         * ```
         */
        zoomOut: () => any;
        /**
         * Toggles the chat visibility, e.g. the bar at the bottom of the game viewport
         * @example
         *
         * ```ts
         * client.zoomIn();
         * ```
         */
        toggleChatVisibility: () => any;
        /**
         * Sets the grab bag used by Grid Loot
         * @example
         *
         * ```ts
         * client.zoomIn();
         * ```
         */
        setGrabBag: () => any;
        /**
         * Toggles whether entities have name plates
         * @example
         *
         * ```ts
         * client.toggleNameOverheads();
         * ```
         */
        toggleNameOverheads: () => any;
        /**
         * Toggles whether mobiles have auras underneath them
         * @example
         *
         * ```ts
         * client.toggleAuras();
         * ```
         */
        toggleAuras: () => any;
        /**
         * Toggles the Circle of Transparency between states
         * @example
         *
         * ```ts
         * client.toggleCircleOfTransparency();
         * ```
         */
        toggleCircleOfTransparency(): void;
        getStatic: (graphic: number) => {
            name: string;
            flags: number;
            graphic: number;
        } | undefined;
        getTile: (graphic: number) => {
            flags: number;
            graphic: number;
        } | undefined;
        getTerrainList: (x: number, y: number) => {
            flags: number;
            graphic: number;
            x: number;
            y: number;
            z: number;
            isLand: boolean;
        }[] | undefined;
        sendBuyRequest: (vendorSerial: number | Mobile, items: {
            serial: number;
            amount: number;
        }[]) => boolean;
        sendSellRequest: (vendorSerial: number | Mobile, items: {
            serial: number;
            amount: number;
        }[]) => boolean;
        queryItemOPL: (serialOrObject: number | SerialObject | GameObject | "world", timeout?: number | undefined) => {
            serial: number;
            data: string | null;
            name: string;
            hue: number;
            graphic: number;
            amount: number;
            isPartialHue: boolean;
            properties?: {
                values: {
                    text: string;
                    id: number;
                    order: number;
                }[];
                text: string;
                id: number;
                order: number;
            }[] | null | undefined;
        };
        queryItemSingleClickName: (serialOrObject: number | SerialObject | GameObject | "world", timeout?: number | undefined) => string;
    }
}
declare module globalThis {
    import { Client } from "Client";
    import { IgnoreList } from "IgnoreList";
    import { Journal } from "Journal";
    import { Player } from "Player";
    import { PopupMenu } from "PopupMenu";
    import { Prompt } from "Prompt";
    import { Target } from "Target";
    import { WorldMap } from "WorldMap";
    import { ScriptConfig } from "config/types";
    export namespace globalThis {
        const console: {
            log(...data: any[]): void;
            info(...data: any[]): void;
            warn(...data: any[]): void;
            error(...data: any[]): void;
            debug(...data: any[]): void;
            clear(): void;
        };
        /**
         * `client` is the main object to use for interacting with the ClassicUO client and the client world.
         */
        const client: Client;
        const player: Player;
        const journal: Journal;
        const target: Target;
        const ignoreList: IgnoreList;
        const popupMenu: PopupMenu;
        const prompt: Prompt;
        const worldMap: WorldMap;
        function ScriptConfig(config: ScriptConfig): void;
        /**
         * Logs the arguments to the console area below the scripting window.
         *
         * @param args List of objects to log to the console.
         *
         * @example Log a simple string
         *
         * ```ts
         * log('Hi there!');
         * ```
         *
         * @example Log character name
         *
         * ```ts
         * log(`My name is ${player.name}`);
         * ```
         * @example Log the equipped helmet
         *
         * ```ts
         * log(`My helmet is`, player.equippedItems.helmet);
         * ```
         */
        function log(...args: any[]): void;
        /**
         * Delays script execution for a certain number of milliseconds.
         *
         * *Note:* The delay timing for long durations is not guaranteed.
         *
         * @param ms Delay in milliseconds
         * @example Using a skill then waiting to use another skill
         *
         * ```ts
         * player.useSkill(Skills.Anatomy);
         * sleep(10000); // sleep 10 seconds
         * player.useSkill(Skills.Meditation);
         * ```
         */
        function sleep(ms: number): void;
        /**
         * Exits early from the script execution, useful to bail out based on certain conditions.
         * @param reason Optional reason for why the script failed, shows up in the console area.
         *
         * @example Kill the script if the character is dead.
         * ```ts
         * if (player.isDead) {
         *   exit("Failed, I'm dead!");
         * }
         * ```
         */
        function exit(reason?: string): void;
    }
    export { Spells } from enums;
    export { Skills } from enums;
    export { Layers } from enums;
    export { Directions } from enums;
    export { SkillLock } from enums;
    export { Notorieties } from enums;
    export { BuffDebuffs } from enums;
    export { Abilities } from enums;
    export { SearchEntityOptions } from enums;
    export { SearchEntityRangeOptions } from enums;
    export { SearchEntityTypeOptions } from enums;
    export { Virtues } from enums;
    export { Constant } from enums;
    export { Client } from "Client";
    export { Entity } from "Entity";
    export { Mobile } from "Mobile";
    export { Player } from "Player";
    export { Item } from "Item";
    export { Gump } from "Gump";
    export { Journal } from "Journal";
    export { Target } from "Target";
    export { IgnoreList } from "IgnoreList";
    export { PopupMenu } from "PopupMenu";
    export { Prompt } from "Prompt";
    export { WorldMap } from "WorldMap";
    export type { ScriptConfig } from "config/types";
}
