# Orrery showcase / 演示说明

[Download both language editions](https://github.com/ItIsMixian/Orrery/raw/refs/heads/main/docs/demo/orrery-demo.zip)

Online: [English story](https://itismixian.github.io/Orrery/demo.en.html) · [中文演示](https://itismixian.github.io/Orrery/demo.html) · [Language selection](https://itismixian.github.io/Orrery/)

Unzip and open `demo.en.html` for the English animated story or `demo.html` for the Chinese original in a local browser. Keep both files together. The files are self-contained and do not require an Orrery service.

下载并解压后，在本地浏览器打开 `demo.en.html`（英文故事）或 `demo.html`（中文原版）。两个文件放在同一目录，无需启动 Orrery 服务。

## What the demonstration means

- The story is a simulation of work joining an existing line, consuming inputs, undergoing rework and delivering again. It is not live project telemetry or a promise that every illustrated lifecycle operation is enabled by default.
- English localization covers the animated story, task and dependency labels, playback controls and explanations. Original project snapshots and the relationship-model source retain their Chinese labels and are explicitly linked; they are not represented as translated historical evidence.
- The relationship model explains Orrery's own design, not a general diagram-generation product.
- The README GIF is a five-second excerpt of the original SVG transition engine, with an end-to-start return for looping. It is not the full story or an execution recording. Static SVG fallbacks are included.

## Actual usage evidence and limits

The README examples describe Orrery managing its own development. The maintainer's local Q4 workflow recorded a real CLI delivery, retained the earlier record prefix, and read the new delivery into the local Graph. Continued reading after restart and beyond the original temporary read expiry was also verified. These are scoped local-development observations, not claims about every task, independent reviewers, every host, or a released binary.

The historical snapshot packaged in the Chinese demo was captured on 2026-09-09 and is explicitly partial and non-live. It is not automatically refreshed by viewing this file.

## Publication boundary

Only documentation and demonstration assets are published. A dedicated GitHub Pages branch serves the two static HTML files and a language-selection page; no Orrery backend, credentials or model API is deployed. This does not publish the local development branch, install new Skills or create a product release. Consult the selected Release notes for installable capabilities.

Static checks covered local asset references, SVG basics, English story identity/timing preservation, JavaScript syntax, GIF frame/size/loop metadata, and source-file preservation. Local browser automation was blocked by a URL policy and was not bypassed; no full automated browser-verification claim is made.
