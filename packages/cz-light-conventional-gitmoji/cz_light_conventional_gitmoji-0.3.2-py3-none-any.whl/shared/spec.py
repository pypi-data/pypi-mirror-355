"""Contains the Gitmoji class."""

from shared.gitmojis import GitMojiConstant

mojis = [
    {
        "type": "fix",
        "icon": GitMojiConstant.GJ_FIX.value,
        "code": ":bug:",
        "desc": "Fix a bug.",
    },
    {
        "type": "feat",
        "icon": GitMojiConstant.GJ_FEAT.value,
        "code": ":sparkles:",
        "desc": "Introduce new features.",
    },
    {
        "type": "docs",
        "icon": GitMojiConstant.GJ_DOCS.value,
        "code": ":memo:",
        "desc": "Add or update documentation.",
    },
    {
        "type": "style",
        "icon": GitMojiConstant.GJ_STYLE.value,
        "code": ":art:",
        "desc": "Improve structure / format of the code.",
    },
    {
        "type": "refactor",
        "icon": GitMojiConstant.GJ_REFACTOR.value,
        "code": ":recycle:",
        "desc": "Refactor code.",
    },
    {
        "type": "perf",
        "icon": GitMojiConstant.GJ_PERF.value,
        "code": ":zap:",
        "desc": "Improve performance.",
    },
    {
        "type": "test",
        "icon": GitMojiConstant.GJ_TEST.value,
        "code": ":white_check_mark:",
        "desc": "Add, update, or pass tests.",
    },
    {
        "type": "build",
        "icon": GitMojiConstant.GJ_BUILD.value,
        "code": ":construction_worker:",
        "desc": "Add or update CI build system.",
    },
    {
        "type": "ci",
        "icon": GitMojiConstant.GJ_CI.value,
        "code": ":green_heart:",
        "desc": "Fix CI Build.",
    },
    {
        "type": "dump",
        "icon": GitMojiConstant.GJ_DUMP.value,
        "code": ":fire:",
        "desc": "Remove code or files.",
    },
    {
        "type": "hotfix",
        "icon": GitMojiConstant.GJ_HOTFIX.value,
        "code": ":ambulance:",
        "desc": "Critical hotfix.",
    },
    {
        "type": "init",
        "icon": GitMojiConstant.GJ_INIT.value,
        "code": ":tada:",
        "desc": "Begin a project.",
    },
    {
        "type": "bump",
        "icon": GitMojiConstant.GJ_BUMP.value,
        "code": ":bookmark:",
        "desc": "Release / Version tags.",
    },
    {
        "type": "dep-drop",
        "icon": GitMojiConstant.GJ_DEP_DROP.value,
        "code": ":arrow_down:",
        "desc": "Downgrade dependencies.",
    },
    {
        "type": "dep-bump",
        "icon": GitMojiConstant.GJ_DEP_BUMP.value,
        "code": ":arrow_up:",
        "desc": "Upgrade dependencies.",
    },
    {
        "type": "dep-add",
        "icon": GitMojiConstant.GJ_DEP_ADD.value,
        "code": ":heavy_plus_sign:",
        "desc": "Add a dependency.",
    },
    {
        "type": "dep-rm",
        "icon": GitMojiConstant.GJ_DEP_RM.value,
        "code": ":heavy_minus_sign:",
        "desc": "Remove a dependency.",
    },
    {
        "type": "config",
        "icon": GitMojiConstant.GJ_CONFIG.value,
        "code": ":wrench:",
        "desc": "Add or update configuration files.",
    },
    {
        "type": "lang",
        "icon": GitMojiConstant.GJ_LANG.value,
        "code": ":globe_with_meridians:",
        "desc": "Internationalization and localization.",
    },
    {
        "type": "merge",
        "icon": GitMojiConstant.GJ_MERGE.value,
        "code": ":twisted_rightwards_arrows:",
        "desc": "Merge branches.",
    },
    {
        "type": "logs-add",
        "icon": GitMojiConstant.GJ_LOGS_ADD.value,
        "code": ":loud_sound:",
        "desc": "Add or update logs.",
    },
    {
        "type": "logs-rm",
        "icon": GitMojiConstant.GJ_LOGS_RM.value,
        "code": ":mute:",
        "desc": "Remove logs.",
    },
    {
        "type": "ignore",
        "icon": GitMojiConstant.GJ_IGNORE.value,
        "code": ":see_no_evil:",
        "desc": "Add or update a .gitignore file.",
    },
    {
        "type": "chore",
        "icon": GitMojiConstant.GJ_CHORE.value,
        "code": ":broom:",
        "desc": "Commit changes related to miscellaneous chores.",
    },
]
