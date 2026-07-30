# 模板素材说明

各游戏特征名定义在：

- `games/honkai3/features.py`
- `games/starrail/features.py`
- `games/zzz/features.py`
- `games/genshin/features.py`
- `games/pcr/features.py`
- `games/bhxy2/features.py`

在 Windows 上使用 label-studio 1.15.0 标注 COCO，导出到 `assets/`，并在 `src/config.py` 的 `template_matching.coco_feature_json` 指向对应 JSON。

分辨率建议：

- 崩坏3 / 星铁 / 绝区零 / 原神 PC：1920x1080 16:9
- 公主连结：540x960 DPI 240
- 崩坏学园2：开发期先固定一种分辨率并写入配置
