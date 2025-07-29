def _mergestr(*s):
    return "\n".join(s)

text = {
    "en": {
        "helps.function.setLang.languageNotSupport": "Unsupported language: ",
        "helps.function.updateLog.versionNotFound": "Version not found: ",
        "helps.function.updateLog.versionFormatError": "The version code format is incorrect: ",
        "helps.upgradeLogs.0_0_1": "The first version, this module was just created.",
    },
    "zh": {
        "helps.function.setLang.languageNotSupport": "不支持的语言：",
        "helps.function.updateLog.versionNotFound": "无法找到版本号：",
        "helps.function.updateLog.versionFormatError": "版本号格式错误：",
        "helps.upgradeLogs.0_0_1": "第一个版本，这个模块刚被创建。",
    },
    "default": {
        "meta.version": "0.0.2a1",
        "meta.lastVersion": "0.0.1rc1"
    }
}
