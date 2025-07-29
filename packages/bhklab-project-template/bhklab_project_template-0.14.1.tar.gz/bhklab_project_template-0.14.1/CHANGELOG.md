# Changelog

## [0.14.1](https://github.com/bhklab/bhklab-project-template/compare/v0.14.0...v0.14.1) (2025-06-13)


### Bug Fixes

* move readme into docs dir to simplify index ([#41](https://github.com/bhklab/bhklab-project-template/issues/41)) ([a3d7fa2](https://github.com/bhklab/bhklab-project-template/commit/a3d7fa2ed1eaec2c5b34602971c5bc12f31d9fa1))

## [0.14.0](https://github.com/bhklab/bhklab-project-template/compare/v0.13.0...v0.14.0) (2025-06-11)


### Features

* add descriptions to example_script and doc-serve tasks in pixi.toml.jinja ([#38](https://github.com/bhklab/bhklab-project-template/issues/38)) ([bd137e2](https://github.com/bhklab/bhklab-project-template/commit/bd137e20b6582c514a59bb8bad5f25a16f6dd69a))
* enhance git version check with regex parsing for improved compatibility ([#36](https://github.com/bhklab/bhklab-project-template/issues/36)) ([800ea0d](https://github.com/bhklab/bhklab-project-template/commit/800ea0d5f2d13fe37da2e7b67201120d348d6d4a))

## [0.13.0](https://github.com/bhklab/bhklab-project-template/compare/v0.12.0...v0.13.0) (2025-06-11)


### Features

* enhance CLI command with detailed epilogue for documentation and issue reporting ([f2c9dce](https://github.com/bhklab/bhklab-project-template/commit/f2c9dce623f6d882f6a17aabf21395cf413d6631))
* expand .gitignore file to include comprehensive entries for OS, Python, R, IDEs, and build artifacts ([1991e2f](https://github.com/bhklab/bhklab-project-template/commit/1991e2f1320e87d1863efe36509d903ecf30da37))


### Bug Fixes

* correct markdown syntax in development guide ([f0428b1](https://github.com/bhklab/bhklab-project-template/commit/f0428b10eb11e7ac56dce9d11c0995a4eb0aca47))
* update rich-click dependency to version 1.8.9 ([cd2fbd7](https://github.com/bhklab/bhklab-project-template/commit/cd2fbd7c16799aa9d3a3278cd7dfb960375dbefc))


### Documentation

* add .gitignore file to documentation navigation ([ea690ea](https://github.com/bhklab/bhklab-project-template/commit/ea690eaf447e5cc69bce927c2370cefe9db05e69))
* enhance development guide with steps for updating package versions in PyPi and conda-forge ([2f068a3](https://github.com/bhklab/bhklab-project-template/commit/2f068a3151ab61daba1b314a7f4b482847f2d08f))

## [0.12.0](https://github.com/bhklab/bhklab-project-template/compare/v0.11.0...v0.12.0) (2025-06-11)


### Features

* add comprehensive overview of DMP directory structure and usage ([e337f08](https://github.com/bhklab/bhklab-project-template/commit/e337f085a8381c74ab27cea63ac8cc1a1fb24481))
* add Development section to navigation in mkdocs ([022304c](https://github.com/bhklab/bhklab-project-template/commit/022304c183c7f23731b6f8f6349686ccc9ac2112))


### Bug Fixes

* add DMP Directories to navigation and enhance markdown extensions ([1cce292](https://github.com/bhklab/bhklab-project-template/commit/1cce29265264cdb8db6b3c1e1a5493c652428f69))
* add DMP-compliant directories information to project overview ([e82d83d](https://github.com/bhklab/bhklab-project-template/commit/e82d83d6384aa49566eab72eea144846e2bed52d))
* adjust fetch depth in checkout step and streamline lockfile update process ([3d73c63](https://github.com/bhklab/bhklab-project-template/commit/3d73c634f02c6df9f1d00eddeba5a5f1cf214672))
* clarify GitHub Pages setup instructions in troubleshooting guide ([dff6cec](https://github.com/bhklab/bhklab-project-template/commit/dff6ceceb5f1265715c6bd4fc606d60dfa0bb553))
* remove commands for `uv` and `copier` from usage documentation ([86e29e9](https://github.com/bhklab/bhklab-project-template/commit/86e29e9e1cc854eab5693ede6e0513c231cc8869))
* remove meeting notes and status documentation from project ([19709d8](https://github.com/bhklab/bhklab-project-template/commit/19709d818a1538dff9ca5b84dd9b4893eb15d091))
* update mkdocs-material dependency version in pixi.toml ([6fef5ee](https://github.com/bhklab/bhklab-project-template/commit/6fef5ee5978d7d12d59b5013b1bdac078d536101))
* update requirements table in documentation for clarity ([2164d81](https://github.com/bhklab/bhklab-project-template/commit/2164d81b8603921f16b89ec9a94cb4cdc70beeed))

## [0.11.0](https://github.com/bhklab/bhklab-project-template/compare/v0.10.0...v0.11.0) (2025-06-03)


### Features

* add debug logging for project creation in CLI ([d4abe28](https://github.com/bhklab/bhklab-project-template/commit/d4abe28d7fb7f65b31c4e66e01be48173c58c584))
* add debug logging option and enhance logging configuration ([21e632b](https://github.com/bhklab/bhklab-project-template/commit/21e632b5f99319a33c2afd1868e340898a0bbb45))
* add logging configuration using loguru ([1faf369](https://github.com/bhklab/bhklab-project-template/commit/1faf369911ea94fdaaaa9ef6d3d2c183782cb6eb))
* add loguru and platformdirs as dependencies ([4adb31c](https://github.com/bhklab/bhklab-project-template/commit/4adb31c80054f19916fc38501abb0f178b6780dc))
* add requirement checks before project creation ([f7c7429](https://github.com/bhklab/bhklab-project-template/commit/f7c7429d1734f1e6e154f6562a75267a15fbea9c))
* add validator to prevent newlines in project description ([55447d6](https://github.com/bhklab/bhklab-project-template/commit/55447d6f8a492b8af1b0d2fbe06e8fab46e50ada))
* implement system requirements checks for git, pixi, and GitHub CLI ([db21919](https://github.com/bhklab/bhklab-project-template/commit/db21919cced8b17aa08c2e9f2510a5b23d6f20e8))


### Bug Fixes

* **ci:** doc deploy ([158ed2e](https://github.com/bhklab/bhklab-project-template/commit/158ed2e65c641ba3d2572f7a9ceea9afb1447d29))
* correct pypi path formatting and update project version to 0.10.0 ([613e2c0](https://github.com/bhklab/bhklab-project-template/commit/613e2c07063953c651e24c5ae5830666316f700d))


### Documentation

* add badges for visibility ([655247f](https://github.com/bhklab/bhklab-project-template/commit/655247fe5ae6861bd8a7f04072febbb1ef6fac72))
* update project requirements documentation for clarity and completeness ([e2b402f](https://github.com/bhklab/bhklab-project-template/commit/e2b402fd91ee0fc9b4139d3364198e3ac768a376))

## [0.10.0](https://github.com/bhklab/bhklab-project-template/compare/v0.9.0...v0.10.0) (2025-05-20)


### Features

* add MkDocs configuration and documentation build tasks ([#25](https://github.com/bhklab/bhklab-project-template/issues/25)) ([9170e4b](https://github.com/bhklab/bhklab-project-template/commit/9170e4b2bf2435777e38d86e2295fc9348b510a6))

## [0.9.0](https://github.com/bhklab/bhklab-project-template/compare/v0.8.0...v0.9.0) (2025-05-20)


### Features

* add data directory audit workflow to check for committed data files ([#5](https://github.com/bhklab/bhklab-project-template/issues/5)) ([c60e45c](https://github.com/bhklab/bhklab-project-template/commit/c60e45c301ede72613efe38a8012dd15eafb0e17))
* Add pypi-dependencies section and update example notebook and script to use `dirs` object ([#24](https://github.com/bhklab/bhklab-project-template/issues/24)) ([1d897ac](https://github.com/bhklab/bhklab-project-template/commit/1d897ac6ddd5875f8bc7725817d1556e30615928))


### Documentation

* Enhance documentation with new sections and troubleshooting guide ([dafdcac](https://github.com/bhklab/bhklab-project-template/commit/dafdcaceb52ebcd250125056c026047d803bd8ef))
* Update README to include usage instructions for `uv` and `copier` ([7127124](https://github.com/bhklab/bhklab-project-template/commit/7127124446155aca03de772d3f3fd97cbfbf5bfb))

## [0.8.0](https://github.com/bhklab/bhklab-project-template/compare/v0.7.0...v0.8.0) (2025-05-20)


### Features

* Add environment variables and example usage scripts ([#8](https://github.com/bhklab/bhklab-project-template/issues/8)) ([78758d1](https://github.com/bhklab/bhklab-project-template/commit/78758d10e2aa3d08ef966b7d3fa17326bdb8d391))

## [0.7.0](https://github.com/bhklab/bhklab-project-template/compare/v0.6.0...v0.7.0) (2025-05-12)


### Features

* dont hatch configure ([720632e](https://github.com/bhklab/bhklab-project-template/commit/720632e04f4053e6bee81877e179a9dd75df2da3))

## [0.6.0](https://github.com/bhklab/bhklab-project-template/compare/v0.5.6...v0.6.0) (2025-05-12)


### Features

* update build to hatch ([2067a86](https://github.com/bhklab/bhklab-project-template/commit/2067a8628d95f0726b5756e33ddc6183b2953892))

## [0.5.6](https://github.com/bhklab/bhklab-project-template/compare/v0.5.5...v0.5.6) (2025-05-12)


### Bug Fixes

* update dependency name in pixi.toml to use hyphen instead of underscore ([38e9c85](https://github.com/bhklab/bhklab-project-template/commit/38e9c85ffb9ed2e926271be67ebe9583f8d844b8))

## [0.5.5](https://github.com/bhklab/bhklab-project-template/compare/v0.5.4...v0.5.5) (2025-05-12)


### Bug Fixes

* correct script name in pyproject.toml ([6a164ec](https://github.com/bhklab/bhklab-project-template/commit/6a164ec2fcd96dc0ae993af5fa5c64d4fdfd6b9a))

## [0.5.4](https://github.com/bhklab/bhklab-project-template/compare/v0.5.3...v0.5.4) (2025-05-12)


### Bug Fixes

* add wheel and sdist targets to build configuration ([3868184](https://github.com/bhklab/bhklab-project-template/commit/3868184be8cc23c9fe0ed574ff843764184fbe4f))
* update sha256 checksum and add LICENSE file ([fa33b17](https://github.com/bhklab/bhklab-project-template/commit/fa33b1747488a4209bed446d253fea4f30815f71))

## [0.5.3](https://github.com/bhklab/bhklab-project-template/compare/v0.5.2...v0.5.3) (2025-05-12)


### Bug Fixes

* add id-token permission for GitHub Actions ([66a91e1](https://github.com/bhklab/bhklab-project-template/commit/66a91e13b2c72f4381ded61f24e88da622ddf4f1))
* correct indentation and streamline publish-pypi job steps ([5e9cacd](https://github.com/bhklab/bhklab-project-template/commit/5e9cacd137e6a46ac8ae712b785cce1b123dd569))
* update project metadata and add type hinting support ([5a6649d](https://github.com/bhklab/bhklab-project-template/commit/5a6649da2696c8fff9a8f6331ba99389f254f6b4))
* update project version to 0.5.2 and sha256 checksum ([defd4c3](https://github.com/bhklab/bhklab-project-template/commit/defd4c3eecb4a051b3be1977b4b43fcbfab69a10))

## [0.5.2](https://github.com/bhklab/bhklab-project-template/compare/v0.5.1...v0.5.2) (2025-05-12)


### Bug Fixes

* dont lock ([2832d1c](https://github.com/bhklab/bhklab-project-template/commit/2832d1ced3268f962e6a43ff4fb6d69fca1a47b7))

## [0.5.1](https://github.com/bhklab/bhklab-project-template/compare/v0.5.0...v0.5.1) (2025-05-12)


### Bug Fixes

* move default ([f932f8c](https://github.com/bhklab/bhklab-project-template/commit/f932f8c04d134e903474c948beb2404ec721652d))

## [0.5.0](https://github.com/bhklab/bhklab-project-template/compare/v0.4.0...v0.5.0) (2025-05-12)


### Features

* Add BHKLab project template CLI tool ([#12](https://github.com/bhklab/bhklab-project-template/issues/12)) ([4209392](https://github.com/bhklab/bhklab-project-template/commit/4209392626923eb0147de6013367cebc1321e2e0))
* Add lockfile update step in release workflow ([daece9c](https://github.com/bhklab/bhklab-project-template/commit/daece9c356b5063c0ed183345d831caef5e54d96))

## [0.4.0](https://github.com/bhklab/bhklab-project-template/compare/v0.3.1...v0.4.0) (2025-05-10)


### Features

* update project_name and project_description placeholders for dynamic values ([ca80e5f](https://github.com/bhklab/bhklab-project-template/commit/ca80e5ff457e44a951589b8da5e72147883f2821))

## [0.3.1](https://github.com/bhklab/bhklab-project-template/compare/v0.3.0...v0.3.1) (2025-05-10)


### Bug Fixes

* ascii art ([3ca1013](https://github.com/bhklab/bhklab-project-template/commit/3ca1013311614640fa9dae48c482cf8c1f72009d))

## [0.3.0](https://github.com/bhklab/bhklab-project-template/compare/v0.2.0...v0.3.0) (2025-05-09)


### Features

* add release command for initial alpha version in project setup ([6988526](https://github.com/bhklab/bhklab-project-template/commit/6988526be15970a69d0d19612b9796963f5d3164))

## [0.2.0](https://github.com/bhklab/bhklab-project-template/compare/v0.1.0...v0.2.0) (2025-05-09)


### Features

* add support for multiple authors in project templates ([47e3ae8](https://github.com/bhklab/bhklab-project-template/commit/47e3ae847bfe41e025b7603ef6cb02fdd0ca8a33))
* enhance project generator messages and structure setup tasks ([f83c0cd](https://github.com/bhklab/bhklab-project-template/commit/f83c0cde76221e183797cab03509c34f8c18cfb9))
