# Weight sources for the SGM rerun

`pretrainedmodels` 0.7.4 downloads `densenet201` and `senet154` from `data.lip6.fr`, whose TLS certificate had expired by September 2026. The first-pass review of rank 13 also recorded that this mirror failed. Neither file was fetched with TLS verification disabled. Both came from Internet Archive captures of the original URLs, and each full SHA-256 was checked against the hash prefix that `pretrainedmodels` and torch hub embed in the filename:

| File | Capture | Bytes | SHA-256 |
| --- | --- | --- | --- |
| `densenet201-5750cbb1e.pth` | `https://web.archive.org/web/2020id_/http://data.lip6.fr/cadene/pretrainedmodels/densenet201-5750cbb1e.pth` | 81,139,790 | `5750cbb1e5c09dc6ed5f4daa6583d7e652b090d5cdbeeecb9393e2b774f07930` |
| `senet154-c7b49a05.pth` | `https://web.archive.org/web/20191202105854id_/https://data.lip6.fr/cadene/pretrainedmodels/senet154-c7b49a05.pth` | 461,488,402 | `c7b49a056b98b0bed65b0237c27acdead655e599669215573d357ad337460413` |

Later SENet-154 captures, from 2021 onwards (digest `AMRFM6…`), is a truncated file of about 1 MB. Its hash does not match, and it was discarded.

The other `pretrainedmodels` weights (`resnet152`, `vgg19`, `vgg19_bn`) come from `download.pytorch.org`. Their hashes are recorded in the run manifest.

`pretrainedmodels` loads checkpoints through `torch.hub.load_state_dict_from_url`, which defaults to `weights_only=False`, so a full unpickle runs. Before evaluation, every cached checkpoint was therefore loaded separately with `torch.load(..., weights_only=True)`. A file that passes references only the allowed tensor and container types, so the full unpickle cannot execute anything else. `densenet201`, `senet154`, `inception_v3_google` and the others passed. `resnet152-b121ed2d.pth` is in the legacy tar format, which the restricted loader cannot read. It was downloaded over valid TLS from `download.pytorch.org`, and its SHA-256 begins with the `b121ed2d` prefix in its filename.
